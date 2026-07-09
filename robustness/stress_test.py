#!/usr/bin/env python3
"""Hidden-instance stress test: perturb training instances and verify the
solver NEVER crashes / hangs / returns infeasible, and that the instance-
computed branches (forced / overload / reclaim) don't flip pathologically.

Rationale: contest scoring gives -1 per hidden instance on any failure, and
v18's branching thresholds (overload 0.44 / 1.05, n>=250 giant gate) plus
seed-pinned restoration slots are tuned on the 40 train instances. Hidden
instances near those boundaries must still run clean.

Usage:
  python stress_test.py [module] [--probs 1,27,38] [--timelimit 60]
                        [--variants all|names,comma,separated]

Each (instance, variant) runs in a fresh subprocess with a hard watchdog at
T + GRACE. Exit code != 0 iff any run fails.
"""
import argparse
import copy
import json
import os
import random
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "baseline")
TRAIN = os.path.join(HERE, "..", "train")
GRACE = 20.0
SEED = 2026


# ---------------------------------------------------------------- variants
def _fix_due(b):
    b["due_date"] = int(max(b["due_date"], b["release_time"] + b["processing_time"]))


def v_bay_grow(prob, rng):
    """All bays 10% bigger: shifts overload/forced ratios DOWN across gates."""
    for bay in prob["bays"]:
        bay["width"] = int(round(bay["width"] * 1.10))
        bay["height"] = int(round(bay["height"] * 1.10))


def v_bay_shrink(prob, rng):
    """All bays 5% smaller: shifts overload UP (may cross 0.44/1.05 gates)."""
    for bay in prob["bays"]:
        bay["width"] = max(2, int(round(bay["width"] * 0.95)))
        bay["height"] = max(2, int(round(bay["height"] * 0.95)))


def v_due_tight(prob, rng):
    """Squeeze slack 40%: more zero-slack blocks, more tardiness pressure."""
    for b in prob["blocks"]:
        span = b["due_date"] - b["release_time"]
        b["due_date"] = b["release_time"] + int(round(span * 0.6))
        _fix_due(b)


def v_release_jitter(prob, rng):
    """Shift releases +-2: perturbs every event-driven admission decision."""
    for b in prob["blocks"]:
        b["release_time"] = max(0, b["release_time"] + rng.randint(-2, 2))
        _fix_due(b)


def v_w1_low(prob, rng):
    """w1 x0.1: preference/balance terms dominate (prob_25/36/40 regime)."""
    prob["weights"]["w1"] = max(1, int(prob["weights"]["w1"] * 0.1))


def v_drop10(prob, rng):
    """Remove a random 10% of blocks (n may cross the n>=250 giant gate)."""
    n = len(prob["blocks"])
    keep = sorted(rng.sample(range(n), int(round(n * 0.9))))
    prob["blocks"] = [prob["blocks"][i] for i in keep]


def v_dup10(prob, rng):
    """Duplicate a random 10% of blocks with +5 release (denser bursts, and
    n may cross the giant gate upward)."""
    n = len(prob["blocks"])
    for i in rng.sample(range(n), max(1, n // 10)):
        b = copy.deepcopy(prob["blocks"][i])
        b["release_time"] += 5
        _fix_due(b)
        prob["blocks"].append(b)


VARIANTS = {
    "bay_grow": v_bay_grow,
    "bay_shrink": v_bay_shrink,
    "due_tight": v_due_tight,
    "release_jitter": v_release_jitter,
    "w1_low": v_w1_low,
    "drop10": v_drop10,
    "dup10": v_dup10,
}


# ---------------------------------------------------------------- branch flags
def branch_flags(prob):
    """Report the solver's instance-computed branch decisions (best-effort)."""
    sys.path.insert(0, BASE)
    flags = {}
    try:
        import myalgorithm as m
        n = len(prob["blocks"])
        flags["n"] = n
        if hasattr(m, "_overload_ratio"):
            flags["overload"] = round(m._overload_ratio(prob), 3)
        if hasattr(m, "_is_forced"):
            flags["forced"] = bool(m._is_forced(prob))
        if "overload" in flags and "forced" in flags:
            flags["reclaim"] = (flags["forced"] and n >= 250) or flags["overload"] > 1.05
    except Exception as e:  # branch introspection must never fail the test
        flags["introspect_error"] = type(e).__name__
    return flags


# ---------------------------------------------------------------- child
def child_main(module, prob_json_path, timelimit, out_path):
    sys.path.insert(0, BASE)
    import importlib
    from utils import check_feasibility
    prob = json.load(open(prob_json_path))
    mod = importlib.import_module(module)
    t0 = time.time()
    sol = mod.algorithm(prob, float(timelimit))
    algo_elapsed = time.time() - t0
    res = check_feasibility(prob, sol)
    with open(out_path, "w") as f:
        json.dump({
            "status": "FEASIBLE" if res.get("feasible") else "INFEASIBLE",
            "objective": res.get("objective"),
            "algo_elapsed": algo_elapsed,
            "overrun": algo_elapsed > float(timelimit),
            "stage": res.get("stage"),
        }, f)


def run_one(module, prob, timelimit):
    pf = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(prob, pf)
    pf.close()
    out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    out.close()
    cmd = [sys.executable, os.path.abspath(__file__), "--child", module,
           pf.name, str(timelimit), out.name]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, timeout=timelimit + GRACE,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "CRASH", "elapsed": time.time() - t0,
                    "detail": (proc.stderr or "").strip()[-400:]}
        with open(out.name) as f:
            r = json.load(f)
        r["elapsed"] = time.time() - t0
        return r
    except subprocess.TimeoutExpired:
        return {"status": "HANG", "elapsed": time.time() - t0}
    finally:
        for p in (pf.name, out.name):
            try:
                os.unlink(p)
            except OSError:
                pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child_main(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return

    ap = argparse.ArgumentParser()
    ap.add_argument("module", nargs="?", default="myalgorithm")
    ap.add_argument("--probs", default="1,27,38")
    ap.add_argument("--timelimit", type=float, default=60.0)
    ap.add_argument("--variants", default="all")
    args = ap.parse_args()

    probs = [int(x) for x in args.probs.split(",")]
    names = list(VARIANTS) if args.variants == "all" else args.variants.split(",")

    print(f"module={args.module} probs={probs} T={args.timelimit:.0f}s "
          f"variants={names}", flush=True)
    print(f"{'prob':>6} {'variant':>16} {'n':>4} {'ovl':>6} {'frc':>5} "
          f"{'rcl':>5} {'status':>10} {'objective':>14} {'algo_s':>7}", flush=True)
    failures = []
    for k in probs:
        base = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
        for name in names:
            rng = random.Random(SEED + k)
            prob = copy.deepcopy(base)
            VARIANTS[name](prob, rng)
            fl = branch_flags(prob)
            r = run_one(args.module, prob, args.timelimit)
            bad = r.get("status") != "FEASIBLE" or r.get("overrun")
            if bad:
                failures.append((k, name, r))
            obj_s = ("{:,.0f}".format(r["objective"])
                     if r.get("objective") is not None else "-")
            print(f"{k:>6} {name:>16} {fl.get('n', '?'):>4} "
                  f"{fl.get('overload', '?'):>6} "
                  f"{str(fl.get('forced', '?'))[:1]:>5} "
                  f"{str(fl.get('reclaim', '?'))[:1]:>5} "
                  f"{r.get('status'):>10} {obj_s:>14} "
                  f"{r.get('algo_elapsed', float('nan')):>7.1f}"
                  + ("  <-- FAIL" if bad else ""), flush=True)
            if r.get("detail"):
                print(f"       detail: {r['detail']}", flush=True)
    print("-" * 80, flush=True)
    print(f"{'FAIL' if failures else 'OK'}: {len(failures)} failure(s) of "
          f"{len(probs) * len(names)} runs", flush=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
