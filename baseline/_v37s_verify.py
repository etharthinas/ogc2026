import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_37s as M
from utils import check_feasibility

def main():
    k = int(sys.argv[1]); secs = float(sys.argv[2])
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    t0 = time.time()
    sol = M.algorithm(prob, secs)
    el = time.time() - t0
    res = check_feasibility(prob, sol)
    print(f"V37S prob_{k} = {res.get('objective'):,.0f} ({el:.1f}s) feasible={res.get('feasible')} obj1={res.get('obj1')}", flush=True)

if __name__ == "__main__":
    main()
