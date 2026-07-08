#!/usr/bin/env python3
"""Warm a converged single-worker incumbent for an instance and save the
assignment to JSON, so LAHC/acceptance experiments can reuse it without
re-warming. Prints the converged objective (the greedy basin to beat)."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
from utils import check_feasibility


def main():
    k = int(sys.argv[1])
    secs = float(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else f"warm_{k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    M._reset_caches()
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    blocks_data = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = M._bay_u(bays)
    forced = M._is_forced(prob, bays)
    raster = M._Raster(prob, bays) if M._HAVE_NUMPY else None
    t0 = time.time()
    dl = t0 + secs
    # best of a few constructions
    orders = [M._area_order(blocks_data), M._edd_order(blocks_data),
              M._congestion_order(blocks_data)]
    best_a, best_o = None, float("inf")
    cdl = t0 + min(secs * 0.25, 60.0)
    for order in orders:
        a = M._construct(prob, order, bays, bay_u, w1, w2, w3, t0, cdl,
                         forced=forced)
        o = M._objective(a, blocks_data, bays, bay_u, w1, w2, w3)[0]
        if o < best_o:
            best_a, best_o = a, o
    print(f"construct best = {best_o:,.0f} ({time.time()-t0:.1f}s)", flush=True)
    # improve to convergence with repack (mirrors W2 giant/forced polish)
    a, o = M._improve(prob, best_a, bays, bay_u, w1, w2, w3, dl, forced,
                      seed=2222, raster=raster, repack_every=3, xbay=forced,
                      deep=False)
    el = time.time() - t0
    sol = {"operations": M._build_operations(a)}
    res = check_feasibility(prob, sol)
    print(f"WARM prob_{k} = {o:,.0f}  ({el:.1f}s)  feasible={res.get('feasible')}"
          f"  obj1={res.get('obj1')}", flush=True)
    json.dump({str(bi): v for bi, v in a.items()},
              open(os.path.join(HERE, out), "w"))
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
