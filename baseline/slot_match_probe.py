#!/usr/bin/env python3
"""v20 ceiling probe: identity re-matching over the incumbent's fixed slots.

Keep every (bay, position, orientation-footprint, entry, exit) slot of the v18
incumbent EXACTLY as-is; re-assign which block occupies which slot. A block may
take a slot if (optimistic bbox proxy) each of its layers' bounding boxes fits
within the slot's same-layer bbox for some orientation, entry >= release, and
the slot window covers its processing time. Cost = w1*tardiness + w3*pref.

This is an OPTIMISTIC ceiling (bbox fit does not imply polygon containment).
If the optimal matching barely beats identity, the mechanism is dead; if it
finds millions, build the exact-containment version.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
from ortools.sat.python import cp_model


def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (max(xs) - min(xs), max(ys) - min(ys))


def main():
    for k in [int(x) for x in sys.argv[1:]] or [31, 39, 27, 38]:
        prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
        bd = prob["blocks"]
        n = len(bd)
        w = prob["weights"]; w1, w3 = w["w1"], w["w3"]
        A = {int(x): y for x, y in
             json.load(open(os.path.join(HERE, f"v18_{k}.json"))).items()}

        # slot j: bboxes of placed orientation's layers
        slot_bb = {}
        for j in range(n):
            oj = A[j]["orient_idx"]
            slot_bb[j] = [bbox(l) for l in bd[j]["shape"][oj]["layers"]]

        # block i: per-orientation layer bboxes
        blk_bb = {}
        for i in range(n):
            blk_bb[i] = [[bbox(l) for l in o["layers"]] for o in bd[i]["shape"]]

        EPS = 1e-6
        pairs = []   # (i, j, cost)
        base_cost = 0
        for i in range(n):
            rel_i = bd[i]["release_time"]; p_i = bd[i]["processing_time"]
            due_i = bd[i]["due_date"]; prefs = bd[i]["bay_preferences"]
            for j in range(n):
                ent, ext = A[j]["entry_time"], A[j]["exit_time"]
                if ent < rel_i or ent + p_i > ext:
                    if i == j:
                        raise RuntimeError("identity infeasible?")
                    continue
                sb = slot_bb[j]
                ok = False
                if i == j:
                    ok = True
                else:
                    for ob in blk_bb[i]:
                        if len(ob) <= len(sb) and all(
                                ob[L][0] <= sb[L][0] + EPS and
                                ob[L][1] <= sb[L][1] + EPS
                                for L in range(len(ob))):
                            ok = True
                            break
                if not ok:
                    continue
                tard = max(0, ent + p_i - due_i)
                cost = w1 * tard + w3 * (max(prefs) - prefs[A[j]["bay_id"]])
                pairs.append((i, j, cost))
                if i == j:
                    base_cost += cost

        deg = len(pairs) / n
        m = cp_model.CpModel()
        x = {}
        by_i = {}; by_j = {}
        for (i, j, c) in pairs:
            v = m.NewBoolVar(f"x{i}_{j}")
            x[(i, j)] = v
            by_i.setdefault(i, []).append(v)
            by_j.setdefault(j, []).append(v)
        for i in range(n):
            m.AddExactlyOne(by_i[i])
        for j, vs in by_j.items():
            m.AddAtMostOne(vs)
        m.Minimize(sum(c * x[(i, j)] for (i, j, c) in pairs))
        sol = cp_model.CpSolver()
        sol.parameters.max_time_in_seconds = 60
        sol.parameters.num_search_workers = 8
        st = sol.Solve(m)
        best = sol.ObjectiveValue()
        nmoved = sum(1 for (i, j, c) in pairs
                     if i != j and sol.Value(x[(i, j)]))
        print(f"prob_{k}: avg_compat_deg={deg:.1f} identity_cost={base_cost:,} "
              f"matched_cost={best:,.0f} delta={best-base_cost:+,.0f} "
              f"moved={nmoved}/{n} status={sol.StatusName(st)}", flush=True)


if __name__ == "__main__":
    main()
