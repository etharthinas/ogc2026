#!/usr/bin/env python3
"""Peak-RSS profile of a solver run (parent + the 4 worker processes).

The evaluation server enforces 16GB; the CP-SAT components planned for v19
(flow plan / MPC / layout book) add model memory on top of the raster caches,
so measure BEFORE wiring them in. Samples the whole process tree every 0.5s.

Usage:
  python mem_profile.py [module] [--prob 38] [--timelimit 120]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "baseline")
TRAIN = os.path.join(HERE, "..", "train")


def child_main(module, prob_path, timelimit):
    sys.path.insert(0, BASE)
    import importlib
    from utils import check_feasibility
    prob = json.load(open(prob_path))
    mod = importlib.import_module(module)
    sol = mod.algorithm(prob, float(timelimit))
    res = check_feasibility(prob, sol)
    print(f"CHILD_RESULT feasible={res.get('feasible')} "
          f"objective={res.get('objective')}", flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child_main(sys.argv[2], sys.argv[3], sys.argv[4])
        return

    import psutil

    ap = argparse.ArgumentParser()
    ap.add_argument("module", nargs="?", default="myalgorithm")
    ap.add_argument("--prob", type=int, default=38)
    ap.add_argument("--timelimit", type=float, default=120.0)
    args = ap.parse_args()

    prob_path = os.path.join(TRAIN, f"prob_{args.prob}.json")
    cmd = [sys.executable, os.path.abspath(__file__), "--child",
           args.module, prob_path, str(args.timelimit)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    ps = psutil.Process(proc.pid)

    peak = 0.0
    peak_np = 0
    samples = []
    t0 = time.time()
    while proc.poll() is None:
        try:
            procs = [ps] + ps.children(recursive=True)
            rss = sum(p.memory_info().rss for p in procs
                      if p.is_running()) / 1e9
            if rss > peak:
                peak, peak_np = rss, len(procs)
            samples.append((time.time() - t0, rss))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        time.sleep(0.5)
        if time.time() - t0 > args.timelimit + 60:
            proc.kill()
            print("HANG: killed after T+60s", flush=True)
            break

    out = proc.stdout.read() if proc.stdout else ""
    print(out.strip(), flush=True)
    print(f"prob_{args.prob} @{args.timelimit:.0f}s: peak RSS = {peak:.2f} GB "
          f"across {peak_np} processes ({len(samples)} samples)", flush=True)
    # coarse timeline (10 buckets) to see WHEN memory peaks
    if samples:
        tmax = samples[-1][0]
        buckets = {}
        for t, r in samples:
            buckets.setdefault(min(9, int(10 * t / max(tmax, 1e-9))), []).append(r)
        line = " ".join(f"{max(v):.1f}" for _, v in sorted(buckets.items()))
        print(f"timeline (max GB per decile): {line}", flush=True)
    limit = 16.0
    print(f"{'FAIL' if peak > limit * 0.85 else 'OK'}: peak {peak:.2f} GB vs "
          f"{limit:.0f} GB server limit (alert at 85%)", flush=True)
    sys.exit(1 if peak > limit * 0.85 else 0)


if __name__ == "__main__":
    main()
