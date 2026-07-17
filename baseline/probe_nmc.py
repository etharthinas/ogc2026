#!/usr/bin/env python3
"""Signal probe: does 20b-2's nm_compete (near-miss anchors compete in the
dispatcher's MAIN contact-ranked pass) still add value on the v33/jv6 lineage,
whose deep-nestle near_k family already recovers near-miss anchors on failure?

Original raw ablation (v20 base, dev/jiyoon): 31 -278k / 39 -1,471k / 33 -563k
/ 27 +50k; end-to-end 38 -2.32M. v25's deep-nestle may have absorbed part of
this. This probe re-measures RAW on the jv6b machinery: nearmiss=8+beam with
nm_compete False vs True, plus the deep near_k variants (16/32) the v25 family
uses, since compete may stack with deeper near sets.

Usage: python probe_nmc.py [prob_indices...]   (default: 38 27 39 31 33 26)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [38, 39, 27, 31]     # 39/31 = original-ablation signal cells
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, gam, al,
                 nm, nk, cmp, budget=150.0):
    raster.reset()
    raster.near_k = nk
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=True,
                              nearmiss=nm, nm_compete=cmp)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


def probe(k):
    # CRITICAL (2026-07-18): module caches (_BLK/_CC/_CE/_CX/_MREL) are
    # keyed by block_id, NOT instance -- multi-instance probe processes
    # cross-contaminate geometry without this reset. Every cross-instance
    # probe number produced before this fix is GARBAGE (only each
    # process's FIRST instance was clean).
    M._reset_caches()
    M._MREL.clear()
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    raster = M._Raster(prob, bays)

    print(f"\nprob_{k}: w1={w1} w3={w3}", flush=True)
    best = None
    for (kap, gam, al) in CONFIGS:
        for nk in (3, 32):
            try:
                t0, o1_0, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                              raster, kap, gam, al, 8, nk,
                                              False)
                t1, o1_1, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                              raster, kap, gam, al, 8, nk,
                                              True)
            except Exception as e:
                print(f"  cfg(k={kap},a={al},nk={nk}): ERR "
                      f"{type(e).__name__}: {e}", flush=True)
                continue
            d = t1 - t0
            print(f"  cfg(k={kap},a={al},nk={nk}): off={t0:,.0f}"
                  f"(o1={o1_0:,.0f}) cmp={t1:,.0f}(o1={o1_1:,.0f}) "
                  f"d={d:+,.0f}", flush=True)
            if best is None or d < best:
                best = d
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best nm_compete delta = {best:+,.0f}  [{verdict}]",
          flush=True)
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
    print("SUMMARY (nm_compete on vs off, best config, raw dispatch):",
          flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
