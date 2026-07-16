import json
import os
import sys
import time

if __name__ == "__main__":
    import myalgorithm_33 as v
    from utils import check_feasibility
    path = sys.argv[1] if len(sys.argv) > 1 else "../train/prob_1.json"
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    prob = json.load(open(path))
    t = time.time()
    sol = v.algorithm(prob, tl)
    dt = time.time() - t
    r = check_feasibility(prob, sol)
    print(f"[drive33] {os.path.basename(path)} tl={tl} elapsed={dt:.1f}s "
          f"feasible={r['feasible']} obj={r.get('objective')}", flush=True)
