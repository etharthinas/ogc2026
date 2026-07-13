#!/usr/bin/env python3
"""v20 Tier-T: slack-heterogeneity + per-layer capacity analysis of the big rocks.

Questions the 19a density measurement did NOT answer:
1. Is due-date slack heterogeneous? (If yes, WHICH blocks absorb queue delay is
   a live lever even under saturation.)
2. What is the realized per-LAYER density (the true capacity constraint)?
   19a used footprint area, which double-counts stacked blocks (>1.0 readings).
3. Given the incumbent's realized delay mass, what is the minimal tardiness if
   the same delays were redistributed optimally across blocks? (redistribution
   bound: not a valid LB on the problem, but an upper bound on what pure
   re-ordering could ever recover — and a refutation test for "structural").
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def polyarea(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def layer_areas(block, oi):
    return [polyarea(l) for l in block["shape"][oi]["layers"]]


def quant(xs, q):
    xs = sorted(xs)
    i = min(len(xs) - 1, int(q * len(xs)))
    return xs[i]


def main(ks):
    for k in ks:
        prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
        bd = prob["blocks"]
        n = len(bd)
        w1 = prob["weights"]["w1"]
        bay_area = [b["width"] * b["height"] for b in prob["bays"]]
        C = sum(bay_area)

        # orientation-invariance of areas?
        b0 = bd[0]
        a_by_o = [tuple(round(a, 3) for a in layer_areas(b0, oi))
                  for oi in range(len(b0["shape"]))]
        inv = len(set(a_by_o)) == 1

        slack = [bd[i]["due_date"] - bd[i]["release_time"] - bd[i]["processing_time"]
                 for i in range(n)]
        rel = [bd[i]["release_time"] for i in range(n)]
        due = [bd[i]["due_date"] for i in range(n)]
        p = [bd[i]["processing_time"] for i in range(n)]
        a0 = [layer_areas(bd[i], 0)[0] for i in range(n)]  # layer-0 area
        amax = [max(layer_areas(bd[i], 0)) for i in range(n)]
        nlay = [len(bd[i]["shape"][0]["layers"]) for i in range(n)]

        print(f"=== prob_{k}: n={n} bays={len(bay_area)} C={C} w1={w1} "
              f"area-orient-invariant={inv}")
        print(f"  releases: [{min(rel)},{max(rel)}]  dues: [{min(due)},{max(due)}]  "
              f"p: med={quant(p,0.5)} max={max(p)}")
        print(f"  slack: min={min(slack)} q25={quant(slack,0.25)} med={quant(slack,0.5)} "
              f"q75={quant(slack,0.75)} q90={quant(slack,0.9)} max={max(slack)}")
        print(f"  layers: dist={ {l: nlay.count(l) for l in sorted(set(nlay))} }")
        print(f"  layer0 area: sum={sum(a0):.0f} demand a0*p={sum(x*y for x,y in zip(a0,p)):.0f} "
              f" C*(maxdue-minrel)={C*(max(due)-min(rel)):.0f}")

        # incumbent
        inc_path = os.path.join(HERE, f"v18_{k}.json")
        if not os.path.exists(inc_path):
            print("  (no incumbent json)")
            continue
        A = {int(x): y for x, y in json.load(open(inc_path)).items()}
        T = [max(0, A[i]["exit_time"] - due[i]) for i in range(n)]
        delay = [A[i]["exit_time"] - (rel[i] + p[i]) for i in range(n)]  # >=0
        dwell = [A[i]["exit_time"] - A[i]["entry_time"] - p[i] for i in range(n)]
        qd = [A[i]["entry_time"] - rel[i] for i in range(n)]
        print(f"  incumbent: tard={sum(T):,} (w1*={w1*sum(T):,}) "
              f"delay_mass={sum(delay):,} queue={sum(qd):,} dwell_over_p={sum(dwell):,}")
        # top tardy blocks: their slack and area
        top = sorted(range(n), key=lambda i: -T[i])[:12]
        print("  top tardy (id, T, slack, a0, p):",
              [(i, T[i], slack[i], round(a0[i]), p[i]) for i in top])

        # redistribution bound: same total delay mass, assigned to maximize
        # slack absorption. Greedy: give delay to blocks with largest slack
        # first (each block can absorb 'slack' units free, unlimited after).
        # Minimal tardiness for total delay D = sum over chosen of (d_i -
        # slack_i)+ ... optimal: fill slack of all blocks first.
        D = sum(delay)
        total_slack = sum(max(0, s) for s in slack)
        min_tard_redist = max(0, D - total_slack)
        print(f"  redistribution floor: delay_mass={D:,} total_slack={total_slack:,} "
              f"-> min tard if freely redistributable = {min_tard_redist:,} "
              f"(w1* = {w1*min_tard_redist:,})")

        # BUT delay mass is not conserved: area-weighted version.
        # area-time conservation: sum a0_i*(time in bay) <= C * busy_span.
        # weighted delay redistribution: delivering delay to small blocks is
        # cheaper in area-time. Compare area-weighted delay:
        awd = sum(a0[i] * delay[i] for i in range(n))
        print(f"  area-weighted delay mass = {awd:,.0f} (a0-weighted)")

        # per-layer realized peak density (TRUE capacity check), per bay
        nb = len(bay_area)
        maxL = max(nlay)
        for bj in range(nb):
            ids = [i for i in A if A[i]["bay_id"] == bj]
            evs = sorted(set([A[i]["entry_time"] for i in ids] +
                             [A[i]["exit_time"] for i in ids]))
            pk = [0.0] * maxL
            for t in evs:
                act = [i for i in ids
                       if A[i]["entry_time"] <= t < A[i]["exit_time"]]
                for L in range(maxL):
                    occ = sum(layer_areas(bd[i], A[i]["orient_idx"])[L]
                              for i in act if nlay[i] > L)
                    d = occ / bay_area[bj]
                    if d > pk[L]:
                        pk[L] = d
            print(f"  bay{bj} per-layer PEAK density: "
                  f"{[round(x,3) for x in pk]}")
        sys.stdout.flush()


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [38, 27, 39, 31])
