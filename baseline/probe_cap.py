#!/usr/bin/env python3
"""Signal probe: cand_cap widening (exact-gate budget per bay/orient) on the
giant rocks. ledger_27_diag measured feasible-placement fraction 0.25-0.29%
with the production caps; diag_v25's exhaustive 400-anchor scan found strictly
more room (lenient 0.57-1.01%). If admissions are being missed purely by the
cap cliff, raw totals drop with a bigger cap. cap 12 -> cap_for deep = 48;
cap 48 -> 192. Pure param, no new code path.

Usage: python probe_cap.py [prob_indices...]   (default: 38 27)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [38, 27]
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, gam, al, cap,
                 budget=150.0):
    raster.reset()
    raster.near_k = 3
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=True,
                              nearmiss=8, cand_cap=cap)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


def probe(k):
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    raster = M._Raster(prob, bays)
    print(f"\nprob_{k}: w1={w1}", flush=True)
    best = None
    for (kap, gam, al) in CONFIGS:
        try:
            t0, o1_0, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                          raster, kap, gam, al, 12)
            t1, o1_1, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                          raster, kap, gam, al, 48)
        except Exception as e:
            print(f"  cfg(k={kap},a={al}): ERR {type(e).__name__}: {e}",
                  flush=True)
            continue
        d = t1 - t0
        print(f"  cfg(k={kap},a={al}): cap12={t0:,.0f}(o1={o1_0:,.0f}) "
              f"cap48={t1:,.0f}(o1={o1_1:,.0f}) d={d:+,.0f}", flush=True)
        if best is None or d < best:
            best = d
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best cap delta = {best:+,.0f}  [{verdict}]", flush=True)
    return k, best, verdict


if __name__ == "__main__":
    idx = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT
    rows = []
    for k in idx:
        try:
            rows.append(probe(k))
        except Exception as e:
            print(f"prob_{k}: FATAL {type(e).__name__}: {e}", flush=True)
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY (cap48 vs cap12, best config, raw dispatch):", flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
