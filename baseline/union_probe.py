#!/usr/bin/env python3
"""v20: entry-effective (union-projection) density profile of an incumbent.

For each bay, replay the incumbent chronologically in the v18 raster and
report at each event: any-layer union density (fraction of cells blocked for
an entering block's layer-0) vs layer-0-only density. The difference is
'overhang poisoning' -- floor area unusable for admissions because upper
layers of present blocks hang over it.

Usage: union_probe.py <prob> [step]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import myalgorithm_18 as M
import numpy as np


def main():
    k = int(sys.argv[1])
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bd = prob["blocks"]
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    A = {int(x): y for x, y in
         json.load(open(os.path.join(HERE, f"v18_{k}.json"))).items()}
    n = len(bd)
    raster = M._Raster(prob, bays)
    C = [b.width * b.height for b in bays]
    evs = []
    for i in A:
        a = A[i]
        evs.append((a["entry_time"], 1, i))
        evs.append((a["exit_time"], 0, i))
    evs.sort(key=lambda e: (e[0], e[1]))   # exits first at same tick
    rel = [bd[i]["release_time"] for i in range(n)]
    print(f"prob_{k}: bays C={C}")
    print("  t | per-bay union dens | per-bay L0 dens | queued")
    cur = set()
    lastt = None
    out = []
    for (t, typ, i) in evs:
        a = A[i]
        if typ == 0:
            raster.remove(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            cur.discard(i)
        else:
            raster.add(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            cur.add(i)
        out.append(t)
        qn = sum(1 for j in range(n) if rel[j] <= t and A[j]["entry_time"] > t)
        ud, l0 = [], []
        for bj in range(len(bays)):
            occ = raster.occ[bj]
            if occ:
                grids = list(occ.values())
                u = np.zeros_like(grids[0], dtype=bool)
                for g in grids:
                    u |= (g > 0)
                ud.append(round(float(u.sum()) / C[bj], 3))
                g0 = occ.get(0)
                l0.append(round(float((g0 > 0).sum()) / C[bj], 3)
                          if g0 is not None else 0.0)
            else:
                ud.append(0.0); l0.append(0.0)
        if t != lastt and qn > 0:
            print(f"  {t:4d} | {ud} | {l0} | q={qn}")
        lastt = t


if __name__ == "__main__":
    main()
