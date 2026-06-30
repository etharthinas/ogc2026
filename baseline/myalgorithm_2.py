# myalgorithm_2.py
# =============================================================================
# v2: EDD Temporal Leveling + Thorough Placement + LNS improvement
# =============================================================================
# See heuristics/heuristic_2.md for the plan. Reuses v1's verified feasibility
# core (_can_place etc.) and replaces the ordering + placement + adds an
# improvement loop that spends the remaining time budget reducing tardiness.

import math
import time

from utils import (
    Bay, Block,
    check_entry, check_exit, check_collisions, check_feasibility,
    _resolve_layers, _bounding_box, _bb_overlap,
)

# -----------------------------------------------------------------------------
# Static per-block geometry helpers (verbatim from v1)
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
# Time-overlap + crane-presence helpers (verbatim from v1)
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
    if not bay.contains_block(new_blk):
        return False
    full = sched + [(new_blk, entry, exit_t)]
    pres = _present_at_entry(entry, new_blk.block_id, full)
    if check_entry(bay, pres, new_blk, fast=True):
        return False
    pres = _present_at_exit(exit_t, new_blk.block_id, full)
    if check_exit(bay, pres, new_blk, fast=True):
        return False
    for b, a, e in sched:
        co_time = _overlaps(entry, exit_t, a, e)
        if co_time and check_collisions(bay, [new_blk, b]):
            return False
        if (entry < a < exit_t) or (entry == a and new_blk.block_id < b.block_id):
            if check_entry(bay, [new_blk], b, fast=True):
                return False
        if (entry < e < exit_t) or (exit_t == e and new_blk.block_id > b.block_id):
            if check_exit(bay, [new_blk], b, fast=True):
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
    """Entry-time candidates in [release, alap] at which the set of co-present
    blocks changes -- the only times where feasibility can flip. Sliding a
    feasible window later until it hits a conflict boundary lands on one of
    these, so checking them (descending) finds the LATEST feasible entry
    exactly, without scanning every integer."""
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
    """(Block, a, e) for blocks whose interval touches [t, exit_t] -- the only
    blocks that can collide, bury, or block the crane for a window [t,exit_t)."""
    return [(it[0], it[1], it[2]) for it in sched_bay
            if it[1] <= exit_t and t <= it[2]]


def _find_earliest_slot(bay, sched_bay, bi, blk, orients, lb, proc,
                        time_cap=40, pos_cap=24):
    """Earliest feasible (orient, x, y, entry) with entry >= lb, packing densely.
    Scans entry candidates ascending (lb and block exit/entry times); for each,
    tries bottom-left positions among the blocks present in that window. Returns
    the first (= earliest, least-tardy) feasible placement, or None."""
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
                nb = Block(block_id=bi, block_data=blk, x=cx, y=cy, orient_idx=oi)
                if _can_place(bay, relx, nb, t, exit_t):
                    return (oi, cx, cy, t)
    return None


# -----------------------------------------------------------------------------
# Ordering: congestion-first (from v1 -- better on hard instances than EDD)
# -----------------------------------------------------------------------------

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
# Objective helpers (cheap, geometry-free)
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
# Thorough placement of one block given current per-bay sched state
# -----------------------------------------------------------------------------

def _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                 pos_cap=40, tardy_cap=8, dense=True, forced=False):
    """Pass A finds a zero-tardiness slot (most-preferred bay's first bottom-left
    zero slot when w1 dominates); Pass B finds the least-tardy placement. On
    forced-tardy instances Pass A is skipped (dense earliest-slot from release
    still captures zero tardiness where space allows, but far faster)."""
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
                    nb = Block(block_id=bi, block_data=blk, x=cx, y=cy, orient_idx=oi)
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
    # When forced, search from release so zero-tardy slots are still captured.
    lb = release if forced else max(release, due - proc)
    if dense:
        # Dense earliest-feasible packing (maximizes bay throughput).
        for bay_id in bay_order:
            bay = bays[bay_id]
            slot = _find_earliest_slot(bay, sched[bay_id], bi, blk, orients, lb, proc)
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
        # Cheap fallback (v1-style): few positions x candidate exit-times.
        for bay_id in bay_order:
            bay = bays[bay_id]
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=12):
                    nb = Block(block_id=bi, block_data=blk, x=cx, y=cy, orient_idx=oi)
                    entry = _find_tardy_slot(bay, sched[bay_id], nb, release, due,
                                             proc, tardy_cap=tardy_cap)
                    if entry is None:
                        continue
                    exit_t = entry + proc
                    sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3])
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, exit_t)
    return best   # may be None -> caller force-places


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
    nb = Block(block_id=bi, block_data=blk, x=cx, y=cy, orient_idx=oi)
    sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
    bay_loads[bay_id] += blk["workload"]
    assignments[bi] = {
        "block_id": bi, "bay_id": bay_id, "x": int(cx), "y": int(cy),
        "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
    }


def _construct(prob_info, order, bays, bay_u, w1, w2, w3, t_start, timelimit,
               forced=False):
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    assignments = {}
    n = len(order)
    for idx, bi in enumerate(order):
        blk = blocks_data[bi]
        elapsed = time.time() - t_start
        time_left = timelimit * 0.95 - elapsed
        remaining = n - idx
        # Dense packing only while there is ample time per remaining block;
        # otherwise use the cheap (but still proper) placement so construction
        # always finishes WITHOUT empty-bay serialization. The empty-bay
        # force-place is only a last resort if cheap placement also fails. This
        # makes construction robust to wall-clock under-estimation (CPU
        # contention): a misfired budget degrades to cheap, not catastrophic.
        dense = time_left > 0 and (time_left / remaining) > 0.25
        place = _place_block(bi, blk, bays, sched, bay_loads, bay_u,
                             w1, w2, w3, dense=dense, forced=forced)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        _add(sched, bay_loads, assignments, bi, blk, place)
    return assignments, sched, bay_loads


# -----------------------------------------------------------------------------
# LNS improvement: destroy most-tardy blocks + neighbors, repair
# -----------------------------------------------------------------------------

def _rebuild_sched(assignments, blocks_data, n_bays):
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    for bi, a in assignments.items():
        nb = Block(block_id=bi, block_data=blocks_data[bi],
                   x=a["x"], y=a["y"], orient_idx=a["orient_idx"])
        sched[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"], nb.bounding_rect()))
        bay_loads[a["bay_id"]] += blocks_data[bi]["workload"]
    return sched, bay_loads


def _improve(prob_info, assignments, bays, bay_u, w1, w2, w3, t_start, timelimit):
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)

    best_assign = {k: dict(v) for k, v in assignments.items()}
    best_obj, _, _, _ = _objective(best_assign, blocks_data, bays, bay_u, w1, w2, w3)

    import random
    rng = random.Random(12345)
    rounds = 0
    while time.time() - t_start < timelimit * 0.95:
        rounds += 1
        # tardy blocks, worst first
        tardy = [(bi, a["exit_time"] - blocks_data[bi]["due_date"])
                 for bi, a in best_assign.items()
                 if a["exit_time"] > blocks_data[bi]["due_date"]]
        if not tardy:
            break
        tardy.sort(key=lambda z: -z[1])
        # destroy set: a chunk of tardy blocks (vary size across rounds)
        k = min(len(tardy), 3 + (rounds % 6) * 2)
        removed = set(bi for bi, _ in tardy[:k])
        # add a few random non-tardy neighbors in the same bays/time to open space
        bays_touched = set(best_assign[bi]["bay_id"] for bi in removed)
        extra_pool = [bi for bi, a in best_assign.items()
                      if bi not in removed and a["bay_id"] in bays_touched]
        rng.shuffle(extra_pool)
        for bi in extra_pool[:k]:
            removed.add(bi)

        work = {bi: dict(a) for bi, a in best_assign.items() if bi not in removed}
        sched, bay_loads = _rebuild_sched(work, blocks_data, n_bays)
        # repair: insert removed blocks EDD order
        rem_order = sorted(removed, key=lambda i: (blocks_data[i]["due_date"],
                                                   -_min_area(blocks_data[i])))
        ok = True
        for bi in rem_order:
            if time.time() - t_start > timelimit * 0.97:
                ok = False; break
            blk = blocks_data[bi]
            place = _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3)
            if place is None:
                place = _force_place(bi, blk, bays, sched)
            _add(sched, bay_loads, work, bi, blk, place)
        if not ok or len(work) != len(best_assign):
            continue
        new_obj, _, _, _ = _objective(work, blocks_data, bays, bay_u, w1, w2, w3)
        if new_obj < best_obj - 1e-9:
            sol = {"operations": _build_operations(work)}
            res = check_feasibility(prob_info, sol)
            if res["feasible"] and res["objective"] < best_obj - 1e-9:
                best_obj = res["objective"]
                best_assign = {k: dict(v) for k, v in work.items()}
    return best_assign


# -----------------------------------------------------------------------------
# Build operations dict (verbatim from v1)
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
    return {"operations": _build_operations(fallback)}


# -----------------------------------------------------------------------------
# Required entry point
# -----------------------------------------------------------------------------

def _is_forced(prob_info, bays):
    """True if even the mandatory (must-coexist) area demand exceeds total bay
    capacity -- zero tardiness is impossible, so skip the (doomed) ALAP
    zero-slot pass and pack densely from the start."""
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


def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w1 = prob_info.get("weights", {}).get("w1", 1.0)
    w2 = prob_info.get("weights", {}).get("w2", 1.0)
    w3 = prob_info.get("weights", {}).get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)

    try:
        order = _congestion_order(blocks_data)
        assignments, sched, bay_loads = _construct(
            prob_info, order, bays, bay_u, w1, w2, w3, t_start, timelimit, forced)
        sol = {"operations": _build_operations(assignments)}
        res = check_feasibility(prob_info, sol)
        if res["feasible"]:
            if ENABLE_LNS:
                assignments = _improve(prob_info, assignments, bays, bay_u,
                                       w1, w2, w3, t_start, timelimit)
                sol2 = {"operations": _build_operations(assignments)}
                res2 = check_feasibility(prob_info, sol2)
                if res2["feasible"]:
                    return sol2
            return sol
    except Exception:
        pass

    return _empty_bay_solution(prob_info, bays)


ENABLE_LNS = True
