#!/usr/bin/env python3
"""DEV-ONLY standalone LAHC explorer (heuristic_19.md Improvement 5, unit-test
stage — NOT wired into the submission portfolio yet).

Hypothesis: v18's LNS is objective-gated (never accepts uphill), which a
published comparison (Santini/Ropke/Hvattum 2018) ranks clearly inferior; the
banked incumbents on 31/39/26/33 are deep deterministic basins. This driver
starts from a v18-built incumbent and runs Improved-LAHC over a SISR-style
spatio-temporal string ruin, banking only the verified best-seen.

Design choices (see heuristics/research_survey_v19.md §2):
  - Improved LAHC: accept iff f(cand) <= hist[i mod L] OR f(cand) <= f(cur),
    with <= so tardiness plateaus can drift. L=1000 default (GDRR's value for
    100-300 items).
  - Ruin: spatio-temporal string — same bay, dwell-overlapping, (x,y)-nearest
    cluster around a contribution-weighted seed (avg ~10, cap 15), with a
    split variant (p=0.3) and a bay-time-strip second operator (p=0.25).
  - Repair: existing greedy (_place_block, raster-windowed) with a bay-order
    "blink" (p=0.1: shuffled bay preference order) as cheap repair noise.
  - Reactive escalation: on long idle streaks the ruin grows (string -> strip).

Usage:
  conda run -n ogc2026 python explorer_lahc.py --prob 31 --build 120 \
      --explore 300 [--L 1000] [--seed 1234]
  conda run -n ogc2026 python explorer_lahc.py --prob 31 --baseline 420
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm as m  # noqa: E402
from utils import Bay, check_feasibility  # noqa: E402


def ops_to_assignments(sol):
    assign = {}
    for t, ops in sol["operations"].items():
        for op in ops:
            bi = op["block_id"]
            if op["type"] == "ENTRY":
                a = assign.setdefault(bi, {"block_id": bi})
                a.update(bay_id=op["bay_id"], x=op["x"], y=op["y"],
                         orient_idx=op["orient_idx"], entry_time=int(t))
            else:
                assign.setdefault(bi, {"block_id": bi})["exit_time"] = int(t)
    return assign


def sisr_destroy(cur, blocks_data, w1, w3, rng, avg_size=10, cap=15,
                 p_split=0.3, p_strip=0.25, strip_scale=2):
    """Spatio-temporal string removal (SISR adapted to bay packing)."""
    weighted = []
    for bi, a in cur.items():
        blk = blocks_data[bi]
        c = (w1 * max(0, a["exit_time"] - blk["due_date"])
             + w3 * (max(blk["bay_preferences"])
                     - blk["bay_preferences"][a["bay_id"]]))
        if c > 0:
            weighted.append((c, bi))
    if weighted and rng.random() < 0.8:
        # roulette over contribution (keeps some exploration on clean blocks)
        tot = sum(c for c, _ in weighted)
        r = rng.random() * tot
        acc = 0.0
        seed = weighted[-1][1]
        for c, bi in weighted:
            acc += c
            if acc >= r:
                seed = bi
                break
    else:
        seed = rng.choice(list(cur))
    sa = cur[seed]
    bay = sa["bay_id"]
    if rng.random() < p_strip:
        procs = sorted(blocks_data[bi]["processing_time"] for bi in cur)
        half = max(1, procs[len(procs) // 2] * strip_scale)
        lo, hi = sa["entry_time"] - half, sa["exit_time"] + half
        rem = {bi for bi, a in cur.items()
               if a["bay_id"] == bay and a["entry_time"] < hi
               and a["exit_time"] > lo}
        return rem or {seed}
    lo, hi = sa["entry_time"], sa["exit_time"]
    sx, sy = sa["x"], sa["y"]
    cand = []
    for bi, a in cur.items():
        if bi == seed or a["bay_id"] != bay:
            continue
        if a["entry_time"] < hi and a["exit_time"] > lo:
            cand.append(((a["x"] - sx) ** 2 + (a["y"] - sy) ** 2, bi))
    cand.sort()
    size = min(cap, max(3, int(rng.gauss(avg_size, 3))))
    rem = {seed} | {bi for _, bi in cand[:size - 1]}
    if cand and len(rem) > 2 and rng.random() < p_split:
        rem.discard(cand[0][1])  # split-string: leave a core in place
    return rem


def lahc_explore(prob_info, assign0, deadline, seed=1234, L=300,
                 p_bayblink=0.05, log_every=200, avg_size=6,
                 slot_time_cap=18, slot_pos_cap=14, ils_burst=0.0):
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = m._bay_u(bays)
    n_bays = len(bays)
    n = len(assign0)
    forced = m._is_forced(prob_info, bays)
    raster = m._Raster(prob_info, bays)
    rng = random.Random(seed)

    cur = {k: dict(v) for k, v in assign0.items()}
    cur_obj = m._objective(cur, blocks_data, bays, bay_u, w1, w2, w3)[0]
    best = {k: dict(v) for k, v in cur.items()}
    best_obj = cur_obj
    hist = [cur_obj] * L
    it = accepts = idle = 0
    esc = 0  # reactive ruin escalation level
    deltas = []  # candidate-quality diagnostic: new_obj - cur_obj

    while time.time() < deadline:
        it += 1
        strip_p = (0.15, 0.35, 0.7)[min(esc, 2)]
        avg = (avg_size, avg_size + 4, avg_size + 8)[min(esc, 2)]
        removed = sisr_destroy(cur, blocks_data, w1, w3, rng,
                               avg_size=avg, cap=avg + 4, p_strip=strip_p,
                               strip_scale=1 + esc)
        work = {bi: dict(a) for bi, a in cur.items() if bi not in removed}
        sched, bay_loads = m._rebuild_sched(work, blocks_data, n_bays)
        rem_order = m._repair_order(removed, blocks_data, rng.randint(0, 3),
                                    rng)
        broken = False
        for bi in rem_order:
            if time.time() > deadline:
                broken = True
                break
            blk = blocks_data[bi]
            bo = None
            if n_bays >= 2 and rng.random() < p_bayblink:
                bo = list(range(n_bays))
                rng.shuffle(bo)  # blink: perturbed bay order
            place = m._place_block(bi, blk, bays, sched, bay_loads, bay_u,
                                   w1, w2, w3, forced=forced,
                                   slot_time_cap=slot_time_cap,
                                   slot_pos_cap=slot_pos_cap,
                                   bay_order=bo, raster=raster)
            if place is None:
                place = m._force_place(bi, blk, bays, sched)
            m._add(sched, bay_loads, work, bi, blk, place)
        if broken or len(work) != n:
            continue
        if ils_burst > 0:
            # ILS: the ruin+rebuild is the PERTURBATION; run a short bounded
            # descent (the strongest existing local search) before evaluating,
            # so candidates are local optima, not raw greedy rebuilds.
            try:
                work, _ = m._improve(prob_info, work, bays, bay_u, w1, w2, w3,
                                     min(deadline, time.time() + ils_burst),
                                     forced, seed=rng.randint(0, 10 ** 6),
                                     raster=raster, repack_every=3)
            except Exception:
                pass
        new_obj = m._objective(work, blocks_data, bays, bay_u, w1, w2, w3)[0]
        deltas.append(new_obj - cur_obj)
        v = hist[it % L]
        if new_obj <= v or new_obj <= cur_obj:
            cur, cur_obj = work, new_obj
            accepts += 1
        hist[it % L] = cur_obj
        if cur_obj < best_obj - 1e-9:
            best = {k: dict(x) for k, x in cur.items()}
            best_obj = cur_obj
            idle = 0
            esc = 0
        else:
            idle += 1
            # reactive escalation: idle streak ~2% of elapsed iterations
            if idle > max(200, int(0.02 * it) + 200) * (esc + 1):
                esc = min(esc + 1, 2)
        if log_every and it % log_every == 0:
            ds = sorted(deltas[-log_every:])
            print(f"  it={it} acc={accepts/it:.2f} cur={cur_obj:,.0f} "
                  f"best={best_obj:,.0f} idle={idle} esc={esc} "
                  f"delta[min/p10/p50]={ds[0]:,.0f}/"
                  f"{ds[len(ds)//10]:,.0f}/{ds[len(ds)//2]:,.0f}", flush=True)
    return best, best_obj, {"iters": it, "accepts": accepts,
                            "deltas": sorted(deltas)[:20]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prob", type=int, required=True)
    ap.add_argument("--build", type=float, default=120.0)
    ap.add_argument("--explore", type=float, default=300.0)
    ap.add_argument("--baseline", type=float, default=0.0,
                    help="run plain v18 for this many seconds instead")
    ap.add_argument("--L", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--avg", type=int, default=6, help="mean ruin size")
    ap.add_argument("--stc", type=int, default=18, help="slot_time_cap")
    ap.add_argument("--spc", type=int, default=14, help="slot_pos_cap")
    ap.add_argument("--fresh", action="store_true",
                    help="start from a raw EDD construction, not v18")
    ap.add_argument("--ils", type=float, default=0.0,
                    help="seconds of bounded _improve descent per iteration")
    args = ap.parse_args()

    prob = json.load(open(os.path.join(TRAIN, f"prob_{args.prob}.json")))

    if args.baseline > 0:
        t0 = time.time()
        sol = m.algorithm(prob, args.baseline)
        res = check_feasibility(prob, sol)
        print(f"BASELINE prob_{args.prob} @{args.baseline:.0f}s: "
              f"feasible={res.get('feasible')} obj={res.get('objective'):,.0f} "
              f"({time.time()-t0:.0f}s)", flush=True)
        return

    if args.fresh:
        # trajectory start: one raw EDD construction (no polish) — LAHC then
        # owns the whole descent, so uphill tolerance is active from step 1.
        bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
        w = prob.get("weights", {})
        bay_u = m._bay_u(bays)
        order = m._edd_order(prob["blocks"])
        assign0 = m._construct(prob, order, bays, bay_u,
                               w.get("w1", 1.0), w.get("w2", 1.0),
                               w.get("w3", 1.0), time.time(),
                               time.time() + args.build,
                               forced=m._is_forced(prob, bays))
        sol = {"operations": m._build_operations(assign0)}
        res = check_feasibility(prob, sol)
        print(f"fresh EDD construction: feasible={res.get('feasible')} "
              f"obj={res.get('objective'):,.0f}", flush=True)
    else:
        print(f"building incumbent: v18 @{args.build:.0f}s ...", flush=True)
        sol = m.algorithm(prob, args.build)
        res = check_feasibility(prob, sol)
        print(f"incumbent: feasible={res.get('feasible')} "
              f"obj={res.get('objective'):,.0f}", flush=True)
        assign0 = ops_to_assignments(sol)

    deadline = time.time() + args.explore
    print(f"exploring: LAHC L={args.L} seed={args.seed} "
          f"@{args.explore:.0f}s ...", flush=True)
    best, best_obj, st = lahc_explore(prob, assign0, deadline,
                                      seed=args.seed, L=args.L,
                                      avg_size=args.avg,
                                      slot_time_cap=args.stc,
                                      slot_pos_cap=args.spc,
                                      ils_burst=args.ils)
    print(f"explorer done: iters={st['iters']} accepts={st['accepts']} "
          f"internal_best={best_obj:,.0f}", flush=True)
    if st.get("deltas"):
        print("  smallest candidate deltas vs cur: "
              + ", ".join(f"{d:,.0f}" for d in st["deltas"][:8]), flush=True)

    sol2 = {"operations": m._build_operations(best)}
    res2 = check_feasibility(prob, sol2)
    print(f"RESULT prob_{args.prob}: incumbent={res.get('objective'):,.0f} -> "
          f"explorer={res2.get('objective') if res2.get('feasible') else 'INFEASIBLE'}"
          f" (feasible={res2.get('feasible')}, iters={st['iters']})",
          flush=True)


if __name__ == "__main__":
    main()
