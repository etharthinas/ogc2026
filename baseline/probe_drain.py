#!/usr/bin/env python3
"""Signal probe: DRAIN LOOKAHEAD (untried joint order+geometry) on the giants.

At each admission, pick the passing placement that leaves the most of the next
`drain` most-urgent queued blocks still placeable -- a 1-step joint order+
geometry step directly targeting queue-drain rate (ledger_27_diag: 100% of
giant obj1 is entry-delay; jay's order-forcing 29a-d was schedule-level and
geometry-blind -- this is per-placement and geometry-exact).

Isolates the drain effect on the NON-beam constructor: beam=False, drain=0 vs
drain in {6,10}. If drain sharply cuts raw obj1, wire it into beam_admit next.

Usage: python probe_drain.py [prob_indices...]   (default 38 27 39)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [38, 27, 39]
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, gam, al, drain,
                 budget=150.0):
    raster.reset()
    raster.near_k = 3
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=False,
                              nearmiss=8, drain=drain)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


def probe(k):
    M._reset_caches()
    M._MREL.clear()
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
                                          raster, kap, gam, al, 0)
            row = f"  cfg(k={kap},a={al}): d0={t0:,.0f}(o1={o1_0:,.0f})"
            for dm in (6, 10):
                td, o1_d, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                              raster, kap, gam, al, dm)
                d = td - t0
                row += f" | d{dm}={td:,.0f}(o1={o1_d:,.0f}) delta={d:+,.0f}"
                if best is None or d < best:
                    best = d
            print(row, flush=True)
        except Exception as e:
            print(f"  cfg(k={kap},a={al}): ERR {type(e).__name__}: {e}",
                  flush=True)
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best drain delta = {best:+,.0f}  [{verdict}]", flush=True)
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
    print("SUMMARY (drain vs off, best config, raw non-beam dispatch):",
          flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
