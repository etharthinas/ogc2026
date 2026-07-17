# exp_joint_frozen.py  --  v34 diagnostic: JOINT (swap/chain) TIME-FROZEN
# obj2/obj3 relocation ceiling experiment.
# =============================================================================
# Motivation: v34's single-move tail fired on {31,38} with ZERO accepted moves
# -- space saturation means no OFF-preference block has any feasible SINGLE
# time-frozen relocation. But SWAPS / CHAINS can still be feasible: A moves into
# B's vacated spot while B moves elsewhere, simultaneously.
#
# Soundness (why this escapes the S4 merge model's inexpressibility): with ALL
# entry/exit times FROZEN to the champion's, the replay order and co-resident
# sets are FIXED -- only positions vary. Pairwise position-compatibility between
# two blocks' candidate placements is then EXACT (collision over the fixed time
# overlap + crane dominance against the fixed co-resident sets). So a joint
# CP-SAT over time-frozen position choices is sound AND complete for this move
# class. We reuse the S4 merge's exact frozen-time pair predicate verbatim
# (_merge_incompatible == exact static reduction of _can_place, windows fixed).
#
# Pipeline per instance k:
#   1. Load champion baseline/v25_k.json (bid -> {bay_id,x,y,orient_idx,
#      entry_time,exit_time}) and train/prob_k.json.
#   2. MOVABLE SET: off-preference blocks (assigned bay != argmax pref) + blocks
#      in the Z2-max (max normalized load) bay + every block whose footprint
#      spatially overlaps (dilated ~2 cells) any of those during the frozen
#      intervals; cap ~80. Everything else FIXED at the champion.
#   3. CANDIDATE POOL / movable: champion placement + feasible (bay,x,y,orient)
#      at the FROZEN [entry,exit) enumerated with raster.scan_scoped against
#      FIXED blocks ONLY (movable excluded from the obstacle set; their mutual
#      interactions are the CP-SAT's pairwise constraints), exact-gated with
#      _can_place vs the fixed co-residents; cap ~40, preferred-bay + diverse.
#   4. PAIRWISE COMPAT: for movable pairs whose candidates share a bay, exact
#      frozen-time incompatibility via _merge_incompatible (mask pre-filter ->
#      _exact_pair_rel). Incompatible candidate pairs are mutually exclusive.
#   5. CP-SAT: one candidate / movable; incompat pairs excluded; objective =
#      w3*obj3 + w2*(linearized Z2). obj1 frozen by construction (asserted).
#      Warm-started from the champion. 300s.
#   6. Replay-verify with utils.check_feasibility; report per instance movable
#      count, avg candidates, swaps found, dObj2/dObj3, weighted delta vs banked.
#
# OFFLINE DIAGNOSTIC ONLY -- generous budgets, never part of a submission.
# =============================================================================
import os
import sys
import json
import time
import math

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
os.chdir(_HERE)  # myalgorithm_34 does `from utils import ...` relative to cwd

import myalgorithm_34 as M          # reuse every audited primitive
from ortools.sat.python import cp_model

BANKED = {31: 8_124_019, 38: 36_351_493}
MOV_CAP = 80
CAND_CAP = 40
DILATE = 2
CPSAT_S = 300.0
SCALE = 1000          # imbalance linearization scale
WSCALE = 1000         # weight scale (keeps small w2 precise vs large w3)


def _bbox_of(bi, blk, x, y, oi):
    nb = M._mkblock(bi, blk, x, y, oi)
    return nb.bounding_rect()          # (x0, y0, x1, y1) world coords


def _time_overlap(a1, e1, a2, e2):
    # broad co-residence test (present-at-entry/exit or interval overlap),
    # matching _time_overlap_rel / _rel_sched_bbox.
    return a1 <= e2 and a2 <= e1


def run_instance(k):
    print("=" * 78)
    print(f"[exp_joint_frozen] instance prob_{k}")
    t0 = time.time()
    prob = json.load(open(os.path.join(_HERE, "..", "train", f"prob_{k}.json")))
    champ_raw = json.load(open(os.path.join(_HERE, f"v25_{k}.json")))
    champ = {}
    for _bid, a in champ_raw.items():
        bi = int(a["block_id"])
        champ[bi] = {"block_id": bi, "bay_id": int(a["bay_id"]),
                     "x": int(a["x"]), "y": int(a["y"]),
                     "orient_idx": int(a["orient_idx"]),
                     "entry_time": int(a["entry_time"]),
                     "exit_time": int(a["exit_time"])}

    blocks_data = prob["blocks"]
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    n_bays = len(bays)
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    M._reset_caches()
    raster = M._Raster(prob, bays)

    base_obj, base_o1, base_o2, base_o3 = M._objective(
        champ, blocks_data, bays, bay_u, w1, w2, w3)
    print(f"  weights w1={w1} w2={w2} w3={w3}")
    print(f"  champion obj={base_obj:.1f}  obj1={base_o1:.0f} "
          f"obj2={base_o2:.0f} obj3={base_o3:.0f}")

    # -- per-bay champion load / normalized load -----------------------------
    loads = [0.0] * n_bays
    for bi, a in champ.items():
        loads[a["bay_id"]] += blocks_data[bi]["workload"]
    norm = [bay_u[j] * loads[j] for j in range(n_bays)]
    z2_bay = max(range(n_bays), key=lambda j: norm[j])

    # -- MOVABLE SEEDS: off-preference + Z2-max bay --------------------------
    seeds = set()
    for bi, a in champ.items():
        prefs = blocks_data[bi]["bay_preferences"]
        if a["bay_id"] != max(range(n_bays), key=lambda j: prefs[j]) \
                and prefs[a["bay_id"]] < max(prefs):
            seeds.add(bi)
    for bi, a in champ.items():
        if a["bay_id"] == z2_bay:
            seeds.add(bi)

    # precompute champion world bboxes
    cbb = {bi: _bbox_of(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
           for bi, a in champ.items()}

    # -- spatial-overlap expansion (dilated), within same bay + time overlap --
    expand = {}   # bi -> overlap count with seeds
    for bi, a in champ.items():
        if bi in seeds:
            continue
        bxa = cbb[bi]
        cnt = 0
        for sb in seeds:
            sa = champ[sb]
            if sa["bay_id"] != a["bay_id"]:
                continue
            if not _time_overlap(a["entry_time"], a["exit_time"],
                                 sa["entry_time"], sa["exit_time"]):
                continue
            sbb = cbb[sb]
            # dilated bbox overlap
            if (bxa[0] - DILATE < sbb[2] and sbb[0] < bxa[2] + DILATE
                    and bxa[1] - DILATE < sbb[3] and sbb[1] < bxa[3] + DILATE):
                cnt += 1
        if cnt:
            expand[bi] = cnt

    movable = set(seeds)
    for bi in sorted(expand, key=lambda b: -expand[b]):
        if len(movable) >= MOV_CAP:
            break
        movable.add(bi)
    # if seeds alone exceed the cap, keep them all (value is in the seeds)
    movable = list(movable)
    fixed = [bi for bi in champ if bi not in set(movable)]
    print(f"  Z2-max bay={z2_bay}  seeds={len(seeds)} "
          f"expand_pool={len(expand)}  movable={len(movable)} fixed={len(fixed)}")

    # -- FIXED obstacle schedule per bay (block, entry, exit) -----------------
    fixed_by_bay = [[] for _ in range(n_bays)]
    for bi in fixed:
        a = champ[bi]
        nb = M._mkblock(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
        fixed_by_bay[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"]))

    # -- CANDIDATE POOL per movable ------------------------------------------
    # each candidate: dict(bi, oi, x, y, entry, exit, bay, pen3)
    pool = {}
    for bi in movable:
        a = champ[bi]
        blk = blocks_data[bi]
        entry, exit_t = a["entry_time"], a["exit_time"]
        prefs = blk["bay_preferences"]
        s_max = max(prefs)
        orients = M._unique_orients(blk)
        seen = set()
        cands = []

        def _add_cand(bay_id, x, y, oi):
            key = (bay_id, x, y, oi)
            if key in seen:
                return
            seen.add(key)
            cands.append({"bi": bi, "oi": oi, "x": int(x), "y": int(y),
                          "entry": entry, "exit": exit_t, "bay": bay_id,
                          "pen3": s_max - prefs[bay_id]})

        # champion placement ALWAYS first -> guarantees a feasible fallback.
        _add_cand(a["bay_id"], a["x"], a["y"], a["orient_idx"])

        # bays in preference-descending order (prefer preferred-bay candidates)
        bay_order = sorted(range(n_bays), key=lambda j: -prefs[j])
        per_bay_cap = max(4, CAND_CAP // n_bays)
        for bay_id in bay_order:
            if len(cands) >= CAND_CAP:
                break
            bay = bays[bay_id]
            # fixed co-residents of this bay during [entry, exit)
            relx = [(nb, e, xt) for (nb, e, xt) in fixed_by_bay[bay_id]
                    if _time_overlap(entry, exit_t, e, xt)]
            actives = [(nb.block_id, nb.orient_idx, nb.x, nb.y)
                       for (nb, _e, _x) in relx]
            got = 0
            for oi in orients:
                if not M._orient_fits(blk, oi, bay):
                    continue
                feas, cx0, cy0, occ_fp = raster.scan_scoped(bay_id, actives, bi, oi)
                if feas is None or not feas.any():
                    continue
                cells = M._order_cells(raster, feas, cx0, cy0, bi, oi,
                                       raster.W[bay_id], occ_fp, True, None)
                # spatial diversity: stride-sample the ordered anchors
                stride = max(1, len(cells) // (per_bay_cap * 3))
                for idx in range(0, len(cells), stride):
                    if got >= per_bay_cap or len(cands) >= CAND_CAP:
                        break
                    x, y = cells[idx]
                    nb = M._mkblock(bi, blk, x, y, oi)
                    if M._can_place(bay, relx, nb, entry, exit_t):
                        _add_cand(bay_id, x, y, oi)
                        got += 1
        pool[bi] = cands

    avg_c = sum(len(v) for v in pool.values()) / max(1, len(pool))
    print(f"  candidates: total={sum(len(v) for v in pool.values())} "
          f"avg/block={avg_c:.1f}")

    # -- CP-SAT model --------------------------------------------------------
    model = cp_model.CpModel()
    z = {}            # (bi, cidx) -> BoolVar
    for bi in movable:
        vs = []
        for cidx, _c in enumerate(pool[bi]):
            v = model.NewBoolVar(f"z_{bi}_{cidx}")
            z[(bi, cidx)] = v
            vs.append(v)
        model.Add(sum(vs) == 1)
        model.AddHint(z[(bi, 0)], 1)     # warm start = champion (index 0)

    # pairwise incompatibility (frozen-time exact, same bay only)
    n_pairs = 0
    n_constr = 0
    mov_list = list(movable)
    for ii in range(len(mov_list)):
        bi = mov_list[ii]
        ai = champ[bi]
        for jj in range(ii + 1, len(mov_list)):
            bj = mov_list[jj]
            aj = champ[bj]
            # frozen-time relation depends only on intervals; if the intervals
            # can never co-interact, no candidate pair can ever conflict.
            if not _time_overlap(ai["entry_time"], ai["exit_time"],
                                 aj["entry_time"], aj["exit_time"]):
                continue
            n_pairs += 1
            ci = pool[bi]
            cj = pool[bj]
            for a_idx, pa in enumerate(ci):
                for b_idx, pb in enumerate(cj):
                    if pa["bay"] != pb["bay"]:
                        continue      # different bays never interact
                    if M._merge_incompatible(raster, bays[pa["bay"]],
                                             blocks_data, pa, pb):
                        model.Add(z[(bi, a_idx)] + z[(bj, b_idx)] <= 1)
                        n_constr += 1
    print(f"  interacting movable pairs={n_pairs}  incompat constraints={n_constr}")

    # objective: w3*obj3 + w2*linearized Z2 (obj1 frozen).
    # fixed contributions are constants (obj3) / base loads (obj2).
    fixed_o3 = 0
    for bi in fixed:
        prefs = blocks_data[bi]["bay_preferences"]
        fixed_o3 += max(prefs) - prefs[champ[bi]["bay_id"]]
    base_load_fixed = [0.0] * n_bays
    for bi in fixed:
        base_load_fixed[champ[bi]["bay_id"]] += blocks_data[bi]["workload"]

    obj3_terms = []
    for bi in movable:
        for cidx, c in enumerate(pool[bi]):
            if c["pen3"]:
                obj3_terms.append(c["pen3"] * z[(bi, cidx)])

    # scaled normalized load per bay: N_p = round(SCALE*u_p*load_p)
    Np = []
    for p in range(n_bays):
        terms = [int(round(SCALE * bay_u[p] * base_load_fixed[p]))]
        for bi in movable:
            wl = blocks_data[bi]["workload"]
            coeff = int(round(SCALE * bay_u[p] * wl))
            for cidx, c in enumerate(pool[bi]):
                if c["bay"] == p and coeff:
                    terms.append(coeff * z[(bi, cidx)])
        Np.append(sum(terms))
    z2var = model.NewIntVar(0, 10 ** 12, "z2")
    for p in range(n_bays):
        for q in range(n_bays):
            if p != q:
                model.Add(z2var >= Np[p] - Np[q])

    cW2 = int(round(w2 * WSCALE))
    cW3 = int(round(w3 * WSCALE))
    # both terms carried in units of (WSCALE * SCALE * true-component)
    model.Minimize(cW3 * SCALE * (fixed_o3 + sum(obj3_terms)) + cW2 * z2var)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = CPSAT_S
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = 1
    status = solver.Solve(model)
    print(f"  CP-SAT status={solver.StatusName(status)} "
          f"solve_time={solver.WallTime():.1f}s")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("  NO SOLUTION -- aborting instance")
        return

    # -- reconstruct full assignment ----------------------------------------
    new_assign = {bi: dict(a) for bi, a in champ.items()}  # fixed keep champion
    swaps = 0
    for bi in movable:
        chosen = None
        for cidx, c in enumerate(pool[bi]):
            if solver.Value(z[(bi, cidx)]) == 1:
                chosen = c
                break
        if chosen is None:
            chosen = pool[bi][0]
        a = new_assign[bi]
        moved = (chosen["bay"] != champ[bi]["bay_id"]
                 or chosen["x"] != champ[bi]["x"]
                 or chosen["y"] != champ[bi]["y"]
                 or chosen["oi"] != champ[bi]["orient_idx"])
        if moved:
            swaps += 1
        a["bay_id"] = chosen["bay"]
        a["x"] = chosen["x"]; a["y"] = chosen["y"]
        a["orient_idx"] = chosen["oi"]
        # entry/exit DELIBERATELY UNCHANGED (frozen)

    new_obj, new_o1, new_o2, new_o3 = M._objective(
        new_assign, blocks_data, bays, bay_u, w1, w2, w3)
    # obj1-FREEZE assertion
    assert abs(new_o1 - base_o1) < 1e-9, \
        f"obj1 changed {base_o1} -> {new_o1} (freeze violated)"

    # -- official replay verification ----------------------------------------
    sol = {"operations": M._build_operations(new_assign)}
    res = M.check_feasibility(prob, sol)
    d_o2 = new_o2 - base_o2
    d_o3 = new_o3 - base_o3
    weighted_delta = w2 * d_o2 + w3 * d_o3

    print(f"  RESULT feasible={res['feasible']} "
          f"official_obj={res['objective']}")
    if res["feasible"]:
        print(f"    official obj1={res['obj1']:.0f} obj2={res['obj2']:.0f} "
              f"obj3={res['obj3']:.0f}")
    print(f"  swaps/chains applied = {swaps}")
    print(f"  dObj2 = {d_o2:.0f}  (champ {base_o2:.0f} -> {new_o2:.0f})")
    print(f"  dObj3 = {d_o3:.0f}  (champ {base_o3:.0f} -> {new_o3:.0f})")
    print(f"  weighted internal delta = w2*dObj2 + w3*dObj3 = "
          f"{weighted_delta:.1f}")
    banked = BANKED.get(k)
    if banked:
        frac = (-weighted_delta) / banked * 100.0
        print(f"  banked obj2/3 mass = {banked}  -> unlocked "
              f"{-weighted_delta:.1f} = {frac:.2f}% of banked")
    print(f"  instance wall = {time.time() - t0:.1f}s")
    return {"k": k, "movable": len(movable), "avg_cand": avg_c,
            "swaps": swaps, "dObj2": d_o2, "dObj3": d_o3,
            "weighted_delta": weighted_delta,
            "feasible": bool(res["feasible"])}


def main():
    ks = [31, 38]
    if len(sys.argv) > 1:
        ks = [int(x) for x in sys.argv[1:]]
    results = []
    for k in ks:
        try:
            r = run_instance(k)
            if r:
                results.append(r)
        except Exception as e:
            import traceback
            print(f"  INSTANCE {k} FAILED: {e}")
            traceback.print_exc()
    print("=" * 78)
    print("VERDICT SUMMARY")
    for r in results:
        print(f"  prob_{r['k']}: movable={r['movable']} avg_cand={r['avg_cand']:.1f} "
              f"swaps={r['swaps']} dObj2={r['dObj2']:.0f} dObj3={r['dObj3']:.0f} "
              f"wdelta={r['weighted_delta']:.1f} feas={r['feasible']}")
    any_unlock = any(r["swaps"] > 0 and r["weighted_delta"] < -1e-6
                     for r in results)
    print(f"  JOINT TIME-FROZEN RELOCATION UNLOCKS LOCKED obj2/3 MASS: "
          f"{'YES' if any_unlock else 'NO'}")


if __name__ == "__main__":
    main()
