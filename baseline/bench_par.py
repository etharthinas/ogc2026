#!/usr/bin/env python3
"""Parallel benchmark harness for dev iterations.

Usage:
  python bench_par.py <module> <timelimit> [prob_indices...] [--jobs N]

Runs several instances concurrently (default 2 slots). Because the algorithm
itself spawns up to 4 worker processes per instance and is timing-sensitive,
co-run results are slightly PESSIMISTIC vs a serial run -- fine for dev
validation, but record official results.csv rows with a serial bench_row.py.

Safety rails (this machine and the eval server both have 16GB):
  * giant instances (n >= 250) run EXCLUSIVELY (their 4 workers already use
    most of the RAM/cores; co-running them corrupted prob_38 measurements);
  * a new instance only starts when enough RAM is free (default 6GB).
"""
import sys, os, json, time, ctypes, threading, queue as _queue, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

from utils import check_feasibility  # noqa: E402

try:  # keep Windows awake for the whole run
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
except Exception:
    pass


def free_ram_gb():
    class MSX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MSX(); m.dwLength = ctypes.sizeof(MSX)
    try:
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys / 1e9
    except Exception:
        return 99.0


def main():
    args = [a for a in sys.argv[1:]]
    jobs = 2
    if "--jobs" in args:
        i = args.index("--jobs")
        jobs = int(args[i + 1])
        del args[i:i + 2]
    mod_name = args[0]
    timelimit = float(args[1])
    indices = [int(x) for x in args[2:]] or list(range(1, 41))
    mod = importlib.import_module(mod_name)

    sizes = {}
    for k in indices:
        with open(os.path.join(TRAIN, f"prob_{k}.json")) as f:
            sizes[k] = len(json.load(f)["blocks"])

    lock = threading.Lock()          # serializes result printing
    heavy_gate = threading.Semaphore(1)  # giants run one-at-a-time, alone
    slots = threading.Semaphore(jobs)
    results = {}
    t_all = time.time()

    def is_heavy(k):
        return sizes[k] >= 250

    def run_one(k):
        path = os.path.join(TRAIN, f"prob_{k}.json")
        with open(path) as f:
            prob = json.load(f)
        while free_ram_gb() < 2.0:   # RAM gate (was 6.0; desktop load now leaves
            time.sleep(5)            # ~3GB free -- rely on compression/paging)
        t0 = time.time()
        try:
            sol = mod.algorithm(prob, timelimit)
            res = check_feasibility(prob, sol)
        except Exception as e:
            with lock:
                print(f"prob_{k:>2}: CRASH {type(e).__name__}: {e}", flush=True)
            results[k] = None
            return
        el = time.time() - t0
        with lock:
            if res.get("feasible"):
                results[k] = res["objective"]
                print(f"prob_{k:>2}: {res['objective']:>14,.0f}  ({el:5.1f}s)  "
                      f"obj1={res.get('obj1')} n={sizes[k]}", flush=True)
            else:
                results[k] = None
                print(f"prob_{k:>2}: INFEASIBLE stage={res.get('stage')} ({el:5.1f}s)",
                      flush=True)

    def worker(k):
        if is_heavy(k):
            # giants grab ALL slots -> exclusive machine use. heavy_gate
            # serializes the slot-collection so two giants can't deadlock
            # holding partial slot sets.
            with heavy_gate:
                for _ in range(jobs):
                    slots.acquire()
                try:
                    run_one(k)
                finally:
                    for _ in range(jobs):
                        slots.release()
        else:
            slots.acquire()
            try:
                run_one(k)
            finally:
                slots.release()

    # lights first (they early-stop fast and pack the slots), giants last
    order = sorted(indices, key=lambda k: (is_heavy(k), -sizes[k]))
    threads = []
    for k in order:
        t = threading.Thread(target=worker, args=(k,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(1.0)  # stagger process spawns
    for t in threads:
        t.join()

    total = sum(v for v in results.values() if v is not None)
    nfeas = sum(1 for v in results.values() if v is not None)
    print("-" * 60, flush=True)
    print(f"TOTAL = {total:,.0f}   feasible {nfeas}/{len(indices)}   "
          f"wall {time.time() - t_all:,.0f}s", flush=True)
    row = (mod_name + "," +
           ",".join(str(int(results[k])) if results.get(k) is not None else ""
                    for k in indices) + f",{int(total)}")
    print("CSVROW " + row, flush=True)


if __name__ == "__main__":
    main()
