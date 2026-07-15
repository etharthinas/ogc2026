#!/usr/bin/env python3
"""v25 giant-burst diagnostic: is the residual tardiness a PACKING problem
(bays half-empty during the release burst while blocks queue -> admission fails
to find placements) or a SEQUENCING problem (bays genuinely saturated; loss is
which blocks wait)?

Reuses the myalgorithm (v25) raster machinery: per-layer collision-true density
(NOT footprint sums), conservative scan() anchors + near-miss scan_near()
anchors exact-gated by _can_place. Emits JSON to <out> for the ledger.

Usage: diag_v25.py <k> <incumbent_json> <out_json>
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import myalgorithm as M
from myalgorithm import _Raster, _can_place, _unique_orients, _orient_fits
from utils import Bay, Block

INF = float("inf")


def main():
    k = int(sys.argv[1]); inc = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else f"diag_{k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bd = prob["blocks"]; n = len(bd)
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    nb = len(bays)
    area = [float(b.width * b.height) for b in bays]
    w1 = prob.get("weights", {}).get("w1", 1.0)
    A = {int(x): y for x, y in json.load(open(os.path.join(HERE, inc))).items()}

    rel = [bd[i]["release_time"] for i in range(n)]
    due = [bd[i]["due_date"] for i in range(n)]
    proc = [bd[i]["processing_time"] for i in range(n)]
    entry = {i: A[i]["entry_time"] for i in A}
    exit_ = {i: A[i]["exit_time"] for i in A}
    horizon = max(exit_.values())

    # per-bay realized schedule of Block objects (obstacles for _can_place)
    sched = [[] for _ in bays]
    for i in A:
        a = A[i]
        blk = Block(block_id=i, block_data=bd[i], x=a["x"], y=a["y"],
                    orient_idx=a["orient_idx"])
        sched[a["bay_id"]].append((blk, a["entry_time"], a["exit_time"]))

    raster = _Raster(prob, bays)
    # monotone event replay so raster.occ = residents(entry<=t<exit) at grid t
    events = []
    for i in A:
        events.append((A[i]["entry_time"], 1, i))
        events.append((A[i]["exit_time"], 0, i))
    events.sort(key=lambda e: e[0])
    ptr = 0

    # unique orients that fit each bay (cache)
    fit_orients = {}
    for i in range(n):
        uo = _unique_orients(bd[i])
        fit_orients[i] = {bj: [oi for oi in uo if _orient_fits(bd[i], oi, bays[bj])]
                          for bj in range(nb)}

    # ---- (a) timeline grid ----
    grid = sorted(set(int(round(t)) for t in np.linspace(0, horizon, 200)))
    timeline = []
    # ---- (b) accumulators ----
    b_total = 0          # queue-block-moments (queue>0 samples x queued blocks)
    b_feasible = 0       # strict: slack on top of full realized schedule
    b_saturated = 0      # strict: NO placement existed
    b_lenient = 0        # lenient: instantaneous room vs residents-at-t only
    per_bay_burst_dens0 = [[] for _ in bays]   # layer0 dens during burst
    per_bay_burst_dens1 = [[] for _ in bays]   # layer1+ dens during burst
    burst_samples = 0

    def bay_dens(bj):
        occ = raster.occ[bj]
        g0 = occ.get(0)
        d0 = float((g0 > 0).sum()) / area[bj] if g0 is not None else 0.0
        H, W = raster.H[bj], raster.W[bj]
        up = np.zeros((H, W), dtype=bool)
        for l, g in occ.items():
            if l >= 1:
                up |= (g > 0)
        d1 = float(up.sum()) / area[bj]
        return d0, d1

    def feasible_anywhere(i, t):
        """Did queued block i have ANY exact-feasible placement at time t in ANY
        bay? Two obstacle sets, both from conservative scan()+near-miss anchors
        exact-gated by _can_place:
          strict  = full realized overlap set (future entrants immovable) ->
                    faithful 'was there slack on top of everything realized';
          lenient = only blocks RESIDENT at t (ignore imminent future entrants)
                    -> instantaneous geometric room (fragmentation/crane only).
        Returns (strict_ok, lenient_ok). strict_ok implies lenient_ok."""
        et = t; xt = t + proc[i]
        strict_ok = False; lenient_ok = False
        for bj in range(nb):
            ojs = fit_orients[i][bj]
            if not ojs:
                continue
            sc_full = [tr for tr in sched[bj] if tr[0].block_id != i]
            sc_res = [tr for tr in sc_full if tr[1] <= t < tr[2]]
            for oi in ojs:
                feas, cx0, cy0 = raster.scan(bj, i, oi)
                anchors = []
                if feas is not None and feas.any():
                    anchors.extend((int(r), int(c))
                                   for r, c in np.argwhere(feas)[:400])
                near = raster.scan_near(bj, i, oi)
                if near is not None and near.any():
                    anchors.extend((int(r), int(c))
                                   for r, c in np.argwhere(near)[:400])
                for (r, c) in anchors:
                    x = c - cx0; y = r - cy0
                    nbk = M._mkblock(i, bd[i], x, y, oi)
                    if not _can_place(bays[bj], sc_res, nbk, et, xt):
                        continue           # fails lenient -> fails strict too
                    lenient_ok = True
                    if _can_place(bays[bj], sc_full, nbk, et, xt):
                        return True, True
                if lenient_ok and strict_ok:
                    return True, True
        return strict_ok, lenient_ok

    for t in grid:
        while ptr < len(events) and events[ptr][0] <= t:
            _te, typ, i = events[ptr]
            a = A[i]
            if typ == 1:
                raster.add(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            else:
                raster.remove(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            ptr += 1
        resident = sum(1 for i in A if entry[i] <= t < exit_[i])
        qids = [i for i in range(n) if rel[i] <= t < entry.get(i, INF)]
        qrem = sum(proc[i] for i in qids)
        d0 = []; d1 = []
        for bj in range(nb):
            a0, a1 = bay_dens(bj)
            d0.append(round(a0, 3)); d1.append(round(a1, 3))
        timeline.append({"t": t, "resident": resident, "queue": len(qids),
                         "qrem_proc": qrem,
                         "dens0": d0, "dens1": d1})
        if qids:
            burst_samples += 1
            for bj in range(nb):
                per_bay_burst_dens0[bj].append(d0[bj])
                per_bay_burst_dens1[bj].append(d1[bj])
            for i in qids:
                b_total += 1
                s_ok, l_ok = feasible_anywhere(i, t)
                if s_ok:
                    b_feasible += 1
                else:
                    b_saturated += 1
                if l_ok:
                    b_lenient += 1

    # ---- (c) tardiness attribution ----
    tardy = [i for i in A if exit_[i] > due[i]]
    obj1 = sum(max(0, exit_[i] - due[i]) for i in A)
    # decomposition per tardy block:
    #   tardiness = entry_delay + floor(rel+proc-due) + dwell_excess  (identity)
    sum_entry_delay = 0.0
    sum_floor = 0.0
    sum_dwell_excess = 0.0
    tard_from_queued = 0.0     # obj1 mass from blocks that queued (entry>release)
    tard_from_immediate = 0.0  # obj1 mass from blocks entered at release
    tvals = []
    for i in tardy:
        tard = exit_[i] - due[i]
        tvals.append(tard)
        ed = entry[i] - rel[i]
        fl = max(0, rel[i] + proc[i] - due[i])
        de = exit_[i] - entry[i] - proc[i]
        sum_entry_delay += ed
        sum_floor += fl
        sum_dwell_excess += de
        if entry[i] > rel[i]:
            tard_from_queued += tard
        else:
            tard_from_immediate += tard
    tvals.sort(reverse=True)
    # histogram buckets
    buckets = [(1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 10**9)]
    hist = {f"{lo}-{hi if hi < 10**9 else 'inf'}":
            sum(1 for v in tvals if lo <= v < hi) for lo, hi in buckets}

    # ---- (d) dwell check ----
    dwell_excess = [(i, exit_[i] - entry[i] - proc[i]) for i in A]
    n_dwell = sum(1 for _, de in dwell_excess if de > 0)
    max_dwell = max((de for _, de in dwell_excess), default=0)

    # burst window
    bt = [row["t"] for row in timeline if row["queue"] > 0]
    burst_window = [min(bt), max(bt)] if bt else None
    peak_queue = max((row["queue"] for row in timeline), default=0)

    def stats(lst):
        if not lst:
            return {"min": 0, "max": 0, "mean": 0}
        return {"min": round(min(lst), 3), "max": round(max(lst), 3),
                "mean": round(sum(lst) / len(lst), 3)}

    result = {
        "k": k, "inc": inc, "n": n, "nb": nb, "w1": w1,
        "area": area, "horizon": horizon,
        "obj1_tardiness": obj1, "w1_obj1": w1 * obj1,
        "n_tardy": len(tardy),
        "burst_window": burst_window, "peak_queue": peak_queue,
        "burst_samples": burst_samples,
        "b_total_moments": b_total,
        "b_feasible_existed": b_feasible,
        "b_saturated": b_saturated,
        "b_lenient_room": b_lenient,
        "b_frac_feasible": (b_feasible / b_total) if b_total else None,
        "b_frac_lenient": (b_lenient / b_total) if b_total else None,
        "burst_dens0_per_bay": [stats(per_bay_burst_dens0[bj]) for bj in range(nb)],
        "burst_dens1_per_bay": [stats(per_bay_burst_dens1[bj]) for bj in range(nb)],
        "tard_hist": hist,
        "tard_top10": tvals[:10],
        "sum_entry_delay_tardy": sum_entry_delay,
        "sum_floor_tardy": sum_floor,
        "sum_dwell_excess_tardy": sum_dwell_excess,
        "tard_from_queued": tard_from_queued,
        "tard_from_immediate": tard_from_immediate,
        "dwell_n_over_proc": n_dwell, "dwell_max_excess": max_dwell,
        "timeline": timeline,
    }
    json.dump(result, open(os.path.join(HERE, out), "w"), indent=1)
    print(json.dumps({kk: vv for kk, vv in result.items() if kk != "timeline"},
                     indent=1))
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
