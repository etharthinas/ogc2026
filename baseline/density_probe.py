#!/usr/bin/env python3
"""v20: where does the realization gap come from?

For an assignment (v18 incumbent json), compute:
 - merged layer-0 density time-profile (occupied layer0-area / C) at each event
 - queue profile: total layer0-area of released-but-not-yet-entered blocks
 - for each queued block at each event: could its area have fit (sum-wise)?
   -> fragmentation/crane loss = free_area when blocks are queued.

Usage: density_probe.py <prob> [incumbent_json]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def polyarea(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def main():
    k = int(sys.argv[1])
    inc = sys.argv[2] if len(sys.argv) > 2 else f"v18_{k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bd = prob["blocks"]
    n = len(bd)
    C = sum(b["width"] * b["height"] for b in prob["bays"])
    A = {int(x): y for x, y in json.load(open(os.path.join(HERE, inc))).items()}
    a0 = [polyarea(bd[i]["shape"][A[i]["orient_idx"]]["layers"][0])
          for i in range(n)]
    rel = [bd[i]["release_time"] for i in range(n)]

    evs = sorted(set([A[i]["entry_time"] for i in A] +
                     [A[i]["exit_time"] for i in A] + rel))
    print(f"prob_{k} {inc}: C={C}")
    print("  t | dens(layer0) | queued_blocks | queued_area | free_area")
    tot_freearea_while_queued = 0.0
    peak = 0.0
    for t in evs:
        occ = sum(a0[i] for i in A
                  if A[i]["entry_time"] <= t < A[i]["exit_time"])
        d = occ / C
        peak = max(peak, d)
        qids = [i for i in range(n)
                if rel[i] <= t and A[i]["entry_time"] > t]
        qa = sum(a0[i] for i in qids)
        free = C - occ
        if qids:
            tot_freearea_while_queued += free
        if qids or d > 0.4:
            print(f"  {t:4d} | {d:5.3f} | {len(qids):3d} | {qa:7.0f} | {free:7.0f}")
    print(f"  peak merged layer0 density = {peak:.3f}")


if __name__ == "__main__":
    main()
