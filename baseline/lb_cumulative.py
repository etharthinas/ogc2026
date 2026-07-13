#!/usr/bin/env python3
"""v20 Improvement-1 (the one 19a skipped): honest non-preemptive lower bound.

Relaxation: merge all bays into one resource; per-layer cumulative capacity
C = sum(bay areas) for each layer level; exact integer durations, entry >=
release, exit = entry + p (longer dwell never helps). Geometry, crane, and
bay-containment are relaxed away, Z2/Z3 dropped -> objective bound on w1*Z1
is a VALID lower bound on the instance's tardiness component.

cap_frac < 1.0 gives a 'realistic target' at an assumed achievable per-layer
packing density instead of a bound.

Usage: lb_cumulative.py <prob> [cap_frac] [budget_s]
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
from ortools.sat.python import cp_model


def polyarea(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def main():
    k = int(sys.argv[1])
    cap_frac = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 300.0
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bd = prob["blocks"]
    n = len(bd)
    w1 = prob["weights"]["w1"]
    C = sum(b["width"] * b["height"] for b in prob["bays"])
    cap = int(math.floor(C * cap_frac))

    rel = [b["release_time"] for b in bd]
    due = [b["due_date"] for b in bd]
    p = [b["processing_time"] for b in bd]
    # per-layer demand: min over orientations, per layer, floored (valid LB)
    maxL = max(len(b["shape"][0]["layers"]) for b in bd)
    dem = []
    for b in bd:
        per = []
        for L in range(maxL):
            areas = []
            for o in b["shape"]:
                if len(o["layers"]) > L:
                    areas.append(polyarea(o["layers"][L]))
                else:
                    areas.append(0.0)
            per.append(int(math.floor(min(areas))))
        dem.append(per)

    H = max(due) + sum(sorted(p)[-10:])  # generous horizon
    m = cp_model.CpModel()
    starts, ivs, tards = [], [], []
    for i in range(n):
        s = m.NewIntVar(rel[i], H - p[i], f"s{i}")
        iv = m.NewIntervalVar(s, p[i], s + p[i], f"iv{i}")
        t = m.NewIntVar(0, H, f"t{i}")
        m.AddMaxEquality(t, [s + p[i] - due[i], 0])
        starts.append(s); ivs.append(iv); tards.append(t)
    for L in range(maxL):
        li = [i for i in range(n) if dem[i][L] > 0]
        if li:
            m.AddCumulative([ivs[i] for i in li], [dem[i][L] for i in li], cap)
    m.Minimize(sum(tards))

    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = budget
    sol.parameters.num_search_workers = 8
    sol.parameters.log_search_progress = False
    st = sol.Solve(m)
    name = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE"}.get(st, str(st))
    lb = sol.BestObjectiveBound()
    ub = sol.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else float("inf")
    print(f"prob_{k} cap_frac={cap_frac} cap={cap} status={name} "
          f"tard_LB={lb:.0f} tard_UB={ub:.0f} "
          f"w1*LB={w1*lb:,.0f} w1*UB={w1*ub:,.0f} time={sol.WallTime():.1f}s",
          flush=True)


if __name__ == "__main__":
    main()
