# radical_s4_merge.py -- RADICAL EPOCH strategy S4: SOLUTION-MERGE RECOMBINATION
# (path-relinking / cross-candidate merge). See heuristics/heuristic_32.md (S4).
#
# Idea: the M25 portfolio already produces 20-30 DIVERSE full solutions per run
# whose UNION contains better mixtures that min-wins never recombines. This arm:
#   1. HARVEST: run M25's real portfolio workers, drain the on_best stream in the
#      parent (the standard queue the parent uses), keep EVERY streamed candidate
#      -- not just the final winner -- as the diverse solution set.
#   2. POOL: per block b, pool P[b] = its distinct (bay,x,y,orient,entry,exit)
#      placements across the harvested solutions (dedup).
#   3. RECOMBINE (CP-SAT): binary y[b,p], pick exactly one placement per block;
#      pairwise incompatibility ONLY for placements that share a bay AND overlap
#      in time, computed with M25's raster masks + exact _can_place primitives
#      (M25._exact_pair_rel). Objective = true weighted objective (exact tardiness
#      + preference from the fixed placement, imbalance linearized as a max over
#      per-bay weighted workload sums). Warm start = best feasible harvested
#      solution (AddHint). workers=4.
#   4. REPLAY REPAIR: a merged schedule's crane feasibility is order-dependent, so
#      rebuild ops + utils.check_feasibility; per violating block revert to its
#      warm-start placement (<=3 rounds); if still infeasible, drop the merge.
#   5. OUTPUT: best of (merged-if-feasible, best harvested). Always feasible.
#
# Standalone: exposes algorithm(prob_info, timelimit). M25's portfolio spawns its
# own worker processes (standard); the recombination CP-SAT runs in the parent
# afterward. Import-safe with a __main__ guard.
# =============================================================================

import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import myalgorithm_25 as M25  # reuses raster/scan/objective/ops machinery
from utils import Bay, check_feasibility

try:
    import numpy as _np  # noqa: F401  (raster masks need numpy)
    _HAVE_NUMPY = True
except Exception:  # pragma: no cover
    _HAVE_NUMPY = False


# -----------------------------------------------------------------------------
# 1. HARVEST -- run M25's portfolio workers, keep the full on_best stream.
# -----------------------------------------------------------------------------

def _harvest(prob_info, harvest_tl, t_start):
    """Spawn M25's real portfolio workers (_worker_main) and drain their
    best-so-far queue in the parent -- the SAME on_best/queue hook M25's own
    parent uses -- but keep EVERY streamed (obj, assign) incumbent, not just the
    final winner. Returns the raw candidate list [(internal_obj, assign)]."""
    import multiprocessing as _mp
    nw = min(4, _mp.cpu_count() or 1)
    if nw < 2:
        return []
    ctx = _mp.get_context()
    q = ctx.Queue()
    inboxes = [ctx.Queue() for _ in range(nw)]      # M25 island broadcasts
    procs = []
    for wid in range(nw):
        p = ctx.Process(target=M25._worker_main,
                        args=(wid, prob_info, harvest_tl, t_start, q,
                              inboxes[wid]),
                        daemon=True)
        p.start()
        procs.append(p)

    cands = []
    gbest = float("inf")
    # Workers self-stop near t_start + harvest_tl; drain a bit past that.
    drain_stop = t_start + harvest_tl + max(2.0, harvest_tl * 0.03)
    while time.time() < drain_stop:
        try:
            item = q.get(timeout=0.25)
            cands.append(item)
            # Faithfully mirror M25's island broadcast (global best -> inboxes)
            # so harvested trajectories match M25's real portfolio behavior.
            if item[0] < gbest * 0.998:
                gbest = item[0]
                for ib in inboxes:
                    try:
                        ib.put(item)
                    except Exception:
                        pass
        except Exception:
            if all(not p.is_alive() for p in procs):
                break
    # Final non-blocking drain before terminate (a killed mid-put corrupts pipes)
    while True:
        try:
            cands.append(q.get(timeout=0.05))
        except Exception:
            break
    for p in procs:
        try:
            if p.is_alive():
                p.terminate()
        except Exception:
            pass
    return cands


# -----------------------------------------------------------------------------
# 2. POOL -- per-block distinct placements across harvested solutions.
# -----------------------------------------------------------------------------

def _sol_sig(assign):
    return tuple(sorted(
        (bi, a["bay_id"], a["x"], a["y"], a["orient_idx"],
         a["entry_time"], a["exit_time"])
        for bi, a in assign.items()))


def _build_pool(solutions, n_blocks):
    """solutions: list of assignment dicts. Returns pool: {bi: [placement,...]}
    where placement = dict(bi,bay,x,y,oi,entry,exit); dedup per block."""
    pool = {}
    seen = {}
    for assign in solutions:
        for bi, a in assign.items():
            key = (a["bay_id"], a["x"], a["y"], a["orient_idx"],
                   a["entry_time"], a["exit_time"])
            s = seen.setdefault(bi, set())
            if key in s:
                continue
            s.add(key)
            pool.setdefault(bi, []).append({
                "bi": bi, "bay": a["bay_id"], "x": a["x"], "y": a["y"],
                "oi": a["orient_idx"], "entry": a["entry_time"],
                "exit": a["exit_time"],
            })
    return pool


# -----------------------------------------------------------------------------
# 3. Pairwise incompatibility (fixed entry/exit -> static boolean per pair).
# -----------------------------------------------------------------------------

def _incompatible(raster, bay, blocks_data, pa, pb):
    """True iff placements pa (block b1), pb (block b2) cannot BOTH be selected.
    Exact static reduction of M25._can_place with the two entry/exit windows
    FIXED. Same-bay only (caller guarantees). Uses conservative mask pre-filter
    then M25._exact_pair_rel for the crane/collision relations."""
    b1, o1, x1, y1 = pa["bi"], pa["oi"], pa["x"], pa["y"]
    b2, o2, x2, y2 = pb["bi"], pb["oi"], pb["x"], pb["y"]
    e1, xt1 = pa["entry"], pa["exit"]
    e2, xt2 = pb["entry"], pb["exit"]
    # Cheap conservative mask filter: masks fully clear => provably compatible.
    col_m, b12_m, b21_m = M25._mask_pair_rel(raster, b1, o1, x1, y1,
                                             b2, o2, x2, y2)
    if not (col_m or b12_m or b21_m):
        return False
    col, e12, x12, e21, x21 = M25._exact_pair_rel(
        raster, bay, blocks_data, b1, o1, x1, y1, b2, o2, x2, y2)
    # collision: incompatible iff presence intervals strictly overlap.
    if col and (e1 < xt2 and e2 < xt1):
        return True
    # b2 obstructs b1's ENTRY moment e1 (mirror _can_place present-at-entry tie).
    if e12 and ((e2 < e1 < xt2) or (e2 == e1 and b2 < b1)):
        return True
    # b2 obstructs b1's EXIT moment xt1 (present-at-exit tie).
    if x12 and ((e2 < xt1 < xt2) or (xt2 == xt1 and b2 > b1)):
        return True
    # b1 obstructs b2's ENTRY moment e2.
    if e21 and ((e1 < e2 < xt1) or (e1 == e2 and b1 < b2)):
        return True
    # b1 obstructs b2's EXIT moment xt2.
    if x21 and ((e1 < xt2 < xt1) or (xt1 == xt2 and b1 > b2)):
        return True
    return False


def _precompute_pairs(raster, bays, blocks_data, pool, deadline):
    """All incompatible (node_a, node_b) placement-index pairs. Bay-grouped +
    closed-interval sweep so cost stays O(same-bay time-overlapping pairs).
    node = (bi, pidx). A wall-clock guard keeps it bounded: a MISSED
    incompatibility only lets an infeasible merge slip through, which the replay
    repair catches -- so early stopping is sound, never unsound."""
    # Flatten nodes per bay: (entry, exit, bi, pidx, placement)
    by_bay = {}
    for bi, plist in pool.items():
        for pidx, pl in enumerate(plist):
            by_bay.setdefault(pl["bay"], []).append(
                (pl["entry"], pl["exit"], bi, pidx, pl))
    pairs = []
    n_checks = 0
    for bay_id, nodes in by_bay.items():
        bay = bays[bay_id]
        nodes.sort(key=lambda t: t[0])          # by entry
        active = []                             # sweep set: closed-interval live
        for cur in nodes:
            ce, cx, cbi, cpi, cpl = cur
            # drop nodes whose exit < cur.entry (no closed-interval intersection)
            active = [a for a in active if a[1] >= ce]
            for oth in active:
                oe, ox, obi, opi, opl = oth
                if obi == cbi:
                    continue                    # same block: exactly-one handles
                n_checks += 1
                if _incompatible(raster, bay, blocks_data, cpl, opl):
                    pairs.append(((cbi, cpi), (obi, opi)))
            active.append(cur)
            if (n_checks & 1023) == 0 and time.time() > deadline:
                return pairs, n_checks, True
    return pairs, n_checks, False


# -----------------------------------------------------------------------------
# 4. RECOMBINATION CP-SAT.
# -----------------------------------------------------------------------------

def _recombine(prob_info, bays, bay_u, w1, w2, w3, pool, incompat_pairs,
               warm_assign, budget_s):
    """Pick one placement per block minimizing the true objective, subject to
    the pairwise incompatibilities. Warm-started from warm_assign. Returns a
    merged assignment dict or None."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    if budget_s <= 0.5:
        return None
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    SU = 1000                                   # imbalance scale (u_j is a ratio)
    m = cp_model.CpModel()

    yv = {}                                     # (bi, pidx) -> BoolVar
    base_cost = {}                              # (bi, pidx) -> int (w1*tard+w3*pref)
    # per-bay weighted-workload linear terms for the imbalance max.
    wl_terms = [[] for _ in range(n_bays)]      # bay -> list[(coef, var)]
    su = [int(round(SU * bay_u[j])) for j in range(n_bays)]

    for bi, plist in pool.items():
        vs = []
        blk = blocks_data[bi]
        due = blk["due_date"]
        prefs = blk["bay_preferences"]
        s_max = max(prefs)
        wl = int(round(blk["workload"]))
        for pidx, pl in enumerate(plist):
            v = m.NewBoolVar(f"y_{bi}_{pidx}")
            yv[(bi, pidx)] = v
            vs.append(v)
            tard = max(0, pl["exit"] - due)
            pref_pen = s_max - prefs[pl["bay"]]
            base_cost[(bi, pidx)] = int(round(SU * (w1 * tard + w3 * pref_pen)))
            wl_terms[pl["bay"]].append((wl, v))
        m.AddExactlyOne(vs)

    for (n1, n2) in incompat_pairs:
        m.Add(yv[n1] + yv[n2] <= 1)

    obj_terms = [base_cost[k] * v for k, v in yv.items()]

    # Imbalance: obj2 = max_{p!=q} |u_p*load_p - u_q*load_q|. Linearize with a
    # single Zmax var (SU-scaled to match base_cost's SU factor).
    if n_bays >= 2 and w2 != 0:
        wl_expr = []
        big = 0
        for j in range(n_bays):
            terms = wl_terms[j]
            wl_expr.append(sum(c * v for c, v in terms) if terms else 0)
            big += su[j] * sum(c for c, _ in terms)
        zmax = m.NewIntVar(0, max(1, big), "zmax")
        for p in range(n_bays):
            for qq in range(n_bays):
                if p == qq:
                    continue
                m.Add(zmax >= su[p] * wl_expr[p] - su[qq] * wl_expr[qq])
        obj_terms.append(int(round(w2)) * zmax)

    m.Minimize(sum(obj_terms))

    # Warm start: the best feasible harvested solution (all its placements are in
    # the pool by construction).
    if warm_assign is not None:
        idx = {}
        for bi, plist in pool.items():
            for pidx, pl in enumerate(plist):
                idx[(bi, pl["bay"], pl["x"], pl["y"], pl["oi"],
                     pl["entry"], pl["exit"])] = pidx
        ok = True
        hints = []
        for bi, a in warm_assign.items():
            key = (bi, a["bay_id"], a["x"], a["y"], a["orient_idx"],
                   a["entry_time"], a["exit_time"])
            pidx = idx.get(key)
            if pidx is None:
                ok = False
                break
            hints.append((bi, pidx))
        if ok:
            for (bi, pidx) in hints:
                for pp in range(len(pool[bi])):
                    m.AddHint(yv[(bi, pp)], 1 if pp == pidx else 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget_s)
    solver.parameters.num_search_workers = 4
    try:
        status = solver.Solve(m)
    except Exception:
        return None
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    merged = {}
    for bi, plist in pool.items():
        chosen = None
        for pidx in range(len(plist)):
            if solver.Value(yv[(bi, pidx)]):
                chosen = plist[pidx]
                break
        if chosen is None:
            return None
        merged[bi] = {
            "block_id": bi, "bay_id": chosen["bay"], "x": int(chosen["x"]),
            "y": int(chosen["y"]), "orient_idx": chosen["oi"],
            "entry_time": int(chosen["entry"]), "exit_time": int(chosen["exit"]),
        }
    return merged


# -----------------------------------------------------------------------------
# 5. REPLAY-FEASIBILITY REPAIR (order-dependent crane replay).
# -----------------------------------------------------------------------------

_BLOCK_RE = re.compile(r"block (\d+)")


def _repair_replay(prob_info, merged, warm_assign, rounds=3):
    """Rebuild ops + check_feasibility; per violating block revert to its
    warm-start placement. Up to `rounds` passes. Returns (assign, feasible)."""
    cur = {bi: dict(a) for bi, a in merged.items()}
    for _ in range(rounds + 1):
        sol = {"operations": M25._build_operations(cur)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            return cur, False
        if res.get("feasible"):
            return cur, True
        bad = set()
        for v in res.get("violations", []):
            for mm in _BLOCK_RE.findall(v):
                bad.add(int(mm))
        if not bad or warm_assign is None:
            return cur, False
        reverted = False
        for bi in bad:
            if bi in warm_assign and cur.get(bi) != warm_assign[bi]:
                cur[bi] = dict(warm_assign[bi])
                reverted = True
        if not reverted:
            return cur, False
    # final check after last revert round
    try:
        res = check_feasibility(prob_info, {"operations": M25._build_operations(cur)})
        return cur, bool(res.get("feasible"))
    except Exception:
        return cur, False


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------

def _verify(prob_info, assign):
    try:
        res = check_feasibility(prob_info, {"operations": M25._build_operations(assign)})
        return bool(res.get("feasible"))
    except Exception:
        return False


def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    n_blocks = len(blocks_data)
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = M25._bay_u(bays)

    def iobj(a):
        return M25._objective(a, blocks_data, bays, bay_u, w1, w2, w3)[0]

    # --- 1. HARVEST ---------------------------------------------------------
    harvest_tl = timelimit * 0.70
    try:
        M25._reset_caches()
        cands = _harvest(prob_info, harvest_tl, t_start)
    except Exception:
        cands = []

    # Fallbacks if harvest failed to produce anything usable.
    if not cands:
        try:
            return M25.algorithm(prob_info, max(1.0, timelimit - (time.time() - t_start)))
        except Exception:
            return {"operations": M25._build_operations(
                M25._empty_bay_solution(prob_info, bays))}

    # Dedup full solutions, sort by internal objective.
    uniq = {}
    for obj, assign in cands:
        if assign is None or len(assign) != n_blocks:
            continue
        sig = _sol_sig(assign)
        if sig not in uniq or obj < uniq[sig][0]:
            uniq[sig] = (obj, assign)
    harvested = sorted(uniq.values(), key=lambda c: c[0])
    n_distinct = len(harvested)

    # Best OFFICIALLY-feasible harvested solution = guaranteed fallback + warm.
    best_feasible = None
    for obj, assign in harvested[:12]:
        if _verify(prob_info, assign):
            best_feasible = assign
            break

    # --- 2. POOL (from the top-K distinct solutions) ------------------------
    K_SOL = 20
    pool_solutions = [a for _, a in harvested[:K_SOL]]
    if best_feasible is not None and all(
            _sol_sig(s) != _sol_sig(best_feasible) for s in pool_solutions):
        pool_solutions.append(best_feasible)
    pool = _build_pool(pool_solutions, n_blocks)
    pool_sizes = [len(p) for p in pool.values()]
    pool_avg = (sum(pool_sizes) / len(pool_sizes)) if pool_sizes else 0.0

    warm = best_feasible if best_feasible is not None else pool_solutions[0]
    warm_obj = iobj(warm)

    # --- 3. RECOMBINATION CP-SAT --------------------------------------------
    merged_gain = 0.0
    result_assign = best_feasible if best_feasible is not None else None
    result_obj = warm_obj if best_feasible is not None else float("inf")

    safety = min(max(3.0, timelimit * 0.05), 15.0)
    hard_stop = t_start + timelimit - safety
    can_solve = _HAVE_NUMPY and len(pool) == n_blocks and time.time() < hard_stop - 2.0

    n_pairs = n_checks = 0
    pair_timeout = False
    if can_solve:
        try:
            raster = M25._Raster(prob_info, bays)
            pre_deadline = min(hard_stop - 2.0,
                               time.time() + max(2.0, (hard_stop - time.time()) * 0.45))
            incompat, n_checks, pair_timeout = _precompute_pairs(
                raster, bays, blocks_data, pool, pre_deadline)
            n_pairs = len(incompat)
            solve_budget = hard_stop - time.time() - 1.0
            merged = _recombine(prob_info, bays, bay_u, w1, w2, w3, pool,
                                incompat, warm, solve_budget)
            if merged is not None:
                # --- 4. REPLAY REPAIR ---
                repaired, feasible = _repair_replay(prob_info, merged, warm, rounds=3)
                if feasible:
                    mobj = iobj(repaired)
                    if mobj < result_obj - 1e-9:
                        merged_gain = result_obj - mobj if result_obj < float("inf") else 0.0
                        result_assign = repaired
                        result_obj = mobj
        except Exception:
            pass

    # --- 5. OUTPUT: best of (merged-if-feasible, best harvested) ------------
    if result_assign is None or not _verify(prob_info, result_assign):
        # No feasible merge and no feasible harvested in the top-12: search
        # deeper for any feasible harvested, else empty-bay guarantee.
        result_assign = None
        for _, assign in harvested:
            if _verify(prob_info, assign):
                result_assign = assign
                break
        if result_assign is None:
            result_assign = M25._empty_bay_solution(prob_info, bays)
        result_obj = iobj(result_assign)

    print(f"[S4] own={result_obj:.0f} harvested={n_distinct} "
          f"pool_avg={pool_avg:.2f} merged_gain={merged_gain:.0f}"
          f"  (pairs={n_pairs} checks={n_checks}"
          f"{' TIMEOUT' if pair_timeout else ''} warm={warm_obj:.0f})",
          flush=True)
    return {"operations": M25._build_operations(result_assign)}


if __name__ == "__main__":
    import json
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        _HERE, "..", "train", "prob_1.json")
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    with open(path) as f:
        prob = json.load(f)
    t0 = time.time()
    sol = algorithm(prob, tl)
    dt = time.time() - t0
    res = check_feasibility(prob, sol)
    print(f"[main] {os.path.basename(path)} tl={tl} elapsed={dt:.1f}s "
          f"feasible={res['feasible']} obj={res.get('objective')}")
