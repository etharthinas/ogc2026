# radical_s2_backward.py -- RADICAL EPOCH strategy S2 (heuristic_32.md).
# =============================================================================
# BACKWARD (due-date-anchored) construction. Every prior version (v3..v25)
# builds FORWARD from releases and lets tardiness be whatever is left over.
# S2 builds RIGHT-TO-LEFT in time: process blocks in DESC due order, anchor
# each block's exit at its due date, and place it at the LATEST feasible entry
# (scanning earlier only when blocked). The fixed point of backward-greedy is a
# different basin family than forward-greedy's -- the cheapest true paradigm
# flip. All heavy machinery (raster, _can_place, _order_cells, _improve,
# operations builder, objective) is REUSED from v25 by import.
#
# WHY THE FEASIBILITY CHECK IS DIRECTION-AGNOSTIC (the crux):
#   Co-residency collisions + crane entry/exit obstruction are properties of
#   the REAL-TIME schedule state, not of the order blocks were placed. v25's
#   `_can_place(bay, sched, new, entry, exit)` evaluates exactly those rules
#   against the real-time intervals of already-placed blocks:
#     * crane ENTRY check at `entry` vs blocks resident at that instant,
#     * crane EXIT  check at `exit`  vs blocks resident at that instant,
#     * pairwise collision over the overlap, plus the replay tie rules.
#   So "reverse-time semantics" require NO special code: a block processed
#   later in build order (earlier due) simply lands at an EARLIER real-time
#   interval, and `_can_place` catches every interaction with the later-due
#   blocks already sitting at later real times. The ONLY thing that reverses is
#   the SEARCH DIRECTION over candidate entry times: we scan LATEST-first and
#   take the first feasible, whereas forward construction scans earliest-first.
#
# Guaranteed feasible: self-checks with utils.check_feasibility and delegates
# to v25.algorithm on any infeasibility. Import-safe; single process.
# =============================================================================

import time
import math

import myalgorithm_25 as M25
from utils import check_feasibility


# -----------------------------------------------------------------------------
# Reverse-direction placement search: LATEST feasible entry <= max(release,
# due-proc), scanning earlier candidate entry times only when blocked.
# -----------------------------------------------------------------------------

def _place_backward(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                    raster, time_cap=14, pos_cap=24):
    """Find the placement whose exit sits as close to the due date as feasible.

    For each bay we enumerate candidate entry times DESCENDING from the ALAP
    anchor and return the first (latest) feasible one; across bays we pick the
    lowest v25-objective contribution (tardiness, then imbalance, then
    preference). Returns a place tuple (bay_id, x, y, oi, entry, exit) or None.

    ALAP anchor = max(release, due-proc): exit is anchored at the due date when
    that is reachable (due-proc >= release), else at release+proc (the minimum
    possible exit) for a structurally tardy block. Either way entry >= release,
    so the backward pass is release-legal by construction.
    """
    release = int(blk["release_time"])
    due = int(blk["due_date"])
    proc = int(blk["processing_time"])
    workload = blk["workload"]
    prefs = blk["bay_preferences"]
    s_max = max(prefs)
    orients = M25._unique_orients(blk)
    n_bays = len(bays)
    alap = max(release, due - proc)

    def bscore(bay_id, tard, top_y):
        new_load = bay_loads[bay_id] + workload
        imbal = max((abs(bay_u[bay_id] * new_load - bay_u[j] * bay_loads[j])
                     for j in range(n_bays) if j != bay_id), default=0.0)
        return (w1 * tard + w2 * imbal + w3 * (s_max - prefs[bay_id])
                + 1e-4 * top_y)

    bay_order = sorted(range(n_bays), key=lambda j: prefs[j], reverse=True)
    best = None
    best_score = float("inf")

    for bay_id in bay_order:
        bay = bays[bay_id]
        sched_bay = sched[bay_id]
        # Candidate entry times in [release, alap], collected from ALAP itself,
        # release, and contact points against already-placed blocks (align our
        # window's edges with theirs -- the reverse of forward contact times).
        times = {alap, release}
        for it in sched_bay:
            a, e = it[1], it[2]
            for t in (e, e - proc, a, a - proc):
                if release <= t <= alap:
                    times.add(int(t))
        # DESCENDING: latest entry first. Cap breadth like v25's slot search.
        ordered = sorted(times, reverse=True)[:time_cap]

        slot = None
        for t in ordered:
            exit_t = t + proc
            relx = M25._time_overlap_rel(sched_bay, t, exit_t)
            for oi in orients:
                if not M25._orient_fits(blk, oi, bay):
                    continue
                if raster is not None:
                    actives = [(it0.block_id, it0.orient_idx, it0.x, it0.y)
                               for (it0, _a, _e) in relx]
                    feas, cx0, cy0, occ_fp = raster.scan_scoped(
                        bay_id, actives, bi, oi)
                    if feas is None or not feas.any():
                        continue
                    cells = M25._order_cells(
                        raster, feas, cx0, cy0, bi, oi, raster.W[bay_id],
                        occ_fp, True, None)
                    tried = 0
                    for (x, y) in cells:
                        nb = M25._mkblock(bi, blk, x, y, oi)
                        if M25._can_place(bay, relx, nb, t, exit_t):
                            slot = (oi, x, y, t)
                            break
                        tried += 1
                        if tried >= pos_cap:
                            break
                else:
                    blk_bb = M25._orient_bbox(blk, oi)
                    active_blocks = [rr[0] for rr in relx]
                    for (x, y) in M25._candidate_positions(
                            bay, active_blocks, blk_bb, cap=pos_cap):
                        nb = M25._mkblock(bi, blk, x, y, oi)
                        if M25._can_place(bay, relx, nb, t, exit_t):
                            slot = (oi, x, y, t)
                            break
                if slot is not None:
                    break
            if slot is not None:
                break

        if slot is not None:
            oi, x, y, entry = slot
            exit_t = entry + proc
            blk_bb = M25._orient_bbox(blk, oi)
            tard = max(0.0, exit_t - due)
            sc = bscore(bay_id, tard, top_y=y + blk_bb[3])
            if sc < best_score:
                best_score = sc
                best = (bay_id, x, y, oi, entry, exit_t)

    return best


# -----------------------------------------------------------------------------
# Legalization.
# -----------------------------------------------------------------------------

def _legalize_release(assignments, prob_info, bays, bay_u, w1, w2, w3,
                      raster, forced):
    """Sub-pass (a): any block whose entry < release is illegal. Remove it and
    re-place FORWARD at the earliest feasible entry >= release against the
    remaining schedule (v25 `_place_block`; `_force_place` guarantee on
    failure). Defensive here -- the ALAP anchor keeps entry >= release -- but
    kept for correctness and to honor the S2 protocol. Returns repaired count.
    """
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    bad = [bi for bi, a in assignments.items()
           if a["entry_time"] < int(blocks_data[bi]["release_time"])]
    if not bad:
        return 0
    for bi in bad:
        assignments.pop(bi, None)
    sched, bay_loads = M25._rebuild_sched(assignments, blocks_data, n_bays)
    for bi in sorted(bad, key=lambda i: (blocks_data[i]["due_date"],
                                         blocks_data[i]["processing_time"])):
        blk = blocks_data[bi]
        place = M25._place_block(bi, blk, bays, sched, bay_loads, bay_u,
                                 w1, w2, w3, forced=forced,
                                 slot_time_cap=40, slot_pos_cap=30,
                                 raster=raster)
        if place is None:
            place = M25._force_place(bi, blk, bays, sched)
        M25._add(sched, bay_loads, assignments, bi, blk, place)
    return len(bad)


def _left_shift(assignments, prob_info, bays, deadline):
    """Sub-pass (b): global LEFT-SHIFT. Process blocks in ASC entry order; for
    each, try moving its entry EARLIER (>= release) at fixed (bay,x,y,orient) if
    crane + collision allow against the current schedule. This drains the
    right-shift slack the backward pass introduces (blocks anchored near their
    due dates while the floor ahead of them is free). Coordinate descent in ASC
    order so a block's vacated tail is visible to later (higher-entry) blocks.
    Returns the number of blocks actually shifted.
    """
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    # per-bay membership (block ids), refreshed from assignments as we mutate
    order = sorted(assignments,
                   key=lambda bi: (assignments[bi]["entry_time"], bi))
    moved = 0
    for bi in order:
        if time.time() > deadline:
            break
        a = assignments[bi]
        bay_id = a["bay_id"]
        bay = bays[bay_id]
        blk = blocks_data[bi]
        release = int(blk["release_time"])
        proc = int(blk["processing_time"])
        e0 = a["entry_time"]
        if e0 <= release:
            continue
        # schedule of this bay excluding bi (current real-time state)
        sched_excl = []
        for bj, aj in assignments.items():
            if bj == bi or aj["bay_id"] != bay_id:
                continue
            nbj = M25._mkblock(bj, blocks_data[bj], aj["x"], aj["y"],
                               aj["orient_idx"])
            sched_excl.append((nbj, aj["entry_time"], aj["exit_time"]))
        # candidate earlier entries: release + neighbour exits in [release, e0)
        cand = {release}
        for (_nb, aj, ej) in sched_excl:
            for t in (ej, aj - proc):
                if release <= t < e0:
                    cand.add(int(t))
        nb = M25._mkblock(bi, blk, a["x"], a["y"], a["orient_idx"])
        for t in sorted(cand):          # ASCENDING -> earliest feasible wins
            if t >= e0:
                break
            if M25._can_place(bay, sched_excl, nb, t, t + proc):
                a["entry_time"] = int(t)
                a["exit_time"] = int(t + proc)
                moved += 1
                break
    return moved


# -----------------------------------------------------------------------------
# Top-level backward construction + legalize + polish.
# -----------------------------------------------------------------------------

def _backward_construct(prob_info, bays, bay_u, w1, w2, w3, raster, forced):
    """Run the backward pass; returns (assignments, backward_placed_count).
    Blocks the reverse search cannot place are captured and forward-placed
    here (still release-legal) so the assignment is always complete."""
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    # DESC due order; tie -> longer processing first (harder blocks anchored
    # into late space first).
    order = sorted(range(len(blocks_data)),
                   key=lambda i: (-int(blocks_data[i]["due_date"]),
                                  -int(blocks_data[i]["processing_time"]), i))
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    assignments = {}
    placed = 0
    unplaced = []
    for bi in order:
        blk = blocks_data[bi]
        place = _place_backward(bi, blk, bays, sched, bay_loads, bay_u,
                                w1, w2, w3, raster)
        if place is None:
            unplaced.append(bi)
            continue
        M25._add(sched, bay_loads, assignments, bi, blk, place)
        placed += 1
    # complete the assignment with forward placement for any reverse-failures
    for bi in unplaced:
        blk = blocks_data[bi]
        place = M25._place_block(bi, blk, bays, sched, bay_loads, bay_u,
                                 w1, w2, w3, forced=forced,
                                 slot_time_cap=40, slot_pos_cap=30,
                                 raster=raster)
        if place is None:
            place = M25._force_place(bi, blk, bays, sched)
        M25._add(sched, bay_loads, assignments, bi, blk, place)
    return assignments, placed


def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    try:
        return _run(prob_info, timelimit, t_start)
    except Exception:
        # Any structural failure -> delegate to v25 with the remaining budget.
        remaining = max(1.0, timelimit - (time.time() - t_start))
        print("[S2] FALLBACK", flush=True)
        return M25.algorithm(prob_info, remaining)


def _run(prob_info, timelimit, t_start):
    M25._reset_caches()
    bays = [M25.Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = M25._bay_u(bays)
    forced = M25._is_forced(prob_info, bays)
    raster = M25._Raster(prob_info, bays) if M25._HAVE_NUMPY else None

    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    deadline = t_start + timelimit - reserve

    # 1. BACKWARD PASS ------------------------------------------------------
    assignments, backward_placed = _backward_construct(
        prob_info, bays, bay_u, w1, w2, w3, raster, forced)

    # 2. LEGALIZATION -------------------------------------------------------
    repaired = _legalize_release(assignments, prob_info, bays, bay_u,
                                 w1, w2, w3, raster, forced)
    shifted = _left_shift(assignments, prob_info, bays, deadline)
    legalized = repaired + shifted

    # 3. POLISH -- v25 basin-hopping improver on the legalized assignment ---
    if time.time() < deadline:
        try:
            improved, _obj = M25._improve(
                prob_info, assignments, bays, bay_u, w1, w2, w3, deadline,
                forced, seed=4242, raster=raster,
                repack_every=(3 if forced else 4), xbay=forced,
                repack_win_scale=2.0)
            if improved is not None and len(improved) == len(assignments):
                assignments = improved
        except Exception:
            pass

    own_obj = M25._objective(assignments, blocks_data, bays, bay_u,
                             w1, w2, w3)[0]

    # 4. OUTPUT + SELF-CHECK ------------------------------------------------
    sol = {"operations": M25._build_operations(assignments)}
    ok = False
    try:
        res = check_feasibility(prob_info, sol)
        ok = bool(res.get("feasible"))
    except Exception:
        ok = False

    if not ok:
        remaining = max(1.0, timelimit - (time.time() - t_start))
        print("[S2] FALLBACK", flush=True)
        return M25.algorithm(prob_info, remaining)

    print(f"[S2] own={own_obj:.0f} backward_placed={backward_placed} "
          f"legalized={legalized}", flush=True)
    return sol


if __name__ == "__main__":
    import sys
    import json
    path = sys.argv[1] if len(sys.argv) > 1 else "../train/prob_1.json"
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    with open(path, "r") as f:
        prob = json.load(f)
    t0 = time.time()
    sol = algorithm(prob, tl)
    dt = time.time() - t0
    res = check_feasibility(prob, sol)
    print(f"instance={prob.get('name')} elapsed={dt:.1f}s "
          f"feasible={res['feasible']} objective={res.get('objective')}")
