# radical_s1_brkga.py -- RADICAL EPOCH strategy S1 (heuristic_32.md)
# =============================================================================
# BRKGA over the v25 DECODER INPUTS.  The v29 lesson: forced foreign orders
# realize catastrophically because only the greedy decoder knows geometry.  So
# we search the space the decoder maps well -- a biased-random-key genome that
# feeds v25's event-driven raster dispatcher -- and let selection co-adapt
# (order x placement x bay-choice) with ZERO realization gap: every genome
# decodes to a complete FEASIBLE assignment by construction (raster scan +
# exact _can_place gate + force-place tail, all borrowed verbatim from v25).
#
# Genome (flat float32 array), for n blocks / m bays:
#   [0:n]            priority keys in [0,1)   -- LOWER key = higher admission
#                                               priority (replaces v25 ATC)
#   [n:n+n*m]        bay-bias matrix in [-1,1] -- tilts v25 bay economics
#   [-3] gamma  [-2] bias_scale  [-1] contact-gene   (3 global policy genes)
#
# Machinery REUSED from myalgorithm_25 (imported, never copied):
#   _Raster (masks/scan/add/remove/footprint), _order_cells, _rel_sched_bbox,
#   _can_place, _mkblock, _force_place, _orient_fits, _unique_orients,
#   _min_area, _objective, _bay_u, _build_operations, _improve, Bay,
#   check_feasibility, and _dispatch_construct (used ONCE for the warm start).
# The event-loop decoder below is a thin wrapper: same structure as
# _dispatch_construct, but ATC priority -> genome key, and bay economics get a
# genome bias term.  All geometry/feasibility calls delegate to v25.
# =============================================================================
import os
import sys
import time
import heapq
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import myalgorithm_25 as M25   # noqa: E402


_CAND_CAP = 12          # exact _can_place gates per (bay,orient), == v25 default
_N_GLOBAL = 3           # gamma, bias_scale, contact-gene
_ELITE_FRAC = 0.30
_MUTANT_FRAC = 0.15
_ELITE_GENE_PROB = 0.70
_EVOLVE_FRAC = 0.85     # stop evolving here; spend the tail on _improve
_TARGET_GENS = 12       # aim for >= this many generations when scaling pop


def _brkga(prob_info, timelimit, t0):
    M25._reset_caches()
    bays = [M25.Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    n = len(blocks_data)
    m = len(bays)
    w = prob_info.get("weights", {})
    w1 = w.get("w1", 1.0)
    w2 = w.get("w2", 1.0)
    w3 = w.get("w3", 1.0)
    bay_u = M25._bay_u(bays)
    raster = M25._Raster(prob_info, bays)

    procs = [int(b["processing_time"]) for b in blocks_data]
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    orients_of = [M25._unique_orients(b) for b in blocks_data]
    rel_sorted = sorted(range(n), key=lambda i: rels[i])
    max_pref = [max(b["bay_preferences"]) for b in blocks_data]
    bias_unit = max(1.0, 0.5 * w1 + 0.5 * w3)

    hard_deadline = t0 + timelimit
    evolve_deadline = t0 + timelimit * _EVOLVE_FRAC
    improve_deadline = t0 + timelimit * 0.97   # reserve tail for check_feasibility

    glen = n + n * m + _N_GLOBAL
    rng = np.random.default_rng(0xC0FFEE)

    # -- decoder ---------------------------------------------------------------
    def decode(genome):
        """Event-driven greedy construction driven by the genome. Mirrors
        v25._dispatch_construct, but admission order = genome key (ascending)
        and bay choice = v25 economics + genome bias. Deterministic (no rng into
        _order_cells) so a genome's fitness is stable across generations.
        Returns (internal_objective, assignment_dict). Always complete/feasible:
        the force-place tail schedules any straggler in a fresh empty-bay
        window against a full rebuilt schedule."""
        keys = genome[0:n]
        bias = genome[n:n + n * m].reshape(n, m)
        gamma = float(min(1.0, max(0.0, genome[-3])))
        bscale = float(min(2.0, max(0.0, genome[-2])))
        prefer_contact = bool(genome[-1] > 0.5)

        raster.reset()
        sched = [[] for _ in range(m)]          # bay -> [(blk, entry, exit, bbox)]
        assignments = {}
        exits_at = {}                            # t -> [(bay, bi, oi, x, y)]
        heap = sorted(set(rels))
        heapq.heapify(heap)
        scheduled = set(heap)
        queue = set()
        rp = 0
        last_t = None

        def bay_score(bi, bay_id):
            prefs = blocks_data[bi]["bay_preferences"]
            bay = bays[bay_id]
            area = bay.width * bay.height
            util = 0.0
            if raster.occ[bay_id]:
                util = float(raster.footprint(bay_id).sum()) / max(1.0, area)
            s = w3 * (max_pref[bi] - prefs[bay_id]) + gamma * w1 * util
            s += bscale * float(bias[bi, bay_id]) * bias_unit
            return s

        def try_place(bi, t):
            blk = blocks_data[bi]
            exit_t = t + procs[bi]
            order = sorted(range(m), key=lambda j: bay_score(bi, j))
            for bay_id in order:
                bay = bays[bay_id]
                rel = M25._rel_sched_bbox(sched[bay_id], t, exit_t)
                occ_fp = raster.footprint(bay_id) if prefer_contact else None
                for oi in orients_of[bi]:
                    if not M25._orient_fits(blk, oi, bay):
                        continue
                    feas, cx0, cy0 = raster.scan(bay_id, bi, oi)
                    if feas is None or not feas.any():
                        continue
                    cells = M25._order_cells(raster, feas, cx0, cy0, bi, oi,
                                             raster.W[bay_id], occ_fp,
                                             prefer_contact, None)
                    tried = 0
                    for (x, y) in cells:
                        nb = M25._mkblock(bi, blk, x, y, oi)
                        if M25._can_place(bay, rel, nb, t, exit_t):
                            return (bay_id, x, y, oi, t, exit_t)
                        tried += 1
                        if tried >= _CAND_CAP:
                            break
            return None

        def commit(bi, place):
            bay_id, x, y, oi, entry, exit_t = place
            nb = M25._mkblock(bi, blocks_data[bi], x, y, oi)
            sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
            assignments[bi] = {
                "block_id": bi, "bay_id": bay_id, "x": int(x), "y": int(y),
                "orient_idx": oi, "entry_time": int(entry),
                "exit_time": int(exit_t),
            }
            raster.add(bay_id, bi, oi, x, y)
            exits_at.setdefault(exit_t, []).append((bay_id, bi, oi, x, y))
            if exit_t not in scheduled:
                heapq.heappush(heap, exit_t)
                scheduled.add(exit_t)
            queue.discard(bi)

        while heap:
            t = heapq.heappop(heap)
            scheduled.discard(t)
            if t == last_t:
                continue
            last_t = t
            ev = exits_at.pop(t, None)
            if ev:
                touched = set()
                for (bay_id, bi, oi, x, y) in ev:
                    raster.remove(bay_id, bi, oi, x, y)
                    touched.add(bay_id)
                for bj in touched:
                    sched[bj] = [it for it in sched[bj] if it[2] > t]
            while rp < n and rels[rel_sorted[rp]] <= t:
                queue.add(rel_sorted[rp])
                rp += 1
            if not queue:
                continue
            if time.time() > hard_deadline:
                break
            for bi in sorted(queue, key=lambda b: keys[b]):
                place = try_place(bi, t)
                if place is not None:
                    commit(bi, place)
            if queue and not heap:
                break

        # force-place tail against a COMPLETE rebuilt schedule so every
        # straggler lands in a genuinely empty bay-window (time-disjoint from
        # all placed blocks => trivially collision-free and crane-clear).
        full_sched = [[] for _ in range(m)]
        for bi, a in assignments.items():
            nb = M25._mkblock(bi, blocks_data[bi], a["x"], a["y"],
                              a["orient_idx"])
            full_sched[a["bay_id"]].append(
                (nb, a["entry_time"], a["exit_time"], nb.bounding_rect()))
        remaining = [bi for bi in range(n) if bi not in assignments]
        remaining.sort(key=lambda bi: (dues[bi], -M25._min_area(blocks_data[bi])))
        for bi in remaining:
            blk = blocks_data[bi]
            bay_id, x, y, oi, entry, exit_t = M25._force_place(
                bi, blk, bays, full_sched)
            nb = M25._mkblock(bi, blk, x, y, oi)
            full_sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
            assignments[bi] = {
                "block_id": bi, "bay_id": bay_id, "x": int(x), "y": int(y),
                "orient_idx": oi, "entry_time": int(entry),
                "exit_time": int(exit_t),
            }

        obj = M25._objective(assignments, blocks_data, bays,
                             bay_u, w1, w2, w3)[0]
        return obj, assignments

    # -- genome factories ------------------------------------------------------
    def random_genome():
        g = np.empty(glen, dtype=np.float64)
        g[0:n] = rng.random(n)
        g[n:n + n * m] = rng.uniform(-1.0, 1.0, n * m)
        g[-3] = rng.uniform(0.0, 1.0)
        g[-2] = rng.uniform(0.0, 1.5)
        g[-1] = rng.random()
        return g

    # -- WARM START: one v25-champion ATC realization, rank-encoded ------------
    raster.reset()
    atc_assign = M25._dispatch_construct(prob_info, bays, bay_u, w1, w2, w3,
                                         evolve_deadline, raster)
    order_ids = sorted(range(n), key=lambda bi: (atc_assign[bi]["entry_time"],
                                                 atc_assign[bi]["bay_id"], bi))
    warm_keys = np.empty(n, dtype=np.float64)
    for rank, bi in enumerate(order_ids):
        warm_keys[bi] = (rank + 0.5) / n
    warm_bias = np.zeros((n, m), dtype=np.float64)
    for bi in range(n):
        warm_bias[bi, atc_assign[bi]["bay_id"]] = -0.5   # nudge toward realized bay

    def warm_genome(jit):
        g = np.empty(glen, dtype=np.float64)
        g[0:n] = np.clip(warm_keys + rng.normal(0.0, jit, n), 0.0, 1.0)
        b = np.clip(warm_bias + rng.normal(0.0, jit, (n, m)), -1.0, 1.0)
        g[n:n + n * m] = b.ravel()
        g[-3] = 0.5
        g[-2] = 0.5
        g[-1] = 0.3
        return g

    # -- measure decode cost on the (near-exact) warm genome, then size pop ----
    seed0 = warm_genome(0.0)
    t_d = time.time()
    obj0, assign0 = decode(seed0)
    t_dec = max(1e-4, time.time() - t_d)

    avail = evolve_deadline - time.time()
    budget_dec = max(1, int(avail / t_dec))
    pop = 30
    if budget_dec < pop * _TARGET_GENS:
        pop = budget_dec // _TARGET_GENS
    pop = int(min(30, max(8, pop)))
    n_elite = max(2, int(_ELITE_FRAC * pop))
    n_mutant = max(1, int(_MUTANT_FRAC * pop))

    decodes = 1   # count genome decodes (the warm ATC dispatch is separate)
    best_obj, best_assign = obj0, assign0

    def safe_decode(g):
        nonlocal decodes, best_obj, best_assign
        try:
            o, a = decode(g)
        except Exception:
            return None
        decodes += 1
        if o < best_obj:
            best_obj, best_assign = o, a
        return {"g": g, "obj": o, "assign": a}

    # -- initial population: warm elites + random mutants ----------------------
    population = [{"g": seed0, "obj": obj0, "assign": assign0}]
    n_warm = min(pop - 1, 4)
    for _ in range(n_warm):
        ind = safe_decode(warm_genome(0.05))
        if ind is not None:
            population.append(ind)
    while len(population) < pop:
        ind = safe_decode(random_genome())
        if ind is not None:
            population.append(ind)

    # -- BRKGA generations -----------------------------------------------------
    def crossover(ge, gne):
        mask = rng.random(glen) < _ELITE_GENE_PROB
        return np.where(mask, ge, gne).copy()

    gens = 0
    while time.time() < evolve_deadline:
        gens += 1
        population.sort(key=lambda ind: ind["obj"])
        elites = population[:n_elite]
        non_elites = population[n_elite:] or elites
        newpop = elites[:]                       # elites survive unchanged
        for _ in range(n_mutant):
            if time.time() >= evolve_deadline:
                break
            ind = safe_decode(random_genome())
            if ind is not None:
                newpop.append(ind)
        while len(newpop) < pop and time.time() < evolve_deadline:
            pe = elites[int(rng.integers(len(elites)))]
            pne = non_elites[int(rng.integers(len(non_elites)))]
            ind = safe_decode(crossover(pe["g"], pne["g"]))
            if ind is not None:
                newpop.append(ind)
        population = newpop

    # -- verify best decode, then spend the tail on v25 _improve ---------------
    def verified(assign):
        sol = {"operations": M25._build_operations(assign)}
        try:
            if M25.check_feasibility(prob_info, sol)["feasible"]:
                return sol
        except Exception:
            return None
        return None

    best_sol = verified(best_assign)
    report_obj = best_obj

    if time.time() < improve_deadline - 0.5:
        try:
            imp_assign, imp_obj = M25._improve(
                prob_info, best_assign, bays, bay_u, w1, w2, w3,
                improve_deadline, forced=False, raster=None)
            if imp_obj < best_obj:
                vs = verified(imp_assign)
                if vs is not None:
                    best_sol, report_obj = vs, imp_obj
        except Exception:
            pass

    if best_sol is not None:
        print("[S1] own=%d gens=%d decodes=%d" % (int(report_obj), gens, decodes),
              flush=True)
        return best_sol

    # decode + improve both failed official verification -> delegate to v25.
    print("[S1] FALLBACK", flush=True)
    rem = max(1.0, hard_deadline - time.time())
    return M25.algorithm(prob_info, rem)


def algorithm(prob_info, timelimit=60):
    t0 = time.time()
    try:
        return _brkga(prob_info, timelimit, t0)
    except Exception:
        print("[S1] FALLBACK", flush=True)
        rem = max(1.0, timelimit - (time.time() - t0))
        return M25.algorithm(prob_info, rem)


if __name__ == "__main__":
    import json
    _prob = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        _HERE, "..", "train", "prob_1.json")
    _tl = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    with open(_prob) as _f:
        _pi = json.load(_f)
    _st = time.time()
    _sol = algorithm(_pi, _tl)
    _res = M25.check_feasibility(_pi, _sol)
    print("instance=%s blocks=%d feasible=%s obj=%s elapsed=%.1fs" % (
        os.path.basename(_prob), len(_pi["blocks"]), _res["feasible"],
        _res.get("objective"), time.time() - _st))
