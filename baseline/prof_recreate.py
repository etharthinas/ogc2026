#!/usr/bin/env python3
"""Profile the ruin-recreate hot path on a saved incumbent."""
import sys, os, json, time, random, cProfile, pstats, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M

k = int(sys.argv[1]); inc = sys.argv[2]; iters = int(sys.argv[3]) if len(sys.argv) > 3 else 20
prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
M._reset_caches()
bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
bd = prob["blocks"]; w = prob.get("weights", {})
w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
bu = M._bay_u(bays); forced = M._is_forced(prob, bays)
raster = M._Raster(prob, bays)
start = {int(bi): v for bi, v in json.load(open(os.path.join(HERE, inc))).items()}
n = len(start); rng = random.Random(1)


def one():
    removed = set(rng.sample(list(start), 10))
    work = {bi: dict(a) for bi, a in start.items() if bi not in removed}
    sched, loads = M._rebuild_sched(work, bd, len(bays))
    for bi in M._repair_order(removed, bd, 0, rng):
        blk = bd[bi]
        place = M._place_block(bi, blk, bays, sched, loads, bu, w1, w2, w3,
                               forced=forced, slot_time_cap=40, slot_pos_cap=30,
                               raster=raster)
        if place is None:
            place = M._force_place(bi, blk, bays, sched)
        M._add(sched, loads, work, bi, blk, place)
    M._objective(work, bd, bays, bu, w1, w2, w3)


t0 = time.time()
pr = cProfile.Profile(); pr.enable()
for _ in range(iters):
    one()
pr.disable()
el = time.time() - t0
print(f"{iters} recreates in {el:.2f}s = {iters/el:.2f}/s ({1000*el/iters:.0f} ms/iter)")
s = io.StringIO(); ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(18)
print(s.getvalue())
