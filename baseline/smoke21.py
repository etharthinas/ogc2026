import sys, json, time
sys.path.insert(0, '.')
import myalgorithm_25 as M
from utils import check_feasibility

if __name__ == "__main__":
    prob = json.load(open('../train/prob_31.json'))
    t0 = time.time()
    sol = M.algorithm(prob, 90)
    res = check_feasibility(prob, sol)
    print('smoke 31@90s:', res['feasible'], f"{res['objective']:,.0f}",
          f'{time.time()-t0:.0f}s', flush=True)
