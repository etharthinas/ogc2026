#!/usr/bin/env python3
"""Capture a fresh v25 solution: run the real algorithm() from myalgorithm.py
(the v25 SOTA) on train/prob_<k>.json at a given timelimit, verify the banked
objective via utils.check_feasibility, and save the returned operations->assign
dict as <out>. Keeps a __main__ guard (Windows spawn re-imports __main__)."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm as M
from utils import check_feasibility


def ops_to_assign(ops):
    assign = {}
    for t_str, oplist in ops.items():
        t = int(t_str)
        for op in oplist:
            bi = int(op["block_id"])
            a = assign.setdefault(bi, {"block_id": bi})
            if op["type"] == "ENTRY":
                a["bay_id"] = int(op["bay_id"]); a["x"] = int(op["x"])
                a["y"] = int(op["y"]); a["orient_idx"] = int(op["orient_idx"])
                a["entry_time"] = t
            else:
                a["exit_time"] = t
    return assign


def main():
    k = int(sys.argv[1]); secs = float(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else f"v25_{k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    t0 = time.time()
    sol = M.algorithm(prob, secs)
    el = time.time() - t0
    res = check_feasibility(prob, sol)
    assign = ops_to_assign(sol["operations"])
    print(f"v25 prob_{k} = {res.get('objective'):,.0f}  ({el:.1f}s)  "
          f"feasible={res.get('feasible')} obj1={res.get('obj1')} "
          f"nblocks={len(assign)}", flush=True)
    json.dump({str(bi): v for bi, v in assign.items()},
              open(os.path.join(HERE, out), "w"))
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
