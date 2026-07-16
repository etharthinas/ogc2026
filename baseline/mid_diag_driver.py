#!/usr/bin/env python3
"""Serial capture+diag driver for the mid-tier eligible instances.

For each k in KS: (1) capture_v25.py k 600 v25_k.json  (reproduces the banked
v25 incumbent by running the real algorithm), (2) diag_v25.py k v25_k.json
diag<k>.json (burst diagnostic: feasible-placement fraction, per-layer density,
tardiness attribution). Kills each step's full process tree afterward (bench-
style exit hangs / spawn workers survive parent exit on Windows).

Run detached; progress lines go to stdout (redirect to a log and poll it).
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
KS = [26, 31, 33, 37, 39]

try:
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
except Exception:
    pass


def run_step(args, timeout):
    p = subprocess.Popen([PY] + args, cwd=HERE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True)
    out = []
    t0 = time.time()
    try:
        o, _ = p.communicate(timeout=timeout)
        out.append(o or "")
    except subprocess.TimeoutExpired:
        out.append("[driver] TIMEOUT, killing tree\n")
    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                   capture_output=True)
    print("".join(out).strip(), flush=True)
    print(f"[driver] step {' '.join(args)} done in {time.time()-t0:.0f}s",
          flush=True)


def main():
    for k in KS:
        run_step(["capture_v25.py", str(k), "600", f"v25_{k}.json"], 680)
        run_step(["diag_v25.py", str(k), f"v25_{k}.json", f"diag{k}.json"], 900)
    print("DRIVER_ALLDONE", flush=True)


if __name__ == "__main__":
    main()
