#!/usr/bin/env python3
"""From a saved incumbent, run one acceptance variant of _improve and report.
Variants: greedy (obj-gated, default), sa (simulated-annealing acceptance,
the wired-but-unused uphill path). Isolates the acceptance rule using the
EXISTING improver machinery (no new move code).

Usage: python accept_test.py <k> <incumbent.json> <secs> <mode> <seed>
  mode: greedy | sa
"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
from utils import check_feasibility


def main():
    k = int(sys.argv[1]); inc = sys.argv[2]; secs = float(sys.argv[3])
    mode = sys.argv[4] if len(sys.argv) > 4 else "greedy"
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 4242
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    M._reset_caches()
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bd = prob["blocks"]; w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bu = M._bay_u(bays); forced = M._is_forced(prob, bays)
    raster = M._Raster(prob, bays) if M._HAVE_NUMPY else None
    start = {int(bi): v for bi, v in json.load(open(os.path.join(HERE, inc))).items()}
    start_obj = M._objective(start, bd, bays, bu, w1, w2, w3)[0]
    print(f"prob_{k}: start={start_obj:,.0f} mode={mode} seed={seed} forced={forced}",
          flush=True)
    t0 = time.time()
    a, o = M._improve(prob, start, bays, bu, w1, w2, w3, t0 + secs, forced,
                      seed=seed, sa=(mode == "sa"), raster=raster,
                      repack_every=3, xbay=forced, deep=False)
    el = time.time() - t0
    sol = {"operations": M._build_operations(a)}
    res = check_feasibility(prob, sol)
    print(f"{mode.upper():>7} = {o:>14,.0f}  ({el:.1f}s) d_start={o-start_obj:+,.0f} "
          f"feasible={res.get('feasible')}", flush=True)


if __name__ == "__main__":
    main()
