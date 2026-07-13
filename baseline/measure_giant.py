#!/usr/bin/env python3
"""Tier-T (Improvement 1/8) decisive measurement on a v18 incumbent:
does the giant's tardiness come from SPACE saturation (bays already ~full ->
near-optimal, no packing lever) or from admission/order slack (bays have room
-> untapped mass a better constructor could reach)?

Reports per bay: peak realized density, density during the congestion peak;
overall: total admission delay (sum entry-release), total tardiness, and the
release-burst profile.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M


def main():
    k = int(sys.argv[1]); inc = sys.argv[2]
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bd = prob["blocks"]
    w = prob.get("weights", {})
    w1 = w.get("w1", 1.0)
    A = {bi: v for bi, v in
         ((int(x), y) for x, y in json.load(open(os.path.join(HERE, inc))).items())}
    n = len(A)
    bay_area = [b.width * b.height for b in bays]
    n_bays = len(bays)

    # per-block placed-orientation footprint area
    def farea(bi):
        return M._orient_area(bd[bi], A[bi]["orient_idx"])

    # ---- density over time, per bay ----
    peak_dens = [0.0] * n_bays
    # weighted (by duration) mean density during the busy span
    all_times = sorted(set([A[bi]["entry_time"] for bi in A] +
                           [A[bi]["exit_time"] for bi in A]))
    # sample at each entry event (state changes there)
    for bj in range(n_bays):
        ids = [bi for bi in A if A[bi]["bay_id"] == bj]
        evs = sorted(set([A[bi]["entry_time"] for bi in ids] +
                         [A[bi]["exit_time"] for bi in ids]))
        for t in evs:
            occ = sum(farea(bi) for bi in ids
                      if A[bi]["entry_time"] <= t < A[bi]["exit_time"])
            d = occ / bay_area[bj]
            if d > peak_dens[bj]:
                peak_dens[bj] = d

    # ---- admission delay & tardiness ----
    adm_delay = sum(A[bi]["entry_time"] - bd[bi]["release_time"] for bi in A)
    tard = sum(max(0, A[bi]["exit_time"] - bd[bi]["due_date"]) for bi in A)
    n_tardy = sum(1 for bi in A if A[bi]["exit_time"] > bd[bi]["due_date"])
    # blocks whose entry > release (queued at all)
    n_queued = sum(1 for bi in A if A[bi]["entry_time"] > bd[bi]["release_time"])

    # ---- release burst profile ----
    rels = sorted(bd[bi]["release_time"] for bi in range(n))
    span = rels[-1] - rels[0] if rels[-1] > rels[0] else 1
    # how concentrated: fraction released in first 20% of release span
    burst_cut = rels[0] + 0.2 * span
    frac_early = sum(1 for r in rels if r <= burst_cut) / n

    # ---- global peak: max total occupied fraction across all bays at once ----
    print(f"prob_{k}: n={n} bays={n_bays} w1={w1}", flush=True)
    print(f"  bay_area = {bay_area}", flush=True)
    print(f"  peak realized density per bay = "
          f"{[round(d,3) for d in peak_dens]}", flush=True)
    print(f"  total tardiness (units) = {tard:,}  (w1*tard = {w1*tard:,.0f})  "
          f"n_tardy={n_tardy}/{n}", flush=True)
    print(f"  total admission delay (sum entry-release) = {adm_delay:,}  "
          f"n_queued={n_queued}/{n}", flush=True)
    print(f"  release span = {span}, frac released in first 20% = "
          f"{frac_early:.2f}", flush=True)
    # verdict hint
    md = max(peak_dens)
    print(f"  -> max peak density = {md:.3f} "
          f"({'SATURATED (little packing room)' if md > 0.90 else 'SLACK (packing room exists)'})",
          flush=True)


if __name__ == "__main__":
    main()
