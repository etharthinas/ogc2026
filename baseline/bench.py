#!/usr/bin/env python3
"""Benchmark harness for the OGC2026 algorithm.

Usage:
  python bench.py <module> <timelimit> [prob_indices...]
    <module>     e.g. myalgorithm  or  myalgorithm_5
    <timelimit>  per-instance wall seconds
    [indices]    optional list of problem numbers (1..40); default = all 40

Prints per-instance objective + feasibility and the running total. Verifies
every solution with the official utils.check_feasibility.
"""
import sys, os, json, time, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

from utils import check_feasibility  # noqa: E402


def run(mod_name, timelimit, indices):
    mod = importlib.import_module(mod_name)
    total = 0.0
    n_feas = 0
    results = {}
    for k in indices:
        path = os.path.join(TRAIN, f"prob_{k}.json")
        with open(path) as f:
            prob = json.load(f)
        t0 = time.time()
        try:
            sol = mod.algorithm(prob, timelimit)
        except Exception as e:
            print(f"prob_{k:>2}: CRASH {type(e).__name__}: {e}", flush=True)
            results[k] = ("CRASH", None)
            continue
        elapsed = time.time() - t0
        res = check_feasibility(prob, sol)
        feas = res.get("feasible", False)
        obj = res.get("objective")
        if feas:
            n_feas += 1
            total += obj
            results[k] = ("PASS", obj)
            print(f"prob_{k:>2}: {obj:>14,.0f}  ({elapsed:5.1f}s)  "
                  f"obj1={res.get('obj1')} obj2={res.get('obj2')} obj3={res.get('obj3')}",
                  flush=True)
        else:
            results[k] = ("FAIL", res.get("stage"))
            print(f"prob_{k:>2}: INFEASIBLE stage={res.get('stage')} ({elapsed:5.1f}s)",
                  flush=True)
    print("-" * 60, flush=True)
    print(f"TOTAL (feasible only) = {total:,.0f}   feasible {n_feas}/{len(indices)}",
          flush=True)
    return results, total


if __name__ == "__main__":
    mod_name = sys.argv[1] if len(sys.argv) > 1 else "myalgorithm"
    timelimit = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    if len(sys.argv) > 3:
        indices = [int(x) for x in sys.argv[3:]]
    else:
        indices = list(range(1, 41))
    run(mod_name, timelimit, indices)
