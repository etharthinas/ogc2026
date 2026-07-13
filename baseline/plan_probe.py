#!/usr/bin/env python3
"""v20 spot probe: plan-guided admission (Improvement 2, correctly calibrated).

Pipeline (offline prototype, zero submission risk):
 1. Solve the non-preemptive per-layer cumulative plan (merged bays) at a
    calibrated cap_frac, hinted with the v18 incumbent's entry times.
 2. Realize with v18's _dispatch_construct using targets=plan (the existing
    round-3 gate machinery: hold sacrificed blocks to their planned entry,
    urgency keys on the plan).
 3. Polish: _improve -> _cpsat_retime -> _improve (giant envelope).
 4. Report objective vs banked incumbent.

Usage: plan_probe.py <prob> <cap_frac> <plan_budget_s> <improve_budget_s> [kappa alpha]
"""
import json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
from ortools.sat.python import cp_model


def polyarea(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def solve_plan(prob, cap_frac, budget, hint=None, workers=8):
    bd = prob["blocks"]
    n = len(bd)
    C = sum(b["width"] * b["height"] for b in prob["bays"])
    cap = int(math.floor(C * cap_frac))
    rel = [b["release_time"] for b in bd]
    due = [b["due_date"] for b in bd]
    p = [b["processing_time"] for b in bd]
    maxL = max(len(b["shape"][0]["layers"]) for b in bd)
    dem = []
    for b in bd:
        per = []
        for L in range(maxL):
            areas = [polyarea(o["layers"][L]) if len(o["layers"]) > L else 0.0
                     for o in b["shape"]]
            per.append(int(math.floor(min(areas))))
        dem.append(per)
    H = max(due) + sum(sorted(p)[-10:])
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
    # lexicographic-ish: tardiness dominates; the start-sum term left-shifts
    # the plan so non-sacrificed blocks get target == release (a gratuitously
    # late plan entry becomes an idle-space gate at realization).
    m.Minimize(1000 * sum(tards) + sum(starts[i] - rel[i] for i in range(n)))
    if hint is not None:
        for i in range(n):
            if i in hint:
                m.AddHint(starts[i], min(max(rel[i], hint[i]), H - p[i]))
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = budget
    sol.parameters.num_search_workers = workers
    sol.parameters.random_seed = 20
    st = sol.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None
    plan = {i: int(sol.Value(starts[i])) for i in range(n)}
    ptard = sum(sol.Value(t) for t in tards)
    return plan, ptard


def main():
    k = int(sys.argv[1])
    cap_frac = float(sys.argv[2])
    pb = float(sys.argv[3])
    ib = float(sys.argv[4])
    kappa = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0
    alpha = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
    beam = bool(int(os.environ.get("PROBE_BEAM", "0")))
    delta = int(os.environ.get("PROBE_DELTA", "0"))  # admit up to delta early
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bd = prob["blocks"]
    w = prob["weights"]
    w1, w2, w3 = w["w1"], w["w2"], w["w3"]
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    forced = M._is_forced(prob, bays)

    inc_path = os.path.join(HERE, f"v18_{k}.json")
    hint = None
    inc_obj = None
    if os.path.exists(inc_path):
        A = {int(x): y for x, y in json.load(open(inc_path)).items()}
        hint = {bi: A[bi]["entry_time"] for bi in A}
        inc_obj = M._objective(A, bd, bays, bay_u, w1, w2, w3)[0]

    t0 = time.time()
    plan, ptard = solve_plan(prob, cap_frac, pb, hint=hint)
    print(f"[plan] cap={cap_frac} tard={ptard:.0f} (w1*={w1*ptard:,.0f}) "
          f"t={time.time()-t0:.0f}s beam={beam} delta={delta}", flush=True)
    if plan is None:
        return
    if delta:
        plan = {i: max(bd[i]["release_time"], t - delta)
                for i, t in plan.items()}

    M._reset_caches()
    raster = M._Raster(prob, bays)
    t1 = time.time()
    deadline = t1 + 3600  # dispatch runs to completion
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, deadline, raster,
                              kappa=kappa, gamma=0.5, alpha=alpha,
                              score_pos=True, targets=plan, beam=beam)
    o = M._objective(a, bd, bays, bay_u, w1, w2, w3)[0]
    slips = [a[bi]["entry_time"] - plan[bi] for bi in a]
    pos = [s for s in slips if s > 0]
    rtard = sum(max(0, a[bi]["exit_time"] - bd[bi]["due_date"]) for bi in a)
    print(f"[realize] obj={o:,.0f} tard={rtard} t={time.time()-t1:.0f}s "
          f"(incumbent={inc_obj:,.0f}) slip: n_pos={len(pos)}/{len(slips)} "
          f"sum={sum(pos)} max={max(pos) if pos else 0}", flush=True)
    if os.environ.get("PROBE_FAST"):
        print(f"FINAL prob_{k}: obj={o:,.0f} (no polish) "
              f"delta={o-inc_obj:+,.0f}", flush=True)
        return

    # polish: improve -> retime -> improve
    t2 = time.time()
    dl = time.time() + ib
    r, o2 = M._improve(prob, a, bays, bay_u, w1, w2, w3, dl, forced,
                       seed=2020, raster=raster, repack_every=3, xbay=False,
                       deep=True)
    print(f"[improve1] obj={o2:,.0f} t={time.time()-t2:.0f}s", flush=True)
    try:
        rc = M._cpsat_retime(prob, r, bays, bd, 30.0, time.time() + 40.0)
    except Exception as e:
        print("retime fail:", e)
        rc = None
    if rc is not None:
        oc = M._objective(rc, bd, bays, bay_u, w1, w2, w3)[0]
        if oc < o2:
            r, o2 = rc, oc
        print(f"[retime] obj={oc:,.0f}", flush=True)
    dl2 = time.time() + ib * 0.6
    r2, o3 = M._improve(prob, r, bays, bay_u, w1, w2, w3, dl2, forced,
                        seed=2021, raster=raster, repack_every=3, xbay=True,
                        deep=True)
    if o3 < o2:
        r, o2 = r2, o3
    print(f"[improve2] obj={o2:,.0f}", flush=True)

    # official check
    sol = {"operations": M._build_operations(r)}
    res = M.check_feasibility(prob, sol)
    print(f"FINAL prob_{k}: obj={o2:,.0f} feasible={res['feasible']} "
          f"vs incumbent {inc_obj:,.0f}  delta={o2-inc_obj:+,.0f}", flush=True)


if __name__ == "__main__":
    main()
