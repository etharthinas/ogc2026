#!/usr/bin/env python3
"""Run LAHC (and a greedy control) from a SAVED warm incumbent, so acceptance
configs can be swept cheaply. Isolates the acceptance-rule variable.

Usage:
  python lahc_run.py <k> <incumbent.json> <secs> <L> <kmin> <kmax> <seed> [greedy]
    kmin/kmax : ruin size as a FRACTION (e.g. 0.03 0.08) -> small/fast, or
                large (0.10 0.30). Interpreted as fraction of n.
    greedy    : if the 8th arg == 'g', also run a same-budget greedy control.
"""
import sys, os, json, time, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
from utils import check_feasibility

W = (1.0, 1.0, 1.0)


def objf(a, bd, bays, bu):
    return M._objective(a, bd, bays, bu, W[0], W[1], W[2])[0]


def select_removed(cur, bd, bays, mode, k, rng):
    n_bays = len(bays); keys = list(cur)
    if mode == 'tardy':
        rem = M._destroy_tardy(cur, bd, max(2, k // 2), rng)
        if rem is None:
            rem = M._destroy_window(cur, bd, rng)
        return set(rem)
    if mode == 'window':
        rem = M._destroy_window(cur, bd, rng)
        extra = rng.sample(keys, min(len(keys), max(0, k - len(rem))))
        return set(rem) | set(extra)
    if mode == 'bayslice':
        bj = rng.randrange(n_bays)
        inb = sorted((bi for bi in keys if cur[bi]["bay_id"] == bj),
                     key=lambda bi: cur[bi]["entry_time"])
        if len(inb) <= k or not inb:
            return set(inb) if inb else set(rng.sample(keys, min(k, len(keys))))
        s = rng.randrange(0, len(inb) - k)
        return set(inb[s:s + k])
    if mode == 'worst':
        scored = []
        for bi in keys:
            a = cur[bi]; blk = bd[bi]
            tard = max(0, a["exit_time"] - blk["due_date"])
            prefs = blk["bay_preferences"]
            scored.append((W[0] * tard + W[2] * (max(prefs) - prefs[a["bay_id"]]), bi))
        scored.sort(key=lambda z: -z[0])
        top = [bi for _, bi in scored[:max(k * 2, k)]]
        return set(rng.sample(top, min(k, len(top))))
    return set(rng.sample(keys, min(k, len(keys))))


TCAP = int(os.environ.get("OGC_TCAP", "40"))
PCAP = int(os.environ.get("OGC_PCAP", "30"))


def recreate(cur, removed, bd, bays, bu, forced, raster, rng, om, deadline):
    n_bays = len(bays)
    work = {bi: dict(a) for bi, a in cur.items() if bi not in removed}
    sched, loads = M._rebuild_sched(work, bd, n_bays)
    for bi in M._repair_order(removed, bd, om, rng):
        if time.time() > deadline:
            return None
        blk = bd[bi]
        place = M._place_block(bi, blk, bays, sched, loads, bu, W[0], W[1], W[2],
                               forced=forced, slot_time_cap=TCAP, slot_pos_cap=PCAP,
                               raster=raster)
        if place is None:
            place = M._force_place(bi, blk, bays, sched)
        M._add(sched, loads, work, bi, blk, place)
    return work if len(work) == len(cur) else None


def main():
    global W
    k = int(sys.argv[1]); inc = sys.argv[2]; secs = float(sys.argv[3])
    L = int(sys.argv[4]); kmin = float(sys.argv[5]); kmax = float(sys.argv[6])
    seed = int(sys.argv[7]) if len(sys.argv) > 7 else 31
    do_greedy = len(sys.argv) > 8 and sys.argv[8] == 'g'
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    M._reset_caches()
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bd = prob["blocks"]; w = prob.get("weights", {})
    W = (w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0))
    bu = M._bay_u(bays); forced = M._is_forced(prob, bays)
    raster = M._Raster(prob, bays) if M._HAVE_NUMPY else None
    start = {int(bi): v for bi, v in json.load(open(os.path.join(HERE, inc))).items()}
    n = len(start)
    start_obj = objf(start, bd, bays, bu)
    print(f"prob_{k}: n={n} bays={len(bays)} forced={forced} start={start_obj:,.0f}"
          f"  L={L} ruin=[{kmin},{kmax}] seed={seed}", flush=True)

    if do_greedy:
        tg = time.time()
        ga, go = M._improve(prob, start, bays, bu, W[0], W[1], W[2], tg + secs,
                            forced, seed=7777, raster=raster, repack_every=3,
                            xbay=forced, deep=False)
        print(f"GREEDY = {go:>14,.0f}  ({time.time()-tg:.1f}s) "
              f"d_start={go-start_obj:+,.0f}", flush=True)

    rng = random.Random(seed)
    cur = {kk: dict(v) for kk, v in start.items()}
    cur_obj = start_obj
    best = {kk: dict(v) for kk, v in start.items()}; best_obj = start_obj
    # hist_init: 'start' (classic LAHC) or 'inf' (seed exploration by accepting
    # the initial worsening moves, escaping the cold-start-from-optimum trap).
    hist_init = os.environ.get("OGC_HISTINIT", "start")
    seed_val = float("inf") if hist_init == "inf" else cur_obj
    hist = [seed_val] * L
    modes = ['tardy', 'window', 'worst', 'bayslice']
    t0 = time.time(); dl = t0 + secs; it = 0; acc = 0
    while time.time() < dl:
        mode = modes[it % len(modes)]
        frac = rng.uniform(kmin, kmax)
        kk = max(2, int(frac * n))
        removed = select_removed(cur, bd, bays, mode, kk, rng)
        if not removed:
            it += 1; continue
        cand = recreate(cur, removed, bd, bays, bu, forced, raster, rng,
                        it % 4, dl)
        it += 1
        if cand is None:
            continue
        co = objf(cand, bd, bays, bu)
        v = it % L
        if co <= hist[v] + 1e-9 or co <= cur_obj + 1e-9:
            cur, cur_obj = cand, co; acc += 1
        if cur_obj < hist[v]:
            hist[v] = cur_obj
        if co < best_obj - 1e-9:
            best_obj = co; best = {k2: dict(v2) for k2, v2 in cand.items()}
    el = time.time() - t0
    sol = {"operations": M._build_operations(best)}
    res = check_feasibility(prob, sol)
    print(f"LAHC   = {best_obj:>14,.0f}  ({el:.1f}s) it={it} acc={acc} "
          f"thr={it/max(el,1e-9):.1f}/s d_start={best_obj-start_obj:+,.0f} "
          f"feasible={res.get('feasible')}", flush=True)


if __name__ == "__main__":
    main()
