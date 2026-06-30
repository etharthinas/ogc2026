#!/usr/bin/env python3
"""Fair head-to-head: for each instance run modA then modB at the same time
limit (adjacent in time, single-thread, no contention) and print both + delta."""
import sys, os, json, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from utils import check_feasibility

def one(mod, prob, tl):
    t0 = time.time()
    sol = mod.algorithm(prob, tl)
    el = time.time() - t0
    res = check_feasibility(prob, sol)
    return res.get("feasible"), res.get("objective"), res.get("obj1"), el

if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    tl = float(sys.argv[3])
    idx = [int(x) for x in sys.argv[4:]]
    mA = importlib.import_module(a); mB = importlib.import_module(b)
    tot = {a: 0.0, b: 0.0}
    for k in idx:
        prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
        fa, oa, t1a, ea = one(mA, prob, tl)
        fb, ob, t1b, eb = one(mB, prob, tl)
        if fa: tot[a] += oa
        if fb: tot[b] += ob
        d = (oa - ob) if (fa and fb) else float('nan')
        pct = (d / oa * 100) if (fa and fb and oa) else 0.0
        print(f"prob_{k:>2}: {a}={oa:>13,.0f}(t1={t1a:.0f}) | {b}={ob:>13,.0f}(t1={t1b:.0f}) "
              f"| delta={d:>+12,.0f} ({pct:+.1f}%)", flush=True)
    print("-"*90, flush=True)
    print(f"{a} total={tot[a]:,.0f}   {b} total={tot[b]:,.0f}   "
          f"improvement={tot[a]-tot[b]:+,.0f}", flush=True)
