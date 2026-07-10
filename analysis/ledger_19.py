#!/usr/bin/env python3
"""19a — Honest capacity ledger (heuristic_19.md Improvement 1, v0).

Per instance, solve a NON-PREEMPTIVE capacity relaxation with CP-SAT:
  - one optional interval per (block, bay); exactly-one bay per block;
  - exact integer entry/exit times: entry >= release, exit = entry + processing
    (blocks may stay longer in reality; that only raises tardiness, so
    exit = entry + p is the relaxation's best case — valid for a lower bound);
  - per-bay AddCumulative over BASE-LAYER areas: any real geometric packing
    satisfies sum(area) <= Area_k at every instant, so this is a relaxation.
    Demands use floor(min-orientation base-layer area) (underestimate = valid);
    capacity uses ceil(cap_frac * Area_k) (overestimate = valid at cap_frac=1).
  - objective: w1 * sum tardiness. Z2/Z3 dropped (dropping terms keeps the LB
    valid); combine externally with the joint_floor_obj1=0 row.

cap_frac = 1.0   -> mathematically valid LOWER BOUND on w1*Z1.
cap_frac = 0.6 / 0.5 -> NOT bounds: realistic-target scenarios (v18's best
observed effective density is 0.48; the fluid analysis says tardiness ~0 at
0.55+ for everything except 27/38).

We report CP-SAT's proven BestObjectiveBound (valid even on timeout), plus
the incumbent value as an upper bound on the relaxation's own optimum.

Usage:
  python ledger_19.py [--probs 21-40] [--budget 60] [--caps 1.0,0.6,0.5]
Writes a markdown table to stdout; redirect to a file for the ledger.
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")

from ortools.sat.python import cp_model  # noqa: E402

# v18 @600s values (results.csv row 'algorithm 18 (4w 600s)') for context
V18 = {1: 18357, 2: 6620, 3: 66190, 4: 35566, 5: 91320, 6: 90319, 7: 91676,
       8: 11420, 9: 104880, 10: 95550, 11: 47096, 12: 141078, 13: 105068,
       14: 107689, 15: 49304, 16: 78538, 17: 78064, 18: 93930, 19: 84213,
       20: 195290, 21: 1380772, 22: 934883, 23: 3390436, 24: 643943,
       25: 338322, 26: 9653490, 27: 29185135, 28: 3565230, 29: 557994,
       30: 4083746, 31: 11268243, 32: 3881748, 33: 9566490, 34: 1978590,
       35: 1346898, 36: 188270, 37: 5807047, 38: 45806839, 39: 12361461,
       40: 2300281}
# joint Z2+Z3 floor (results.csv row 'joint_floor_obj1=0')
FLOOR = {21: 80470, 22: 36937, 23: 4579, 24: 24755, 25: 5547, 26: 74172,
         27: 31156, 28: 17238, 29: 34782, 30: 16252, 31: 178971, 32: 28565,
         33: 19080, 34: 20986, 35: 22945, 36: 25379, 37: 63004, 38: 17678,
         39: 25594, 40: 25677}


def shoelace(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def block_min_area(block):
    """floor of min-over-orientations base-layer area (valid underestimate)."""
    best = None
    for orient in block["shape"]:
        a = shoelace(orient["layers"][0])  # base layer polygon
        if best is None or a < best:
            best = a
    return max(1, math.floor(best))


def solve_instance(k, cap_frac, budget_s):
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    blocks, bays = prob["blocks"], prob["bays"]
    w1 = prob["weights"]["w1"]
    n, m = len(blocks), len(bays)
    bay_area = [math.ceil(cap_frac * b["width"] * b["height"]) for b in bays]
    areas = [block_min_area(b) for b in blocks]
    # horizon: latest release + generous room; tardiness only grows with time,
    # so a too-small horizon could cut the true optimum — use a slack of
    # total-processing/m over the natural end.
    rel = [b["release_time"] for b in blocks]
    proc = [b["processing_time"] for b in blocks]
    due = [b["due_date"] for b in blocks]
    horizon = max(max(r + p for r, p in zip(rel, proc)), max(due)) \
        + math.ceil(sum(proc) / m) + max(proc)

    mdl = cp_model.CpModel()
    tardies = []
    for i in range(n):
        entry = mdl.NewIntVar(rel[i], horizon - proc[i], f"e{i}")
        exit_ = mdl.NewIntVar(rel[i] + proc[i], horizon, f"x{i}")
        mdl.Add(exit_ == entry + proc[i])
        lits = []
        for j in range(m):
            y = mdl.NewBoolVar(f"y{i}_{j}")
            lits.append(y)
        mdl.AddExactlyOne(lits)
        for j in range(m):
            iv = mdl.NewOptionalIntervalVar(entry, proc[i], exit_, lits[j],
                                            f"iv{i}_{j}")
            if not hasattr(mdl, "_bay_ivs"):
                mdl._bay_ivs = {}
            mdl._bay_ivs.setdefault(j, []).append((iv, areas[i]))
        t = mdl.NewIntVar(0, horizon, f"t{i}")
        mdl.AddMaxEquality(t, [0, exit_ - due[i]])
        tardies.append(t)
    for j in range(m):
        ivs = [iv for iv, _ in mdl._bay_ivs.get(j, [])]
        dem = [a for _, a in mdl._bay_ivs.get(j, [])]
        if ivs:
            mdl.AddCumulative(ivs, dem, bay_area[j])
    mdl.Minimize(sum(tardies))

    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = budget_s
    sv.parameters.num_workers = 4
    status = sv.Solve(mdl)
    name = sv.StatusName(status)
    lb = sv.BestObjectiveBound() if status in (cp_model.OPTIMAL,
                                               cp_model.FEASIBLE) else 0
    ub = sv.ObjectiveValue() if status in (cp_model.OPTIMAL,
                                           cp_model.FEASIBLE) else None
    return {"status": name, "lb_tard": int(lb), "ub_tard":
            (int(ub) if ub is not None else None), "w1": w1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probs", default="21-40")
    ap.add_argument("--budget", type=float, default=60.0)
    ap.add_argument("--caps", default="1.0,0.6,0.5")
    args = ap.parse_args()
    if "-" in args.probs:
        a, b = args.probs.split("-")
        probs = list(range(int(a), int(b) + 1))
    else:
        probs = [int(x) for x in args.probs.split(",")]
    caps = [float(c) for c in args.caps.split(",")]

    print(f"# Ledger 19a v0 — non-preemptive area-cumulative relaxation "
          f"(budget {args.budget:.0f}s/solve)\n")
    hdr = "| prob | v18 | floor(Z2+Z3) | " + " | ".join(
        f"cap={c:g} LB(w1·Z1) [status]" for c in caps) + " | verdict |"
    print(hdr)
    print("|" + "---|" * (3 + len(caps) + 1))
    for k in probs:
        cells = []
        lb10 = 0
        for c in caps:
            t0 = time.time()
            r = solve_instance(k, c, args.budget)
            w1lb = r["lb_tard"] * r["w1"]
            if c == 1.0:
                lb10 = w1lb
            ub = (f"/{r['ub_tard'] * r['w1']:,}" if r["ub_tard"] is not None
                  else "")
            cells.append(f"{w1lb:,}{ub} [{r['status'][:4]} "
                         f"{time.time()-t0:.0f}s]")
        v18 = V18.get(k, 0)
        fl = FLOOR.get(k, 0)
        target = lb10 + fl
        gap = v18 - target
        verdict = ("SATURATED" if gap < 0.15 * v18 else
                   "CHASE" if gap > 0.5 * v18 else "MAYBE")
        print(f"| {k} | {v18:,} | {fl:,} | " + " | ".join(cells) +
              f" | {verdict} (valid-LB gap {gap:,}) |", flush=True)


if __name__ == "__main__":
    main()
