#!/usr/bin/env python3
"""20b-1 A/B probe: does threading near-miss into the improver's reinsert
paths turn polish on nm builds from retime-only (+0, measured twice in
heuristic_20) into a real gain?

Build ONE nm+beam construction (the v20 W1 explorer's recipe, per-instance
grid-winner kappa/alpha), then improve two fresh copies with the SAME seed:
  A: nearmiss=0 (v20a behaviour — repack/reinsert see conservative masks)
  B: nearmiss=8 (20b-1 — reinsert paths recover near-miss anchors)
Identical seeds isolate the nm effect. B's result is officially verified.

Usage: python probe_20b.py --prob 31 [--kappa 0.5 --alpha 0.5] [--imp 150]
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prob", type=int, required=True)
    ap.add_argument("--kappa", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--imp", type=float, default=150.0)
    ap.add_argument("--seed", type=int, default=4242)
    args = ap.parse_args()

    prob = json.load(open(os.path.join(TRAIN, f"prob_{args.prob}.json")))
    m._reset_caches()
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    blocks_data = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = m._bay_u(bays)
    forced = m._is_forced(prob, bays)
    raster = m._Raster(prob, bays)

    def iobj(a):
        return m._objective(a, blocks_data, bays, bay_u, w1, w2, w3)[0]

    t0 = time.time()
    a0 = m._dispatch_construct(prob, bays, bay_u, w1, w2, w3,
                               time.time() + 600, raster, kappa=args.kappa,
                               gamma=0.5, alpha=args.alpha, score_pos=True,
                               beam=True, nearmiss=8)
    o0 = iobj(a0)
    print(f"prob_{args.prob} nm+beam build (k={args.kappa}, a={args.alpha}): "
          f"{o0:,.0f}  ({time.time()-t0:.0f}s)", flush=True)

    results = {}
    for label, nm in (("A nm=0", 0), ("B nm=8", 8)):
        src = {k: dict(v) for k, v in a0.items()}
        t1 = time.time()
        r, o = m._improve(prob, src, bays, bay_u, w1, w2, w3,
                          time.time() + args.imp, forced, seed=args.seed,
                          raster=raster, repack_every=3, nearmiss=nm)
        results[label] = (o, r)
        print(f"  improve {args.imp:.0f}s {label}: {o0:,.0f} -> {o:,.0f} "
              f"(delta {o - o0:+,.0f})  ({time.time()-t1:.0f}s)", flush=True)

    oA, oB = results["A nm=0"][0], results["B nm=8"][0]
    rB = results["B nm=8"][1]
    res = check_feasibility(prob, {"operations": m._build_operations(rB)})
    print(f"VERDICT prob_{args.prob}: A(nm=0)={oA:,.0f}  B(nm=8)={oB:,.0f}  "
          f"B-A={oB - oA:+,.0f}  B_official="
          f"{res.get('objective') if res.get('feasible') else 'INFEASIBLE'}",
          flush=True)


if __name__ == "__main__":
    main()
