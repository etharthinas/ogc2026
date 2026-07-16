#!/usr/bin/env python3
"""exp_pool_diversity.py -- CEILING measurement for cross-paradigm SOLUTION-MERGE
recombination on the FORCED instances {26,27}.

Hypothesis (coordinator): the S4 merge gained 0 on forced {26,27} because v25's
own portfolio candidates are structurally HOMOGENEOUS (same forward-greedy
queue), so the recombination CP-SAT has no profitable swaps to make. If we inject
structurally DIVERSE full solutions from the radical arms (S1 BRKGA random-key,
S2 backward, S3 partition-first) into the pool, the CP-SAT may find improving
cross-paradigm swaps. If the ceiling is ~0 even with rich pools + generous solve
time, the whole family closes.

This is an OFFLINE diagnostic: no budget constraint, long runs are fine.

Per instance k in {26,27}:
  1. CHAMPION + BASE POOL: v25_{k}.json champion (banked-equivalent) as warm
     start; also harvest v25's portfolio at 600s (all streamed candidates) via
     radical_s4_merge._harvest.
  2. DIVERSITY INJECTION: 6-10 structurally different full solutions:
       s2_backward   -- backward (due-anchored) builds + legalize + polish
       s3_partition  -- distinct CP-SAT partitions realized by the v25 dispatcher
       s1_brkga      -- one real BRKGA evolved decode
       s1_randomkey  -- random admission-order forward constructions (BRKGA-
                        flavored random-key proxy; the real decode() is a
                        non-importable closure inside _brkga)
  3. MERGE (generous): pool = champion + v25 candidates + diverse; pairwise
     space-time-crane compat; CP-SAT (300s, warm = champion); replay repair;
     official check_feasibility. A v25-ONLY control merge isolates the value the
     diverse injection adds beyond v25's homogeneous set.
  4. Report: pool sizes, per-source counts, merged obj vs banked, and WHICH
     sources contributed the swapped placements in an improved merge.

Windows spawn note: harvest spawns myalgorithm_25 workers; keep everything under
the __main__ guard so re-imported children don't re-run the experiment.
"""
import copy
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import myalgorithm_25 as M25
import radical_s4_merge as S4
from utils import check_feasibility

BANKED = {26: 8_551_513, 27: 24_972_962}

HARVEST_S = float(os.environ.get("EXP_HARVEST_S", "600"))
SOLVE_FULL_S = float(os.environ.get("EXP_SOLVE_FULL_S", "300"))
SOLVE_CTRL_S = float(os.environ.get("EXP_SOLVE_CTRL_S", "120"))
PAIR_BUDGET_S = float(os.environ.get("EXP_PAIR_S", "150"))
POOL_CAP = int(os.environ.get("EXP_POOL_CAP", "60"))     # per-block placement cap


# ---------------------------------------------------------------------------
# solution helpers
# ---------------------------------------------------------------------------

def _load_champion(k):
    d = json.load(open(os.path.join(HERE, f"v25_{k}.json")))
    return {int(bi): v for bi, v in d.items()}


def _obj(assign, prob, bays, bay_u):
    w = prob.get("weights", {})
    return M25._objective(assign, prob["blocks"], bays, bay_u,
                          w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0))[0]


def _feasible(prob, assign):
    try:
        return bool(check_feasibility(
            prob, {"operations": M25._build_operations(assign)}).get("feasible"))
    except Exception:
        return False


def _ops_to_assign(ops):
    assign = {}
    for t_str, oplist in ops.items():
        t = int(t_str)
        for op in oplist:
            bi = int(op["block_id"])
            a = assign.setdefault(bi, {"block_id": bi})
            if op["type"] == "ENTRY":
                a["bay_id"] = int(op["bay_id"]); a["x"] = int(op["x"])
                a["y"] = int(op["y"]); a["orient_idx"] = int(op["orient_idx"])
                a["entry_time"] = t
            else:
                a["exit_time"] = t
    return assign


# ---------------------------------------------------------------------------
# diversity generation
# ---------------------------------------------------------------------------

def _gen_s2_backward(prob, bays, bay_u, w1, w2, w3, forced, raster, n):
    """Backward (due-anchored) construction + legalize, then two polished
    variants (different improver seeds). Returns list of (label, assign)."""
    import radical_s2_backward as S2
    out = []
    try:
        M25._reset_caches()
        if raster is not None:
            raster.reset()
        base, _placed = S2._backward_construct(
            prob, bays, bay_u, w1, w2, w3, raster, forced)
        S2._legalize_release(base, prob, bays, bay_u, w1, w2, w3, raster, forced)
        S2._left_shift(base, prob, bays, time.time() + 20.0)
        if len(base) == n:
            out.append(("s2_backward", {bi: dict(a) for bi, a in base.items()}))
        for seed in (4242, 8888):
            try:
                cp = {bi: dict(a) for bi, a in base.items()}
                imp, _o = M25._improve(
                    prob, cp, bays, bay_u, w1, w2, w3,
                    time.time() + 25.0, forced, seed=seed, raster=raster,
                    repack_every=(3 if forced else 4), xbay=forced,
                    repack_win_scale=2.0)
                if imp is not None and len(imp) == n:
                    out.append(("s2_backward", imp))
            except Exception:
                pass
    except Exception as e:
        print(f"  [s2] FAILED: {e}", flush=True)
    return out


def _gen_s3_partition(prob, bays, bay_u, w1, w2, w3, raster, n):
    """Enumerate distinct CP-SAT partitions and realize each with the v25
    dispatcher constrained to the partition. Returns list of (label, assign)."""
    import radical_s3_partition as S3
    out = []
    try:
        M25._reset_caches()
        parts, _cf = S3._enumerate_partitions(
            prob, bays, S3.CAP_FRAC_DEFAULT, S3.K_PARTITIONS,
            cp_total_s=60.0, cp_first_s=15.0, debug=False)
        for i, part in enumerate(parts):
            try:
                part_prob = S3._partition_prob(prob, part)
                if raster is not None:
                    raster.reset()
                assign = S3._realize(part_prob, bays, bay_u, w1, w2, w3, raster,
                                     time.time() + 25.0, seed=4200 + i)
                if assign is not None and len(assign) == n:
                    # placements are real; obj/feasibility judged on ORIGINAL prob
                    out.append(("s3_partition", {bi: dict(a)
                                                 for bi, a in assign.items()}))
            except Exception:
                pass
    except Exception as e:
        print(f"  [s3] FAILED: {e}", flush=True)
    return out


def _gen_s1_brkga(prob, n):
    """One real BRKGA evolved decode via radical_s1_brkga.algorithm."""
    import radical_s1_brkga as S1
    out = []
    try:
        sol = S1.algorithm(prob, 90.0)
        a = _ops_to_assign(sol["operations"])
        if len(a) == n:
            out.append(("s1_brkga", a))
    except Exception as e:
        print(f"  [s1_brkga] FAILED: {e}", flush=True)
    return out


def _gen_s1_randomkey(prob, bays, bay_u, w1, w2, w3, forced, n, count=3):
    """Random admission-order forward constructions -- a robust proxy for BRKGA
    random-key decodes (the real decode() is a closure inside _brkga). Different
    random orders -> structurally different packings."""
    out = []
    for s in range(count):
        try:
            M25._reset_caches()
            rng = random.Random(97531 + s)
            order = list(range(n))
            rng.shuffle(order)
            assign = M25._construct(prob, order, bays, bay_u, w1, w2, w3,
                                    time.time(), time.time() + 40.0,
                                    forced=forced)
            if len(assign) == n:
                out.append(("s1_randomkey", {bi: dict(a)
                                             for bi, a in assign.items()}))
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# source-tagged pool
# ---------------------------------------------------------------------------

def _add_solution(pool, seen, assign, source, n):
    if assign is None or len(assign) != n:
        return False
    for bi, a in assign.items():
        bi = int(bi)
        key = (a["bay_id"], a["x"], a["y"], a["orient_idx"],
               a["entry_time"], a["exit_time"])
        d = seen.setdefault(bi, {})
        pl = d.get(key)
        if pl is None:
            pl = {"bi": bi, "bay": a["bay_id"], "x": a["x"], "y": a["y"],
                  "oi": a["orient_idx"], "entry": a["entry_time"],
                  "exit": a["exit_time"], "sources": set()}
            d[key] = pl
            pool.setdefault(bi, []).append(pl)
        pl["sources"].add(source)
    return True


def _cap_pool(pool, cap):
    """Bound per-block placement count while ALWAYS keeping champion + any
    diverse-source placement; fill remaining slots with v25/harvest placements."""
    div = {"s2_backward", "s3_partition", "s1_brkga", "s1_randomkey", "champion"}
    for bi, plist in pool.items():
        if len(plist) <= cap:
            continue
        keep = [p for p in plist if p["sources"] & div]
        rest = [p for p in plist if not (p["sources"] & div)]
        room = max(0, cap - len(keep))
        pool[bi] = keep + rest[:room]


def _key_of(a):
    return (a["bay_id"], a["x"], a["y"], a["orient_idx"],
            a["entry_time"], a["exit_time"])


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def _run_merge(prob, bays, bay_u, w1, w2, w3, pool, champion, solve_s, label):
    """Precompute pairwise compat, CP-SAT recombine (warm=champion), replay
    repair, official check. Returns (assign_or_None, obj_or_inf, feasible)."""
    raster = M25._Raster(prob, bays)
    t0 = time.time()
    incompat, n_checks, timed_out = S4._precompute_pairs(
        raster, bays, prob["blocks"], pool, deadline=t0 + PAIR_BUDGET_S)
    pre_dt = time.time() - t0
    print(f"    [{label}] pairs: checks={n_checks} incompat={len(incompat)} "
          f"precompute={pre_dt:.1f}s{' TIMEOUT' if timed_out else ''}", flush=True)
    merged = S4._recombine(prob, bays, bay_u, w1, w2, w3, pool, incompat,
                           champion, budget_s=solve_s)
    if merged is None:
        print(f"    [{label}] CP-SAT: no solution", flush=True)
        return None, float("inf"), False
    repaired, feas = S4._repair_replay(prob, merged, champion, rounds=3)
    if not feas:
        print(f"    [{label}] merged INFEASIBLE after replay repair", flush=True)
        return None, float("inf"), False
    off = _feasible(prob, repaired)
    ob = _obj(repaired, prob, bays, bay_u)
    return repaired, ob, off


def _source_contribution(pool, merged, champion):
    """For each block whose chosen placement differs from the champion, attribute
    the swap to the sources that provided it. Returns (provided, exclusive) dicts
    source -> swap count, plus total swaps."""
    provided, exclusive = {}, {}
    swaps = 0
    for bi, a in merged.items():
        bi = int(bi)
        ck = _key_of(champion[bi])
        mk = _key_of(a)
        if mk == ck:
            continue
        swaps += 1
        srcs = set()
        for pl in pool.get(bi, []):
            if (pl["bay"], pl["x"], pl["y"], pl["oi"], pl["entry"],
                    pl["exit"]) == mk:
                srcs = pl["sources"]
                break
        nonchamp = srcs - {"champion"}
        for s in nonchamp:
            provided[s] = provided.get(s, 0) + 1
        if len(nonchamp) == 1:
            s = next(iter(nonchamp))
            exclusive[s] = exclusive.get(s, 0) + 1
    return provided, exclusive, swaps


# ---------------------------------------------------------------------------
# per-instance driver
# ---------------------------------------------------------------------------

def run_instance(k):
    print("=" * 78, flush=True)
    print(f"INSTANCE prob_{k}  (banked = {BANKED[k]:,})", flush=True)
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    n = len(prob["blocks"])
    bays = [M25.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M25._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    forced = M25._is_forced(prob, bays)

    champion = _load_champion(k)
    champ_obj = _obj(champion, prob, bays, bay_u)
    champ_feas = _feasible(prob, champion)
    print(f"  champion: obj={champ_obj:,.0f} feasible={champ_feas} "
          f"(banked {BANKED[k]:,}) n={n} bays={len(bays)} forced={forced}",
          flush=True)

    # -- 1. harvest v25 portfolio --------------------------------------------
    print(f"  harvesting v25 portfolio {HARVEST_S:.0f}s ...", flush=True)
    th = time.time()
    try:
        v25_cands = S4._harvest(prob, HARVEST_S, th)
    except Exception as e:
        print(f"  [harvest] FAILED: {e}", flush=True)
        v25_cands = []
    # dedup v25 candidates by signature
    v25_uniq = {}
    for obj, assign in v25_cands:
        if assign is None or len(assign) != n:
            continue
        v25_uniq[S4._sol_sig(assign)] = (obj, assign)
    v25_sols = [a for _, a in sorted(v25_uniq.values(), key=lambda c: c[0])]
    print(f"  v25 harvest: streamed={len(v25_cands)} distinct={len(v25_sols)} "
          f"({time.time() - th:.0f}s)", flush=True)

    # -- 2. diversity injection ----------------------------------------------
    print("  generating diverse solutions ...", flush=True)
    raster = M25._Raster(prob, bays) if M25._HAVE_NUMPY else None
    diverse = []
    diverse += _gen_s2_backward(prob, bays, bay_u, w1, w2, w3, forced, raster, n)
    diverse += _gen_s3_partition(prob, bays, bay_u, w1, w2, w3, raster, n)
    diverse += _gen_s1_brkga(prob, n)
    diverse += _gen_s1_randomkey(prob, bays, bay_u, w1, w2, w3, forced, n)
    # per-source feasibility + objective summary
    src_count = {}
    for label, a in diverse:
        feas = _feasible(prob, a)
        ob = _obj(a, prob, bays, bay_u)
        c = src_count.setdefault(label, [0, 0])
        c[0] += 1
        c[1] += 1 if feas else 0
        print(f"    {label}: obj={ob:,.0f} feasible={feas}", flush=True)
    print(f"  diverse solutions: {len(diverse)} "
          f"({ {s: f'{c[0]}({c[1]}feas)' for s, c in src_count.items()} })",
          flush=True)

    # -- 3a. CONTROL merge: champion + v25 harvest only ----------------------
    pool_ctrl, seen_ctrl = {}, {}
    _add_solution(pool_ctrl, seen_ctrl, champion, "champion", n)
    n_v25_in = sum(_add_solution(pool_ctrl, seen_ctrl, a, "v25", n)
                   for a in v25_sols)
    _cap_pool(pool_ctrl, POOL_CAP)
    ctrl_sizes = [len(p) for p in pool_ctrl.values()]
    print(f"  CONTROL pool (champion+v25): avg={sum(ctrl_sizes)/len(ctrl_sizes):.1f} "
          f"max={max(ctrl_sizes)} v25_sols_in={n_v25_in}", flush=True)
    ctrl_assign, ctrl_obj, ctrl_feas = _run_merge(
        prob, bays, bay_u, w1, w2, w3, pool_ctrl, champion, SOLVE_CTRL_S,
        "control")

    # -- 3b. FULL merge: champion + v25 harvest + diverse --------------------
    pool_full, seen_full = {}, {}
    _add_solution(pool_full, seen_full, champion, "champion", n)
    for a in v25_sols:
        _add_solution(pool_full, seen_full, a, "v25", n)
    for label, a in diverse:
        _add_solution(pool_full, seen_full, a, label, n)
    _cap_pool(pool_full, POOL_CAP)
    full_sizes = [len(p) for p in pool_full.values()]
    # count distinct placements contributed exclusively by diverse sources
    div_srcs = {"s2_backward", "s3_partition", "s1_brkga", "s1_randomkey"}
    div_only_pl = sum(1 for plist in pool_full.values() for p in plist
                      if p["sources"] & div_srcs and not (p["sources"] & {"v25", "champion"}))
    print(f"  FULL pool (champion+v25+diverse): avg={sum(full_sizes)/len(full_sizes):.1f} "
          f"max={max(full_sizes)} total_placements={sum(full_sizes)} "
          f"diverse_exclusive_placements={div_only_pl}", flush=True)
    full_assign, full_obj, full_feas = _run_merge(
        prob, bays, bay_u, w1, w2, w3, pool_full, champion, SOLVE_FULL_S,
        "full")

    # -- 4. report -----------------------------------------------------------
    banked = BANKED[k]
    print("-" * 78, flush=True)
    print(f"  RESULT prob_{k}: banked={banked:,} champion={champ_obj:,.0f}",
          flush=True)
    if ctrl_feas:
        print(f"    control merge (champ+v25):        {ctrl_obj:,.0f}  "
              f"(vs banked {ctrl_obj - banked:+,.0f})", flush=True)
    else:
        print("    control merge: infeasible/no-improve", flush=True)
    if full_feas:
        print(f"    FULL merge (champ+v25+diverse):   {full_obj:,.0f}  "
              f"(vs banked {full_obj - banked:+,.0f})", flush=True)
        prov, excl, swaps = _source_contribution(pool_full, full_assign, champion)
        print(f"    swaps vs champion: {swaps}", flush=True)
        print(f"    source PROVIDED swapped placements:  {prov}", flush=True)
        print(f"    source EXCLUSIVE swapped placements: {excl}", flush=True)
        diverse_gain = (full_obj < champ_obj - 1e-9) and bool(
            (prov.get("s2_backward", 0) + prov.get("s3_partition", 0)
             + prov.get("s1_brkga", 0) + prov.get("s1_randomkey", 0)) > 0)
        print(f"    diverse sources contributed to an improved merge: "
              f"{diverse_gain}", flush=True)
    else:
        print("    FULL merge: infeasible/no-improve", flush=True)
    print("=" * 78, flush=True)
    return {
        "k": k, "banked": banked, "champion": champ_obj,
        "control": ctrl_obj if ctrl_feas else None,
        "full": full_obj if full_feas else None,
    }


def main():
    ks = [int(x) for x in sys.argv[1:]] or [26, 27]
    print(f"exp_pool_diversity: instances={ks} harvest={HARVEST_S:.0f}s "
          f"solve_full={SOLVE_FULL_S:.0f}s solve_ctrl={SOLVE_CTRL_S:.0f}s",
          flush=True)
    results = []
    for k in ks:
        try:
            results.append(run_instance(k))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"INSTANCE prob_{k} CRASHED: {e}", flush=True)
    print("\n########## SUMMARY ##########", flush=True)
    for r in results:
        cd = f"{r['control']:,.0f}" if r["control"] is not None else "n/a"
        fd = f"{r['full']:,.0f}" if r["full"] is not None else "n/a"
        print(f"prob_{r['k']}: banked={r['banked']:,} champion={r['champion']:,.0f} "
              f"control={cd} full={fd}", flush=True)


if __name__ == "__main__":
    main()
