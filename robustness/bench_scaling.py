#!/usr/bin/env python3
"""Timelimit-scaling spot bench: does the solver degrade gracefully when the
server hands it a SHORT (or long) timelimit?

The contest passes `timelimit` per instance ("a few minutes to half an hour",
undisclosed). Our results.csv convention is 600s, so this script checks the
other operating points: for each (instance, T) it runs the algorithm in a
FRESH subprocess, enforces a hard watchdog at T + GRACE, and reports
objective / elapsed / margin. Any overrun or crash is a would-be -1 on the
leaderboard.

Usage:
  python bench_scaling.py [module] [--probs 1,27,31,38] [--limits 60,120,300]

Numbers from a laptop are NOT comparable to the official Windows bench rows;
this is a robustness check, not a performance row.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "baseline")
TRAIN = os.path.join(HERE, "..", "train")
GRACE = 15.0  # watchdog slack over T before we declare a hang


def run_child(module, prob_path, timelimit):
    """Run one instance in a fresh interpreter; return result dict."""
    out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    out.close()
    cmd = [sys.executable, os.path.abspath(__file__), "--child", module,
           prob_path, str(timelimit), out.name]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, timeout=timelimit + GRACE,
                              capture_output=True, text=True)
        elapsed = time.time() - t0
        if proc.returncode != 0:
            return {"status": "CRASH", "elapsed": elapsed,
                    "detail": (proc.stderr or "").strip()[-400:]}
        with open(out.name) as f:
            res = json.load(f)
        res["elapsed"] = elapsed
        return res
    except subprocess.TimeoutExpired:
        return {"status": "HANG", "elapsed": time.time() - t0,
                "detail": f"no return within T+{GRACE:.0f}s"}
    finally:
        try:
            os.unlink(out.name)
        except OSError:
            pass


def child_main(module, prob_path, timelimit, out_path):
    sys.path.insert(0, BASE)
    import importlib
    from utils import check_feasibility
    prob = json.load(open(prob_path))
    mod = importlib.import_module(module)
    t0 = time.time()
    sol = mod.algorithm(prob, float(timelimit))
    algo_elapsed = time.time() - t0
    res = check_feasibility(prob, sol)
    out = {
        "status": "FEASIBLE" if res.get("feasible") else "INFEASIBLE",
        "objective": res.get("objective"),
        "obj1": res.get("obj1"), "obj2": res.get("obj2"),
        "obj3": res.get("obj3"),
        "algo_elapsed": algo_elapsed,
        "overrun": algo_elapsed > float(timelimit),
    }
    with open(out_path, "w") as f:
        json.dump(out, f)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child_main(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return

    ap = argparse.ArgumentParser()
    ap.add_argument("module", nargs="?", default="myalgorithm")
    ap.add_argument("--probs", default="1,27,31,38")
    ap.add_argument("--limits", default="60,120,300")
    args = ap.parse_args()

    probs = [int(x) for x in args.probs.split(",")]
    limits = [float(x) for x in args.limits.split(",")]

    print(f"module={args.module}  probs={probs}  limits={limits}", flush=True)
    print(f"{'prob':>6} {'T':>6} {'status':>10} {'objective':>16} "
          f"{'algo_s':>8} {'wall_s':>8} {'overrun':>8}", flush=True)
    failures = 0
    rows = []
    for k in probs:
        prob_path = os.path.join(TRAIN, f"prob_{k}.json")
        for T in limits:
            r = run_child(args.module, prob_path, T)
            status = r.get("status", "?")
            obj = r.get("objective")
            overrun = r.get("overrun", status in ("HANG",))
            if status != "FEASIBLE" or overrun:
                failures += 1
            rows.append((k, T, r))
            print(f"{k:>6} {T:>6.0f} {status:>10} "
                  f"{(f'{obj:,.0f}' if obj is not None else '-'):>16} "
                  f"{r.get('algo_elapsed', float('nan')):>8.1f} "
                  f"{r['elapsed']:>8.1f} {str(overrun):>8}", flush=True)
            if r.get("detail"):
                print(f"       detail: {r['detail']}", flush=True)
    print("-" * 70, flush=True)
    # scaling summary: objective at each T relative to the largest T
    for k in probs:
        vals = {T: r.get("objective") for (kk, T, r) in rows if kk == k}
        base_T = max(limits)
        base = vals.get(base_T)
        if base:
            rel = ", ".join(
                f"T={T:.0f}: {vals[T]/base:6.3f}x" for T in limits
                if vals.get(T) is not None)
            print(f"prob_{k}: objective vs T={base_T:.0f}  ({rel})", flush=True)
    print(f"{'FAIL' if failures else 'OK'}: {failures} failure(s) "
          f"(non-feasible or overrun)", flush=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
