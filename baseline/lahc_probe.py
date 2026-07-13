#!/usr/bin/env python3
"""Standalone LAHC ruin-and-recreate probe (heuristic_19 Improvement 5).

Isolates the ONE untried mechanism family (non-greedy acceptance) from the
portfolio wiring. Question answered: can Late-Acceptance Hill Climbing over
ruin-and-recreate moves beat the greedy-improver basin on the stuck instances
(prob_31 banked 11,268,243; prob_39 12,361,461)?

Usage:
  python lahc_probe.py <k> <warm_s> <lahc_s> [L] [ruin_lo] [ruin_hi] [seed]
Compares three numbers:
  START  : construct+improve for warm_s (the greedy basin)
  GREEDY : same start then improve for another lahc_s (greedy control)
  LAHC   : same start then LAHC ruin-recreate for lahc_s
All best-seen values are verified with the official check_feasibility.
"""
import sys, os, json, time, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
from utils import check_feasibility


def obj_of(assign, blocks_data, bays, bay_u, w1, w2, w3):
    return M._objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]


def select_removed(cur, blocks_data, bays, mode, k, rng):
    """Return a set of block ids to ruin (size ~k)."""
    n_bays = len(bays)
    keys = list(cur)
    if mode == 'random':
        return set(rng.sample(keys, min(k, len(keys))))
    if mode == 'bayslice':
        # a random bay, contiguous entry-time slice covering ~k blocks
        bj = rng.randrange(n_bays)
        in_bay = sorted((bi for bi in keys if cur[bi]["bay_id"] == bj),
                        key=lambda bi: cur[bi]["entry_time"])
        if not in_bay:
            return set(rng.sample(keys, min(k, len(keys))))
        if len(in_bay) <= k:
            return set(in_bay)
        s = rng.randrange(0, len(in_bay) - k)
        return set(in_bay[s:s + k])
    if mode == 'window':
        # time-window around the tardiest cluster, ACROSS all bays
        tardy = [(bi, cur[bi]["exit_time"] - blocks_data[bi]["due_date"])
                 for bi in keys
                 if cur[bi]["exit_time"] > blocks_data[bi]["due_date"]]
        if tardy:
            tardy.sort(key=lambda z: -z[1])
            seed = tardy[0][0]
        else:
            seed = rng.choice(keys)
        center = cur[seed]["entry_time"]
        procs = [blocks_data[bi]["processing_time"] for bi in keys]
        half = max(1, int(sorted(procs)[len(procs) // 2]) * 3)
        lo, hi = center - half, center + half
        rem = set(bi for bi in keys
                  if cur[bi]["entry_time"] < hi and cur[bi]["exit_time"] > lo)
        # cap/pad to ~k
        if len(rem) > k:
            rem = set(rng.sample(list(rem), k))
        return rem or {seed}
    # 'worst': worst-contribution blocks by w1*tardiness + w3*pref penalty
    W = M._Wtmp
    scored = []
    for bi in keys:
        a = cur[bi]
        blk = blocks_data[bi]
        tard = max(0, a["exit_time"] - blk["due_date"])
        prefs = blk["bay_preferences"]
        pen = max(prefs) - prefs[a["bay_id"]]
        scored.append((W[0] * tard + W[2] * pen, bi))
    scored.sort(key=lambda z: -z[0])
    top = [bi for _, bi in scored[:max(k * 2, k)]]
    return set(rng.sample(top, min(k, len(top))))


def recreate(cur, removed, blocks_data, bays, bay_u, w1, w2, w3, forced,
             raster, rng, order_mode, deadline):
    work = {bi: dict(a) for bi, a in cur.items() if bi not in removed}
    n_bays = len(bays)
    sched, bay_loads = M._rebuild_sched(work, blocks_data, n_bays)
    rem_order = M._repair_order(removed, blocks_data, order_mode, rng)
    for bi in rem_order:
        if time.time() > deadline:
            return None
        blk = blocks_data[bi]
        place = M._place_block(bi, blk, bays, sched, bay_loads, bay_u,
                               w1, w2, w3, forced=forced,
                               slot_time_cap=40, slot_pos_cap=30, raster=raster)
        if place is None:
            place = M._force_place(bi, blk, bays, sched)
        M._add(sched, bay_loads, work, bi, blk, place)
    if len(work) != len(cur):
        return None
    return work


def build_start(prob_info, bays, bay_u, w1, w2, w3, forced, raster, warm_s):
    blocks_data = prob_info["blocks"]
    t0 = time.time()
    dl = t0 + warm_s
    # a few construction orders, keep best, then improve
    orders = [M._area_order(blocks_data), M._edd_order(blocks_data),
              M._congestion_order(blocks_data)]
    best_a, best_o = None, float("inf")
    for order in orders:
        a = M._construct(prob_info, order, bays, bay_u, w1, w2, w3,
                         t0, min(dl, t0 + warm_s * 0.35), forced=forced)
        o = obj_of(a, blocks_data, bays, bay_u, w1, w2, w3)
        if o < best_o:
            best_a, best_o = a, o
    # improve on the best construction for the rest of warm budget
    a, o = M._improve(prob_info, best_a, bays, bay_u, w1, w2, w3, dl, forced,
                      seed=2222, raster=raster, repack_every=3, xbay=forced,
                      deep=False)
    return a, o


def run_lahc(start, start_obj, prob_info, bays, bay_u, w1, w2, w3, forced,
             raster, deadline, L, ruin_lo, ruin_hi, seed):
    blocks_data = prob_info["blocks"]
    n = len(start)
    rng = random.Random(seed)
    cur = {k: dict(v) for k, v in start.items()}
    cur_obj = start_obj
    best = {k: dict(v) for k, v in start.items()}
    best_obj = start_obj
    hist = [cur_obj] * L
    modes = ['window', 'worst', 'bayslice', 'random']
    it = 0
    accepts = 0
    while time.time() < deadline:
        mode = modes[it % len(modes)]
        frac = rng.uniform(ruin_lo, ruin_hi)
        k = max(2, int(frac * n))
        removed = select_removed(cur, blocks_data, bays, mode, k, rng)
        if not removed:
            it += 1
            continue
        cand = recreate(cur, removed, blocks_data, bays, bay_u, w1, w2, w3,
                        forced, raster, rng, it % 4, deadline)
        it += 1
        if cand is None:
            continue
        cand_obj = obj_of(cand, blocks_data, bays, bay_u, w1, w2, w3)
        v = it % L
        if cand_obj <= hist[v] + 1e-9 or cand_obj <= cur_obj + 1e-9:
            cur, cur_obj = cand, cand_obj
            accepts += 1
        if cur_obj < hist[v]:
            hist[v] = cur_obj
        if cand_obj < best_obj - 1e-9:
            best_obj = cand_obj
            best = {k2: dict(v2) for k2, v2 in cand.items()}
    return best, best_obj, it, accepts


def main():
    k = int(sys.argv[1])
    warm_s = float(sys.argv[2])
    lahc_s = float(sys.argv[3])
    L = int(sys.argv[4]) if len(sys.argv) > 4 else 50
    ruin_lo = float(sys.argv[5]) if len(sys.argv) > 5 else 0.10
    ruin_hi = float(sys.argv[6]) if len(sys.argv) > 6 else 0.30
    seed = int(sys.argv[7]) if len(sys.argv) > 7 else 31
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    M._reset_caches()
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    blocks_data = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    M._Wtmp = (w1, w2, w3)
    bay_u = M._bay_u(bays)
    forced = M._is_forced(prob, bays)
    raster = M._Raster(prob, bays) if M._HAVE_NUMPY else None

    print(f"prob_{k}: n={len(blocks_data)} bays={len(bays)} forced={forced} "
          f"w1={w1} w2={w2} w3={w3}  L={L} ruin=[{ruin_lo},{ruin_hi}] seed={seed}",
          flush=True)

    # 1) START (greedy basin)
    t0 = time.time()
    start, start_obj = build_start(prob, bays, bay_u, w1, w2, w3, forced,
                                   raster, warm_s)
    print(f"START  = {start_obj:>14,.0f}   ({time.time()-t0:5.1f}s warm)", flush=True)

    # 2) GREEDY control: continue improving the same start for lahc_s
    tg = time.time()
    g_a, g_o = M._improve(prob, start, bays, bay_u, w1, w2, w3, tg + lahc_s,
                          forced, seed=7777, raster=raster, repack_every=3,
                          xbay=forced, deep=False)
    print(f"GREEDY = {g_o:>14,.0f}   ({time.time()-tg:5.1f}s)  "
          f"delta_vs_start={g_o-start_obj:+,.0f}", flush=True)

    # 3) LAHC ruin-recreate from the same start
    tl = time.time()
    best, best_obj, it, acc = run_lahc(start, start_obj, prob, bays, bay_u,
                                       w1, w2, w3, forced, raster,
                                       tl + lahc_s, L, ruin_lo, ruin_hi, seed)
    el = time.time() - tl
    print(f"LAHC   = {best_obj:>14,.0f}   ({el:5.1f}s)  iters={it} "
          f"accepts={acc} thr={it/max(el,1e-9):.1f}/s  "
          f"delta_vs_start={best_obj-start_obj:+,.0f} "
          f"delta_vs_greedy={best_obj-g_o:+,.0f}", flush=True)

    # verify LAHC best officially
    sol = {"operations": M._build_operations(best)}
    res = check_feasibility(prob, sol)
    print(f"LAHC best feasible={res.get('feasible')} obj={res.get('objective')}",
          flush=True)


if __name__ == "__main__":
    main()
