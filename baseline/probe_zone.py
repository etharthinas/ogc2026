#!/usr/bin/env python3
"""Signal probe: TEMPORAL ZONING (exit-cohort co-location) on the burst giants.

Mechanism (untried in either graveyard): fragmentation on 38/27 comes from
temporally scattered exits nibbling the floor into unusable holes. Zoning
re-ranks the top-K contact cells to prefer neighbors exiting near the new
block's exit_t, so each exit wave frees one LARGE contiguous region -> faster
queue drain -> lower entry-delay tardiness (100% of giant obj1).

zone=0 (off) vs zone in {12, 24}. Uses the FIXED probe harness (per-instance
cache reset). Usage: python probe_zone.py [prob_indices...] (default 38 27 39 31)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [38, 27, 39, 31]
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, gam, al, zone,
                 budget=150.0):
    raster.reset()
    raster.near_k = 3
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=True,
                              nearmiss=8, zone=zone)
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
            row = f"  cfg(k={kap},a={al}): z0={t0:,.0f}(o1={o1_0:,.0f})"
            for z in (12, 24):
                tz, o1_z, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                              raster, kap, gam, al, z)
                d = tz - t0
                row += f" | z{z}={tz:,.0f}(o1={o1_z:,.0f}) d={d:+,.0f}"
                if best is None or d < best:
                    best = d
            print(row, flush=True)
        except Exception as e:
            print(f"  cfg(k={kap},a={al}): ERR {type(e).__name__}: {e}",
                  flush=True)
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best zone delta = {best:+,.0f}  [{verdict}]", flush=True)
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
    print("SUMMARY (zone vs off, best config, raw dispatch):", flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
