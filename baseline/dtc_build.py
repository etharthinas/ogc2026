#!/usr/bin/env python3
"""dtc_build.py -- STANDALONE probe for arm 37b ("die together, pack together").

Death-time-clustered, fragmentation-aware anchor scoring at CONSTRUCTION time.
Mirrors what one giant worker does -- the nm+beam raster dispatcher build
(`_dispatch_construct`, kappa=2/gamma=0.5/alpha=0.5, beam, near_k~16) followed
by an `_improve` polish -- but with a MODIFIED anchor-selection score.

The modification is injected by RUNTIME MONKEYPATCH of two module-level names in
myalgorithm_36 (never touches the frozen file, entirely in-process):

  * `_rel_sched_bbox`  -> thin wrapper that stashes, per placement attempt, the
    time-overlapping residents (each carries block_id/orient/x/y + exit time)
    and the candidate block's exit time into a module global _DTC['ctx'].
    `_dispatch_construct.try_place` always calls this immediately before it
    ranks a bay's anchors with `_order_cells`, so the context is always fresh
    and bay-consistent.
  * `_order_cells`     -> faithful superset of the original: byte-identical when
    DTC is off (so the `_improve` polish and any None-context call reproduce the
    frozen behaviour exactly), plus a death-proximity / cohort-stripe term added
    to the contact score when DTC is on.

Two scoring modes:
  --mode adj    : for each candidate anchor, aggregate over the 4-neighbour
                  resident cells a weight (1 - |exit_new - exit_neighbor|/TAU)+,
                  convolved with the block footprint exactly like the contact
                  field. Walls contribute 0 (death-neutral; wall preference
                  stays via the untouched contact term). Big = adjacent to
                  residents that vacate at a similar time -> contiguous holes.
  --mode cohort : quantize exit time into buckets (width ~BUCKET) -> a bay
                  x-stripe by bucket index; bonus for landing the block centre
                  in its stripe. Cruder but global.

--dtc-weight scales the DTC term RELATIVE to the contact term (both live on the
footprint-perimeter scale). Default sweep values: {0.5, 2.0, 8.0}.

CLI:  dtc_build.py <k> <budget_s> [--dtc-weight W] [--mode adj|cohort] [--seed N]
Output line: DTC prob_<k>: mode=<m> w=<w> raw=<..> polished=<..> official=<..> feasible=<..>
Also writes baseline/dtc_<k>_<mode>_<w>.json (block_id -> assignment).

Windows spawn safe (single process, __main__ guard). Run from baseline/ with
the repo venv:  ..\.venv_ogc\Scripts\python.exe dtc_build.py 1 60
"""
import sys
import os
import json
import time
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import myalgorithm_36 as M
from utils import Bay, check_feasibility, check_entry, check_exit

_np = np
_swv = M._swv
_neighbor_field = M._neighbor_field

# ---------------------------------------------------------------------------
# DTC runtime state (single process, set by the driver + the _rel wrapper).
# ---------------------------------------------------------------------------
_DTC = {
    "on": False,      # gate: True only during the DTC construction build
    "mode": "adj",    # "adj" | "cohort"
    "w": 2.0,         # weight of the DTC term relative to contact
    "tau": 12.0,      # adj: exit-time proximity scale (ticks)
    "bucket": 8.0,    # cohort: exit-time bucket width (ticks)
    "nstripe": 8,     # cohort: number of bay x-stripes
    "ctx": None,      # per-attempt {exit_t, t, residents, grid}
    "raster": None,   # the active _Raster (for resident footprint masks)
}

_ORIG_REL = M._rel_sched_bbox
_ORIG_ORDER = M._order_cells


def _death_field(weight_grid):
    """4-neighbour SUM of `weight_grid` -- the death-time analogue of
    `_neighbor_field`, but WITHOUT the border/wall +1 (walls are death-neutral:
    they never vacate, so they carry no exit-cohort information)."""
    H, W = weight_grid.shape
    N = _np.zeros((H, W), dtype=_np.float64)
    N[1:, :] += weight_grid[:-1, :]
    N[:-1, :] += weight_grid[1:, :]
    N[:, 1:] += weight_grid[:, :-1]
    N[:, :-1] += weight_grid[:, 1:]
    return N


def _build_weight_grid(H, W):
    """Bay-local (H,W) float grid: each currently-resident cell carries
    (1 - |exit_new - exit_res| / TAU) clamped to [0,1]; empty cells 0.
    Residents come from the stashed _rel_sched_bbox result."""
    ctx = _DTC["ctx"]
    raster = _DTC["raster"]
    exit_t = ctx["exit_t"]
    tau = _DTC["tau"]
    grid = _np.zeros((H, W), dtype=_np.float64)
    for (blk, _a, e) in ctx["residents"]:
        wt = 1.0 - abs(exit_t - float(e)) / tau
        if wt <= 0.0:
            continue
        mask, cx0, cy0 = raster.mask(blk.block_id, blk.orient_idx)
        fp = mask.any(axis=0)                       # (MH, MW) footprint
        MH, MW = fp.shape
        r = int(blk.y) + cy0
        c = int(blk.x) + cx0
        r0 = max(0, r); c0 = max(0, c)
        r1 = min(H, r + MH); c1 = min(W, c + MW)
        if r1 <= r0 or c1 <= c0:
            continue
        sub = fp[r0 - r:r1 - r, c0 - c:c1 - c]
        # max so overlapping stamps keep the strongest cohort affinity
        _np.maximum(grid[r0:r1, c0:c1], sub * wt, out=grid[r0:r1, c0:c1])
    return grid


def _dtc_order_cells(raster, feas, cx0, cy0, bi, oi, W, occ_fp, prefer_contact,
                     rng, ovh_bay=None, ovh_w=2.0):
    """Superset of M._order_cells. DTC term is added ONLY when _DTC['on'] and a
    fresh context exists; otherwise this delegates to the frozen original so the
    polish improver and every non-construction call stay byte-exact."""
    # w=0 short-circuits to the frozen scorer (w=0 adj/cohort == stock, modulo
    # the side-effect-free _rel_sched_bbox stash). Off / no-context also delegate.
    if (not (_DTC["on"] and _DTC["ctx"] is not None)) or _DTC["w"] == 0.0:
        return _ORIG_ORDER(raster, feas, cx0, cy0, bi, oi, W, occ_fp,
                           prefer_contact, rng, ovh_bay=ovh_bay, ovh_w=ovh_w)

    rc = _np.argwhere(feas)
    if len(rc) == 0:
        return []
    r = rc[:, 0]; c = rc[:, 1]
    bl = (r * (W + 1) + c).astype(_np.float64)
    if rng is not None and len(rc) > 1:
        bl = bl + rng.uniform(0.0, 2.0) * _np.array(
            [rng.random() for _ in range(len(rc))])

    if prefer_contact and occ_fp is not None and occ_fp.any():
        N = _neighbor_field(occ_fp)
        bfp = raster.mask_fp(bi, oi).astype(_np.int32)
        MH, MW = bfp.shape
        win = _swv(N, (MH, MW))                       # (R,C,MH,MW)
        contact = _np.einsum('rcij,ij->rc', win, bfp)
        cval = contact[r, c].astype(_np.float64)

        w = _DTC["w"]
        if _DTC["mode"] == "adj":
            H, Wg = occ_fp.shape
            ctx = _DTC["ctx"]
            grid = ctx.get("grid")
            if grid is None:
                grid = _build_weight_grid(H, Wg)
                ctx["grid"] = grid
            if grid.any():
                Nw = _death_field(grid)
                winw = _swv(Nw, (MH, MW))
                death = _np.einsum('rcij,ij->rc', winw, bfp)
                cval = cval + w * death[r, c]
        else:   # cohort
            exit_t = _DTC["ctx"]["exit_t"]
            nst = _DTC["nstripe"]
            bucket = int(exit_t // _DTC["bucket"])
            stripe = bucket % nst
            center = (stripe + 0.5) / nst * float(W)
            # block centre column of each candidate; linear falloff over the bay
            ccenter = c.astype(_np.float64) + MW / 2.0
            stripe_bonus = 1.0 - _np.abs(ccenter - center) / max(1.0, float(W))
            perim = 2.0 * (MH + MW)          # put term on the contact scale
            cval = cval + w * perim * stripe_bonus

        idx = _np.lexsort((bl, -cval))
    else:
        idx = _np.argsort(bl)
    return [(int(c[ii]) - cx0, int(r[ii]) - cy0) for ii in idx]


def _dtc_rel_sched_bbox(sched_bay, entry, exit_t):
    """Wrapper: delegate to the frozen original, then stash the residents +
    candidate exit for the next _order_cells call (construction only)."""
    res = _ORIG_REL(sched_bay, entry, exit_t)
    if _DTC["on"]:
        _DTC["ctx"] = {"exit_t": float(exit_t), "t": float(entry),
                       "residents": res, "grid": None}
    return res


def _realize_operations(prob, bays, assign):
    """Best-effort crane-aware realizer (the vendored analogue of the frozen
    v2 same-tick realizer / the parent's role of only banking feasible replays).

    `_build_operations` emits same-tick ops in block_id order, which matches
    `_can_place`'s block_id tie-break -- but that gate is applied INCREMENTALLY
    at build time and the improver re-places non-monotonically, so the final
    replay order can be crane-infeasible even though every individual placement
    passed. This re-derives, per bay per tick, a Stage-5-legal order: exits
    before entries; within each, a greedy sequence in which every mover's crane
    path is clear against the blocks present at that instant (matching the
    official replay's growing/shrinking bay_present set). Purely an operation
    REORDER -- positions/times are untouched, so obj1/obj2/obj3 are identical.
    Returns an operations dict (same shape as _build_operations)."""
    blk = {}
    for bi, a in assign.items():
        bi = int(bi)
        nb = M._mkblock(bi, prob["blocks"][bi], a["x"], a["y"], a["orient_idx"])
        blk[bi] = (nb, int(a["bay_id"]), int(a["entry_time"]), int(a["exit_time"]))
    ticks = sorted({v[2] for v in blk.values()} | {v[3] for v in blk.values()})
    present = {}                       # bay_id -> [block_id] currently resident
    ops = {}
    for t in ticks:
        oplist = []
        exits = [bi for bi, v in blk.items() if v[3] == t]
        entries = [bi for bi, v in blk.items() if v[2] == t]
        # -- exits first (Stage-5) -------------------------------------------
        for bay_id in sorted({blk[bi][1] for bi in exits}):
            cur = list(present.get(bay_id, []))
            rem = sorted(bi for bi in exits if blk[bi][1] == bay_id)
            order = []
            while rem:
                pick = None
                for bi in rem:
                    others = [blk[o][0] for o in cur if o != bi]
                    if not check_exit(bays[bay_id], others, blk[bi][0], fast=True):
                        pick = bi
                        break
                if pick is None:            # stuck -> emit rest (will fail check)
                    order.extend(rem)
                    break
                order.append(pick)
                rem.remove(pick)
                cur.remove(pick)
            for bi in order:
                oplist.append({"type": "EXIT", "block_id": bi, "bay_id": bay_id})
            present[bay_id] = cur
        # -- then entries ----------------------------------------------------
        for bay_id in sorted({blk[bi][1] for bi in entries}):
            cur = list(present.get(bay_id, []))
            rem = sorted(bi for bi in entries if blk[bi][1] == bay_id)
            order = []
            while rem:
                pick = None
                for bi in rem:
                    others = [blk[o][0] for o in cur]
                    if not check_entry(bays[bay_id], others, blk[bi][0], fast=True):
                        pick = bi
                        break
                if pick is None:
                    order.extend(rem)
                    break
                order.append(pick)
                rem.remove(pick)
                cur.append(pick)
            for bi in order:
                a = assign[bi]
                oplist.append({"type": "ENTRY", "block_id": bi, "bay_id": bay_id,
                               "x": int(a["x"]), "y": int(a["y"]),
                               "orient_idx": int(a["orient_idx"])})
            present[bay_id] = cur
        ops[str(t)] = oplist
    return ops


def _verify(prob, bays, assign):
    """Official check with a realizer rescue. Returns
    (res, ops, used_realizer): res is the check_feasibility dict of the chosen
    ops (plain if already feasible, else the realized one)."""
    ops = M._build_operations(assign)
    res = check_feasibility(prob, {"operations": ops})
    if res.get("feasible"):
        return res, ops, False
    try:
        ops2 = _realize_operations(prob, bays, assign)
        res2 = check_feasibility(prob, {"operations": ops2})
    except Exception as e:
        return res, ops, False
    if res2.get("feasible"):
        return res2, ops2, True
    return res, ops, False


def run(k, budget_s, dtc_weight, mode, seed, build_frac=0.45, stock=False):
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{k}.json")))
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    blocks_data = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = M._bay_u(bays)
    forced = M._is_forced(prob, bays)

    raster = M._Raster(prob, bays)

    # install monkeypatches (skipped entirely for the --stock control)
    if not stock:
        M._order_cells = _dtc_order_cells
        M._rel_sched_bbox = _dtc_rel_sched_bbox
    _DTC["mode"] = mode
    _DTC["w"] = float(dtc_weight)
    _DTC["raster"] = raster
    tag = "stock" if stock else mode

    t0 = time.time()
    build_dl = t0 + budget_s * build_frac
    polish_dl = t0 + budget_s * 0.92

    # -- construction build (nm+beam raster dispatcher, near_k~16) -------------
    raster.reset()
    _DTC["on"] = not stock
    _DTC["ctx"] = None
    assign = M._dispatch_construct(
        prob, bays, bay_u, w1, w2, w3, build_dl, raster,
        kappa=2.0, gamma=0.5, rng=None, alpha=0.5, score_pos=True,
        beam=True, beam_m=4, nearmiss=16, mpc=False)
    _DTC["on"] = False
    _DTC["ctx"] = None

    raw = M._objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]
    build_s = time.time() - t0

    # -- polish (standard scoring: DTC off, _order_cells == frozen) -----------
    r_assign, polished = M._improve(
        prob, assign, bays, bay_u, w1, w2, w3, polish_dl, forced,
        seed=seed, raster=raster, repack_every=3, xbay=True, deep=forced,
        nearmiss=0)

    # -- official objective (with realizer rescue on infeasible replays) ------
    res, ops, used_realizer = _verify(prob, bays, r_assign)
    feasible = bool(res.get("feasible"))
    if feasible:
        official = f"{res.get('objective'):,.0f}"
        extra = f"obj1={res.get('obj1')}" + (" realized" if used_realizer else "")
    else:
        official = "INFEASIBLE"
        viol = res.get("violations") or []
        v0 = (viol[0][:90] if viol else "")
        extra = f"stage={res.get('stage')} nviol={len(viol)} v0={v0!r}"

    print(f"DTC prob_{k}: mode={tag} w={dtc_weight} raw={raw:,.0f} "
          f"polished={polished:,.0f} official={official} "
          f"feasible={feasible}  (build {build_s:.1f}s {extra})", flush=True)

    out = f"dtc_{k}_{tag}_{dtc_weight}.json"
    json.dump({str(bi): v for bi, v in r_assign.items()},
              open(os.path.join(HERE, out), "w"))
    print(f"saved -> {out}", flush=True)
    return (res.get("objective") if feasible else None), feasible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("k", type=int)
    ap.add_argument("budget_s", type=float)
    ap.add_argument("--dtc-weight", type=float, default=2.0)
    ap.add_argument("--mode", choices=["adj", "cohort"], default="adj")
    ap.add_argument("--seed", type=int, default=1616)
    ap.add_argument("--stock", action="store_true",
                    help="true control: NO monkeypatch, frozen functions only")
    a = ap.parse_args()
    run(a.k, a.budget_s, a.dtc_weight, a.mode, a.seed, stock=a.stock)


if __name__ == "__main__":
    main()
