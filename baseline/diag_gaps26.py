#!/usr/bin/env python3
"""prob_26 gap-structure diagnostic: WHY does prob_26 show ~0.63% feasible
queue-block-moments while burst layer-0 density is only ~0.50-0.53 (bays ~half
empty)? Hypothesis: the free ~48% is SHREDDED by near-full-height residents into
1D strip gaps narrower than the queued blocks (fragmentation), and/or free cells
are CRANE-POISONED by neighboring overhangs (layer-0 free but entry/exit blocked).

Patterned after diag_v25.py: loads the v25_26.json incumbent, replays resident
sets over ~200 grid samples via the myalgorithm _Raster, and at each burst sample
(queue>0) per bay measures:
  (1) layer-0 gap structure: largest inscribed free rectangle (w,h) + free area +
      horizontal free-run 'sliver' mass (runs narrower than the min queued width);
  (2) queued demands: per-block integer footprint bbox (w,h) + min area;
  (3) MATCH classification per (sample,bay):
        (c) exact-feasible placement existed (lenient residents)   -> ~0 expected
        (a) some queued bbox fits the largest free rect but NO exact-feasible
            placement exists                       -> crane / shape (overhang)
        (b) largest free rect < EVERY queued bbox  -> strip fragmentation
  (4) crane poisoning: for class-(a) bays, enumerate layer-0-collision-free
      anchors (block footprint fully inside the free-0 mask) and classify each
      failing anchor as CRANE-only (entry/exit blocked, no layer-collision) vs
      COLLISION (upper-layer overlap). crane_only / (crane_only+collision).

Single process, no multiprocessing. Emits diag_gaps26.json + a printed summary.

Usage: diag_gaps26.py [incumbent_json=v25_26.json] [out=diag_gaps26.json]
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import myalgorithm as M
from myalgorithm import (_Raster, _can_place, _unique_orients, _orient_fits,
                         _collide, _entry_blocked, _exit_blocked, _overlaps,
                         _min_area, _mkblock)
from utils import Bay, Block

INF = float("inf")
K = 26
N_SAMPLES = 200
ANCHOR_CAP = 140          # max layer-0-free anchors classified per (block,orient)
BLOCKS_PER_BAY = 8        # queued blocks probed per (sample,bay) for crane metric


def largest_free_rect(free):
    """Largest inscribed axis-aligned all-True rectangle in bool (H,W) `free`.
    Returns (area, w, h) via the classic largest-rectangle-in-histogram sweep."""
    H, W = free.shape
    if H == 0 or W == 0:
        return 0, 0, 0
    heights = np.zeros(W, dtype=np.int32)
    best = (0, 0, 0)
    for r in range(H):
        row = free[r]
        heights = np.where(row, heights + 1, 0)
        # largest rectangle in this histogram
        stack = []
        i = 0
        hh = heights
        while i <= W:
            cur = int(hh[i]) if i < W else 0
            if not stack or cur >= int(hh[stack[-1]]):
                stack.append(i); i += 1
            else:
                top = stack.pop()
                h = int(hh[top])
                w = i if not stack else i - stack[-1] - 1
                if h * w > best[0]:
                    best = (h * w, w, h)
    return best


def horiz_sliver_cells(free, min_w):
    """Total free cells lying in maximal horizontal free runs narrower than
    `min_w` (per row). A proxy for width shredded below the queue's needs."""
    if min_w <= 0:
        return 0
    H, W = free.shape
    sliver = 0
    for r in range(H):
        run = 0
        for c in range(W):
            if free[r, c]:
                run += 1
            else:
                if 0 < run < min_w:
                    sliver += run
                run = 0
        if 0 < run < min_w:
            sliver += run
    return sliver


def classify_anchor(bay, sched_res, new_blk, entry, exit_t):
    """Return 'ok' | 'bounds' | 'collision' | 'crane' for placing new_blk over
    the lenient (resident-at-t) obstacle set. Mirrors _can_place's pairwise
    checks but reports WHICH class blocks it (collision = any-layer overlap;
    crane = entry/exit prism blocked with no collision)."""
    if not bay.contains_block(new_blk):
        return 'bounds'
    nbid = new_blk.block_id
    collide = False
    for b, a, e in sched_res:
        if _overlaps(entry, exit_t, a, e) and _collide(bay, new_blk, b):
            collide = True
            break
    crane = False
    for b, a, e in sched_res:
        if (a < entry < e) or (a == entry and b.block_id < nbid):
            if _entry_blocked(bay, b, new_blk):
                crane = True
                break
    if not crane:
        for b, a, e in sched_res:
            if (a < exit_t < e) or (e == exit_t and b.block_id > nbid):
                if _exit_blocked(bay, b, new_blk):
                    crane = True
                    break
    if not crane:
        for b, a, e in sched_res:
            if (entry < a < exit_t) or (entry == a and nbid < b.block_id):
                if _entry_blocked(bay, new_blk, b):
                    crane = True
                    break
            if (entry < e < exit_t) or (exit_t == e and nbid > b.block_id):
                if _exit_blocked(bay, new_blk, b):
                    crane = True
                    break
    if collide:
        return 'collision'
    if crane:
        return 'crane'
    return 'ok'


def main():
    inc = sys.argv[1] if len(sys.argv) > 1 else "v25_26.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "diag_gaps26.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{K}.json")))
    bd = prob["blocks"]; n = len(bd)
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    nb = len(bays)
    area = [float(b.width * b.height) for b in bays]
    A = {int(x): y for x, y in json.load(open(os.path.join(HERE, inc))).items()}

    rel = [bd[i]["release_time"] for i in range(n)]
    due = [bd[i]["due_date"] for i in range(n)]
    proc = [bd[i]["processing_time"] for i in range(n)]
    entry = {i: A[i]["entry_time"] for i in A}
    exit_ = {i: A[i]["exit_time"] for i in A}
    horizon = max(exit_.values())

    # per-bay realized schedule of Block objects (obstacles)
    sched = [[] for _ in bays]
    for i in A:
        a = A[i]
        blk = Block(block_id=i, block_data=bd[i], x=a["x"], y=a["y"],
                    orient_idx=a["orient_idx"])
        sched[a["bay_id"]].append((blk, a["entry_time"], a["exit_time"]))

    raster = _Raster(prob, bays)
    events = []
    for i in A:
        events.append((A[i]["entry_time"], 1, i))
        events.append((A[i]["exit_time"], 0, i))
    events.sort(key=lambda e: e[0])
    ptr = 0

    # fitting orients + integer footprint bbox (MW,MH) per (block,bay,orient)
    fit_orients = {}
    bbox_cells = {}          # (i,oi) -> (MW, MH)
    minarea = [int(_min_area(bd[i])) for i in range(n)]
    for i in range(n):
        uo = _unique_orients(bd[i])
        fit_orients[i] = {bj: [oi for oi in uo if _orient_fits(bd[i], oi, bays[bj])]
                          for bj in range(nb)}
        for oi in uo:
            mask, cx0, cy0 = raster.mask(i, oi)
            bbox_cells[(i, oi)] = (int(mask.shape[2]), int(mask.shape[1]))

    grid = sorted(set(int(round(t)) for t in np.linspace(0, horizon, N_SAMPLES)))

    # accumulators -----------------------------------------------------------
    cls_count = {"a": 0, "b": 0, "c": 0}       # per (sample,bay) with queue>0
    bay_sample_total = 0
    lr_w = []; lr_h = []; lr_area = []         # largest-free-rect stats (burst bays)
    q_bw = []; q_bh = []                        # queued bbox stats (fitting, burst)
    free_frac = []                             # layer-0 free fraction per burst bay
    sliver_frac = []                           # sliver cells / free cells
    crane_only = 0; collision_blocked = 0; ok_anchors = 0
    burst_samples = 0
    per_bay_dens0 = [[] for _ in bays]
    timeline = []

    def bay_dens0(bj):
        g0 = raster.occ[bj].get(0)
        return float((g0 > 0).sum()) / area[bj] if g0 is not None else 0.0

    for t in grid:
        while ptr < len(events) and events[ptr][0] <= t:
            _te, typ, i = events[ptr]
            a = A[i]
            if typ == 1:
                raster.add(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            else:
                raster.remove(a["bay_id"], i, a["orient_idx"], a["x"], a["y"])
            ptr += 1
        qids = [i for i in range(n) if rel[i] <= t < entry.get(i, INF)]
        d0row = [round(bay_dens0(bj), 3) for bj in range(nb)]
        timeline.append({"t": t, "queue": len(qids), "dens0": d0row})
        if not qids:
            continue
        burst_samples += 1
        for bj in range(nb):
            per_bay_dens0[bj].append(d0row[bj])

        for bj in range(nb):
            H, W = raster.H[bj], raster.W[bj]
            g0 = raster.occ[bj].get(0)
            free = (g0 <= 0) if g0 is not None else np.ones((H, W), dtype=bool)
            free = np.asarray(free, dtype=bool)
            nfree = int(free.sum())
            _ar, rw, rh = largest_free_rect(free)
            bay_sample_total += 1
            lr_w.append(rw); lr_h.append(rh); lr_area.append(_ar)
            free_frac.append(nfree / area[bj])

            # queued blocks that FIT this bay (with an orient); bbox list
            qfit = []          # (i, oi, MW, MH)
            for i in qids:
                ojs = fit_orients[i][bj]
                if not ojs:
                    continue
                # smallest-bbox-area fitting orient
                oi = min(ojs, key=lambda o: bbox_cells[(i, o)][0]
                         * bbox_cells[(i, o)][1])
                MW, MH = bbox_cells[(i, oi)]
                qfit.append((i, oi, MW, MH))
                q_bw.append(MW); q_bh.append(MH)
            if not qfit:
                continue

            min_qw = min(min(mw, mh) for _, _, mw, mh in qfit)  # min side any queued
            sliver_frac.append(horiz_sliver_cells(free, min_qw) / max(1, nfree))

            def fits_rect(MW, MH):
                return ((MW <= rw and MH <= rh) or (MH <= rw and MW <= rh))

            fits_any = any(fits_rect(mw, mh) for _, _, mw, mh in qfit)

            # lenient residents (present at t) in this bay
            sc_res = [tr for tr in sched[bj] if tr[1] <= t < tr[2]]

            # exact-feasible existence (lenient) via raster anchors + gate
            exact_ok = False
            for (i, oi, MW, MH) in qfit:
                feas, cx0, cy0 = raster.scan(bj, i, oi)
                anchors = []
                if feas is not None and feas.any():
                    anchors += [(int(r), int(c)) for r, c in np.argwhere(feas)[:300]]
                near = raster.scan_near(bj, i, oi)
                if near is not None and near.any():
                    anchors += [(int(r), int(c)) for r, c in np.argwhere(near)[:300]]
                for (r, c) in anchors:
                    nbk = _mkblock(i, bd[i], c - cx0, r - cy0, oi)
                    if _can_place(bays[bj], sc_res, nbk, t, t + proc[i]):
                        exact_ok = True
                        break
                if exact_ok:
                    break

            if exact_ok:
                cls_count["c"] += 1
            elif fits_any:
                cls_count["a"] += 1
            else:
                cls_count["b"] += 1

            # crane-poisoning probe (only meaningful when bbox fits the free rect
            # but nothing is exact-feasible => class 'a'): enumerate layer-0-clean
            # anchors and classify their failure mode.
            if fits_any and not exact_ok:
                probed = 0
                for (i, oi, MW, MH) in sorted(qfit, key=lambda z: z[2] * z[3]):
                    if not fits_rect(MW, MH):
                        continue
                    if probed >= BLOCKS_PER_BAY:
                        break
                    probed += 1
                    mask, cx0, cy0 = raster.mask(i, oi)
                    xt = t + proc[i]
                    na = 0
                    # top-left grid cell (r0,c0) s.t. the MH x MW footprint is
                    # fully inside the layer-0 free mask (=> no layer-0 collision).
                    for r0 in range(0, H - MH + 1):
                        if na >= ANCHOR_CAP:
                            break
                        rowok = free[r0:r0 + MH, :]
                        for c0 in range(0, W - MW + 1):
                            if not rowok[:, c0:c0 + MW].all():
                                continue
                            nbk = _mkblock(i, bd[i], c0 - cx0, r0 - cy0, oi)
                            cls = classify_anchor(bays[bj], sc_res, nbk, t, xt)
                            if cls == 'crane':
                                crane_only += 1
                            elif cls == 'collision':
                                collision_blocked += 1
                            elif cls == 'ok':
                                ok_anchors += 1
                            na += 1
                            if na >= ANCHOR_CAP:
                                break

    # summary stats ----------------------------------------------------------
    def med(x):
        return float(np.median(x)) if x else 0.0

    def mean(x):
        return float(np.mean(x)) if x else 0.0

    tot = max(1, bay_sample_total)
    fa = cls_count["a"] / tot
    fb = cls_count["b"] / tot
    fc = cls_count["c"] / tot
    denom_anchor = crane_only + collision_blocked
    crane_frac = crane_only / denom_anchor if denom_anchor else None

    result = {
        "k": K, "inc": inc, "n": n, "nb": nb, "area": area, "horizon": horizon,
        "n_grid": len(grid), "burst_samples": burst_samples,
        "bay_sample_total": bay_sample_total,
        "burst_dens0_per_bay_mean": [round(mean(per_bay_dens0[bj]), 3)
                                     for bj in range(nb)],
        "class_counts": cls_count,
        "frac_a_crane_or_shape": round(fa, 4),
        "frac_b_fragmentation": round(fb, 4),
        "frac_c_feasible": round(fc, 4),
        "largest_free_rect_w": {"mean": round(mean(lr_w), 2),
                                "median": med(lr_w)},
        "largest_free_rect_h": {"mean": round(mean(lr_h), 2),
                                "median": med(lr_h)},
        "largest_free_rect_area_median": med(lr_area),
        "queued_bbox_w_median": med(q_bw),
        "queued_bbox_h_median": med(q_bh),
        "layer0_free_frac_mean": round(mean(free_frac), 3),
        "sliver_frac_mean": round(mean(sliver_frac), 3),
        "crane_only_anchors": crane_only,
        "collision_anchors": collision_blocked,
        "ok_anchors_lenient": ok_anchors,
        "crane_only_blocked_frac": (round(crane_frac, 4)
                                    if crane_frac is not None else None),
        "timeline": timeline,
    }
    json.dump(result, open(os.path.join(HERE, out), "w"), indent=1)

    # printed 10-line summary
    print("=" * 68)
    print(f"prob_26 GAP DIAGNOSTIC  (n={n}, bays={[ (b.width,b.height) for b in bays]})")
    print(f" burst (sample,bay) probed: {bay_sample_total}  "
          f"burst_samples={burst_samples}  dens0/bay="
          f"{result['burst_dens0_per_bay_mean']}")
    print(f" CLASS (a) fits-rect-but-infeasible [crane/shape]: {fa*100:5.1f}%  "
          f"({cls_count['a']})")
    print(f" CLASS (b) largest-rect < every queued bbox [FRAG]: {fb*100:5.1f}%  "
          f"({cls_count['b']})")
    print(f" CLASS (c) exact-feasible existed (lenient):        {fc*100:5.1f}%  "
          f"({cls_count['c']})")
    print(f" largest free rect (w x h): median "
          f"{med(lr_w):.0f} x {med(lr_h):.0f}  mean "
          f"{mean(lr_w):.1f} x {mean(lr_h):.1f}")
    print(f" queued bbox (w x h): median {med(q_bw):.0f} x {med(q_bh):.0f}   "
          f"layer0 free frac mean {mean(free_frac):.3f}")
    print(f" sliver mass (free cells in runs < min queued width): "
          f"{mean(sliver_frac)*100:.1f}% of free")
    print(f" crane-only-blocked anchor frac (of layer0-clean failing anchors): "
          f"{crane_frac if crane_frac is None else round(crane_frac,4)}"
          f"   crane={crane_only} collision={collision_blocked} ok={ok_anchors}")
    verdict = ("FRAGMENTATION-bound" if fb > 2 * max(fa, 1e-9)
               else "CRANE/SHAPE-bound" if fa > 2 * max(fb, 1e-9)
               else "MIXED")
    print(f" READING: {verdict}")
    print("=" * 68)
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
