#!/usr/bin/env python3
"""Run a module over all 40 (or given) instances, print per-instance results
AND a results.csv-style row `label,v1,...,v40,total`."""
import sys, os, json, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)
from utils import check_feasibility

# Keep Windows awake for the whole benchmark (sleep mid-run corrupts results:
# the algorithm's time.time() deadline checks fire immediately on wake and it
# returns an incomplete solution). ES_CONTINUOUS | ES_SYSTEM_REQUIRED.
try:
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
except Exception:
    pass

def main():
    mod_name = sys.argv[1]
    timelimit = float(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) > 3 else mod_name
    indices = list(range(1, 41))
    mod = importlib.import_module(mod_name)
    vals = {}
    total = 0.0; nfeas = 0
    for k in indices:
        prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
        t0 = time.time()
        try:
            sol = mod.algorithm(prob, timelimit)
            res = check_feasibility(prob, sol)
        except Exception as e:
            print(f"prob_{k:>2}: CRASH {type(e).__name__}: {e}", flush=True)
            vals[k] = None; continue
        el = time.time() - t0
        if res.get("feasible"):
            obj = res["objective"]; vals[k] = obj; total += obj; nfeas += 1
            print(f"prob_{k:>2}: {obj:>14,.0f}  ({el:5.1f}s)  obj1={res.get('obj1')}", flush=True)
        else:
            vals[k] = None
            print(f"prob_{k:>2}: INFEASIBLE stage={res.get('stage')} ({el:5.1f}s)", flush=True)
    print("-"*60, flush=True)
    print(f"TOTAL = {total:,.0f}   feasible {nfeas}/40", flush=True)
    row = label + "," + ",".join(str(int(vals[k])) if vals.get(k) is not None else "" for k in indices) + f",{int(total)}"
    print("CSVROW " + row, flush=True)

if __name__ == "__main__":
    main()
