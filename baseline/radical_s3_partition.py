# radical_s3_partition.py -- S3 of the radical-rewrite epoch (heuristic_32.md).
# =============================================================================
# PARTITION-FIRST search. The one axis no v1..v31 mechanism ever touched:
# WHICH BLOCKS COMPETE for the same floor. Bay assignment is normally an
# emergent accident of the local bay-choice economics inside v25's dispatcher.
# Here it becomes a first-class search level:
#
#   1. ASSIGNMENT MODEL (CP-SAT, no geometry): x[b,j] = block b -> bay j, only
#      where b FITS bay j in some orientation. Per-bay area-time capacity from
#      v25's realized burst densities (CAP_FRAC knob ~0.55-0.65), soft via an
#      overflow slack so structurally-overloaded instances (prob_26/27) stay
#      feasible. Objective = w3*preference + w2*workload-imbalance (linearized
#      max) + a congestion proxy (load above a smoothed per-bay share).
#   2. DIVERSITY: after each solution add a no-good cut forcing >= ceil(0.15*n)
#      assignment differences, re-solve, collect K diverse partitions within a
#      shared CP-SAT budget.
#   3. REALIZATION: per partition, deep-copy prob_info and REWRITE every block's
#      bay_preferences so the assigned bay is maximally preferred and all others
#      strongly inferior, then run v25's dispatcher + improver constrained to
#      the partition (bay economics + the improver's obj-gate both respect it).
#      obj3 is scored against the ORIGINAL preferences (true objective), and the
#      final ops are verified with utils.check_feasibility on the ORIGINAL
#      prob_info.
#   4. BUDGET: partitions realized serially (slice = remaining/(K-realized));
#      the best two by true objective get the leftover polish (v25._improve on
#      the ORIGINAL objective). Best-ever full solution always tracked.
#   5. Fallback: v25.algorithm(prob_info, remaining) on infeasibility / total
#      realization failure (prints [S3] FALLBACK); else [S3] own=... line.
#
# Reuses v25's raster/scan/dispatch/improve/objective machinery by import.
# Import-safe, __main__-guarded, single process (CP-SAT capped at 4 workers).
# =============================================================================

import os
import sys
import time
import math

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import myalgorithm_25 as M25          # v25 machinery (raster/dispatch/improve)

try:
    from utils import check_feasibility
except Exception:                      # pragma: no cover
    check_feasibility = None

try:
    from ortools.sat.python import cp_model
    _HAVE_CP = True
except Exception:                      # pragma: no cover
    cp_model = None
    _HAVE_CP = False


# -- knobs --------------------------------------------------------------------
CAP_FRAC_DEFAULT = 0.60    # per-bay area-time budget fraction (v25 densities 0.5-0.7)
K_PARTITIONS = 5           # diverse partitions to enumerate
DIFF_FRAC = 0.15           # no-good cut: >= ceil(DIFF_FRAC*n) assignment changes
CONG_KNOB = 1.0            # congestion-proxy weight multiplier
CP_TOTAL_CAP = 90.0        # max wall seconds for the whole CP-SAT phase
CP_FIRST_CAP = 18.0        # max wall seconds for the first (warm) solve
_PREF_LOCK = 10 ** 6       # overridden preference gap that locks the partition


# =============================================================================
# 1. ASSIGNMENT MODEL + 2. DIVERSITY ENUMERATION
# =============================================================================

def _feasible_bays(blocks, bays):
    """For each block, the set of bay indices it fits in SOME orientation
    (empty-bay bbox test via v25 geometry). Blocks that fit nowhere (should not
    happen on valid instances) are allowed everywhere so the model stays sat."""
    m = len(bays)
    out = []
    for b in blocks:
        oris = M25._unique_orients(b)
        fit = [j for j in range(m)
               if any(M25._orient_fits(b, oi, bays[j]) for oi in oris)]
        out.append(fit if fit else list(range(m)))
    return out


def _enumerate_partitions(prob_info, bays, cap_frac, k, cp_total_s, cp_first_s,
                          debug=False):
    """Solve the assignment CP-SAT and enumerate up to `k` diverse partitions.
    Returns (partitions, capfrac_used) where each partition is a list assign[b]
    = bay index. Empty list if CP-SAT unavailable / first solve fails."""
    if not _HAVE_CP:
        return [], cap_frac
    blocks = prob_info["blocks"]
    n = len(blocks)
    m = len(bays)
    w = prob_info.get("weights", {})
    w1 = float(w.get("w1", 1.0)); w2 = float(w.get("w2", 1.0))
    w3 = float(w.get("w3", 1.0))

    feas = _feasible_bays(blocks, bays)

    # ---- area-time capacity, scaled to keep CP-SAT coefficients bounded ------
    areas = [M25._min_area(b) for b in blocks]
    procs = [max(1, int(b["processing_time"])) for b in blocks]
    raw_load = [areas[i] * procs[i] for i in range(n)]
    total_demand = sum(raw_load) or 1.0
    scale = max(1.0, total_demand / 50000.0)          # -> loads ~O(5e4) total
    load = [max(1, int(round(rl / scale))) for rl in raw_load]

    bay_area = [b.width * b.height for b in bays]
    total_area = sum(bay_area) or 1.0
    rmin = min(b["release_time"] for b in blocks)
    dmax = max(b["due_date"] for b in blocks)
    horizon = max(1, int(dmax - rmin))                # matches _overload_ratio
    cap = [int(round(cap_frac * bay_area[j] * horizon / scale)) for j in range(m)]
    total_load = sum(load)
    share = [int(round(total_load * bay_area[j] / total_area)) for j in range(m)]

    # ---- preference penalties (integer) --------------------------------------
    maxpref = [max(b["bay_preferences"]) for b in blocks]
    pref_pen = [[int(maxpref[i] - blocks[i]["bay_preferences"][j]) for j in range(m)]
                for i in range(n)]

    # ---- workload (for the balance term), scaled bay-utilization -------------
    workload = [float(b["workload"]) for b in blocks]
    bay_u = M25._bay_u(bays)
    bu_int = [max(1, int(round(u * 1000))) for u in bay_u]

    model = cp_model.CpModel()
    x = {}
    for i in range(n):
        for j in feas[i]:
            x[(i, j)] = model.NewBoolVar("x_%d_%d" % (i, j))
        model.AddExactlyOne(x[(i, j)] for j in feas[i])

    load_j = []          # scaled area-time load per bay
    wl_j = []            # scaled workload per bay (bu_int * workload)
    over = []            # overflow above hard-ish capacity (soft)
    cong = []            # load above the smoothed fair share (soft)
    for j in range(m):
        members = [(i, x[(i, j)]) for i in range(n) if (i, j) in x]
        lj = model.NewIntVar(0, total_load, "load_%d" % j)
        model.Add(lj == sum(load[i] * v for i, v in members))
        load_j.append(lj)
        wj = model.NewIntVar(0, int(sum(bu_int[j] * wl for wl in workload)) + 1,
                             "wl_%d" % j)
        model.Add(wj == sum(int(round(bu_int[j] * workload[i])) * v
                            for i, v in members))
        wl_j.append(wj)
        ov = model.NewIntVar(0, total_load, "over_%d" % j)
        model.Add(ov >= lj - cap[j])
        over.append(ov)
        cg = model.NewIntVar(0, total_load, "cong_%d" % j)
        model.Add(cg >= lj - share[j])
        cong.append(cg)

    # linearized workload-imbalance upper bound (the Z2 max over bay pairs)
    imbal_ub = model.NewIntVar(0, int(sum(bu_int[j] * sum(workload)
                                          for j in range(m))) + 1, "imbal")
    for p in range(m):
        for q in range(m):
            if p != q:
                model.Add(imbal_ub >= wl_j[p] - wl_j[q])

    # ---- objective coefficients (milli-objective units) ----------------------
    coef_pref = max(1, int(round(1000 * w3)))
    coef_imbal = int(round(w2))                       # wl_j already carries *1000
    base_scale = max(coef_pref, coef_imbal, 1)
    coef_over = 100 * base_scale                       # capacity respected first
    coef_cong = max(1, int(round(CONG_KNOB * 0.01 * base_scale)))

    obj_terms = []
    for i in range(n):
        for j in feas[i]:
            if pref_pen[i][j]:
                obj_terms.append(coef_pref * pref_pen[i][j] * x[(i, j)])
    if coef_imbal > 0:
        obj_terms.append(coef_imbal * imbal_ub)
    for j in range(m):
        obj_terms.append(coef_over * over[j])
        obj_terms.append(coef_cong * cong[j])
    model.Minimize(sum(obj_terms))

    # ---- solve + no-good diversity loop --------------------------------------
    partitions = []
    t_phase0 = time.time()
    cp_deadline = t_phase0 + cp_total_s
    thresh = max(1, int(math.ceil(DIFF_FRAC * n)))
    while len(partitions) < k and time.time() < cp_deadline:
        remaining = cp_deadline - time.time()
        if remaining < 1.0:
            break
        budget = min(cp_first_s if not partitions else max(4.0, remaining),
                     remaining)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(budget)
        solver.parameters.num_search_workers = 4        # single process, <=4 threads
        st = solver.Solve(model)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
        assign = [0] * n
        for i in range(n):
            for j in feas[i]:
                if solver.Value(x[(i, j)]):
                    assign[i] = j
                    break
        partitions.append(assign)
        if debug:
            print("[S3-cp] partition %d obj=%d bays=%s" % (
                len(partitions), int(solver.ObjectiveValue()),
                [sum(1 for a in assign if a == j) for j in range(m)]))
        # no-good: at most n - thresh blocks keep this exact assignment
        model.Add(sum(x[(i, assign[i])] for i in range(n)) <= n - thresh)

    return partitions, cap_frac


# =============================================================================
# 3. REALIZATION per partition (v25 dispatcher constrained to the partition)
# =============================================================================

def _partition_prob(base, assign):
    """Shallow-copy prob_info, rewriting each block's bay_preferences so its
    assigned bay is maximally preferred (_PREF_LOCK) and all others 0. The v25
    bay economics then lock onto the partition; the improver's obj-gate treats
    any off-partition placement as a _PREF_LOCK*w3 penalty (soft enforcement)."""
    m = len(base["bays"])
    new_blocks = []
    for i, b in enumerate(base["blocks"]):
        nb = dict(b)
        prefs = [0] * m
        prefs[assign[i]] = _PREF_LOCK
        nb["bay_preferences"] = prefs
        new_blocks.append(nb)
    p = dict(base)
    p["blocks"] = new_blocks
    return p


def _sync_raster(raster, assign_dict):
    """Rebuild raster occupancy from a full assignment dict (for polishing an
    assignment the raster was not last populated with)."""
    if raster is None:
        return
    raster.reset()
    for bi, a in assign_dict.items():
        raster.add(a["bay_id"], bi, a["orient_idx"], a["x"], a["y"])


def _realize(part_prob, bays, bay_u, w1, w2, w3, raster, slice_deadline, seed):
    """Dispatch a partition-locked construction then improve it within the slice
    (both on the LOCKED preferences, so the partition is respected). Returns the
    assignment dict, or None on failure."""
    forced = M25._is_forced(part_prob, bays)
    if raster is not None:
        raster.reset()
        assign = M25._dispatch_construct(
            part_prob, bays, bay_u, w1, w2, w3, slice_deadline, raster,
            kappa=1.0, gamma=0.5, score_pos=True, beam=False)
    else:
        # no numpy -> raster-free earliest-slot construction
        order = M25._edd_order(part_prob["blocks"])
        assign = M25._construct(part_prob, order, bays, bay_u, w1, w2, w3,
                                time.time(), slice_deadline, forced=forced)
    if time.time() < slice_deadline - 0.5:
        assign, _ = M25._improve(
            part_prob, assign, bays, bay_u, w1, w2, w3, slice_deadline, forced,
            seed=seed, raster=raster)
    return assign


# =============================================================================
# top-level
# =============================================================================

def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    debug = bool(os.environ.get("OGC_S3_DEBUG"))
    try:
        return _algorithm(prob_info, timelimit, t_start, debug)
    except Exception as e:               # any structural failure -> v25
        if debug:
            import traceback
            traceback.print_exc()
        print("[S3] FALLBACK")
        remaining = max(5.0, timelimit - (time.time() - t_start))
        return M25.algorithm(prob_info, remaining)


def _algorithm(prob_info, timelimit, t_start, debug):
    bays = [M25.Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks = prob_info["blocks"]
    n = len(blocks)
    w = prob_info.get("weights", {})
    w1 = float(w.get("w1", 1.0)); w2 = float(w.get("w2", 1.0))
    w3 = float(w.get("w3", 1.0))
    bay_u = M25._bay_u(bays)
    cap_frac = float(os.environ.get("OGC_S3_CAPFRAC", CAP_FRAC_DEFAULT))

    M25._reset_caches()                  # geometry caches are preference-independent

    def true_obj(assign):
        # obj3 scored against the ORIGINAL preferences (blocks == original)
        return M25._objective(assign, blocks, bays, bay_u, w1, w2, w3)[0]

    # reserve time for the final feasibility verification(s)
    verify_reserve = min(max(3.0, timelimit * 0.06), 15.0)
    hard_deadline = t_start + timelimit - verify_reserve

    # ---- CP-SAT phase --------------------------------------------------------
    cp_total = min(CP_TOTAL_CAP, max(6.0, timelimit * 0.35))
    cp_total = min(cp_total, hard_deadline - time.time() - 5.0)
    cp_first = min(CP_FIRST_CAP, cp_total * 0.5)
    partitions, capfrac_used = ([], cap_frac)
    if cp_total > 2.0:
        partitions, capfrac_used = _enumerate_partitions(
            prob_info, bays, cap_frac, K_PARTITIONS, cp_total, cp_first, debug)
    K = len(partitions)

    if debug and K >= 2:
        for a in range(K):
            for b in range(a + 1, K):
                d = sum(1 for i in range(n) if partitions[a][i] != partitions[b][i])
                print("[S3-div] parts %d vs %d differ in %d/%d blocks (%.1f%%)"
                      % (a, b, d, n, 100.0 * d / n))

    if K == 0:
        print("[S3] FALLBACK")
        return M25.algorithm(prob_info, max(5.0, hard_deadline - time.time()
                                            + verify_reserve))

    # ---- realization phase (serial, slice = remaining/(K - realized)) --------
    raster = M25._Raster(prob_info, bays) if M25._HAVE_NUMPY else None
    # reserve a slice of the realization budget for polishing the best two
    realize_end = hard_deadline
    total_realize = realize_end - time.time()
    polish_reserve = max(0.0, 0.25 * total_realize)
    phaseA_end = realize_end - polish_reserve

    candidates = []       # (true_obj, assign, partition_index)
    for i in range(K):
        now = time.time()
        left = K - i
        slice_dl = min(phaseA_end, now + max(2.0, (phaseA_end - now) / left))
        if slice_dl - now < 1.0:
            break
        part_prob = _partition_prob(prob_info, partitions[i])
        try:
            assign = _realize(part_prob, bays, bay_u, w1, w2, w3, raster,
                              slice_dl, seed=4200 + i)
        except Exception:
            if debug:
                import traceback
                traceback.print_exc()
            continue
        if assign is None or len(assign) != n:
            continue
        ob = true_obj(assign)
        candidates.append((ob, assign, i))
        if debug:
            print("[S3-real] partition %d -> true_obj=%.0f" % (i, ob))

    if not candidates:
        print("[S3] FALLBACK")
        return M25.algorithm(prob_info, max(5.0, realize_end - time.time()
                                            + verify_reserve))

    # ---- polish the best two on the TRUE objective (original preferences) ----
    candidates.sort(key=lambda c: c[0])
    best_two = candidates[:2]
    polished = list(candidates)
    for rank, (ob, assign, pidx) in enumerate(best_two):
        now = time.time()
        if realize_end - now < 1.5:
            break
        share = (realize_end - now) / (len(best_two) - rank)
        pol_dl = min(realize_end, now + share)
        try:
            _sync_raster(raster, assign)
            forced = M25._is_forced(prob_info, bays)
            imp, _ = M25._improve(prob_info, assign, bays, bay_u, w1, w2, w3,
                                  pol_dl, forced, seed=9100 + rank, raster=raster)
            polished.append((true_obj(imp), imp, pidx))
        except Exception:
            if debug:
                import traceback
                traceback.print_exc()

    # ---- verify best-first on the ORIGINAL prob_info -------------------------
    polished.sort(key=lambda c: c[0])
    if check_feasibility is None:
        best = polished[0]
        print("[S3] own=%.0f K=%d best_partition=%d capfrac=%.3f"
              % (best[0], K, best[2], capfrac_used))
        return {"operations": M25._build_operations(best[1])}

    for ob, assign, pidx in polished:
        sol = {"operations": M25._build_operations(assign)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            continue
        if res.get("feasible"):
            print("[S3] own=%.0f K=%d best_partition=%d capfrac=%.3f"
                  % (ob, K, pidx, capfrac_used))
            return sol

    # every realized/polished candidate failed official verification -> v25
    print("[S3] FALLBACK")
    return M25.algorithm(prob_info, max(5.0, realize_end - time.time()
                                        + verify_reserve))


if __name__ == "__main__":
    import json
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        _HERE, "..", "train", "prob_1.json")
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    with open(path) as f:
        prob = json.load(f)
    os.environ.setdefault("OGC_S3_DEBUG", "1")
    t0 = time.time()
    sol = algorithm(prob, tl)
    el = time.time() - t0
    ok = None
    if check_feasibility is not None:
        try:
            r = check_feasibility(prob, sol)
            ok = r.get("feasible")
            print("[S3-smoke] feasible=%s obj=%s obj1=%s obj2=%s obj3=%s" % (
                ok, r.get("objective"), r.get("obj1"), r.get("obj2"),
                r.get("obj3")))
        except Exception as e:
            print("[S3-smoke] check_feasibility error:", e)
    print("[S3-smoke] instance=%s n=%d bays=%d elapsed=%.1fs ops_times=%d" % (
        prob.get("name", "?"), len(prob["blocks"]), len(prob["bays"]), el,
        len(sol["operations"])))
