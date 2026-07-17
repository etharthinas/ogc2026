#!/usr/bin/env python3
"""Fair head-to-head with both weighted and w1-lexicographic comparisons.

For each instance run modA then modB at the same wall limit (adjacent in time,
without cross-run contention).  The lexicographic winner is determined by
``(obj1, w2*obj2 + w3*obj3)``; the ordinary official-objective delta is retained
for historical result rows.
"""
import sys, os, json, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from utils import check_feasibility
try:  # keep Windows awake for the whole run (sleep mid-run corrupts results)
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
except Exception:
    pass

def one(mod, prob, tl):
    t0 = time.time()
    sol = mod.algorithm(prob, tl)
    el = time.time() - t0
    res = check_feasibility(prob, sol)
    return res, el

def lex_key(prob, res):
    if not res.get("feasible"):
        return (float("inf"), float("inf"))
    w = prob.get("weights", {})
    residual = w.get("w2", 1.0) * res["obj2"] + w.get("w3", 1.0) * res["obj3"]
    return (res["obj1"], residual)

def brief(res):
    if not res.get("feasible"):
        return "INFEASIBLE"
    return (f"total={res['objective']:,.0f} z1={res['obj1']:.0f} "
            f"z2={res['obj2']:.0f} z3={res['obj3']:.0f}")

if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    tl = float(sys.argv[3])
    idx = [int(x) for x in sys.argv[4:]]
    mA = importlib.import_module(a); mB = importlib.import_module(b)
    tot = {a: 0.0, b: 0.0}
    z1tot = {a: 0.0, b: 0.0}
    lexwins = {a: 0, b: 0, "tie": 0}
    for k in idx:
        prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
        ra, ea = one(mA, prob, tl)
        rb, eb = one(mB, prob, tl)
        if ra.get("feasible"):
            tot[a] += ra["objective"]; z1tot[a] += ra["obj1"]
        if rb.get("feasible"):
            tot[b] += rb["objective"]; z1tot[b] += rb["obj1"]
        ka, kb = lex_key(prob, ra), lex_key(prob, rb)
        winner = a if ka < kb else b if kb < ka else "tie"
        lexwins[winner] += 1
        d = ((ra["objective"] - rb["objective"])
             if ra.get("feasible") and rb.get("feasible") else float("nan"))
        print(f"prob_{k:>2}: {a}[{brief(ra)}] ({ea:.1f}s)", flush=True)
        print(f"         {b}[{brief(rb)}] ({eb:.1f}s) | lex={winner} "
              f"weighted_delta(A-B)={d:+,.0f}", flush=True)
    print("-"*90, flush=True)
    print(f"{a} total={tot[a]:,.0f}   {b} total={tot[b]:,.0f}   "
          f"improvement={tot[a]-tot[b]:+,.0f}", flush=True)
    print(f"obj1 sums: {a}={z1tot[a]:,.0f} {b}={z1tot[b]:,.0f} | "
          f"lex wins {a}={lexwins[a]} {b}={lexwins[b]} ties={lexwins['tie']}", flush=True)
    # Orphaned portfolio workers keep the interpreter alive after all output
    # is written; hard-exit so batch chains never hang between steps.
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
