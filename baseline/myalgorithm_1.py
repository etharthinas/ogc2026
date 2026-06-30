# myalgorithm.py
# =============================================================================
# Congestion-First Construction Heuristic for the OGC 2026 Grand Shipyard Puzzle
# =============================================================================
#
# Implements the heuristic specified in heuristic.md:
#
#   1. Anchor every block as-late-as-possible (ALAP): aim to exit exactly at its
#      due date so tardiness (Z1, the dominant objective term) is zero.
#   2. Build a global footprint-area congestion profile over those ALAP
#      intervals; the peak is a free feasibility oracle (demand > capacity =>
#      zero tardiness is provably impossible for this instance).
#   3. Place the most-constrained blocks first -- those in the most congested
#      time windows, tie-broken by least slack / largest / most-layered.
#   4. For each block pick (bay, orientation, x, y, entry, exit) with exit <= due
#      when possible, sliding earlier (left-shift) within its slack to dodge
#      conflicts; accept tardiness only when no zero-tardiness slot exists.
#   5. Enforce the BURIAL RULE during placement: a new block may never break the
#      crane entry/exit of an already-placed block (the bug the baseline misses).
#   6. Keep a guaranteed-feasible empty-bay fallback as the incumbent so the
#      function can never return an infeasible solution.
#
# The required entry point `algorithm(prob_info, timelimit)` is at the bottom.
# Single-file: no extra modules, only `utils` (the official, unmodified checker).

import math
import time

from utils import (
    Bay, Block,
    check_entry, check_exit, check_collisions, check_feasibility,
    _resolve_layers, _bounding_box, _bb_overlap,
)


# -----------------------------------------------------------------------------
# Static per-block geometry helpers
# -----------------------------------------------------------------------------

def _orient_bbox(block_data, oi):
    """Local bounding box (min_x, min_y, max_x, max_y) of orientation oi,
    relative to the reference point (first vertex of first layer = (0,0))."""
    layers = _resolve_layers(block_data["shape"][oi]["layers"])
    if not layers:
        return (0.0, 0.0, 1.0, 1.0)
    return _bounding_box([v for l in layers for v in l])


def _orient_area(block_data, oi):
    bb = _orient_bbox(block_data, oi)
    return max(1.0, (bb[2] - bb[0]) * (bb[3] - bb[1]))


def _min_area(block_data):
    return min(_orient_area(block_data, oi) for oi in range(len(block_data["shape"])))


def _max_layers(block_data):
    return max(len(_resolve_layers(o["layers"])) for o in block_data["shape"])


def _orient_fits(block_data, oi, bay):
    """True if orientation oi has at least one valid integer reference position."""
    lx0, ly0, lx1, ly1 = _orient_bbox(block_data, oi)
    return (math.ceil(-lx0) <= math.floor(bay.width - lx1) and
            math.ceil(-ly0) <= math.floor(bay.height - ly1))


def _unique_orients(block_data):
    """Distinct orientations by (bounding box, layer count). Many of the up-to-8
    stored orientations are rotations sharing a footprint; trying one per
    distinct geometry keeps the search fast without losing real options."""
    seen = {}
    for oi in range(len(block_data["shape"])):
        bb = _orient_bbox(block_data, oi)
        nl = len(_resolve_layers(block_data["shape"][oi]["layers"]))
        key = (round(bb[0], 3), round(bb[1], 3), round(bb[2], 3), round(bb[3], 3), nl)
        if key not in seen:
            seen[key] = oi
    return list(seen.values())


# -----------------------------------------------------------------------------
# Candidate reference-point positions (bottom-left + contact points)
# -----------------------------------------------------------------------------

def _candidate_positions(bay, placed_blocks, blk_bb, cap=40):
    """Integer (x, y) reference-point candidates using a bottom-left heuristic
    augmented with right/top edge contacts of already-placed blocks."""
    lx0, ly0, lx1, ly1 = blk_bb
    xs = {max(0, math.ceil(-lx0))}
    ys = {max(0, math.ceil(-ly0))}
    for b in placed_blocks:
        bb = b.bounding_rect()
        xs.add(int(math.ceil(bb[2] - lx0)))
        ys.add(int(math.ceil(bb[3] - ly0)))
    out = []
    for x in sorted(xs):
        if x + lx1 > bay.width + 1e-6 or x + lx0 < -1e-6:
            continue
        for y in sorted(ys):
            if y + ly1 > bay.height + 1e-6 or y + ly0 < -1e-6:
                continue
            out.append((int(x), int(y)))
            if len(out) >= cap:
                return out
    return out


# -----------------------------------------------------------------------------
# Time-overlap + crane-presence helpers (mirror check_feasibility semantics)
# -----------------------------------------------------------------------------

def _overlaps(a1, e1, a2, e2):
    return a1 < e2 and a2 < e1


def _present_at_entry(t, x_id, sched):
    """Blocks present in the bay at the instant block x_id descends at time t.

    Mirrors Stage-5 replay ordering: at one time-point all EXITs precede all
    ENTRYs, and ENTRYs run in ascending block_id order. So a same-time block is
    already present iff it enters at t with a smaller id."""
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (a == t and b.block_id < x_id):
            out.append(b)
    return out


def _present_at_exit(t, x_id, sched):
    """Blocks present when block x_id is lifted out at time t. A same-time EXIT
    with a larger id is still present (lower ids exit first); same-time ENTRYs
    run after all exits, so they are absent."""
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (e == t and b.block_id > x_id):
            out.append(b)
    return out


# -----------------------------------------------------------------------------
# Incremental feasibility of placing one block into a bay's current state
# -----------------------------------------------------------------------------

def _can_place(bay, sched, new_blk, entry, exit_t):
    """Return True if placing new_blk at [entry, exit_t) is fully feasible given
    the blocks already in this bay (`sched` = list of (Block, a, e)).

    `sched` should already be pre-filtered to blocks whose footprint bounding
    box overlaps new_blk's -- crane obstruction and same-layer collision are
    both impossible without footprint overlap, so spatially-disjoint blocks
    cannot interact and are safely excluded.

    Checks, all with fast early-exit:
      * new block's own crane ENTRY (incl. bay-boundary) and EXIT,
      * the BURIAL RULE -- new block must not obstruct any already-placed
        block's crane entry or exit while it is co-present,
      * same-layer spatial collisions with co-present blocks.
    This is the local mirror of check_feasibility Stages 2-5 for a single
    incremental placement.
    """
    # Bay-boundary must hold regardless of other blocks.
    if not bay.contains_block(new_blk):
        return False
    full = sched + [(new_blk, entry, exit_t)]

    # -- New block's own descent --------------------------------------------
    pres = _present_at_entry(entry, new_blk.block_id, full)
    if check_entry(bay, pres, new_blk, fast=True):
        return False
    # -- New block's own ascent ---------------------------------------------
    pres = _present_at_exit(exit_t, new_blk.block_id, full)
    if check_exit(bay, pres, new_blk, fast=True):
        return False

    for b, a, e in sched:
        co_time = _overlaps(entry, exit_t, a, e)
        # -- Spatial collision among co-present blocks ----------------------
        if co_time and check_collisions(bay, [new_blk, b]):
            return False
        # -- Burial rule: does new block block b's descent? -----------------
        if (entry < a < exit_t) or (entry == a and new_blk.block_id < b.block_id):
            if check_entry(bay, [new_blk], b, fast=True):
                return False
        # -- Burial rule: does new block block b's ascent? ------------------
        if (entry < e < exit_t) or (exit_t == e and new_blk.block_id > b.block_id):
            if check_exit(bay, [new_blk], b, fast=True):
                return False
    return True


def _empty_bay_entry(sched, r_time, proc):
    """Earliest entry >= r_time at which the bay is completely empty for the
    whole [entry, entry+proc) window. Trivially crane-feasible (bay empty).

    `sched` entries are (Block, entry, exit, bbox); only the times are used."""
    entry = int(r_time)
    changed = True
    while changed:
        changed = False
        exit_t = entry + proc
        for it in sched:
            a, e = it[1], it[2]
            if _overlaps(entry, exit_t, a, e):
                entry = max(entry, e)
                changed = True
    return entry


# -----------------------------------------------------------------------------
# Slot search for a fixed (bay, orientation, position): ALAP then left-shift
# -----------------------------------------------------------------------------

def _rel_sched(sched, nb_bb):
    """The (Block, entry, exit) entries of `sched` whose cached footprint bbox
    overlaps nb_bb -- only these can obstruct the crane or collide (both require
    footprint overlap). `sched` entries are (Block, entry, exit, bbox)."""
    return [(it[0], it[1], it[2]) for it in sched if _bb_overlap(nb_bb, it[3])]


def _find_zero_slot(bay, sched, new_blk, release, due, proc):
    """Latest feasible ZERO-tardiness slot (exit <= due) for new_blk at its
    current placement, or None. ALAP: scan entry from due-proc down to release."""
    alap = due - proc
    if alap < release:
        return None
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    for entry in range(alap, release - 1, -1):
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    return None


def _find_tardy_slot(bay, sched, new_blk, release, due, proc, tardy_cap=48):
    """Least-tardy feasible slot for new_blk; empty-bay window as last resort."""
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    start = max(release, due - proc + 1)
    cand = {start}
    for _, _, e in rel:
        if e >= start:
            cand.add(e)
    for entry in sorted(cand)[:tardy_cap]:
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    entry = _empty_bay_entry(sched, release, proc)
    if _can_place(bay, rel, new_blk, entry, entry + proc):
        return entry
    return None


# -----------------------------------------------------------------------------
# Congestion profile + block ordering
# -----------------------------------------------------------------------------

def _canonical_interval(blk):
    """ALAP interval used for congestion estimation: exit at due date."""
    entry = max(blk["release_time"], blk["due_date"] - blk["processing_time"])
    return int(entry), int(entry + blk["processing_time"])


def _congestion_order(blocks_data, total_area):
    """Order block ids most-constrained-first and report the peak oracle.

    Pressure(i) = max over i's ALAP interval of demand(t)/total_area, i.e. how
    contested i's own time window is. Blocks are then sorted by
    (pressure desc, slack asc, area desc, layers desc)."""
    n = len(blocks_data)
    intervals = [_canonical_interval(b) for b in blocks_data]
    areas = [_min_area(b) for b in blocks_data]

    # Breakpoint sweep of area demand over time.
    events = {}
    for (a, e), ar in zip(intervals, areas):
        events[a] = events.get(a, 0.0) + ar
        events[e] = events.get(e, 0.0) - ar
    times = sorted(events)
    demand_at = {}
    run = 0.0
    for t in times:
        run += events[t]
        demand_at[t] = run
    peak_demand = max(demand_at.values()) if demand_at else 0.0

    def pressure(i):
        a, e = intervals[i]
        best = 0.0
        for t in times:
            if t >= e:
                break
            if t >= a:
                best = max(best, demand_at[t])
        # include the segment that contains `a` even if no breakpoint == a
        return best

    order = sorted(
        range(n),
        key=lambda i: (
            -pressure(i),
            blocks_data[i]["due_date"] - blocks_data[i]["release_time"]
            - blocks_data[i]["processing_time"],            # slack asc
            -areas[i],                                       # area desc
            -_max_layers(blocks_data[i]),                    # layers desc
        ),
    )
    return order, peak_demand


# -----------------------------------------------------------------------------
# Placement scoring across bays (objective approximation)
# -----------------------------------------------------------------------------

def _score(tardiness, pref_pen, workload, bay_loads, bay_id, bay_u,
           w1, w2, w3, top_y):
    new_load = bay_loads[bay_id] + workload
    imbal = max(
        (abs(bay_u[bay_id] * new_load - bay_u[j] * bay_loads[j])
         for j in range(len(bay_loads)) if j != bay_id),
        default=0.0,
    )
    return w1 * tardiness + w2 * imbal + w3 * pref_pen + 1e-4 * top_y


# -----------------------------------------------------------------------------
# Construction
# -----------------------------------------------------------------------------

def _construct(prob_info, order, bays, t_start, timelimit):
    """Place blocks in the given order, congestion-first, returning an
    assignments dict {block_id -> assignment}. Guaranteed to place every block
    (empty-bay fallback as last resort)."""
    bays_data = prob_info["bays"]
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)

    w1 = prob_info.get("weights", {}).get("w1", 1.0)
    w2 = prob_info.get("weights", {}).get("w2", 1.0)
    w3 = prob_info.get("weights", {}).get("w3", 1.0)
    # When tardiness strongly dominates, accept the first zero-tardiness slot in
    # preference order (fast, near-optimal for w1/w3). Otherwise weigh all bays
    # by full score so load balance (w2) and preference (w3) are respected.
    w1_dominant = w1 >= 20.0 * max(w2, w3, 1e-9)

    areas = [b.width * b.height for b in bays]
    avg_area = sum(areas) / n_bays
    bay_u = [avg_area / a for a in areas]

    sched = [[] for _ in range(n_bays)]   # per-bay [(Block, entry, exit, bbox)]
    bay_loads = [0.0] * n_bays
    assignments = {}

    for bi in order:
        blk = blocks_data[bi]
        release = int(blk["release_time"])
        due = int(blk["due_date"])
        proc = int(blk["processing_time"])
        workload = blk["workload"]
        prefs = blk["bay_preferences"]
        s_max = max(prefs)
        orients = _unique_orients(blk)

        # Past the time budget: force every remaining block into an empty window.
        budget_exhausted = (time.time() - t_start) > timelimit * 0.92

        best_score = float("inf")
        best = None
        bay_order = sorted(range(n_bays), key=lambda j: prefs[j], reverse=True)

        # -- Pass A: zero-tardiness placements (the w1 priority) -------------
        if not budget_exhausted:
            for bay_id in bay_order:
                bay = bays[bay_id]
                bay_zero = False
                for oi in orients:
                    if not _orient_fits(blk, oi, bay):
                        continue
                    blk_bb = _orient_bbox(blk, oi)
                    active = [it[0] for it in sched[bay_id] if it[2] > release]
                    for (cx, cy) in _candidate_positions(bay, active, blk_bb):
                        nb = Block(block_id=bi, block_data=blk,
                                   x=cx, y=cy, orient_idx=oi)
                        entry = _find_zero_slot(
                            bay, sched[bay_id], nb, release, due, proc)
                        if entry is None:
                            continue
                        sc = _score(0.0, s_max - prefs[bay_id], workload,
                                    bay_loads, bay_id, bay_u, w1, w2, w3,
                                    top_y=cy + blk_bb[3])
                        if sc < best_score:
                            best_score = sc
                            best = (bay_id, cx, cy, oi, entry, entry + proc)
                        # Positions/orientations in one bay share the dominant
                        # cost terms; the first zero-tardiness slot suffices.
                        bay_zero = True
                        break
                    if bay_zero:
                        break
                if bay_zero and w1_dominant:
                    break   # most-preferred zero-tardiness bay wins

        # -- Pass B: no zero-tardiness slot anywhere -> least-tardy fallback -
        # Scan candidate positions across all bays/orientations and keep the
        # placement with the lowest objective, so the unavoidable tardiness is
        # minimized rather than forced to a single bottom-left position.
        if best is None:
            for bay_id in bay_order:
                bay = bays[bay_id]
                for oi in orients:
                    if not _orient_fits(blk, oi, bay):
                        continue
                    blk_bb = _orient_bbox(blk, oi)
                    active = [it[0] for it in sched[bay_id] if it[2] > release]
                    for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=12):
                        nb = Block(block_id=bi, block_data=blk,
                                   x=cx, y=cy, orient_idx=oi)
                        entry = _find_tardy_slot(
                            bay, sched[bay_id], nb, release, due, proc, tardy_cap=8)
                        if entry is None:
                            continue
                        exit_t = entry + proc
                        sc = _score(max(0.0, exit_t - due), s_max - prefs[bay_id],
                                    workload, bay_loads, bay_id, bay_u,
                                    w1, w2, w3, top_y=cy + blk_bb[3])
                        if sc < best_score:
                            best_score = sc
                            best = (bay_id, cx, cy, oi, entry, exit_t)

        if best is None:
            # Guaranteed-feasible fallback: empty-bay window, min valid position.
            best = _force_place(bi, blk, bays, sched)

        bay_id, cx, cy, oi, entry, exit_t = best
        nb = Block(block_id=bi, block_data=blk, x=cx, y=cy, orient_idx=oi)
        sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
        bay_loads[bay_id] += workload
        assignments[bi] = {
            "block_id": bi, "bay_id": bay_id,
            "x": int(cx), "y": int(cy), "orient_idx": oi,
            "entry_time": int(entry), "exit_time": int(exit_t),
        }

    return assignments


def _force_place(bi, blk, bays, sched):
    """Empty-bay window at the minimum valid position in the best-fitting
    preferred bay. Always crane-feasible because the bay is empty."""
    prefs = blk["bay_preferences"]
    release = int(blk["release_time"])
    proc = int(blk["processing_time"])
    for bay_id in sorted(range(len(bays)), key=lambda j: prefs[j], reverse=True):
        bay = bays[bay_id]
        for oi in range(len(blk["shape"])):
            lx0, ly0, lx1, ly1 = _orient_bbox(blk, oi)
            px_lo, px_hi = math.ceil(-lx0), math.floor(bay.width - lx1)
            py_lo, py_hi = math.ceil(-ly0), math.floor(bay.height - ly1)
            if px_lo > px_hi or py_lo > py_hi:
                continue
            px, py = max(0, px_lo), max(0, py_lo)
            entry = _empty_bay_entry(sched[bay_id], release, proc)
            return (bay_id, px, py, oi, entry, entry + proc)
    raise RuntimeError(f"block {bi} cannot be placed in any bay/orientation")


# -----------------------------------------------------------------------------
# Build operations dict (EXIT before ENTRY, ascending block_id within type)
# -----------------------------------------------------------------------------

def _build_operations(assignments):
    buckets = {}
    for a in assignments.values():
        buckets.setdefault(int(a["exit_time"]), []).append(
            (0, "EXIT", a["block_id"], a["bay_id"], None, None, None))
        buckets.setdefault(int(a["entry_time"]), []).append(
            (1, "ENTRY", a["block_id"], a["bay_id"], a["x"], a["y"], a["orient_idx"]))
    operations = {}
    for t in sorted(buckets):
        ops = sorted(buckets[t], key=lambda r: (r[0], r[2]))
        lst = []
        for _, kind, bid, bay, x, y, oi in ops:
            op = {"type": kind, "block_id": bid, "bay_id": bay}
            if kind == "ENTRY":
                op["x"], op["y"], op["orient_idx"] = x, y, oi
            lst.append(op)
        operations[str(t)] = lst
    return operations


# -----------------------------------------------------------------------------
# Required entry point
# -----------------------------------------------------------------------------

def _empty_bay_solution(prob_info, bays):
    """Pure sequential empty-bay schedule -- always feasible (each block enters
    an empty bay). Used as the safety net if construction fails."""
    fallback = {}
    sched0 = [[] for _ in range(len(bays))]
    for bi, blk in enumerate(prob_info["blocks"]):
        bay_id, px, py, oi, entry, exit_t = _force_place(bi, blk, bays, sched0)
        sched0[bay_id].append(
            (Block(block_id=bi, block_data=blk, x=px, y=py, orient_idx=oi),
             entry, exit_t))
        fallback[bi] = {
            "block_id": bi, "bay_id": bay_id, "x": px, "y": py,
            "orient_idx": oi, "entry_time": entry, "exit_time": exit_t,
        }
    return {"operations": _build_operations(fallback)}


def algorithm(prob_info, timelimit=60):
    """Congestion-first construction with a guaranteed-feasible result.

    Returns a solution dict {"operations": {...}} that is always feasible. The
    congestion-first construction is tried first; only if it fails or returns an
    infeasible result do we fall back to the sequential empty-bay schedule.
    """
    t_start = time.time()
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    total_area = sum(b.width * b.height for b in bays)

    # -- Congestion-first construction ---------------------------------------
    try:
        order, _peak = _congestion_order(blocks_data, total_area)
        assignments = _construct(prob_info, order, bays, t_start, timelimit)
        sol = {"operations": _build_operations(assignments)}
        res = check_feasibility(prob_info, sol)
        if res["feasible"]:
            return sol
    except Exception:
        pass

    # -- Safety net: guaranteed-feasible empty-bay schedule ------------------
    return _empty_bay_solution(prob_info, bays)
