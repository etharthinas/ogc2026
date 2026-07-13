#!/usr/bin/env python3
"""Run the real v18 4-worker algorithm() on an instance, convert its returned
operations dict back to an internal assignment dict, and save it. This gives
LAHC/acceptance experiments the TRUE banked basin to start from."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
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
    out = sys.argv[3] if len(sys.argv) > 3 else f"v18_{k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    t0 = time.time()
    sol = M.algorithm(prob, secs)
    el = time.time() - t0
    res = check_feasibility(prob, sol)
    assign = ops_to_assign(sol["operations"])
    print(f"v18 prob_{k} = {res.get('objective'):,.0f}  ({el:.1f}s)  "
          f"feasible={res.get('feasible')} obj1={res.get('obj1')} "
          f"nblocks={len(assign)}", flush=True)
    json.dump({str(bi): v for bi, v in assign.items()},
              open(os.path.join(HERE, out), "w"))
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
