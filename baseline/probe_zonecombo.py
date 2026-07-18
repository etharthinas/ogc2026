#!/usr/bin/env python3
"""Combination probe: temporal zoning x {deep-nestle nk32, nm_compete} on the
giants where zone broke the absolute frontier (39, 31) + 38. Finds the
max-absolute-value config to deliver as a deep-pipeline seed build.

Usage: python probe_zonecombo.py [prob_indices...]   (default 39 31 38)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [39, 31, 38]
# (kappa, alpha) hot pair per prior probes
KA = [(0.5, 0.5), (1.0, 0.0)]
# variants: (label, nk, cmp, zone)
VARIANTS = [
    ("base",        3,  False, 0),
    ("z12",         3,  False, 12),
    ("z24",         3,  False, 24),
    ("nk32",        32, False, 0),
    ("nk32+z12",    32, False, 12),
    ("nk32+z24",    32, False, 24),
    ("cmp+z12",     3,  True,  12),
    ("cmp+z24",     3,  True,  24),
]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, al, nk, cmp,
                 zone, budget=150.0):
    raster.reset()
    raster.near_k = nk
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=0.5, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=True,
                              nearmiss=8, nm_compete=cmp, zone=zone)
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
    best = (None, None, None)
    for (kap, al) in KA:
        for (lab, nk, cmp, zone) in VARIANTS:
            try:
                t0, o1_0, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                              raster, kap, al, nk, cmp, zone)
            except Exception as e:
                print(f"  k={kap},a={al},{lab}: ERR {type(e).__name__}: {e}",
                      flush=True)
                continue
            print(f"  k={kap},a={al},{lab}: {t0:,.0f} (o1={o1_0:,.0f})",
                  flush=True)
            if best[0] is None or t0 < best[0]:
                best = (t0, f"k={kap},a={al},{lab}", o1_0)
    print(f"  => ABS BEST: {best[1]} = {best[0]:,.0f} (o1={best[2]:,.0f})",
          flush=True)
    return k, best


if __name__ == "__main__":
    idx = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT
    rows = []
    for k in idx:
        try:
            rows.append(probe(k))
        except Exception as e:
            print(f"prob_{k}: FATAL {type(e).__name__}: {e}", flush=True)
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY (absolute best config per instance):", flush=True)
    for k, best in rows:
        print(f"  prob_{k:>2}: {best[1]} = {best[0]:,.0f}", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
