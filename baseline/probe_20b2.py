#!/usr/bin/env python3
"""20b-2 ablation: near cells COMPETING in the main contact-ranked pass
(nm_compete=True) vs v20a fallback-only (False). Deterministic single
dispatches (rng=None), nm=8 + beam, over the per-instance grid configs.

Usage: python probe_20b2.py [--probs 31,39,33,27] [--imp 0]
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm as m  # noqa: E402
from utils import Bay, check_feasibility  # noqa: E402

CONFIGS = ((0.5, 0.5), (2.0, 0.5), (0.5, 1.0), (1.0, 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probs", default="31,39,33,27")
    args = ap.parse_args()

    for k in [int(x) for x in args.probs.split(",")]:
        prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
        m._reset_caches()
        bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
        blocks_data = prob["blocks"]
        w = prob.get("weights", {})
        w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
        bay_u = m._bay_u(bays)
        raster = m._Raster(prob, bays)

        def iobj(a):
            return m._objective(a, blocks_data, bays, bay_u, w1, w2, w3)[0]

        best = {False: None, True: None}
        for kap, al in CONFIGS:
            for compete in (False, True):
                raster.reset()
                t0 = time.time()
                a = m._dispatch_construct(prob, bays, bay_u, w1, w2, w3,
                                          time.time() + 600, raster,
                                          kappa=kap, gamma=0.5, alpha=al,
                                          score_pos=True, beam=True,
                                          nearmiss=8, nm_compete=compete)
                o = iobj(a)
                if best[compete] is None or o < best[compete][0]:
                    best[compete] = (o, a)
                print(f"prob_{k} (k={kap}, a={al}) "
                      f"{'COMPETE' if compete else 'fallback'}: {o:,.0f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        oF, oT = best[False][0], best[True][0]
        res = check_feasibility(
            prob, {"operations": m._build_operations(best[True][1])})
        print(f"BEST prob_{k}: fallback={oF:,.0f}  compete={oT:,.0f}  "
              f"delta={oT - oF:+,.0f}  compete_official="
              f"{res.get('objective') if res.get('feasible') else 'INFEASIBLE'}",
              flush=True)


if __name__ == "__main__":
    main()
