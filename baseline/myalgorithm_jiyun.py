# myalgorithm_jiyun.py  --  jiyun branch, fork of v8 with an explicit 3-phase
# anytime structure and an EARLY-verified feasible fallback.
# =============================================================================
# Same solver machinery as v8 (construction + basin-hopping improver + geometry
# caching); ONLY algorithm() is restructured. The change vs v8:
#   Phase 1  -- ONE fast EDD-earliest construction, verified with the official
#               check_feasibility IMMEDIATELY, and kept as best_feasible_sol.
#               We hold a guaranteed-feasible solution from very early on.
#   Phase 2  -- v8's optimization body (extra constructions + _improve) on the
#               remaining budget, collecting internal candidates.
#   Phase 3  -- best-first official verification of the candidates, but with a
#               HARD time guard (timelimit*0.97): the loop stops the moment the
#               guard trips and returns the already-held best_feasible_sol.
# v8 verified feasibility only at the very end; on big/slow instances a stalled
# end-of-run verify could drop it to the empty-bay solution. Verifying a good
# baseline early removes that cliff, and the guard removes the overrun risk.
# =============================================================================
# Imports ONLY the standard library (math, time, random) and `utils` (contest-
# provided, available via shapely in ogc2026_env.yml). It does NOT import any
# `myalgorithm_N` helper module, so the grader cannot fail with a missing /
# "unavailable python package" error when only myalgorithm.py + utils.py ship.
# =============================================================================
# v8 = v7 (geometry caching) + THOROUGH REPAIR. Caching made each placement
# cheap, so the improver can now afford a much wider per-block search during
# repair (slot_time_cap 18->40, slot_pos_cap 14->30) -- the exact thing v5 kept
# tiny purely for speed. Hypothesis: the plateaus v5/v7 hit on the gap instances
# (prob_39/26/33: relaxed LB far below achieved, yet the improver finds nothing)
# are partly an artifact of the capped repair search missing the denser packing;
# a wider repair may escape them. Tested against v7 on the gap set; kept only if
# it actually lowers the objective (see heuristic_8.md / results.csv).
# =============================================================================
# v7 = v5 + pairwise GEOMETRY CACHING (semantically identical to v5, faster).
# =============================================================================
# Diagnosis: on the packing-limited instances (relaxed LB << v5 result, e.g.
# prob_35/28/31/30/23/39) more improver rounds keep lowering tardiness
# (prob_35: 14.6M@60s -> 11.4M@150s), but v5 is round-starved because every
# placement check rebuilds Shapely intersections. v7 memoizes the three
# pairwise feasibility primitives -- collision, crane-entry obstruction, crane-
# exit obstruction -- keyed by the two placements' (block_id, orient, x, y).
# These are pure geometry (time-independent) and SEPARABLE per existing block
# (the crane path is blocked iff ANY single present block blocks it), so the
# cache is exact: v7 returns the SAME feasibility verdict as v5 for every call,
# just far cheaper after warm-up -> many more destroy/repair rounds per second
# on the instances where that converts directly into less tardiness. The final
# solution is still verified by the official check_feasibility, unchanged.
# (Structurally over-subscribed instances prob_38/27 -- area-time demand exceeds
#  total capacity-time over the whole horizon -- stay near their forced floor;
#  no heuristic removes their tardiness. See heuristic_7.md / results.csv.)
# =============================================================================
# v5: v3's full thorough construction (NO cap) + fast basin-hopping improver.
# =============================================================================
# Fixes v4's two mistakes: (1) removes the construction-time cap so the start is
# always v3's strong thorough construction; the improver takes only leftover
# time. (2) Improver rounds are now small & fast (smaller destroy sets, capped
# repair search, lower kick threshold) so MANY more rounds run per second of
# real compute -> it actually bites on the congested instances where v4's slow
# rounds found nothing. Still returns the best-tracked incumbent (monotone).
#
# --- v4 provenance ---------------------------------------------------------
# v4: EDD-earliest construction + budget rebalance + basin-hopping improver
#     (diversified destroy/repair with escape-kicks, window-destroy mode).
# v3 placement/feasibility core kept verbatim; the
# improver and the time-budget split change. The improver tracks a separate best
# incumbent and returns it -> still monotone in the RESULT (never worse than the
# construction) while exploring more to escape plateaus (e.g. prob_39).
#
# --- v3 provenance ---------------------------------------------------------
# v3: EDD-earliest construction + multi-start best-of (no-regression) + safe
#     tardiness-pull improvement.
# Reuses v2's verified feasibility/placement core
# verbatim; changes ONLY the top-level orchestration:
#   * EDD-earliest construction targets the avoidable tardiness on congested
#     instances (the dominant cost; relaxed LB shows ~90% of it is avoidable).
#   * Per-instance best-of across {EDD-earliest, congestion-ALAP(=v1), seeded
#     perturbations} keeps the best VERIFIED-feasible solution -> can never be
#     worse than v1 on any instance (v2's regression is structurally impossible).
#   * A monotone destroy/repair improver replaces v2's non-monotone LNS.

import math
import time
import random

from utils import (
    Bay, Block,
    check_entry, check_exit, check_collisions, check_feasibility,
    _resolve_layers, _bounding_box, _bb_overlap,
)

# -----------------------------------------------------------------------------
# Pairwise geometry caches (v7). Keyed by placement = (block_id, orient, x, y).
# Pure geometry, time-independent. Cleared per instance in algorithm().
#   _BLK : (bi, oi, x, y)                  -> reusable Block (avoids re-translate)
#   _CC  : frozenset{key_a, key_b}         -> do a, b spatially collide (any layer)
#   _CE  : (existing_key, mover_key)       -> does `existing` block `mover`'s ENTRY
#   _CX  : (existing_key, mover_key)       -> does `existing` block `mover`'s EXIT
# A pair-cache is exact because check_collisions/entry/exit are separable: a
# multi-block verdict is the OR of the single-block verdicts. Bay boundary is
# checked separately via bay.contains_block before any crane call, so the
# self-boundary obstruction never appears here.
# -----------------------------------------------------------------------------
_BLK = {}
_CC = {}
_CE = {}
_CX = {}
_CACHE_CAP = 6_000_000  # safety bound; stop growing caches past this (rare)


def _reset_caches():
    _BLK.clear(); _CC.clear(); _CE.clear(); _CX.clear()


def _mkblock(bi, blk_data, x, y, oi):
    k = (bi, oi, x, y)
    nb = _BLK.get(k)
    if nb is None:
        nb = Block(block_id=bi, block_data=blk_data, x=x, y=y, orient_idx=oi)
        if len(_BLK) < _CACHE_CAP:
            _BLK[k] = nb
    return nb


def _pk(blk):
    return (blk.block_id, blk.orient_idx, blk.x, blk.y)


def _collide(bay, a, b):
    ka, kb = _pk(a), _pk(b)
    key = (ka, kb) if ka <= kb else (kb, ka)
    v = _CC.get(key)
    if v is None:
        v = bool(check_collisions(bay, [a, b]))
        if len(_CC) < _CACHE_CAP:
            _CC[key] = v
    return v


def _entry_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane descent (== v5's
    check_entry(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CE.get(key)
    if v is None:
        v = bool(check_entry(bay, [existing], mover, fast=True))
        if len(_CE) < _CACHE_CAP:
            _CE[key] = v
    return v


def _exit_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane ascent (== v5's
    check_exit(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CX.get(key)
    if v is None:
        v = bool(check_exit(bay, [existing], mover, fast=True))
        if len(_CX) < _CACHE_CAP:
            _CX[key] = v
    return v


# -----------------------------------------------------------------------------
# Static per-block geometry helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _orient_bbox(block_data, oi):
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
    lx0, ly0, lx1, ly1 = _orient_bbox(block_data, oi)
    return (math.ceil(-lx0) <= math.floor(bay.width - lx1) and
            math.ceil(-ly0) <= math.floor(bay.height - ly1))


def _unique_orients(block_data):
    seen = {}
    for oi in range(len(block_data["shape"])):
        bb = _orient_bbox(block_data, oi)
        nl = len(_resolve_layers(block_data["shape"][oi]["layers"]))
        key = (round(bb[0], 3), round(bb[1], 3), round(bb[2], 3), round(bb[3], 3), nl)
        if key not in seen:
            seen[key] = oi
    return list(seen.values())


def _candidate_positions(bay, placed_blocks, blk_bb, cap=60):
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
# Time-overlap + crane-presence helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _overlaps(a1, e1, a2, e2):
    return a1 < e2 and a2 < e1


def _present_at_entry(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (a == t and b.block_id < x_id):
            out.append(b)
    return out


def _present_at_exit(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (e == t and b.block_id > x_id):
            out.append(b)
    return out


def _can_place(bay, sched, new_blk, entry, exit_t):
    # v7: identical verdict to v5, but every Shapely call is routed through the
    # pairwise caches. check_entry/exit over a SET of present blocks is the OR of
    # the per-block checks, so we decompose into cached pairwise queries.
    if not bay.contains_block(new_blk):
        return False
    nbid = new_blk.block_id
    # new_blk ENTRY obstructed by any block present at `entry` (== check_entry
    # over _present_at_entry set).
    for b, a, e in sched:
        if (a < entry < e) or (a == entry and b.block_id < nbid):
            if _entry_blocked(bay, b, new_blk):
                return False
    # new_blk EXIT obstructed by any block present at `exit_t` (== check_exit
    # over _present_at_exit set).
    for b, a, e in sched:
        if (a < exit_t < e) or (e == exit_t and b.block_id > nbid):
            if _exit_blocked(bay, b, new_blk):
                return False
    for b, a, e in sched:
        if _overlaps(entry, exit_t, a, e) and _collide(bay, new_blk, b):
            return False
        if (entry < a < exit_t) or (entry == a and nbid < b.block_id):
            if _entry_blocked(bay, new_blk, b):
                return False
        if (entry < e < exit_t) or (exit_t == e and nbid > b.block_id):
            if _exit_blocked(bay, new_blk, b):
                return False
    return True


def _empty_bay_entry(sched, r_time, proc):
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


def _rel_sched(sched, nb_bb):
    return [(it[0], it[1], it[2]) for it in sched if _bb_overlap(nb_bb, it[3])]


def _zero_candidates(rel, release, alap, proc):
    cand = {alap, release}
    for _, a, e in rel:
        for t in (a, e, a - proc, e - proc):
            for tt in (int(t), int(t) - 1):
                if release <= tt <= alap:
                    cand.add(tt)
    return sorted(cand, reverse=True)


def _find_zero_slot(bay, sched, new_blk, release, due, proc):
    alap = due - proc
    if alap < release:
        return None
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    for entry in _zero_candidates(rel, release, alap, proc):
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    return None


def _find_tardy_slot(bay, sched, new_blk, release, due, proc, tardy_cap=64):
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


def _time_overlap_rel(sched_bay, t, exit_t):
    return [(it[0], it[1], it[2]) for it in sched_bay
            if it[1] <= exit_t and t <= it[2]]


def _find_earliest_slot(bay, sched_bay, bi, blk, orients, lb, proc,
                        time_cap=40, pos_cap=24):
    """Earliest feasible (orient, x, y, entry) with entry >= lb, packing densely.
    Returns the first (= earliest, least-tardy) feasible placement, or None."""
    times = {int(lb)}
    for _, a, e in [(it[0], it[1], it[2]) for it in sched_bay]:
        if e >= lb:
            times.add(int(e))
        if a >= lb:
            times.add(int(a))
    for t in sorted(times)[:time_cap]:
        exit_t = t + proc
        relx = _time_overlap_rel(sched_bay, t, exit_t)
        active = [r[0] for r in relx]
        for oi in orients:
            if not _orient_fits(blk, oi, bay):
                continue
            blk_bb = _orient_bbox(blk, oi)
            for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                nb = _mkblock(bi, blk, cx, cy, oi)
                if _can_place(bay, relx, nb, t, exit_t):
                    return (oi, cx, cy, t)
    return None


# -----------------------------------------------------------------------------
# Orderings
# -----------------------------------------------------------------------------

def _edd_order(blocks_data, jitter=None):
    """Earliest-due-date first; tie shortest proc, largest area, most layers.
    Optional jitter (rng) perturbs ties for multi-start diversity."""
    n = len(blocks_data)
    areas = [_min_area(b) for b in blocks_data]
    base = []
    for i, b in enumerate(blocks_data):
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((b["due_date"] + j, b["processing_time"], -areas[i],
                     -_max_layers(blocks_data[i]), i))
    base.sort()
    return [t[-1] for t in base]


def _congestion_order(blocks_data):
    n = len(blocks_data)
    intervals = []
    areas = [_min_area(b) for b in blocks_data]
    for b in blocks_data:
        entry = max(b["release_time"], b["due_date"] - b["processing_time"])
        intervals.append((int(entry), int(entry + b["processing_time"])))
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

    def pressure(i):
        a, e = intervals[i]
        best = 0.0
        for t in times:
            if t >= e:
                break
            if t >= a:
                best = max(best, demand_at[t])
        return best

    return sorted(
        range(n),
        key=lambda i: (
            -pressure(i),
            blocks_data[i]["due_date"] - blocks_data[i]["release_time"]
            - blocks_data[i]["processing_time"],
            -areas[i],
            -_max_layers(blocks_data[i]),
        ),
    )


# -----------------------------------------------------------------------------
# Objective helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _bay_u(bays):
    areas = [b.width * b.height for b in bays]
    avg = sum(areas) / len(bays)
    return [avg / a for a in areas]


def _objective(assignments, blocks_data, bays, bay_u, w1, w2, w3):
    n_bays = len(bays)
    obj1 = 0.0
    loads = [0.0] * n_bays
    obj3 = 0.0
    for a in assignments.values():
        bi = a["block_id"]; bj = a["bay_id"]
        blk = blocks_data[bi]
        obj1 += max(0.0, a["exit_time"] - blk["due_date"])
        loads[bj] += blk["workload"]
        obj3 += max(blk["bay_preferences"]) - blk["bay_preferences"][bj]
    if n_bays >= 2:
        obj2 = math.floor(max(
            abs(bay_u[p] * loads[p] - bay_u[q] * loads[q])
            for p in range(n_bays) for q in range(n_bays) if p != q))
    else:
        obj2 = 0.0
    return w1 * obj1 + w2 * obj2 + w3 * obj3, obj1, obj2, obj3


# -----------------------------------------------------------------------------
# Thorough placement of one block (verbatim from v2)
# -----------------------------------------------------------------------------

def _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                 pos_cap=40, tardy_cap=8, dense=True, forced=False,
                 bay_order=None, slot_time_cap=40, slot_pos_cap=24):
    release = int(blk["release_time"])
    due = int(blk["due_date"])
    proc = int(blk["processing_time"])
    workload = blk["workload"]
    prefs = blk["bay_preferences"]
    s_max = max(prefs)
    orients = _unique_orients(blk)
    n_bays = len(bays)
    w1_dominant = w1 >= 20.0 * max(w2, w3, 1e-9)

    def score(tardiness, bay_id, top_y):
        new_load = bay_loads[bay_id] + workload
        imbal = max((abs(bay_u[bay_id] * new_load - bay_u[j] * bay_loads[j])
                     for j in range(n_bays) if j != bay_id), default=0.0)
        return (w1 * tardiness + w2 * imbal + w3 * (s_max - prefs[bay_id])
                + 1e-4 * top_y)

    if bay_order is None:
        bay_order = sorted(range(n_bays), key=lambda j: prefs[j], reverse=True)
    best_score = float("inf")
    best = None

    # -- Pass A: zero-tardiness placements (skipped when forced) ----------
    if not forced:
        for bay_id in bay_order:
            bay = bays[bay_id]
            bay_zero = False
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_zero_slot(bay, sched[bay_id], nb, release, due, proc)
                    if entry is None:
                        continue
                    sc = score(0.0, bay_id, top_y=cy + blk_bb[3])
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, entry + proc)
                    bay_zero = True
                    break
                if bay_zero:
                    break
            if bay_zero and w1_dominant:
                break
        if best is not None:
            return best

    # -- Pass B: least-tardy placement ------------------------------------
    lb = release if forced else max(release, due - proc)
    if dense:
        for bay_id in bay_order:
            bay = bays[bay_id]
            slot = _find_earliest_slot(bay, sched[bay_id], bi, blk, orients, lb, proc,
                                       time_cap=slot_time_cap, pos_cap=slot_pos_cap)
            if slot is None:
                continue
            oi, cx, cy, entry = slot
            exit_t = entry + proc
            blk_bb = _orient_bbox(blk, oi)
            sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3])
            if sc < best_score:
                best_score = sc
                best = (bay_id, cx, cy, oi, entry, exit_t)
    else:
        for bay_id in bay_order:
            bay = bays[bay_id]
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=12):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_tardy_slot(bay, sched[bay_id], nb, release, due,
                                             proc, tardy_cap=tardy_cap)
                    if entry is None:
                        continue
                    exit_t = entry + proc
                    sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3])
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, exit_t)
    return best


def _force_place(bi, blk, bays, sched):
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
    raise RuntimeError(f"block {bi} cannot be placed")


# -----------------------------------------------------------------------------
# Construction over a given order
# -----------------------------------------------------------------------------

def _add(sched, bay_loads, assignments, bi, blk, place):
    bay_id, cx, cy, oi, entry, exit_t = place
    nb = _mkblock(bi, blk, cx, cy, oi)
    sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
    bay_loads[bay_id] += blk["workload"]
    assignments[bi] = {
        "block_id": bi, "bay_id": bay_id, "x": int(cx), "y": int(cy),
        "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
    }


def _construct(prob_info, order, bays, bay_u, w1, w2, w3, t_start, deadline,
               forced=False):
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    assignments = {}
    n = len(order)
    for idx, bi in enumerate(order):
        blk = blocks_data[bi]
        time_left = deadline - time.time()
        # HARD DEADLINE STOP: once the budget is spent, do NOT run the (possibly
        # slow) placement search for the remaining blocks. Force-place them
        # cheaply so we still return a COMPLETE, feasible assignment without
        # overrunning the wall-clock limit. The search loop is what blew v8 past
        # its budget (prob_40: 70s > 60s); _force_place is ~O(bay size) per block,
        # so the post-deadline tail costs microseconds each. Worst-case overshoot
        # is the single _place_block call already in flight when the deadline hit,
        # which the caller's end-of-run reserve absorbs.
        if time_left <= 0:
            place = _force_place(bi, blk, bays, sched)
            _add(sched, bay_loads, assignments, bi, blk, place)
            continue
        remaining = n - idx
        dense = (time_left / remaining) > 0.25
        place = _place_block(bi, blk, bays, sched, bay_loads, bay_u,
                             w1, w2, w3, dense=dense, forced=forced)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        _add(sched, bay_loads, assignments, bi, blk, place)
    return assignments


# -----------------------------------------------------------------------------
# Safe monotone improver: destroy worst-tardy + neighbors, repair EDD-earliest,
# keep ONLY if verified-feasible AND strictly better.
# -----------------------------------------------------------------------------

def _rebuild_sched(assignments, blocks_data, n_bays):
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    for bi, a in assignments.items():
        nb = _mkblock(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
        sched[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"], nb.bounding_rect()))
        bay_loads[a["bay_id"]] += blocks_data[bi]["workload"]
    return sched, bay_loads


def _repair_order(removed, blocks_data, mode, rng):
    """Diversified reinsertion orderings — different orderings unlock different
    packings, which is what lets the improver escape EDD-only local optima."""
    rem = list(removed)
    if mode == 0:      # EDD
        rem.sort(key=lambda i: (blocks_data[i]["due_date"],
                                blocks_data[i]["processing_time"],
                                -_min_area(blocks_data[i])))
    elif mode == 1:    # EDD with tie jitter
        rem.sort(key=lambda i: (blocks_data[i]["due_date"] + rng.uniform(-0.5, 0.5),
                                blocks_data[i]["processing_time"]))
    elif mode == 2:    # earliest release first, then due
        rem.sort(key=lambda i: (blocks_data[i]["release_time"],
                                blocks_data[i]["due_date"]))
    else:              # largest area first within due buckets
        rem.sort(key=lambda i: (blocks_data[i]["due_date"], -_min_area(blocks_data[i])))
    return rem


def _destroy_tardy(cur, blocks_data, k, rng):
    tardy = [(bi, a["exit_time"] - blocks_data[bi]["due_date"])
             for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    if not tardy:
        return None
    tardy.sort(key=lambda z: -z[1])
    removed = set(bi for bi, _ in tardy[:k])
    bays_touched = set(cur[bi]["bay_id"] for bi in removed)
    early_pool = sorted(
        [bi for bi, a in cur.items()
         if bi not in removed and a["bay_id"] in bays_touched],
        key=lambda bi: cur[bi]["entry_time"])
    for bi in early_pool[:k]:
        removed.add(bi)
    return removed


def _destroy_window(cur, blocks_data, rng):
    """Remove ALL blocks active in a sampled congested time window of one bay,
    so the bottleneck window is re-packed wholesale (structural rescheduling)."""
    tardy = [bi for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    seed = rng.choice(tardy) if tardy else rng.choice(list(cur))
    bay = cur[seed]["bay_id"]
    center = cur[seed]["entry_time"]
    # window half-width ~ a few typical processing times
    procs = [blocks_data[bi]["processing_time"] for bi in cur]
    half = max(1, int(sorted(procs)[len(procs) // 2]) * 2)
    lo, hi = center - half, center + half
    removed = set(bi for bi, a in cur.items()
                  if a["bay_id"] == bay and a["entry_time"] < hi and a["exit_time"] > lo)
    return removed if removed else {seed}


def _improve(prob_info, assignments, bays, bay_u, w1, w2, w3, deadline, forced):
    """Basin-hopping destroy/repair. Tracks `best` separately from the working
    `cur`; returns `best` -> monotone in the RESULT. Diversifies destroy mode and
    repair ordering, and applies an escape "kick" (a larger destroy accepted even
    if worse) after a plateau, to break out of local structures the pure
    hill-climber (v3) gets stuck in (prob_39). Compares by the cheap internal
    objective; the caller verifies the returned solution officially."""
    blocks_data = prob_info["blocks"]
    n = len(assignments)
    n_bays = len(bays)
    best_assign = {k: dict(v) for k, v in assignments.items()}
    best_obj, _, _, _ = _objective(best_assign, blocks_data, bays, bay_u, w1, w2, w3)
    cur = {k: dict(v) for k, v in best_assign.items()}
    cur_obj = best_obj

    def _tardy_count(assign):
        return sum(1 for bi, a in assign.items()
                   if a["exit_time"] > blocks_data[bi]["due_date"])

    best_tardy = _tardy_count(best_assign)
    rng = random.Random(4242)
    rounds = 0
    no_improve = 0      # for kick triggering (kicks reset this)
    since_best = 0      # rounds since best improved (kicks do NOT reset this)
    KICK = 6
    # Small destroy sets + capped repair search => many more rounds/sec, which is
    # what makes the improver bite under real (and contended) compute budgets.
    while time.time() < deadline:
        # Early stop: nothing tardy left and the search has stalled -> the obj2/
        # obj3 part is exhausted; stop instead of burning the rest of the budget.
        if best_tardy == 0 and since_best > 40:
            break
        rounds += 1
        kick = no_improve >= KICK
        if kick:
            removed = _destroy_window(cur, blocks_data, rng)
            extra = rng.sample(list(cur), min(len(cur), 6))
            removed = set(removed) | set(extra)
        elif rounds % 3 == 0:
            removed = _destroy_window(cur, blocks_data, rng)
        else:
            k = min(6, max(2, n // 40))
            removed = _destroy_tardy(cur, blocks_data, k, rng)
            if removed is None:
                removed = _destroy_window(cur, blocks_data, rng)
        if not removed:
            break

        work = {bi: dict(a) for bi, a in cur.items() if bi not in removed}
        sched, bay_loads = _rebuild_sched(work, blocks_data, n_bays)
        rem_order = _repair_order(removed, blocks_data, rounds % 4, rng)
        ok = True
        for bi in rem_order:
            if time.time() > deadline:
                ok = False; break
            blk = blocks_data[bi]
            place = _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                                 forced=forced, slot_time_cap=40, slot_pos_cap=30)
            if place is None:
                place = _force_place(bi, blk, bays, sched)
            _add(sched, bay_loads, work, bi, blk, place)
        if not ok or len(work) != n:
            continue
        new_obj, _, _, _ = _objective(work, blocks_data, bays, bay_u, w1, w2, w3)
        if new_obj < cur_obj - 1e-9 or kick:
            cur = work
            cur_obj = new_obj
        if new_obj < best_obj - 1e-9:
            best_obj = new_obj
            best_assign = {k: dict(v) for k, v in work.items()}
            best_tardy = _tardy_count(best_assign)
            no_improve = 0
            since_best = 0
        else:
            no_improve = 0 if kick else no_improve + 1
            since_best += 1
    return best_assign, best_obj


# -----------------------------------------------------------------------------
# Build operations dict (verbatim from v2)
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


def _empty_bay_solution(prob_info, bays):
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
    return fallback


# -----------------------------------------------------------------------------
# Forced detection (verbatim from v2)
# -----------------------------------------------------------------------------

def _is_forced(prob_info, bays):
    cap = sum(b.width * b.height for b in bays)
    ev = {}
    for b in prob_info["blocks"]:
        r = b["release_time"]; du = b["due_date"]; p = b["processing_time"]
        ms = du - p; me = r + p
        if ms < me:
            a = _min_area(b)
            ev[ms] = ev.get(ms, 0.0) + a
            ev[me] = ev.get(me, 0.0) - a
    run = 0.0; peak = 0.0
    for t in sorted(ev):
        run += ev[t]; peak = max(peak, run)
    return peak > cap


# -----------------------------------------------------------------------------
# Required entry point
# -----------------------------------------------------------------------------

def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    _reset_caches()  # v7: caches hold instance-specific geometry; never share.
    # Reserve a slice at the end for the official feasibility check(s).
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    search_deadline = t_start + timelimit * 0.95 - reserve
    # Hard guard: never START a check_feasibility past this. The 1% margin below
    # (0.99) plus a duration estimate (vdur) keep the LAST verify from overrunning
    # the wall-clock budget on big/slow instances -> never a crash (-1 point).
    verify_guard = t_start + timelimit * 0.97
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w1 = prob_info.get("weights", {}).get("w1", 1.0)
    w2 = prob_info.get("weights", {}).get("w2", 1.0)
    w3 = prob_info.get("weights", {}).get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)

    def iobj(assign):
        return _objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]

    edd = _edd_order(blocks_data)
    cong = _congestion_order(blocks_data)

    # ------------------------------------------------------------------ Phase 1
    # Fast primary construction, verified with the OFFICIAL check_feasibility
    # immediately, and held as best_feasible_sol. From here on we always have an
    # officially-feasible solution to return (anytime guarantee). The empty-bay
    # solution seeds it so we are covered even before the first verify.
    empty_assign = _empty_bay_solution(prob_info, bays)
    best_feasible_sol = {"operations": _build_operations(empty_assign)}
    best_feasible_iobj = iobj(empty_assign)
    vdur = None  # measured cost of ONE check_feasibility on this instance

    # Primary order matches v8: forced -> EDD(forced=True); uncongested -> CONG.
    # Given the FULL window like v8 (the construction self-throttles per-block, so
    # big instances finish in ~half the budget and Phase 2 gets the rest; on tight
    # budgets it uses more time and the improver simply gets little, which is safe).
    candidates = []  # (internal_obj, assign)
    primary_order = edd if forced else cong
    try:
        base_assign = _construct(prob_info, primary_order, bays, bay_u, w1, w2, w3,
                                 t_start, search_deadline, forced=forced)
        base_iobj = iobj(base_assign)
        candidates.append((base_iobj, base_assign))
        if time.time() < verify_guard:
            sol = {"operations": _build_operations(base_assign)}
            _tv = time.time()
            res = check_feasibility(prob_info, sol)
            vdur = time.time() - _tv
            if res["feasible"]:
                best_feasible_sol = sol
                best_feasible_iobj = base_iobj
    except Exception:
        pass

    # ------------------------------------------------------------------ Phase 2
    # Optimization on the remaining budget -- v8's candidate generation, verbatim.
    if not forced:
        # CONG(forced=False) already built in Phase 1; add EDD(forced=True)
        # secondary + bounded EDD-jitter perturbations, exactly as v8.
        if time.time() < search_deadline:
            try:
                assign = _construct(prob_info, edd, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=True)
                candidates.append((iobj(assign), assign))
            except Exception:
                pass
        rng = random.Random(2026)
        stale = 0
        best_so_far = min((c[0] for c in candidates), default=float("inf"))
        while time.time() < search_deadline and stale < 4:
            try:
                order = _edd_order(blocks_data, jitter=rng)
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=forced)
                o = iobj(assign)
                candidates.append((o, assign))
                if o < best_so_far - 1e-9:
                    best_so_far = o; stale = 0
                else:
                    stale += 1
            except Exception:
                break

    # Basin-hopping improver on the current best candidate (the main engine).
    if candidates and time.time() < search_deadline:
        try:
            candidates.sort(key=lambda c: c[0])
            improved, iobj_imp = _improve(prob_info, candidates[0][1], bays, bay_u,
                                          w1, w2, w3, search_deadline, forced)
            candidates.append((iobj_imp, improved))
        except Exception:
            pass

    # ------------------------------------------------------------------ Phase 3
    # Verify candidates best-first, adopting the first officially-feasible one
    # that beats the held solution. A hard time guard + duration estimate stop
    # the loop before it can overrun; whatever is not reached leaves the held
    # (Phase-1-verified) solution in place -- never a fall to empty-bay unless
    # Phase 1 itself failed to verify.
    def _can_verify_now():
        if time.time() >= verify_guard:
            return False
        if vdur is not None and time.time() + vdur * 1.5 >= t_start + timelimit * 0.99:
            return False
        return True

    candidates.sort(key=lambda c: c[0])
    for o, assign in candidates:
        if o >= best_feasible_iobj - 1e-9:
            break  # sorted asc: nothing left can beat the held feasible solution
        if not _can_verify_now():
            break
        sol = {"operations": _build_operations(assign)}
        _tv = time.time()
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            dt = time.time() - _tv
            vdur = dt if vdur is None else max(vdur, dt)
            continue
        dt = time.time() - _tv
        vdur = dt if vdur is None else max(vdur, dt)
        if res["feasible"]:
            best_feasible_sol = sol
            best_feasible_iobj = o
            break
    return best_feasible_sol
