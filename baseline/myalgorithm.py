# myalgorithm_14.py  --  v14 = v13 + JOINT WINDOW REPACK (LNS-XL, geometry lever) +
#                        MULTI-ORDER ADMISSION BEAM + REPACK-HEAVY WORKERS.
#                        See heuristic_14.md.
# =============================================================================
# v14. Three additions over v13 (goal: full-40 train < 150M; v13 focus-6 = 121.57M).
#  Diagnosis: v13 exhausted three ADMISSION-TIMING levers (alpha-ATC, CP-SAT
#  retime, fluid-target gating) on the overloaded pair -- order/timing is
#  saturated. The residual lever is GEOMETRY: the dispatcher and repair place ONE
#  block at a time into whatever concave scrap exists, so a dense interlocked
#  cluster is only reachable by placing its members TOGETHER.
#  1. JOINT WINDOW REPACK (`_repack_window`). A new LNS-XL improver move for tardy
#     instances: pick the most CONGESTED (bay, time-window) from the incumbent's
#     own schedule (area-time in queue/tardiness overlap), DESTROY every block of
#     that bay whose [entry,exit) intersects it (typ 10-30), then REBUILD only the
#     destroyed set with the un-destroyed neighbours held FIXED (scoped raster
#     occupancy). Try k orders (area-desc / due-asc / min-slack / most-constrained
#     -first = fewest raster-feasible cells), each a greedy earliest-feasible
#     raster placement, and keep the best rebuild. Blocks that fail to place in the
#     bay fall back to the normal repair path (force-place guarantee stands). The
#     rebuild is accepted ONLY if the FULL internal objective strictly improves
#     (obj-gated inside `_improve`; restore-on-reject is automatic since a fresh
#     `work` dict is only adopted when better). Wired into `_improve` as a
#     `repack_every`-th-round move (0 == off == byte-exact v13; W0 untouched).
#  2. MULTI-ORDER ADMISSION BEAM (`_dispatch_construct(beam=True)`). At events with
#     >= beam_m queued candidates, evaluate k=3 greedy fills (ATC order, area-desc,
#     most-constrained-first) via trial-commit + rollback of the raster/sched, and
#     COMMIT the fill with the best (admitted area, then placement cost). Kills the
#     "first-fit forecloses the interlock" failure at admission. beam=False
#     reproduces v13's single-pass dispatch BYTE-FOR-BYTE (the v13 loop is just
#     refactored through `apply_place`); beam is only a NEW lottery ticket, with
#     the no-beam entries kept FIRST so best-of always protects v13's basins.
#  3. REPACK-HEAVY WORKERS. Giants (nw=3): W2's polish interleaves joint-repack
#     rounds (repack_every=3) with classic destroy/repair; W1 keeps the classic
#     AREA basin as a repack-free portfolio anchor. Non-giants: the W3 dispatcher's
#     post-lottery polish gains repack rounds (repack_every=4), and W2's overloaded
#     polish gets repack_every=3 (attacks prob_27). W0 anchor untouched; all
#     accepts internal-objective-gated; parent official verify unchanged. (nw=4
#     giant repack-specialist deferred pending an RSS measurement -- v13 was
#     2.83GB/3w.)
# =============================================================================
# v13. Three additions over v12 (goal: full-40 train < 150M; v12 = 174.59M):
#  1. RASTER-WINDOWED REPAIR (`_find_earliest_slot_raster` + `_Raster.scan_scoped`).
#     v12's improver repaired only via AABB-corner candidates -- the 55-72%
#     inside-bbox density ceiling. v13 gives the worker's raster to the improver:
#     per candidate entry time it builds a SCOPED occupancy from only the
#     time-overlapping blocks, full-position scans, ranks feasible cells by
#     PERIMETER CONTACT (block-footprint dotted with the occupied/wall neighbour
#     field -- `_order_cells`/`_neighbour_field`), and exact-gates with
#     _can_place. Concavity-filling placements AABB corners never propose become
#     reachable. Gated to forced/congested instances. The same contact ordering
#     upgrades the dispatcher's try_place (score_pos), with an adaptive cand_cap
#     (12->48 on deep entry queues) killing the 12-cell rejection cliff.
#  2. VOLUME-AWARE TRIAGE. ATC generalized to priority ~ 1/(a^alpha * p) *
#     exp(-slack/(kappa*pbar)); alpha=0 reproduces v12 exactly, alpha>0 strands
#     large-footprint blocks under overload (fluid-SPT). Multiplicative jitter.
#     Giants (v12: one dispatch) now run a W2 mini-lottery over alpha/kappa;
#     W3's lottery gains the alpha dimension.
#  3. THROUGHPUT. Scan cache per (bay,bi,oi,ver), footprint cache per (bay,ver),
#     exit-time SET (O(1) heap membership), prune exited blocks from the
#     dispatcher sched, drop fully-vacated occupancy layers -- all
#     result-transparent, they only multiply builds/rounds. W0 stays byte-exact.
# =============================================================================
# v12 = v11 + RASTER GEOMETRY ENGINE (numpy conservative occupancy scan) +
#       TIME-ORDERED DISPATCHER construction + CP-SAT retime audit fixes.
# =============================================================================
# v12 (see heuristic_12.md). Three additions over v11:
#  1. RASTER ENGINE (`_Raster`). Per (block, orient, layer) a conservative
#     boolean unit-grid mask (a cell is set iff the layer polygon *touches* its
#     closed unit square -> mask-disjoint from the occupancy union implies the
#     polygons share no cell, hence no positive-area overlap: provably feasible
#     for BOTH the same-layer collision rule AND the crane j>=k prism rule,
#     since entry and exit share identical geometry). Per-bay per-layer int
#     occupancy grids are maintained incrementally; a numpy sliding-window scan
#     returns EVERY entry-clear integer position at once (vs v11's handful of
#     AABB contact points) -- the direct fix for the 55% density ceiling. It is
#     conservative (only ever rejects edge-touching placements), so any position
#     it returns is truly feasible; the chosen candidate is still gated by the
#     exact cached `_can_place` (which also enforces reverse exit-blocking) and
#     the whole solution is officially verified by the parent.
#  2. TIME-ORDERED DISPATCHER (`_dispatch_construct`). Event-driven admission
#     (events = releases + scheduled exits): at each event admit queued blocks
#     in ATC (apparent-tardiness-cost) priority using the raster full scan,
#     never leaving a fitting block queued (kills prob_27's idle-with-fit steps
#     and drains release bursts as fast as geometry allows). Bay choice spills
#     to non-preferred bays when the preferred bay is full (w1 >> w3). Prompt
#     exits at entry+proc (always crane-feasible by the admission invariant).
#     Wired as W2 (default kappa) and W3 (kappa/weight/jitter lottery).
#  3. CP-SAT RETIME FIXES. Pair-count cap per bay, a deadline flag inside the
#     O(m^2) pair-build loop (abort => skip solve, never solve a partial model),
#     solver budget recomputed AFTER the build (no >=1s floor), and the pass
#     gated on improver stall with a hard latest-start.
# =============================================================================
# Imports the standard library (math, time, random, multiprocessing), `utils`
# (contest-provided), and OPTIONALLY ortools (in ogc2026_env.yml; every use is
# wrapped so its absence just disables the CP-SAT pass). No `myalgorithm_N`
# helper imports. To submit a newer version, copy this over myalgorithm.py.
# =============================================================================
# v11 (see heuristic_11.md). Two additions over v10:
#  1. ISLAND MODEL. v10 workers were isolated: nobody polished another worker's
#     winner (prob_38's W1 win got zero help). The parent now broadcasts the
#     global best back to workers via per-worker inbox queues; W1+ improvers
#     adopt an inbox solution when it beats their incumbent. W0 (v9 replica)
#     takes no inbox: it must stay byte-exact v9 as the no-regression anchor.
#  2. CP-SAT TIME-REPAIR. With bay/x/y/orient FIXED, re-optimizing all entry
#     times is a clean subproblem: w2/w3 don't depend on timing, so minimize
#     w1*sum(tardiness) subject to pairwise collision (disjoint intervals) and
#     crane entry/exit blocking (entry_i outside j's presence when j blocks i)
#     -- all relations precomputed with the exact cached geometry primitives.
#     Solved per bay (bays are independent). Workers run it once their improver
#     stalls; the result is pushed like any candidate (parent still verifies
#     officially, so an encoding subtlety can cost a candidate, never
#     correctness). Targets the schedule-limited instances (prob_31/35/30/23/
#     28/21: fluid-LB ~ 0 yet ~5-18M objectives).
# =============================================================================
# v10 (see heuristic_10.md). Two structural observations:
#  1. The eval server allows 4 CPU cores; v9 used ONE. All of v9's compromises
#     (two-pass 35/65 improver split, CON_FRAC construction cap, the
#     construction-cheap gate) are single-budget rationing artifacts. v10 runs a
#     PARALLEL PORTFOLIO of min(4,cpu) worker processes, each an independent
#     full-budget strategy streaming best-so-far assignments to the parent via a
#     queue; the parent picks the best by internal objective and verifies it
#     officially (best-first, empty-bay fallback). Strategies (forced):
#     W0 EDD->improve (v8 anchor), W1 AREA->improve (v9's giant-winner, now with
#     the FULL budget), W2 congestion-aware construction -> improve, W3 jitter
#     multi-start -> simulated-annealing improve. Experimental members are
#     regression-safe: the parent takes the min over workers. Falls back to
#     v9's single-thread path if multiprocessing is unavailable.
#  2. Bay-assignment myopia is a CONSTRUCTION bug: in Pass A, w1-dominant
#     instances take the FIRST preferred bay with a zero-tardiness slot,
#     congesting it so later blocks spill into tardiness (prob_39 fluid-LB 1.3M
#     vs 27M achieved). W2 scores ALL bays' zero-slots and adds a window-
#     utilization penalty (util_gamma * w1 * util) so the greedy pays an
#     anticipatory price for stuffing a crowded bay while spreading is free.
# =============================================================================
# v9. The residual loss after v8 was dominated by instances byte-identical across
# v3..v8 (prob_27/30/35/39): these are deterministic EDD constructions the
# improver cannot beat (only ~12 slow rounds). The lever is a BETTER construction:
#   * MULTI-START over EDD + AREA (largest-footprint-first) + jittered orders,
#     keeping the best. AREA -- placing the hardest-to-fit blocks while bays are
#     empty -- reaches a far better geometric basin on the stuck giants
#     (prob_39 29.75M->27.05M, first movement ever; prob_27 52.4M->48.9M; prob_26
#     20.6M->18.9M; prob_33 17.2M->16.7M). Construction phase capped at CON_FRAC
#     of the window so the improver keeps a guaranteed share.
#   * REGRESSION-SAFE TWO-PASS IMPROVER on forced instances: improve the plain EDD
#     construction first (== v8's result, so never a regression), THEN improve the
#     best other construction only if its RAW objective already beats the
#     EDD-improved one (true on the giants, false on improver-dependent instances).
# Fitting EDD+AREA on the n=250 giants needs ~300s per instance (well within the
# contest's few-minutes-to-half-hour). Full-40 @300s ~= 299.3M (40/40 feasible),
# vs v8's 311.16M. The dormant cross-bay-rebalance / partial-restart operators
# (REBAL_AFTER / RESTART_AFTER = 1e9) are disabled experiments kept for
# provenance; see heuristic_9.md for why they could not crack the stuck optima.
# =============================================================================
# v8 = v7 (geometry caching) + THOROUGH REPAIR. Caching made each placement
# cheap, so the improver can now afford a much wider per-block search during
# repair (slot_time_cap 18->40, slot_pos_cap 14->30) -- the exact thing v5 kept
# tiny purely for speed. Hypothesis: the plateaus v5/v7 hit on the gap instances
# (prob_39/26/33: relaxed LB far below achieved, yet the improver finds nothing)
# are partly an artifact of the capped repair search missing the denser packing;
# a wider repair may escape them. Tested against v7 on the gap set; kept only if
# it actually lowers the objective (see heuristic_8.md / results.csv).
# =============================================================================
# v7 = v5 + pairwise GEOMETRY CACHING (semantically identical to v5, faster).
# =============================================================================
# Diagnosis: on the packing-limited instances (relaxed LB << v5 result, e.g.
# prob_35/28/31/30/23/39) more improver rounds keep lowering tardiness
# (prob_35: 14.6M@60s -> 11.4M@150s), but v5 is round-starved because every
# placement check rebuilds Shapely intersections. v7 memoizes the three
# pairwise feasibility primitives -- collision, crane-entry obstruction, crane-
# exit obstruction -- keyed by the two placements' (block_id, orient, x, y).
# These are pure geometry (time-independent) and SEPARABLE per existing block
# (the crane path is blocked iff ANY single present block blocks it), so the
# cache is exact: v7 returns the SAME feasibility verdict as v5 for every call,
# just far cheaper after warm-up -> many more destroy/repair rounds per second
# on the instances where that converts directly into less tardiness. The final
# solution is still verified by the official check_feasibility, unchanged.
# (Structurally over-subscribed instances prob_38/27 -- area-time demand exceeds
#  total capacity-time over the whole horizon -- stay near their forced floor;
#  no heuristic removes their tardiness. See heuristic_7.md / results.csv.)
# =============================================================================
# v5: v3's full thorough construction (NO cap) + fast basin-hopping improver.
# =============================================================================
# Fixes v4's two mistakes: (1) removes the construction-time cap so the start is
# always v3's strong thorough construction; the improver takes only leftover
# time. (2) Improver rounds are now small & fast (smaller destroy sets, capped
# repair search, lower kick threshold) so MANY more rounds run per second of
# real compute -> it actually bites on the congested instances where v4's slow
# rounds found nothing. Still returns the best-tracked incumbent (monotone).
#
# --- v4 provenance ---------------------------------------------------------
# v4: EDD-earliest construction + budget rebalance + basin-hopping improver
#     (diversified destroy/repair with escape-kicks, window-destroy mode).
# v3 placement/feasibility core kept verbatim; the
# improver and the time-budget split change. The improver tracks a separate best
# incumbent and returns it -> still monotone in the RESULT (never worse than the
# construction) while exploring more to escape plateaus (e.g. prob_39).
#
# --- v3 provenance ---------------------------------------------------------
# v3: EDD-earliest construction + multi-start best-of (no-regression) + safe
#     tardiness-pull improvement.
# Reuses v2's verified feasibility/placement core
# verbatim; changes ONLY the top-level orchestration:
#   * EDD-earliest construction targets the avoidable tardiness on congested
#     instances (the dominant cost; relaxed LB shows ~90% of it is avoidable).
#   * Per-instance best-of across {EDD-earliest, congestion-ALAP(=v1), seeded
#     perturbations} keeps the best VERIFIED-feasible solution -> can never be
#     worse than v1 on any instance (v2's regression is structurally impossible).
#   * A monotone destroy/repair improver replaces v2's non-monotone LNS.

import math
import time
import random

try:
    import numpy as _np
    from numpy.lib.stride_tricks import sliding_window_view as _swv
    _HAVE_NUMPY = True
except Exception:  # pragma: no cover
    _np = None
    _swv = None
    _HAVE_NUMPY = False

from utils import (
    Bay, Block,
    check_entry, check_exit, check_collisions, check_feasibility,
    _resolve_layers, _bounding_box, _bb_overlap, _poly_from_verts,
)

# -----------------------------------------------------------------------------
# Pairwise geometry caches (v7). Keyed by placement = (block_id, orient, x, y).
# Pure geometry, time-independent. Cleared per instance in algorithm().
#   _BLK : (bi, oi, x, y)                  -> reusable Block (avoids re-translate)
#   _CC  : frozenset{key_a, key_b}         -> do a, b spatially collide (any layer)
#   _CE  : (existing_key, mover_key)       -> does `existing` block `mover`'s ENTRY
#   _CX  : (existing_key, mover_key)       -> does `existing` block `mover`'s EXIT
# A pair-cache is exact because check_collisions/entry/exit are separable: a
# multi-block verdict is the OR of the single-block verdicts. Bay boundary is
# checked separately via bay.contains_block before any crane call, so the
# self-boundary obstruction never appears here.
# -----------------------------------------------------------------------------
_BLK = {}
_CC = {}
_CE = {}
_CX = {}
# v10: worker processes share 16GB (both locally and on the eval server), so
# the v9 unlimited-growth caches (6M) must be bounded. Measured on prob_38 (the
# heaviest instance): one dense EDD build needs ~192k _BLK entries and >1M _CE
# entries (~1.5GB RSS); a worker fits comfortably under these caps, and the
# giant instances run only 2 workers (see _algorithm_portfolio).
_BLK_CAP = 250_000
_CACHE_CAP = 2_500_000


def _reset_caches():
    _BLK.clear(); _CC.clear(); _CE.clear(); _CX.clear()


def _mkblock(bi, blk_data, x, y, oi):
    k = (bi, oi, x, y)
    nb = _BLK.get(k)
    if nb is None:
        nb = Block(block_id=bi, block_data=blk_data, x=x, y=y, orient_idx=oi)
        if len(_BLK) < _BLK_CAP:
            _BLK[k] = nb
    return nb


def _pk(blk):
    return (blk.block_id, blk.orient_idx, blk.x, blk.y)


def _collide(bay, a, b):
    ka, kb = _pk(a), _pk(b)
    key = (ka, kb) if ka <= kb else (kb, ka)
    v = _CC.get(key)
    if v is None:
        v = bool(check_collisions(bay, [a, b]))
        if len(_CC) < _CACHE_CAP:
            _CC[key] = v
    return v


def _entry_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane descent (== v5's
    check_entry(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CE.get(key)
    if v is None:
        v = bool(check_entry(bay, [existing], mover, fast=True))
        if len(_CE) < _CACHE_CAP:
            _CE[key] = v
    return v


def _exit_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane ascent (== v5's
    check_exit(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CX.get(key)
    if v is None:
        v = bool(check_exit(bay, [existing], mover, fast=True))
        if len(_CX) < _CACHE_CAP:
            _CX[key] = v
    return v


# -----------------------------------------------------------------------------
# Static per-block geometry helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _orient_bbox(block_data, oi):
    layers = _resolve_layers(block_data["shape"][oi]["layers"])
    if not layers:
        return (0.0, 0.0, 1.0, 1.0)
    return _bounding_box([v for l in layers for v in l])


def _orient_area(block_data, oi):
    bb = _orient_bbox(block_data, oi)
    return max(1.0, (bb[2] - bb[0]) * (bb[3] - bb[1]))


def _min_area(block_data):
    return min(_orient_area(block_data, oi) for oi in range(len(block_data["shape"])))


def _max_layers(block_data):
    return max(len(_resolve_layers(o["layers"])) for o in block_data["shape"])


def _orient_fits(block_data, oi, bay):
    lx0, ly0, lx1, ly1 = _orient_bbox(block_data, oi)
    return (math.ceil(-lx0) <= math.floor(bay.width - lx1) and
            math.ceil(-ly0) <= math.floor(bay.height - ly1))


def _unique_orients(block_data):
    seen = {}
    for oi in range(len(block_data["shape"])):
        bb = _orient_bbox(block_data, oi)
        nl = len(_resolve_layers(block_data["shape"][oi]["layers"]))
        key = (round(bb[0], 3), round(bb[1], 3), round(bb[2], 3), round(bb[3], 3), nl)
        if key not in seen:
            seen[key] = oi
    return list(seen.values())


def _candidate_positions(bay, placed_blocks, blk_bb, cap=60):
    lx0, ly0, lx1, ly1 = blk_bb
    xs = {max(0, math.ceil(-lx0))}
    ys = {max(0, math.ceil(-ly0))}
    for b in placed_blocks:
        bb = b.bounding_rect()
        xs.add(int(math.ceil(bb[2] - lx0)))
        ys.add(int(math.ceil(bb[3] - ly0)))
    out = []
    for x in sorted(xs):
        if x + lx1 > bay.width + 1e-6 or x + lx0 < -1e-6:
            continue
        for y in sorted(ys):
            if y + ly1 > bay.height + 1e-6 or y + ly0 < -1e-6:
                continue
            out.append((int(x), int(y)))
            if len(out) >= cap:
                return out
    return out


# -----------------------------------------------------------------------------
# Time-overlap + crane-presence helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _overlaps(a1, e1, a2, e2):
    return a1 < e2 and a2 < e1


def _present_at_entry(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (a == t and b.block_id < x_id):
            out.append(b)
    return out


def _present_at_exit(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (e == t and b.block_id > x_id):
            out.append(b)
    return out


def _can_place(bay, sched, new_blk, entry, exit_t):
    # v7: identical verdict to v5, but every Shapely call is routed through the
    # pairwise caches. check_entry/exit over a SET of present blocks is the OR of
    # the per-block checks, so we decompose into cached pairwise queries.
    if not bay.contains_block(new_blk):
        return False
    nbid = new_blk.block_id
    # new_blk ENTRY obstructed by any block present at `entry` (== check_entry
    # over _present_at_entry set).
    for b, a, e in sched:
        if (a < entry < e) or (a == entry and b.block_id < nbid):
            if _entry_blocked(bay, b, new_blk):
                return False
    # new_blk EXIT obstructed by any block present at `exit_t` (== check_exit
    # over _present_at_exit set).
    for b, a, e in sched:
        if (a < exit_t < e) or (e == exit_t and b.block_id > nbid):
            if _exit_blocked(bay, b, new_blk):
                return False
    for b, a, e in sched:
        if _overlaps(entry, exit_t, a, e) and _collide(bay, new_blk, b):
            return False
        if (entry < a < exit_t) or (entry == a and nbid < b.block_id):
            if _entry_blocked(bay, new_blk, b):
                return False
        if (entry < e < exit_t) or (exit_t == e and nbid > b.block_id):
            if _exit_blocked(bay, new_blk, b):
                return False
    return True


def _empty_bay_entry(sched, r_time, proc):
    entry = int(r_time)
    changed = True
    while changed:
        changed = False
        exit_t = entry + proc
        for it in sched:
            a, e = it[1], it[2]
            if _overlaps(entry, exit_t, a, e):
                entry = max(entry, e)
                changed = True
    return entry


def _rel_sched(sched, nb_bb):
    return [(it[0], it[1], it[2]) for it in sched if _bb_overlap(nb_bb, it[3])]


def _zero_candidates(rel, release, alap, proc):
    cand = {alap, release}
    for _, a, e in rel:
        for t in (a, e, a - proc, e - proc):
            for tt in (int(t), int(t) - 1):
                if release <= tt <= alap:
                    cand.add(tt)
    return sorted(cand, reverse=True)


def _find_zero_slot(bay, sched, new_blk, release, due, proc):
    alap = due - proc
    if alap < release:
        return None
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    for entry in _zero_candidates(rel, release, alap, proc):
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    return None


def _find_tardy_slot(bay, sched, new_blk, release, due, proc, tardy_cap=64):
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    start = max(release, due - proc + 1)
    cand = {start}
    for _, _, e in rel:
        if e >= start:
            cand.add(e)
    for entry in sorted(cand)[:tardy_cap]:
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    entry = _empty_bay_entry(sched, release, proc)
    if _can_place(bay, rel, new_blk, entry, entry + proc):
        return entry
    return None


def _time_overlap_rel(sched_bay, t, exit_t):
    return [(it[0], it[1], it[2]) for it in sched_bay
            if it[1] <= exit_t and t <= it[2]]


def _find_earliest_slot(bay, sched_bay, bi, blk, orients, lb, proc,
                        time_cap=40, pos_cap=24):
    """Earliest feasible (orient, x, y, entry) with entry >= lb, packing densely.
    Returns the first (= earliest, least-tardy) feasible placement, or None."""
    times = {int(lb)}
    for _, a, e in [(it[0], it[1], it[2]) for it in sched_bay]:
        if e >= lb:
            times.add(int(e))
        if a >= lb:
            times.add(int(a))
    for t in sorted(times)[:time_cap]:
        exit_t = t + proc
        relx = _time_overlap_rel(sched_bay, t, exit_t)
        active = [r[0] for r in relx]
        for oi in orients:
            if not _orient_fits(blk, oi, bay):
                continue
            blk_bb = _orient_bbox(blk, oi)
            for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                nb = _mkblock(bi, blk, cx, cy, oi)
                if _can_place(bay, relx, nb, t, exit_t):
                    return (oi, cx, cy, t)
    return None


def _find_earliest_slot_raster(bay, bay_id, sched_bay, bi, blk, orients, lb, proc,
                               raster, score_pos=True, time_cap=16, pos_cap=28):
    """v13 RASTER-WINDOWED REPAIR: earliest feasible (orient,x,y,entry) reached
    by a full-position raster scan instead of AABB-corner enumeration -- the
    density lever inside the improver. For each candidate entry time t, build a
    SCOPED occupancy from ONLY the time-overlapping blocks (does NOT touch the
    dispatcher's raster.occ), scan every integer anchor, rank feasible cells by
    perimeter contact, and exact-gate with _can_place. Returns the earliest
    feasible placement or None."""
    times = {int(lb)}
    for it in sched_bay:
        a, e = it[1], it[2]
        if e >= lb:
            times.add(int(e))
        if a >= lb:
            times.add(int(a))
    for t in sorted(times)[:time_cap]:
        exit_t = t + proc
        relx = _time_overlap_rel(sched_bay, t, exit_t)
        actives = [(it0.block_id, it0.orient_idx, it0.x, it0.y)
                   for (it0, _a, _e) in relx]
        for oi in orients:
            if not _orient_fits(blk, oi, bay):
                continue
            feas, cx0, cy0, occ_fp = raster.scan_scoped(bay_id, actives, bi, oi)
            if feas is None or not feas.any():
                continue
            cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                 raster.W[bay_id], occ_fp, score_pos, None)
            tried = 0
            for (x, y) in cells:
                nb = _mkblock(bi, blk, x, y, oi)
                if _can_place(bay, relx, nb, t, exit_t):
                    return (oi, x, y, t)
                tried += 1
                if tried >= pos_cap:
                    break
    return None


# -----------------------------------------------------------------------------
# Orderings
# -----------------------------------------------------------------------------

def _edd_order(blocks_data, jitter=None):
    """Earliest-due-date first; tie shortest proc, largest area, most layers.
    Optional jitter (rng) perturbs ties for multi-start diversity."""
    n = len(blocks_data)
    areas = [_min_area(b) for b in blocks_data]
    base = []
    for i, b in enumerate(blocks_data):
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((b["due_date"] + j, b["processing_time"], -areas[i],
                     -_max_layers(blocks_data[i]), i))
    base.sort()
    return [t[-1] for t in base]


def _slack_order(blocks_data, jitter=None):
    """Minimum-slack first (due - release - proc), tie earliest due. Slack is how
    much freedom a block has before it is tardy; scheduling the tightest blocks
    first is a classic alternative basin to pure EDD."""
    base = []
    for i, b in enumerate(blocks_data):
        slack = b["due_date"] - b["release_time"] - b["processing_time"]
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((slack + j, b["due_date"], b["processing_time"], i))
    base.sort()
    return [t[-1] for t in base]


def _area_order(blocks_data, jitter=None):
    """Largest-footprint first within due-date buckets: places the hardest-to-fit
    blocks while the bays are empty, a different geometric basin than EDD."""
    areas = [_min_area(b) for b in blocks_data]
    base = []
    for i, b in enumerate(blocks_data):
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((b["due_date"] + j, -areas[i], b["processing_time"], i))
    base.sort()
    return [t[-1] for t in base]


def _congestion_order(blocks_data):
    n = len(blocks_data)
    intervals = []
    areas = [_min_area(b) for b in blocks_data]
    for b in blocks_data:
        entry = max(b["release_time"], b["due_date"] - b["processing_time"])
        intervals.append((int(entry), int(entry + b["processing_time"])))
    events = {}
    for (a, e), ar in zip(intervals, areas):
        events[a] = events.get(a, 0.0) + ar
        events[e] = events.get(e, 0.0) - ar
    times = sorted(events)
    demand_at = {}
    run = 0.0
    for t in times:
        run += events[t]
        demand_at[t] = run

    def pressure(i):
        a, e = intervals[i]
        best = 0.0
        for t in times:
            if t >= e:
                break
            if t >= a:
                best = max(best, demand_at[t])
        return best

    return sorted(
        range(n),
        key=lambda i: (
            -pressure(i),
            blocks_data[i]["due_date"] - blocks_data[i]["release_time"]
            - blocks_data[i]["processing_time"],
            -areas[i],
            -_max_layers(blocks_data[i]),
        ),
    )


# -----------------------------------------------------------------------------
# Objective helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _bay_u(bays):
    areas = [b.width * b.height for b in bays]
    avg = sum(areas) / len(bays)
    return [avg / a for a in areas]


def _objective(assignments, blocks_data, bays, bay_u, w1, w2, w3):
    n_bays = len(bays)
    obj1 = 0.0
    loads = [0.0] * n_bays
    obj3 = 0.0
    for a in assignments.values():
        bi = a["block_id"]; bj = a["bay_id"]
        blk = blocks_data[bi]
        obj1 += max(0.0, a["exit_time"] - blk["due_date"])
        loads[bj] += blk["workload"]
        obj3 += max(blk["bay_preferences"]) - blk["bay_preferences"][bj]
    if n_bays >= 2:
        obj2 = math.floor(max(
            abs(bay_u[p] * loads[p] - bay_u[q] * loads[q])
            for p in range(n_bays) for q in range(n_bays) if p != q))
    else:
        obj2 = 0.0
    return w1 * obj1 + w2 * obj2 + w3 * obj3, obj1, obj2, obj3


# -----------------------------------------------------------------------------
# Thorough placement of one block (verbatim from v2)
# -----------------------------------------------------------------------------

def _window_util(sched_bay, entry, exit_t, bay_area):
    """Fraction of the bay's area-time committed inside [entry, exit_t) by
    already-placed blocks (bbox areas; cheap anticipatory congestion signal)."""
    span = max(1, exit_t - entry)
    occ = 0.0
    for it in sched_bay:
        a, e, bb = it[1], it[2], it[3]
        ov = min(exit_t, e) - max(entry, a)
        if ov > 0:
            occ += (bb[2] - bb[0]) * (bb[3] - bb[1]) * ov
    return occ / (bay_area * span)


def _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                 pos_cap=40, tardy_cap=8, dense=True, forced=False,
                 bay_order=None, slot_time_cap=40, slot_pos_cap=24,
                 util_gamma=0.0, raster=None):
    release = int(blk["release_time"])
    due = int(blk["due_date"])
    proc = int(blk["processing_time"])
    workload = blk["workload"]
    prefs = blk["bay_preferences"]
    s_max = max(prefs)
    orients = _unique_orients(blk)
    n_bays = len(bays)
    # v10: util_gamma > 0 disables the first-preferred-bay-wins shortcut so ALL
    # bays' zero-slots compete on score (incl. the congestion penalty below).
    w1_dominant = util_gamma <= 0.0 and w1 >= 20.0 * max(w2, w3, 1e-9)

    def score(tardiness, bay_id, top_y, entry=None, exit_t=None):
        new_load = bay_loads[bay_id] + workload
        imbal = max((abs(bay_u[bay_id] * new_load - bay_u[j] * bay_loads[j])
                     for j in range(n_bays) if j != bay_id), default=0.0)
        sc = (w1 * tardiness + w2 * imbal + w3 * (s_max - prefs[bay_id])
              + 1e-4 * top_y)
        if util_gamma > 0.0 and entry is not None:
            bay = bays[bay_id]
            sc += util_gamma * w1 * _window_util(
                sched[bay_id], entry, exit_t, bay.width * bay.height)
        return sc

    if bay_order is None:
        bay_order = sorted(range(n_bays), key=lambda j: prefs[j], reverse=True)
    best_score = float("inf")
    best = None

    # -- Pass A: zero-tardiness placements (skipped when forced) ----------
    if not forced:
        for bay_id in bay_order:
            bay = bays[bay_id]
            bay_zero = False
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_zero_slot(bay, sched[bay_id], nb, release, due, proc)
                    if entry is None:
                        continue
                    sc = score(0.0, bay_id, top_y=cy + blk_bb[3],
                               entry=entry, exit_t=entry + proc)
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, entry + proc)
                    bay_zero = True
                    break
                if bay_zero:
                    break
            if bay_zero and w1_dominant:
                break
        if best is not None:
            return best

    # -- Pass B: least-tardy placement ------------------------------------
    lb = release if forced else max(release, due - proc)
    if dense:
        for bay_id in bay_order:
            bay = bays[bay_id]
            if raster is not None:
                slot = _find_earliest_slot_raster(
                    bay, bay_id, sched[bay_id], bi, blk, orients, lb, proc,
                    raster, score_pos=True,
                    time_cap=min(slot_time_cap, 16), pos_cap=slot_pos_cap)
            else:
                slot = _find_earliest_slot(bay, sched[bay_id], bi, blk, orients,
                                           lb, proc, time_cap=slot_time_cap,
                                           pos_cap=slot_pos_cap)
            if slot is None:
                continue
            oi, cx, cy, entry = slot
            exit_t = entry + proc
            blk_bb = _orient_bbox(blk, oi)
            sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3],
                       entry=entry, exit_t=exit_t)
            if sc < best_score:
                best_score = sc
                best = (bay_id, cx, cy, oi, entry, exit_t)
    else:
        for bay_id in bay_order:
            bay = bays[bay_id]
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=12):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_tardy_slot(bay, sched[bay_id], nb, release, due,
                                             proc, tardy_cap=tardy_cap)
                    if entry is None:
                        continue
                    exit_t = entry + proc
                    sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3],
                               entry=entry, exit_t=exit_t)
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, exit_t)
    return best


def _force_place(bi, blk, bays, sched):
    prefs = blk["bay_preferences"]
    release = int(blk["release_time"])
    proc = int(blk["processing_time"])
    for bay_id in sorted(range(len(bays)), key=lambda j: prefs[j], reverse=True):
        bay = bays[bay_id]
        for oi in range(len(blk["shape"])):
            lx0, ly0, lx1, ly1 = _orient_bbox(blk, oi)
            px_lo, px_hi = math.ceil(-lx0), math.floor(bay.width - lx1)
            py_lo, py_hi = math.ceil(-ly0), math.floor(bay.height - ly1)
            if px_lo > px_hi or py_lo > py_hi:
                continue
            px, py = max(0, px_lo), max(0, py_lo)
            entry = _empty_bay_entry(sched[bay_id], release, proc)
            return (bay_id, px, py, oi, entry, entry + proc)
    raise RuntimeError(f"block {bi} cannot be placed")


# -----------------------------------------------------------------------------
# Construction over a given order
# -----------------------------------------------------------------------------

def _add(sched, bay_loads, assignments, bi, blk, place):
    bay_id, cx, cy, oi, entry, exit_t = place
    nb = _mkblock(bi, blk, cx, cy, oi)
    sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
    bay_loads[bay_id] += blk["workload"]
    assignments[bi] = {
        "block_id": bi, "bay_id": bay_id, "x": int(cx), "y": int(cy),
        "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
    }


def _construct(prob_info, order, bays, bay_u, w1, w2, w3, t_start, deadline,
               forced=False, util_gamma=0.0):
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    assignments = {}
    n = len(order)
    for idx, bi in enumerate(order):
        blk = blocks_data[bi]
        time_left = deadline - time.time()
        remaining = n - idx
        dense = time_left > 0 and (time_left / remaining) > 0.25
        place = _place_block(bi, blk, bays, sched, bay_loads, bay_u,
                             w1, w2, w3, dense=dense, forced=forced,
                             util_gamma=util_gamma)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        _add(sched, bay_loads, assignments, bi, blk, place)
    return assignments


# -----------------------------------------------------------------------------
# Safe monotone improver: destroy worst-tardy + neighbors, repair EDD-earliest,
# keep ONLY if verified-feasible AND strictly better.
# -----------------------------------------------------------------------------

def _rebuild_sched(assignments, blocks_data, n_bays):
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    for bi, a in assignments.items():
        nb = _mkblock(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
        sched[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"], nb.bounding_rect()))
        bay_loads[a["bay_id"]] += blocks_data[bi]["workload"]
    return sched, bay_loads


def _repair_order(removed, blocks_data, mode, rng):
    """Diversified reinsertion orderings — different orderings unlock different
    packings, which is what lets the improver escape EDD-only local optima."""
    rem = list(removed)
    if mode == 0:      # EDD
        rem.sort(key=lambda i: (blocks_data[i]["due_date"],
                                blocks_data[i]["processing_time"],
                                -_min_area(blocks_data[i])))
    elif mode == 1:    # EDD with tie jitter
        rem.sort(key=lambda i: (blocks_data[i]["due_date"] + rng.uniform(-0.5, 0.5),
                                blocks_data[i]["processing_time"]))
    elif mode == 2:    # earliest release first, then due
        rem.sort(key=lambda i: (blocks_data[i]["release_time"],
                                blocks_data[i]["due_date"]))
    else:              # largest area first within due buckets
        rem.sort(key=lambda i: (blocks_data[i]["due_date"], -_min_area(blocks_data[i])))
    return rem


def _destroy_tardy(cur, blocks_data, k, rng):
    tardy = [(bi, a["exit_time"] - blocks_data[bi]["due_date"])
             for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    if not tardy:
        return None
    tardy.sort(key=lambda z: -z[1])
    removed = set(bi for bi, _ in tardy[:k])
    bays_touched = set(cur[bi]["bay_id"] for bi in removed)
    early_pool = sorted(
        [bi for bi, a in cur.items()
         if bi not in removed and a["bay_id"] in bays_touched],
        key=lambda bi: cur[bi]["entry_time"])
    for bi in early_pool[:k]:
        removed.add(bi)
    return removed


def _destroy_bay_rebalance(cur, blocks_data, bays, rng):
    """v9: cross-bay rebalancing destroy (idea #3 from heuristic_7/8).

    Diagnosis: on the congested/plateaued instances the greedy fills each block's
    *preferred* bay to local zero-tardiness, congesting it so that LATER blocks in
    that bay spill into large tardiness -- and v8's improver, which only ever
    re-packs WITHIN the same bays, cannot undo it. This operator targets the bay
    carrying the most tardiness, removes its worst tardy blocks together with a few
    *movable* (slack, non-tardy) neighbours whose windows overlap them, and returns
    a priority order that reinserts the movable blocks FIRST (so they can relocate
    to under-loaded bays) and the tardy blocks LAST (so they reclaim the freed
    space). The repair uses a load-ascending bay order to actually spread the load.
    Only kept if the official internal objective strictly improves, so paying the
    w3 preference penalty is accepted only when the w1 tardiness saving outweighs
    it (which is exactly the regime w1 >> w3 on these instances)."""
    n_bays = len(bays)
    if n_bays < 2:
        return None, None
    bay_tard = [0.0] * n_bays
    for bi, a in cur.items():
        d = a["exit_time"] - blocks_data[bi]["due_date"]
        if d > 0:
            bay_tard[a["bay_id"]] += d
    tb = max(range(n_bays), key=lambda j: bay_tard[j])
    if bay_tard[tb] <= 0:
        return None, None
    tardy = [(bi, a) for bi, a in cur.items()
             if a["bay_id"] == tb and a["exit_time"] > blocks_data[bi]["due_date"]]
    tardy.sort(key=lambda z: -(z[1]["exit_time"] - blocks_data[z[0]]["due_date"]))
    tardy = tardy[:4]
    tardy_ids = [bi for bi, _ in tardy]
    windows = [(a["entry_time"], a["exit_time"]) for _, a in tardy]
    # Movers = other blocks in tb overlapping the tardy windows, ranked
    # least-tardy-first (cheapest to relocate to an under-loaded bay). Tardy-
    # capable: the STUCK optima (prob_27/30/35/39) are fully tardy, so only tardy
    # movers can attack them. Safety on the round-starved prob_38 comes from a
    # HIGH convergence gate at the call site (only after a long genuine plateau,
    # which prob_38 -- still improving via kicks -- rarely reaches).
    movers = []
    for bi, a in cur.items():
        if bi in tardy_ids or a["bay_id"] != tb:
            continue
        for lo, hi in windows:
            if a["entry_time"] < hi and a["exit_time"] > lo:
                t = max(0, a["exit_time"] - blocks_data[bi]["due_date"])
                movers.append((t, bi))
                break
    movers.sort(key=lambda z: z[0])  # least-tardy (most relocatable) first
    mover_ids = [bi for _, bi in movers[:6]]
    if not mover_ids:
        return None, None
    removed = set(tardy_ids) | set(mover_ids)
    priority = mover_ids + tardy_ids  # relocate movers first, then reclaim space
    return removed, priority


def _destroy_window(cur, blocks_data, rng):
    """Remove ALL blocks active in a sampled congested time window of one bay,
    so the bottleneck window is re-packed wholesale (structural rescheduling)."""
    tardy = [bi for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    seed = rng.choice(tardy) if tardy else rng.choice(list(cur))
    bay = cur[seed]["bay_id"]
    center = cur[seed]["entry_time"]
    # window half-width ~ a few typical processing times
    procs = [blocks_data[bi]["processing_time"] for bi in cur]
    half = max(1, int(sorted(procs)[len(procs) // 2]) * 2)
    lo, hi = center - half, center + half
    removed = set(bi for bi, a in cur.items()
                  if a["bay_id"] == bay and a["entry_time"] < hi and a["exit_time"] > lo)
    return removed if removed else {seed}


# -----------------------------------------------------------------------------
# v14: JOINT WINDOW REPACK (LNS-XL). The geometry lever -- coordinated interlock
# needs coordinated placement, so destroy a whole congested (bay,window) and
# rebuild ALL of it jointly with multi-order greedy raster placement, holding the
# un-destroyed neighbours fixed. Obj-gated by the caller (never accepted worse).
# -----------------------------------------------------------------------------

def _repack_window(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng,
                   deadline, forced=False, k_orders=4, max_destroy=30):
    """Pick the most congested (bay, time-window) from `src`, destroy every block
    of that bay whose [entry,exit) intersects it, and rebuild the destroyed set
    jointly (k trial orders, greedy earliest-feasible raster placement against the
    fixed un-destroyed neighbours). Blocks that fail to place in the bay go through
    the normal all-bay repair. Returns a NEW complete assignment dict (candidate),
    or None; the caller obj-gates acceptance. Never mutates `src`."""
    if raster is None or not _HAVE_NUMPY:
        return None
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    n = len(blocks_data)
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    procs = [int(b["processing_time"]) for b in blocks_data]
    areas = [_min_area(b) for b in blocks_data]
    pbar = max(1.0, sum(procs) / max(1, n))
    win_w = max(1, int(2 * pbar))
    sched, bay_loads = _rebuild_sched(src, blocks_data, n_bays)

    # -- congestion metric: candidate windows keyed at tardy/delayed entries -----
    cands = []
    for bj in range(n_bays):
        items = sched[bj]
        if len(items) < 2:
            continue
        centers = set()
        for (blk, e, ex, bb) in items:
            bi = blk.block_id
            if ex > dues[bi] or e > rels[bi]:   # tardy OR admission-delayed
                centers.add(int(e))
        for c in centers:
            lo, hi = c, c + win_w
            score = 0.0
            for (blk, e, ex, bb) in items:
                ov = min(hi, ex) - max(lo, e)
                if ov > 0:
                    bi = blk.block_id
                    score += areas[bi] * ov + w1 * max(0, ex - dues[bi])
            cands.append((score, bj, lo, hi))
    if not cands:
        return None
    cands.sort(key=lambda z: -z[0])
    # rotate among the top few windows for diversity across repack rounds
    pick = cands[rng.randrange(min(3, len(cands)))] if rng is not None else cands[0]
    _, bj, lo, hi = pick
    bay = bays[bj]
    items = sched[bj]
    destroyed = [it[0].block_id for it in items if it[1] < hi and it[2] > lo]
    if len(destroyed) < 2:
        return None
    if len(destroyed) > max_destroy:
        destroyed.sort(key=lambda bi: -(max(0, src[bi]["exit_time"] - dues[bi])
                                        + 1.0 / (1 + abs(src[bi]["entry_time"] - lo))))
        destroyed = destroyed[:max_destroy]
    dset = set(destroyed)
    fixed_bay = [it for it in items if it[0].block_id not in dset]

    # -- trial orders over the destroyed set ------------------------------------
    def feas_count(bi):
        blk = blocks_data[bi]
        actives = [(it[0].block_id, it[0].orient_idx, it[0].x, it[0].y)
                   for it in fixed_bay]
        tot = 0
        for oi in _unique_orients(blk):
            if not _orient_fits(blk, oi, bay):
                continue
            feas, _cx, _cy, _fp = raster.scan_scoped(bj, actives, bi, oi)
            if feas is not None:
                tot += int(feas.sum())
        return tot

    orders = [
        sorted(destroyed, key=lambda bi: -areas[bi]),                       # area-desc
        sorted(destroyed, key=lambda bi: (dues[bi], procs[bi])),            # due-asc
        sorted(destroyed, key=lambda bi: (dues[bi] - procs[bi] - rels[bi])),  # min-slack
        sorted(destroyed, key=feas_count),                                  # most-constrained
    ][:k_orders]

    best = None  # ((num_failed, tard), placements, failed)
    for od in orders:
        if time.time() > deadline:
            break
        work_bay = list(fixed_bay)
        placements = {}
        failed = []
        for bi in od:
            blk = blocks_data[bi]
            proc = procs[bi]
            slot = _find_earliest_slot_raster(
                bay, bj, work_bay, bi, blk, _unique_orients(blk),
                rels[bi], proc, raster, score_pos=True)
            if slot is None:
                failed.append(bi)
                continue
            oi, x, y, entry = slot
            nb = _mkblock(bi, blk, x, y, oi)
            work_bay.append((nb, entry, entry + proc, nb.bounding_rect()))
            placements[bi] = (bj, x, y, oi, entry, entry + proc)
        tard = 0.0
        for bi, pl in placements.items():
            tard += max(0, pl[5] - dues[bi])
        key = (len(failed), tard)
        if best is None or key < best[0]:
            best = (key, placements, failed)
    if best is None:
        return None
    _key, placements, failed = best

    # -- assemble the candidate assignment --------------------------------------
    work = {bi: dict(a) for bi, a in src.items() if bi not in dset}
    for bi, (bjp, x, y, oi, en, ex) in placements.items():
        work[bi] = {"block_id": bi, "bay_id": bjp, "x": int(x), "y": int(y),
                    "orient_idx": oi, "entry_time": int(en), "exit_time": int(ex)}
    if failed:
        sched2, loads2 = _rebuild_sched(work, blocks_data, n_bays)
        for bi in sorted(failed, key=lambda i: (dues[i], -areas[i])):
            blk = blocks_data[bi]
            place = _place_block(bi, blk, bays, sched2, loads2, bay_u, w1, w2, w3,
                                 forced=forced, slot_time_cap=40, slot_pos_cap=30,
                                 raster=raster)
            if place is None:
                place = _force_place(bi, blk, bays, sched2)
            _add(sched2, loads2, work, bi, blk, place)
    if len(work) != n:
        return None
    return work


def _improve(prob_info, assignments, bays, bay_u, w1, w2, w3, deadline, forced,
             seed=4242, sa=False, on_best=None, inbox=None, raster=None,
             repack_every=0):
    """Basin-hopping destroy/repair. Tracks `best` separately from the working
    `cur`; returns `best` -> monotone in the RESULT. Diversifies destroy mode and
    repair ordering, and applies an escape "kick" (a larger destroy accepted even
    if worse) after a plateau, to break out of local structures the pure
    hill-climber (v3) gets stuck in (prob_39). Compares by the cheap internal
    objective; the caller verifies the returned solution officially.
    v10: `seed` diversifies portfolio workers; `sa` enables simulated-annealing
    acceptance of worse repairs (explorer worker); `on_best(obj, assign)` streams
    new incumbents to the parent process."""
    blocks_data = prob_info["blocks"]
    n = len(assignments)
    n_bays = len(bays)
    best_assign = {k: dict(v) for k, v in assignments.items()}
    best_obj, best_o1, _, _ = _objective(best_assign, blocks_data, bays, bay_u, w1, w2, w3)
    cur = {k: dict(v) for k, v in best_assign.items()}
    cur_obj = best_obj

    def _tardy_count(assign):
        return sum(1 for bi, a in assign.items()
                   if a["exit_time"] > blocks_data[bi]["due_date"])

    best_tardy = _tardy_count(best_assign)
    rng = random.Random(seed)
    # SA temperature: a small fraction of the current objective so that typical
    # repair deltas (a few tardy time-units * w1) are accepted early on, with
    # geometric cooling and a reheat on long stalls.
    T0 = max(1.0, 0.01 * best_obj) if sa else 0.0
    T = T0
    rounds = 0
    no_improve = 0      # for kick triggering (kicks reset this)
    since_best = 0      # rounds since best improved (kicks do NOT reset this)
    since_o1 = 0        # rounds since best TARDINESS (obj1) improved -- the real
    #                     convergence signal (tiny obj2/obj3 gains keep resetting
    #                     since_best on forced instances, hiding the obj1 stall)
    n_restart = 0; n_rebal = 0   # debug fire counters (OGC_DEBUG)
    KICK = 6
    REBAL_AFTER = 10**9   # v9: cross-bay rebalance OFF (couldn't crack stuck optima)
    RESTART_AFTER = 10**9 # v9: partial-restart OFF (improver too round-starved to fire)
    RESTART_EVERY = 25    # cadence of restarts once past RESTART_AFTER
    RESTART_FRAC = 0.45   # fraction of the champion rebuilt on a restart
    # Small destroy sets + capped repair search => many more rounds/sec, which is
    # what makes the improver bite under real (and contended) compute budgets.
    while time.time() < deadline:
        # v11 island model: adopt a better global incumbent from the parent.
        # (W0/v9-replica never gets an inbox, so the anchor stays byte-exact.)
        if inbox is not None:
            try:
                while True:
                    o_in, a_in = inbox.get_nowait()
                    if o_in < best_obj - 1e-9:
                        best_obj = o_in
                        best_assign = {k: dict(v) for k, v in a_in.items()}
                        best_tardy = _tardy_count(best_assign)
                        cur = {k: dict(v) for k, v in a_in.items()}
                        cur_obj = o_in
                        no_improve = 0
                        since_best = 0
            except Exception:
                pass
        # Early stop: nothing tardy left and the search has stalled -> the obj2/
        # obj3 part is exhausted; stop instead of burning the rest of the budget.
        if best_tardy == 0 and since_best > 40:
            break
        rounds += 1
        # v14: JOINT WINDOW REPACK round (obj-gated, tardy instances only). Every
        # `repack_every`-th round, destroy+rebuild a whole congested (bay,window)
        # jointly instead of the classic scattered destroy/repair. repack_every==0
        # (W0 + v13-basin tickets) skips this entirely -> byte-exact v13.
        if (repack_every > 0 and raster is not None and best_tardy > 0
                and rounds % repack_every == 0):
            try:
                work = _repack_window(prob_info, cur, bays, bay_u, w1, w2, w3,
                                      raster, rng, deadline, forced=forced)
            except Exception:
                work = None
            if work is not None and len(work) == n:
                new_obj, new_o1, _, _ = _objective(work, blocks_data, bays,
                                                    bay_u, w1, w2, w3)
                if new_obj < cur_obj - 1e-9:
                    cur = work
                    cur_obj = new_obj
                if new_obj < best_obj - 1e-9:
                    best_obj = new_obj
                    best_assign = {k: dict(v) for k, v in work.items()}
                    best_tardy = _tardy_count(best_assign)
                    no_improve = 0
                    since_best = 0
                    if on_best is not None:
                        on_best(best_obj, best_assign)
                else:
                    no_improve += 1
                    since_best += 1
                if new_o1 < best_o1 - 1e-9:
                    best_o1 = new_o1
                    since_o1 = 0
                else:
                    since_o1 += 1
                continue
        kick = no_improve >= KICK
        spread = False       # v9: repair with a load-ascending bay order (rebalance)
        priority = None      # v9: explicit reinsertion order (movers first)
        # v9: DEEP PARTIAL RESTART -- once the search has been stalled for a long
        # time (since_best >= RESTART_AFTER, i.e. genuinely converged with budget
        # to spare, which the round-starved giants NEVER reach so they are
        # untouched), periodically blow away a large random fraction of the
        # CHAMPION and rebuild it from a randomized order, accepting the result
        # even if worse. This is a big basin-hop: the deterministic descent
        # otherwise re-lands in the exact same local optimum every version
        # (prob_27/39/30/35 are byte-identical across v3..v8), and only a large
        # perturbation of the incumbent can reach a different basin.
        restart = (since_o1 >= RESTART_AFTER and since_o1 % RESTART_EVERY == 0)
        src = cur
        if restart:
            n_restart += 1
            src = best_assign
            removed = set(rng.sample(list(src), max(1, int(n * RESTART_FRAC))))
        elif kick:
            removed = _destroy_window(cur, blocks_data, rng)
            extra = rng.sample(list(cur), min(len(cur), 6))
            removed = set(removed) | set(extra)
        elif n_bays >= 2 and since_best >= REBAL_AFTER:
            # v9: cross-bay rebalancing fires ONLY after the improver has truly
            # CONVERGED (>= REBAL_AFTER rounds since the incumbent last improved),
            # never during the descent. This is the hard-won safety property: the
            # big round-starved instances (prob_38 n=250, prob_39 n=250) keep
            # improving in-bay for the WHOLE budget, so `since_best` never reaches
            # REBAL_AFTER -> rebalance never fires -> those instances are byte-for-
            # byte v8 (measured: an eager plateau trigger stole their descent
            # rounds and regressed prob_38 by ~11M). Instances that genuinely
            # converge with budget to spare (prob_27/30/33) reach the gate and get
            # the cross-bay move -- pure upside, since post-convergence in-bay
            # rounds are otherwise wasted. Relieves the most-tardy bay by
            # relocating slack neighbours to under-loaded bays.
            removed, priority = _destroy_bay_rebalance(cur, blocks_data, bays, rng)
            if removed:
                spread = True
            else:
                k = min(6, max(2, n // 40))
                removed = _destroy_tardy(cur, blocks_data, k, rng)
                if removed is None:
                    removed = _destroy_window(cur, blocks_data, rng)
        elif rounds % 3 == 0:
            removed = _destroy_window(cur, blocks_data, rng)
        else:
            k = min(6, max(2, n // 40))
            removed = _destroy_tardy(cur, blocks_data, k, rng)
            if removed is None:
                removed = _destroy_window(cur, blocks_data, rng)
        if not removed:
            break

        work = {bi: dict(a) for bi, a in src.items() if bi not in removed}
        sched, bay_loads = _rebuild_sched(work, blocks_data, n_bays)
        if spread and priority:
            rem_order = [bi for bi in priority if bi in removed]
        elif restart:
            # rebuild the perturbed champion from a fresh randomized order so the
            # descent re-lands somewhere new rather than in the same basin.
            rem_order = _repair_order(removed, blocks_data, rng.randint(0, 3), rng)
            rng.shuffle(rem_order)
        else:
            rem_order = _repair_order(removed, blocks_data, rounds % 4, rng)
        ok = True
        for bi in rem_order:
            if time.time() > deadline:
                ok = False; break
            blk = blocks_data[bi]
            bo = sorted(range(n_bays), key=lambda j: bay_loads[j]) if spread else None
            # v13: raster-windowed repair (density lever) when the instance is
            # forced OR the incumbent still has tardiness (schedule/density-
            # limited mid-tier); zero-tardiness easies keep the cheap AABB
            # repair (raster costs more per move and buys nothing there).
            use_raster = raster if (forced or best_tardy > 0) else None
            place = _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                                 forced=forced, slot_time_cap=40, slot_pos_cap=30,
                                 bay_order=bo, raster=use_raster)
            if place is None:
                place = _force_place(bi, blk, bays, sched)
            _add(sched, bay_loads, work, bi, blk, place)
        if not ok or len(work) != n:
            continue
        new_obj, new_o1, _, _ = _objective(work, blocks_data, bays, bay_u, w1, w2, w3)
        accept = new_obj < cur_obj - 1e-9 or kick or restart
        if not accept and sa and T > 1e-9:
            delta = new_obj - cur_obj
            if delta / T < 30 and rng.random() < math.exp(-delta / T):
                accept = True
        if accept:
            cur = work
            cur_obj = new_obj
        if sa:
            T *= 0.995
            if since_best >= 60:
                T = T0  # reheat after a long stall
        if new_obj < best_obj - 1e-9:
            best_obj = new_obj
            best_assign = {k: dict(v) for k, v in work.items()}
            best_tardy = _tardy_count(best_assign)
            no_improve = 0
            since_best = 0
            if on_best is not None:
                on_best(best_obj, best_assign)
        else:
            no_improve = 0 if (kick or restart) else no_improve + 1
            since_best += 1
        if new_o1 < best_o1 - 1e-9:
            best_o1 = new_o1
            since_o1 = 0
        else:
            since_o1 += 1
    import os as _os
    if _os.environ.get("OGC_DEBUG"):
        print(f"[improve] rounds={rounds} n_restart={n_restart} n_rebal={n_rebal} "
              f"best_o1={best_o1} since_o1={since_o1}", flush=True)
    return best_assign, best_obj


# -----------------------------------------------------------------------------
# Build operations dict (verbatim from v2)
# -----------------------------------------------------------------------------

def _build_operations(assignments):
    buckets = {}
    for a in assignments.values():
        buckets.setdefault(int(a["exit_time"]), []).append(
            (0, "EXIT", a["block_id"], a["bay_id"], None, None, None))
        buckets.setdefault(int(a["entry_time"]), []).append(
            (1, "ENTRY", a["block_id"], a["bay_id"], a["x"], a["y"], a["orient_idx"]))
    operations = {}
    for t in sorted(buckets):
        ops = sorted(buckets[t], key=lambda r: (r[0], r[2]))
        lst = []
        for _, kind, bid, bay, x, y, oi in ops:
            op = {"type": kind, "block_id": bid, "bay_id": bay}
            if kind == "ENTRY":
                op["x"], op["y"], op["orient_idx"] = x, y, oi
            lst.append(op)
        operations[str(t)] = lst
    return operations


def _empty_bay_solution(prob_info, bays):
    fallback = {}
    sched0 = [[] for _ in range(len(bays))]
    for bi, blk in enumerate(prob_info["blocks"]):
        bay_id, px, py, oi, entry, exit_t = _force_place(bi, blk, bays, sched0)
        sched0[bay_id].append(
            (Block(block_id=bi, block_data=blk, x=px, y=py, orient_idx=oi),
             entry, exit_t))
        fallback[bi] = {
            "block_id": bi, "bay_id": bay_id, "x": px, "y": py,
            "orient_idx": oi, "entry_time": entry, "exit_time": exit_t,
        }
    return fallback


# -----------------------------------------------------------------------------
# Forced detection (verbatim from v2)
# -----------------------------------------------------------------------------

def _is_forced(prob_info, bays):
    cap = sum(b.width * b.height for b in bays)
    ev = {}
    for b in prob_info["blocks"]:
        r = b["release_time"]; du = b["due_date"]; p = b["processing_time"]
        ms = du - p; me = r + p
        if ms < me:
            a = _min_area(b)
            ev[ms] = ev.get(ms, 0.0) + a
            ev[me] = ev.get(me, 0.0) - a
    run = 0.0; peak = 0.0
    for t in sorted(ev):
        run += ev[t]; peak = max(peak, run)
    return peak > cap


# -----------------------------------------------------------------------------
# v9 search pipeline (exact replica). Used BOTH by the single-thread fallback
# and by portfolio worker W0: the improver is extremely basin-sensitive (on
# prob_31, EDD+improve plateaus at 19.09M while v9's jittered-construction
# improve reached 17.64M), so preserving v9's exact multi-start rng stream and
# two-pass improver is what guarantees v10 never loses a v9 result.
# -----------------------------------------------------------------------------

def _v9_search(prob_info, timelimit, t_start, push=None):
    """Runs v9's whole search; returns the candidate list [(obj, assign)] and
    streams every candidate/incumbent through push(obj, assign) if given."""
    # Reserve a slice at the end for the official feasibility check(s).
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    search_deadline = t_start + timelimit * 0.95 - reserve
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w1 = prob_info.get("weights", {}).get("w1", 1.0)
    w2 = prob_info.get("weights", {}).get("w2", 1.0)
    w3 = prob_info.get("weights", {}).get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)

    def iobj(assign):
        return _objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]

    # All candidates scored by the CHEAP internal objective; the single best is
    # verified once at the end (no per-strategy check_feasibility -> no overrun).
    candidates = []  # (internal_obj, assign)

    def emit(assign):
        o = iobj(assign)
        candidates.append((o, assign))
        if push is not None:
            push(o, assign)

    edd_assign = None  # the plain-EDD construction (forced): always improved so
    #                    v9 never regresses below v8 on improver-dependent instances

    search_window = search_deadline - t_start
    edd = _edd_order(blocks_data)
    cong = _congestion_order(blocks_data)

    if forced:
        # v9: MULTI-START construction for forced instances. Key finding: on the
        # stuck instances (prob_27/30/35 -- byte-identical across v3..v8) the
        # improver contributes NOTHING; their objective IS the deterministic EDD
        # construction, and the improver's ~70 wasted seconds never beat it. But
        # a *jittered* EDD order yields a strictly better construction on several
        # of them (prob_30 14.39M->12.95M, prob_27 52.40M->51.47M). So instead of
        # one EDD construction + a useless improver, run EDD plus as many dense
        # jittered-EDD constructions as fit in ~70% of the window (keeping the
        # best), then let the improver use the remaining ~30% (which still helps
        # the genuinely round-starved giants like prob_38/39). Each construction
        # is dense (passed the full deadline) and finishes in its natural time, so
        # big instances fit ~1 (≈ old behavior) while small ones fit 2-3.
        rng_c = random.Random(2026)
        t_first = search_window  # conservative default if the first build fails
        try:
            t0c = time.time()
            assign = _construct(prob_info, edd, bays, bay_u, w1, w2, w3,
                                t_start, search_deadline, forced=True)
            t_first = time.time() - t0c
            edd_assign = assign
            emit(assign)
        except Exception:
            pass
        # Multi-start ONLY on "construction-cheap" instances -- those whose first
        # dense build took a small fraction of the window. Rationale + safety:
        #  * On such instances the improver is nearly useless (the stuck optima
        #    prob_27/30/35 are byte-identical across v3..v8), so spare budget is
        #    far better spent on more constructions; jittered EDD orders find
        #    strictly better constructions (prob_30 -2.6M, prob_35 -3.2M).
        #  * The round-starved giants (prob_38/39, n=250) have a SLOW first build
        #    (a large fraction of the window), so they are skipped and keep their
        #    full improver share == v8 (measured: forcing a jitter on prob_38 only
        #    steals descent time). The gate is a *fraction* of the window, so it
        #    adapts to the budget: at larger time limits a giant's build is a
        #    smaller fraction and multi-start turns on once the improver has room.
        # 9b: rotate through DIVERSE base orders. Measured: the largest-footprint-
        # first (AREA) order STRICTLY beats EDD on the stuck giants (prob_27
        # 52.4M->49.7M, prob_39 29.8M->27.1M, prob_26 22.7M->19.4M) -- placing the
        # hardest-to-fit blocks while the bays are empty reaches a far better
        # geometric basin. (SLACK was worse everywhere -> dropped.) Cap the
        # construction phase at CON_FRAC of the window so the improver keeps a
        # guaranteed share (>= 1-CON_FRAC): this prevents the regressions seen when
        # constructions starved improver-dependent instances. At larger time
        # limits this window fits EDD+AREA even on the n=250 giants (needs ~300s),
        # which is where the AREA gains live.
        CON_FRAC = 0.55
        con_cap = t_start + search_window * CON_FRAC
        plan = [
            lambda: _area_order(blocks_data),
            lambda: _edd_order(blocks_data, jitter=rng_c),
            lambda: _area_order(blocks_data, jitter=rng_c),
            lambda: _edd_order(blocks_data, jitter=rng_c),
            lambda: _area_order(blocks_data, jitter=rng_c),
        ]
        gi = 0
        while time.time() + t_first < con_cap:
            try:
                order = plan[gi % len(plan)]()
                gi += 1
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=True)
                emit(assign)
            except Exception:
                break
    else:
        # Uncongested: keep v3's strong behavior -- thorough congestion+zero-slot
        # Pass A primary, EDD secondary, then bounded EDD-jitter perturbations.
        for order, fc in [(cong, False), (edd, True)]:
            if time.time() >= search_deadline:
                break
            try:
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=fc)
                emit(assign)
            except Exception:
                pass
        rng = random.Random(2026)
        stale = 0
        best_so_far = min((c[0] for c in candidates), default=float("inf"))
        while time.time() < search_deadline and stale < 4:
            try:
                order = _edd_order(blocks_data, jitter=rng)
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=forced)
                emit(assign)
                o = candidates[-1][0]
                if o < best_so_far - 1e-9:
                    best_so_far = o; stale = 0
                else:
                    stale += 1
            except Exception:
                break

    # Basin-hopping improver. REGRESSION-SAFE two-pass scheme on forced instances:
    #   pass 1 improves the PLAIN EDD construction (== v8's result, so v9 can never
    #          regress below v8 on improver-dependent instances like prob_33/25/37
    #          whose jittered constructions otherwise led the improver to a worse
    #          local optimum);
    #   pass 2 improves the best OTHER construction ONLY IF its RAW objective
    #          already beats pass 1's result -- true on the giants where AREA wins
    #          outright (so they keep their full improver-polished gain), false on
    #          the improver-dependent instances (so no time is wasted / no worse
    #          basin is chosen). Each pass gets half the remaining budget.
    # Non-forced instances keep the original single-pass improve-the-best.
    if candidates and time.time() < search_deadline:
        try:
            candidates.sort(key=lambda c: c[0])
            if forced and edd_assign is not None:
                # Uneven split: the EDD pass only needs to reach v8's value (which
                # v8 did with little improver time), so give it just 35% and leave
                # 65% for the AREA pass so the giants keep their full polish.
                mid = time.time() + (search_deadline - time.time()) * 0.35
                r1, o1 = _improve(prob_info, edd_assign, bays, bay_u,
                                  w1, w2, w3, mid, forced, on_best=push)
                candidates.append((o1, r1))
                if push is not None:
                    push(o1, r1)
                for o_raw, a_raw in sorted(candidates, key=lambda c: c[0]):
                    if a_raw is edd_assign or a_raw is r1:
                        continue
                    if o_raw < o1 - 1e-9:  # a raw construction already beats EDD+improve
                        r2, o2 = _improve(prob_info, a_raw, bays, bay_u,
                                          w1, w2, w3, search_deadline, forced,
                                          on_best=push)
                        candidates.append((o2, r2))
                        if push is not None:
                            push(o2, r2)
                    break
            else:
                improved, iobj_imp = _improve(prob_info, candidates[0][1], bays, bay_u,
                                              w1, w2, w3, search_deadline, forced,
                                              on_best=push)
                candidates.append((iobj_imp, improved))
                if push is not None:
                    push(iobj_imp, improved)
        except Exception:
            pass
    return candidates


def _algorithm_single(prob_info, timelimit=60, t_start=None):
    """v9 pipeline: search, then verify best-first (no-multiprocessing fallback)."""
    if t_start is None:
        t_start = time.time()
    _reset_caches()  # v7: caches hold instance-specific geometry; never share.
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)
    try:
        candidates = _v9_search(prob_info, timelimit, t_start)
    except Exception:
        candidates = []

    # Verify candidates best-first; return the first officially-feasible one.
    fallback = _empty_bay_solution(prob_info, bays)
    candidates.append((_objective(fallback, blocks_data, bays, bay_u,
                                  w1, w2, w3)[0], fallback))
    candidates.sort(key=lambda c: c[0])
    for _, assign in candidates:
        sol = {"operations": _build_operations(assign)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            continue
        if res["feasible"]:
            return sol
    # Last resort: empty-bay (structurally feasible).
    return {"operations": _build_operations(fallback)}


# =============================================================================
# v12 RASTER GEOMETRY ENGINE (numpy, conservative)
# =============================================================================

class _Raster:
    """Per-instance conservative raster occupancy engine (numpy only).

    For every (block_id, orient_idx) it lazily builds a stack of per-layer
    boolean masks on the unit grid: mask[l][i, j] is set iff layer l's polygon
    *touches* the closed unit square of local cell (cx0+j, cy0+i). Because the
    mask is a superset of the polygon's footprint, two blocks whose masks share
    no cell cannot have any positive-area polygon overlap -- so a mask that is
    disjoint from the occupancy union is provably collision-free AND crane-clear
    (entry and exit obey the same j>=k prism rule; disjointness at every needed
    layer proves both). It is therefore SOUND as a pre-filter: it may reject a
    feasible edge-touching placement (conservative) but never accepts an
    infeasible one. Positions it returns are still gated by the exact cached
    `_can_place` (for reverse exit-blocking against present blocks) before use.

    Per-bay per-layer occupancy grids (int16, HxW) are updated incrementally on
    add()/remove(); `scan()` returns a boolean (R,C) grid of all entry-clear
    anchor windows against the *current* occupancy (crane clearance = for each
    moving layer k, disjoint from the union of present layers >= k)."""

    def __init__(self, prob_info, bays):
        self.blocks_data = prob_info["blocks"]
        self.bays = bays
        self.W = [int(b.width) for b in bays]
        self.H = [int(b.height) for b in bays]
        self._mask = {}                       # (bi, oi) -> (mask, cx0, cy0)
        self._fpm = {}                        # (bi, oi) -> footprint-union mask
        self.occ = [dict() for _ in bays]     # bay -> {layer: int16 grid (H,W)}
        self.ver = [0 for _ in bays]          # occupancy version per bay
        self._uni = [None for _ in bays]      # bay -> (ver, [union_ge grids])
        # v13 throughput caches (transparent -- same numeric results as v12):
        self._scan = [dict() for _ in bays]   # bay -> {(bi,oi): (ver, feas,cx0,cy0)}
        self._fp = [None for _ in bays]       # bay -> (ver, footprint bool grid)

    # -- mask construction -----------------------------------------------------
    def mask(self, bi, oi):
        key = (bi, oi)
        m = self._mask.get(key)
        if m is not None:
            return m
        import shapely
        layers = _resolve_layers(self.blocks_data[bi]["shape"][oi]["layers"])
        allv = [v for L in layers for v in L]
        if not allv:
            m = (_np.zeros((1, 1, 1), dtype=_np.uint8), 0, 0)
            self._mask[key] = m
            return m
        xs = [v[0] for v in allv]; ys = [v[1] for v in allv]
        cx0 = int(math.floor(min(xs))); cx1 = int(math.ceil(max(xs))) - 1
        cy0 = int(math.floor(min(ys))); cy1 = int(math.ceil(max(ys))) - 1
        if cx1 < cx0: cx1 = cx0
        if cy1 < cy0: cy1 = cy0
        MW = cx1 - cx0 + 1; MH = cy1 - cy0 + 1
        nl = len(layers)
        mask = _np.zeros((nl, MH, MW), dtype=_np.uint8)
        cxs = _np.arange(cx0, cx1 + 1)
        cys = _np.arange(cy0, cy1 + 1)
        CX, CY = _np.meshgrid(cxs, cys)       # (MH, MW)
        boxes = shapely.box(CX, CY, CX + 1, CY + 1)
        for l, L in enumerate(layers):
            p = _poly_from_verts(L)
            if p is None:
                continue
            # conservative: a cell is occupied if its unit box touches the poly
            mask[l] = shapely.intersects(boxes, p).astype(_np.uint8)
        m = (mask, cx0, cy0)
        self._mask[key] = m
        return m

    def mask_fp(self, bi, oi):
        """Footprint-union mask (MH,MW) bool = any layer touches the cell.
        Used by contact scoring; cached per (bi,oi)."""
        key = (bi, oi)
        fp = self._fpm.get(key)
        if fp is not None:
            return fp
        mask, cx0, cy0 = self.mask(bi, oi)
        fp = mask.any(axis=0)
        self._fpm[key] = fp
        return fp

    # -- occupancy update (int counts so remove() is exact) --------------------
    def _apply(self, bay, bi, oi, x, y, sign):
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        r = int(y) + cy0; c = int(x) + cx0
        H, W = self.H[bay], self.W[bay]
        r0 = max(0, r); c0 = max(0, c)
        r1 = min(H, r + MH); c1 = min(W, c + MW)
        if r1 <= r0 or c1 <= c0:
            self.ver[bay] += 1
            return
        occ = self.occ[bay]
        for l in range(nl):
            g = occ.get(l)
            if g is None:
                if sign < 0:
                    continue
                g = _np.zeros((H, W), dtype=_np.int16)
                occ[l] = g
            g[r0:r1, c0:c1] += sign * mask[l, r0 - r:r1 - r,
                                           c0 - c:c1 - c].astype(_np.int16)
            # v13: drop a layer once it is fully vacated so _unions/scan loops
            # shrink to the live maxL (perf on giants; result-transparent).
            if sign < 0 and not g.any():
                del occ[l]
        self.ver[bay] += 1

    def reset(self):
        """Clear all occupancy (keep the mask cache) for a fresh construction."""
        for j in range(len(self.bays)):
            self.occ[j] = dict()
            self.ver[j] += 1
            self._uni[j] = None
            self._scan[j] = dict()
            self._fp[j] = None

    def add(self, bay, bi, oi, x, y):
        self._apply(bay, bi, oi, x, y, 1)

    def remove(self, bay, bi, oi, x, y):
        self._apply(bay, bi, oi, x, y, -1)

    def footprint(self, bay):
        """Bool (H,W): any layer occupied (for compactness / util scoring).
        Cached per (bay, ver) -- recomputed only when the occupancy changes."""
        cache = self._fp[bay]
        if cache is not None and cache[0] == self.ver[bay]:
            return cache[1]
        occ = self.occ[bay]
        H, W = self.H[bay], self.W[bay]
        fp = _np.zeros((H, W), dtype=bool)
        for g in occ.values():
            fp |= (g > 0)
        self._fp[bay] = (self.ver[bay], fp)
        return fp

    def _unions(self, bay):
        cache = self._uni[bay]
        if cache is not None and cache[0] == self.ver[bay]:
            return cache[1]
        occ = self.occ[bay]
        H, W = self.H[bay], self.W[bay]
        if not occ:
            self._uni[bay] = (self.ver[bay], [])
            return []
        maxL = max(occ.keys())
        union_ge = [None] * (maxL + 1)
        cum = _np.zeros((H, W), dtype=bool)
        for l in range(maxL, -1, -1):
            g = occ.get(l)
            if g is not None:
                cum = cum | (g > 0)      # new array each time -> distinct refs
            union_ge[l] = cum
        self._uni[bay] = (self.ver[bay], union_ge)
        return union_ge

    def scan(self, bay, bi, oi):
        """Boolean (R,C) grid of entry-clear anchor windows against the current
        occupancy, or None if the block cannot fit the bay. Map window (r,c) to
        an assignment via x = c - cx0, y = r - cy0.
        v13: cached per (bay, bi, oi, ver) -- the dispatcher re-scans the same
        (block,orient) across bays/events with unchanged occupancy constantly."""
        sc = self._scan[bay].get((bi, oi))
        if sc is not None and sc[0] == self.ver[bay]:
            return sc[1], sc[2], sc[3]
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        H, W = self.H[bay], self.W[bay]
        if MH > H or MW > W:
            self._scan[bay][(bi, oi)] = (self.ver[bay], None, cx0, cy0)
            return None, cx0, cy0
        R = H - MH + 1; C = W - MW + 1
        unions = self._unions(bay)
        maxL = len(unions) - 1
        total = _np.zeros((R, C), dtype=_np.int32)
        for k in range(nl):
            if k > maxL:
                break                     # no present layer >= k -> clear
            Vk = unions[k]
            if Vk is None or not Vk.any():
                continue
            mk = mask[k]
            if not mk.any():
                continue
            win = _swv(Vk.astype(_np.int32), (MH, MW))     # (R,C,MH,MW)
            total += _np.einsum('rcij,ij->rc', win, mk.astype(_np.int32))
        feas = (total == 0)
        self._scan[bay][(bi, oi)] = (self.ver[bay], feas, cx0, cy0)
        return feas, cx0, cy0

    def scan_scoped(self, bay, actives, bi, oi):
        """v13 raster-windowed repair primitive. Feasible-anchor grid for
        placing (bi,oi) in `bay` against ONLY `actives` = [(bi2,oi2,x2,y2),...]
        (the blocks time-overlapping the candidate insertion), WITHOUT touching
        self.occ. Returns (feas (R,C) bool | None, cx0, cy0, occ_fp (H,W) bool).
        Sound in exactly the same conservative sense as scan()."""
        H, W = self.H[bay], self.W[bay]
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        if MH > H or MW > W:
            return None, cx0, cy0, None
        R = H - MH + 1; C = W - MW + 1
        layers = {}                            # l -> bool (H,W)
        maxL = -1
        for (b2, o2, x2, y2) in actives:
            m2, c2x, c2y = self.mask(b2, o2)
            nl2, MH2, MW2 = m2.shape
            r = int(y2) + c2y; c = int(x2) + c2x
            r0 = max(0, r); c0 = max(0, c)
            r1 = min(H, r + MH2); c1 = min(W, c + MW2)
            if r1 <= r0 or c1 <= c0:
                continue
            for l in range(nl2):
                g = layers.get(l)
                if g is None:
                    g = _np.zeros((H, W), dtype=bool); layers[l] = g
                g[r0:r1, c0:c1] |= m2[l, r0 - r:r1 - r, c0 - c:c1 - c].astype(bool)
            if nl2 - 1 > maxL:
                maxL = nl2 - 1
        if maxL < 0:
            return _np.ones((R, C), dtype=bool), cx0, cy0, \
                _np.zeros((H, W), dtype=bool)
        union_ge = [None] * (maxL + 1)
        cum = _np.zeros((H, W), dtype=bool)
        for l in range(maxL, -1, -1):
            g = layers.get(l)
            if g is not None:
                cum = cum | g
            union_ge[l] = cum
        occ_fp = union_ge[0]                    # footprint of all actives
        total = _np.zeros((R, C), dtype=_np.int32)
        for k in range(nl):
            if k > maxL:
                break
            Vk = union_ge[k]
            if Vk is None or not Vk.any():
                continue
            mk = mask[k]
            if not mk.any():
                continue
            win = _swv(Vk.astype(_np.int32), (MH, MW))
            total += _np.einsum('rcij,ij->rc', win, mk.astype(_np.int32))
        return (total == 0), cx0, cy0, occ_fp


# =============================================================================
# v13 POSITION-QUALITY ORDERING (contact / perimeter-match scoring)
# =============================================================================

def _neighbor_field(occ_fp):
    """4-neighbour count of occupied-or-wall cells for every cell of the bay.
    Walls are the outside of the grid (borders always count as +1 neighbour).
    A block cell landing here scores high when it nestles against existing
    blocks or a wall -> perimeter match -> denser, concavity-filling packings."""
    H, W = occ_fp.shape
    N = _np.zeros((H, W), dtype=_np.int32)
    o = occ_fp.astype(_np.int32)
    N[1:, :] += o[:-1, :]; N[0, :] += 1        # up  (top border = wall)
    N[:-1, :] += o[1:, :]; N[-1, :] += 1       # down
    N[:, 1:] += o[:, :-1]; N[:, 0] += 1        # left
    N[:, :-1] += o[:, 1:]; N[:, -1] += 1       # right
    return N


def _order_cells(raster, feas, cx0, cy0, bi, oi, W, occ_fp, prefer_contact, rng):
    """Order feasible raster anchors best-first as a list of (x, y). Default is
    v12's bottom-left (low y=r, then low x=c). With `prefer_contact` and a
    non-empty occupancy, rank by perimeter-contact first (block footprint dotted
    with the neighbour-field), BL as tie-break -- the density lever, shared by
    the dispatcher and the raster-repair improver. `rng` jitters ties (lottery).
    When prefer_contact is False and rng is None this reproduces v12 exactly."""
    rc = _np.argwhere(feas)                     # (K,2) as (r,c)
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
        win = _swv(N, (MH, MW))                 # (R,C,MH,MW)
        contact = _np.einsum('rcij,ij->rc', win, bfp)
        cval = contact[r, c].astype(_np.float64)
        idx = _np.lexsort((bl, -cval))          # primary -cval (desc), then bl
    else:
        idx = _np.argsort(bl)                   # pure BL (== v12 when rng None)
    return [(int(c[ii]) - cx0, int(r[ii]) - cy0) for ii in idx]


# =============================================================================
# v13 round-3: FLUID-TARGET ADMISSION GATE (structural-overload lever)
# =============================================================================

def _overload_ratio(prob_info, bays):
    """Total area*time demand / total capacity*time over the due-date horizon.
    > 1 means the instance is STRUCTURALLY oversubscribed (no schedule meets
    all dues even at 100% packing density; measured: prob_38 1.14, prob_27
    1.19, every other train instance <= 0.94 -> threshold 1.05 isolates the
    overloaded pair). On such instances alpha-ATC only reorders priority -- a
    stranded block still gets admitted the moment it fits, consuming the very
    area the sacrifice was supposed to free; the fix is an explicit
    target-schedule admission GATE built from _fluid_targets."""
    cap = sum(b.width * b.height for b in bays)
    bl = prob_info["blocks"]
    vol = sum(_min_area(b) * b["processing_time"] for b in bl)
    rmin = min(b["release_time"] for b in bl)
    dmax = max(b["due_date"] for b in bl)
    return vol / max(1e-9, cap * max(1, dmax - rmin))


def _fluid_targets(prob_info, bays, c_eff, mode):
    """Deterministic greedy fluid target schedule. Aggregate-area relaxation:
    capacity = c_eff * total bay area; blocks are loaded in the discipline
    order at the earliest t >= release where the aggregate area-in-use step
    profile stays <= capacity over [t, t+proc). 'spt' = smallest area*proc
    first (the fluid-SPT sacrifice: the largest space-time volumes are pushed
    to the back of the horizon instead of every block being democratically
    late); 'band' = due-date bands (width 4*pbar), smallest area*proc first
    within a band (keeps rough due order globally, sacrifices within bands).
    Returns {bi: int target entry time}."""
    blocks = prob_info["blocks"]
    n = len(blocks)
    total_area = sum(b.width * b.height for b in bays)
    cap = c_eff * total_area
    areas = [_min_area(b) for b in blocks]
    procs = [max(1, int(b["processing_time"])) for b in blocks]
    rels = [int(b["release_time"]) for b in blocks]
    pbar = max(1.0, sum(procs) / max(1, n))
    if mode == "cut":
        # PURE SACRIFICE: pick the smallest set of largest-a*p blocks whose
        # removal brings total volume under c_eff*area*horizon (here c_eff =
        # the packing density the un-sacrificed mass realistically achieves);
        # everyone else keeps target=release (gate inactive, normal ATC), and
        # ONLY the sacrificed blocks are pushed to the post-burst tail via
        # earliest-fit against the mass's prompt-release profile.
        rmin = min(rels)
        H = max(1, max(b["due_date"] for b in blocks) - rmin)
        vol = sum(areas[i] * procs[i] for i in range(n))
        excess = vol - c_eff * total_area * H
        targets = {i: rels[i] for i in range(n)}
        if excess <= 0:
            return targets
        by_vol = sorted(range(n), key=lambda i: -areas[i] * procs[i])
        sac = []
        rem = excess
        for i in by_vol:
            if rem <= 0:
                break
            sac.append(i)
            rem -= areas[i] * procs[i]
        sac_set = set(sac)
        ev = {}
        for i in range(n):
            if i not in sac_set:
                ev[rels[i]] = ev.get(rels[i], 0.0) + areas[i]
                t2 = rels[i] + procs[i]
                ev[t2] = ev.get(t2, 0.0) - areas[i]
        # earliest-fit the sacrificed blocks (EDD order) at FULL area capacity
        # (the tail is empty; c_eff was only the burst-mass density model).
        fullcap = total_area
        for i in sorted(sac, key=lambda i: blocks[i]["due_date"]):
            a, p = areas[i], procs[i]
            t = rels[i]
            guard = 0
            while guard < 4000:
                guard += 1
                ts = sorted(ev)
                E = len(ts)
                run = 0.0
                idx = 0
                while idx < E and ts[idx] <= t:
                    run += ev[ts[idx]]; idx += 1
                viol = run + a > fullcap + 1e-9
                while not viol and idx < E and ts[idx] < t + p:
                    run += ev[ts[idx]]; idx += 1
                    if run + a > fullcap + 1e-9:
                        viol = True
                if not viol:
                    break
                nxt = None
                for tt in ts:
                    if tt > t and ev[tt] < 0:
                        nxt = tt
                        break
                if nxt is None:
                    break
                t = nxt
            targets[i] = int(t)
            ev[t] = ev.get(t, 0.0) + a
            ev[t + p] = ev.get(t + p, 0.0) - a
        return targets
    if mode == "band":
        # band width ~ one mean processing time: coarse enough to allow SPT
        # sacrifice within a band, fine enough that due order matters globally
        # (4*pbar measured degenerate: all dues fell into 1-2 bands == SPT).
        band = max(1.0, pbar)
        order = sorted(range(n), key=lambda i: (
            math.floor(blocks[i]["due_date"] / band),
            areas[i] * procs[i], blocks[i]["due_date"], i))
    else:
        order = sorted(range(n), key=lambda i: (
            areas[i] * procs[i], blocks[i]["due_date"], i))
    ev = {}                                   # time -> +/- area delta
    targets = {}
    for i in order:
        a, p, r = areas[i], procs[i], rels[i]
        t = r
        if a <= cap + 1e-9:
            guard = 0
            while guard < 4000:
                guard += 1
                ts = sorted(ev)
                E = len(ts)
                # usage on the segment covering t = cum deltas at times <= t
                run = 0.0
                idx = 0
                while idx < E and ts[idx] <= t:
                    run += ev[ts[idx]]; idx += 1
                viol = run + a > cap + 1e-9
                # walk the segments starting strictly inside (t, t+p)
                while not viol and idx < E and ts[idx] < t + p:
                    run += ev[ts[idx]]; idx += 1
                    if run + a > cap + 1e-9:
                        viol = True
                if not viol:
                    break
                # advance to the next exit event (usage only drops there)
                nxt = None
                for tt in ts:
                    if tt > t and ev[tt] < 0:
                        nxt = tt
                        break
                if nxt is None:
                    break                     # no future relief; accept t
                t = nxt
        targets[i] = int(t)
        ev[t] = ev.get(t, 0.0) + a
        ev[t + p] = ev.get(t + p, 0.0) - a
    return targets


# =============================================================================
# v12 TIME-ORDERED DISPATCHER CONSTRUCTION ("the pump")
# =============================================================================

def _dispatch_construct(prob_info, bays, bay_u, w1, w2, w3, deadline, raster,
                        kappa=1.0, gamma=0.5, rng=None, cand_cap=12,
                        alpha=0.0, score_pos=False, eps=0.15, targets=None,
                        beam=False, beam_m=4):
    """Event-driven admission construction using the raster full-position scan.

    Walk event times (releases + scheduled exits); at each event admit queued
    (released, unplaced) blocks in ATC priority order, placing each in the best
    bay that has an entry-clear raster window whose candidate also passes the
    exact `_can_place` gate. Prompt exit at entry+proc. Any block never admitted
    (deadline / spatially impossible with the current set) is force-placed at
    the end so the output is always a complete assignment dict, identical in
    format to `_construct`."""
    import heapq
    blocks_data = prob_info["blocks"]
    n = len(blocks_data)
    n_bays = len(bays)
    procs = [int(b["processing_time"]) for b in blocks_data]
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    pbar = max(1.0, sum(procs) / max(1, n))
    orients_of = [_unique_orients(b) for b in blocks_data]
    # v13 volume-aware triage: normalize min-orient footprint area by the mean
    # so alpha=0 (a^0=1) reproduces v12's ATC exactly, alpha>0 deliberately
    # strands large-footprint blocks under overload (fluid-SPT flavour).
    areas = [_min_area(b) for b in blocks_data]
    abar = max(1e-9, sum(areas) / max(1, n))
    anorm = [a / abar for a in areas]

    sched = [[] for _ in range(n_bays)]      # bay -> [(blk, entry, exit, bbox)]
    bay_loads = [0.0] * n_bays
    assignments = {}

    def atc(bi, t):
        p = procs[bi]
        if targets is None:
            slack = dues[bi] - p - t
        else:
            # round-3 target mode: urgency keys on the LATER of due-slack
            # point and the fluid target -- un-sacrificed blocks (target ==
            # release) keep the exact v12 ATC urgency; sacrificed blocks
            # (target past due) become maximally urgent AT their target
            # instead of long before it (they are gated out until then).
            slack = max(dues[bi] - p, targets[bi]) - t
        idx = (1.0 / ((anorm[bi] ** alpha) * p)) * \
            math.exp(-max(0.0, slack) / (kappa * pbar))
        if rng is not None:
            idx *= (1.0 + rng.uniform(-eps, eps))   # v13: multiplicative jitter
        return idx

    def bay_score(bi, bay_id, t):
        blk = blocks_data[bi]
        prefs = blk["bay_preferences"]
        util = 0.0
        bay = bays[bay_id]
        area = bay.width * bay.height
        occ = raster.occ[bay_id]
        if occ:
            util = float(raster.footprint(bay_id).sum()) / max(1.0, area)
        s = w3 * (max(prefs) - prefs[bay_id]) + gamma * w1 * util
        return s

    def try_place(bi, t, cap):
        """Try to admit block bi entering at time t. Returns placement tuple or
        None. `cap` = max exact _can_place gates per (bay,orient). With
        score_pos, feasible cells are ranked by perimeter contact (density
        lever); otherwise pure bottom-left (== v12 when rng is None)."""
        blk = blocks_data[bi]
        p = procs[bi]
        exit_t = t + p
        order = sorted(range(n_bays), key=lambda j: bay_score(bi, j, t))
        for bay_id in order:
            bay = bays[bay_id]
            rel = _rel_sched_bbox(sched[bay_id], t, exit_t)
            occ_fp = raster.footprint(bay_id) if score_pos else None
            for oi in orients_of[bi]:
                if not _orient_fits(blk, oi, bay):
                    continue
                feas, cx0, cy0 = raster.scan(bay_id, bi, oi)
                if feas is None or not feas.any():
                    continue
                cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                     raster.W[bay_id], occ_fp, score_pos, rng)
                tried = 0
                for (x, y) in cells:
                    nb = _mkblock(bi, blk, x, y, oi)
                    if _can_place(bay, rel, nb, t, exit_t):
                        return (bay_id, x, y, oi, t, exit_t)
                    tried += 1
                    if tried >= cap:
                        break
        return None

    def cap_for(qlen):
        # v13 adaptive cand_cap: a deep entry queue means the bay is congested
        # and the 12-cell cliff wrongly rejects blocks whose 13th cell fits.
        # Widen the exact-gate budget then (only under the new-scoring bundle so
        # the alpha=0/score_pos=False path stays byte-identical to v12).
        if score_pos and qlen >= 20:
            return min(48, cand_cap * 4)
        return cand_cap

    def commit(bi, place):
        bay_id, x, y, oi, entry, exit_t = place
        nb = _mkblock(bi, blocks_data[bi], x, y, oi)
        sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
        bay_loads[bay_id] += blocks_data[bi]["workload"]
        assignments[bi] = {
            "block_id": bi, "bay_id": bay_id, "x": int(x), "y": int(y),
            "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
        }
        raster.add(bay_id, bi, oi, x, y)

    def apply_place(bi, place):
        """Full admission of `bi`: commit + queue/exit/heap bookkeeping. The v13
        single-pass loop is factored through here so beam-off stays byte-exact."""
        nonlocal placed_cnt
        commit(bi, place)
        queue.discard(bi)
        placed_cnt += 1
        et = place[5]
        exits_at.setdefault(et, []).append(
            (place[0], bi, place[3], place[1], place[2]))
        if et not in scheduled:               # ensure the exit event is visited
            heapq.heappush(heap, et)
            scheduled.add(et)

    def beam_admit(t, ordered, cc):
        """v14 MULTI-ORDER ADMISSION BEAM. Trial-fill the queued set under k=3
        orders (ATC / area-desc / most-constrained-first), each via commit+
        rollback of raster/sched, and apply the fill with the best (admitted
        area, then placement cost). Kills first-fit interlock foreclosure."""
        order_atc = ordered
        order_area = sorted(ordered, key=lambda bi: -areas[bi])

        def cellcount(bi):
            blk = blocks_data[bi]
            tot = 0
            for bay_id in range(n_bays):
                bay = bays[bay_id]
                for oi in orients_of[bi]:
                    if not _orient_fits(blk, oi, bay):
                        continue
                    feas, _cx, _cy = raster.scan(bay_id, bi, oi)
                    if feas is not None:
                        tot += int(feas.sum())
            return tot
        order_con = sorted(ordered, key=cellcount)

        best = None   # ((-area, cost), committed_list)
        for od in (order_atc, order_area, order_con):
            if time.time() > deadline:
                break
            committed = []
            for bi in od:
                if time.time() > deadline:
                    break
                if targets is not None and t < targets[bi]:
                    continue
                place = try_place(bi, t, cc)
                if place is not None:
                    commit(bi, place)         # trial: mutate only, no bookkeeping
                    committed.append((bi, place))
            area = sum(areas[bi] for bi, _ in committed)
            cost = 0.0
            for bi, place in committed:
                prefs = blocks_data[bi]["bay_preferences"]
                cost += (w1 * max(0, place[5] - dues[bi])
                         + w3 * (max(prefs) - prefs[place[0]]))
            key = (-area, cost)
            if best is None or key < best[0]:
                best = (key, list(committed))
            for bi, place in reversed(committed):   # rollback (exact int occ)
                bay_id, x, y, oi, en, ex = place
                raster.remove(bay_id, bi, oi, x, y)
                s = sched[bay_id]
                for idx in range(len(s) - 1, -1, -1):
                    if s[idx][0].block_id == bi:
                        del s[idx]
                        break
                bay_loads[bay_id] -= blocks_data[bi]["workload"]
                del assignments[bi]
        if best is not None:
            for bi, place in best[1]:
                apply_place(bi, place)

    # event structure ---------------------------------------------------------
    rel_sorted = sorted(range(n), key=lambda i: rels[i])
    rp = 0
    exits_at = {}                              # time -> [(bay, bi, oi, x, y)]
    ev_times = set(rels)
    if targets is not None:
        ev_times |= {int(v) for v in targets.values()}  # round-3: gate opens
    heap = sorted(ev_times)
    heapq.heapify(heap)
    scheduled = set(heap)                       # v13: O(1) heap membership test
    queue = set()
    placed_cnt = 0
    last_t = None

    while heap:
        t = heapq.heappop(heap)
        scheduled.discard(t)
        if t == last_t:
            continue
        last_t = t
        # 1. process exits at t (free occupancy) + prune exited blocks from the
        #    affected bays' sched (they can never matter for entry>=t; keeps the
        #    _rel_sched_bbox / _can_place scans O(active) on giants).
        ev = exits_at.pop(t, None)
        if ev:
            touched = set()
            for (bay_id, bi, oi, x, y) in ev:
                raster.remove(bay_id, bi, oi, x, y)
                touched.add(bay_id)
            for bj in touched:
                sched[bj] = [it for it in sched[bj] if it[2] > t]
        # 2. admit newly released blocks
        while rp < n and rels[rel_sorted[rp]] <= t:
            queue.add(rel_sorted[rp]); rp += 1
        if not queue:
            continue
        if time.time() > deadline:
            break
        # 3. admission pass in ATC priority order (v14: optional multi-order beam)
        ordered = sorted(queue, key=lambda bi: -atc(bi, t))
        cc = cap_for(len(ordered))
        if beam and len(ordered) >= beam_m:
            beam_admit(t, ordered, cc)
        else:
            for bi in ordered:
                if time.time() > deadline:
                    break
                if targets is not None and t < targets[bi]:
                    continue    # round-3 GATE: hold until the fluid target
                place = try_place(bi, t, cc)
                if place is not None:
                    apply_place(bi, place)
        # if the queue still holds blocks and no future event will free space,
        # inject a probe event so they get force-placed below.
        if queue and not heap:
            break

    # 4. force-place every remaining block (queued + not-yet-released) so the
    #    result is always complete; feed the exact same fallback as _force_place.
    remaining = [bi for bi in range(n) if bi not in assignments]
    remaining.sort(key=lambda bi: (dues[bi], -_min_area(blocks_data[bi])))
    for bi in remaining:
        blk = blocks_data[bi]
        # try a raster admission at the block's release (cheap best-effort),
        # else fall back to the guaranteed empty-bay force placement.
        t = rels[bi]
        place = try_place(bi, t, cand_cap)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        commit(bi, place)

    return assignments


def _rel_sched_bbox(sched_bay, entry, exit_t):
    """(blk, a, e) triples for blocks in the bay whose time interval can matter
    for a placement over [entry, exit_t) -- i.e. present at entry, present at
    exit, or time-overlapping. Kept broad (time only) so `_can_place` sees every
    block it must check; it does its own bbox pruning via the caches."""
    out = []
    for it in sched_bay:
        a, e = it[1], it[2]
        if a <= exit_t and entry <= e:
            out.append((it[0], a, e))
    return out


# -----------------------------------------------------------------------------
# v13 Z3 (bay-preference) RELOCATION ENDGAME (#3c)
# -----------------------------------------------------------------------------

def _z3_relocate(prob_info, assign, bays, bay_u, w1, w2, w3, raster, deadline,
                 pos_cap=16, max_passes=3, time_cap=8):
    """Preference relocation endgame: for each off-preference block (desc by
    w3 gain) try moving it to a higher-preference bay -- first at the SAME
    [entry, exit) interval (tardiness-neutral), then at ALTERNATIVE entry
    times whose full objective delta (w1*d_tard + w2*d_imbal - w3*gain) is
    still strictly negative (measured: the same-interval move almost never
    fits because the preferred bay is full at exactly that interval -- that is
    WHY the block went off-preference; timing freedom is what unlocks the Z3
    money). Candidate cells come from the scoped raster scan, exact-gated by
    _can_place; the delta is computed exactly BEFORE geometry work, so only
    strictly-improving (t, bay) pairs are ever scanned. Removing a block from
    its old bay can never invalidate others (strictly fewer obstacles).
    Returns (new_assign, new_obj) or (None, None)."""
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    if n_bays < 2 or raster is None or not _HAVE_NUMPY:
        return None, None
    cur = {bi: dict(a) for bi, a in assign.items()}
    sched, bay_loads = _rebuild_sched(cur, blocks_data, n_bays)

    def imbal(loads):
        return math.floor(max(
            abs(bay_u[p] * loads[p] - bay_u[q] * loads[q])
            for p in range(n_bays) for q in range(n_bays) if p != q))

    moved_any = False
    for _pass in range(max_passes):
        cand = []
        for bi, a in cur.items():
            prefs = blocks_data[bi]["bay_preferences"]
            gain = max(prefs) - prefs[a["bay_id"]]
            if gain > 0:
                cand.append((gain, bi))
        if not cand:
            break
        cand.sort(reverse=True)
        pass_moved = False
        for _, bi in cand:
            if time.time() > deadline:
                break
            a = cur[bi]
            blk = blocks_data[bi]
            prefs = blk["bay_preferences"]
            entry, exit_t = a["entry_time"], a["exit_time"]
            proc = exit_t - entry
            due = int(blk["due_date"])
            rel_t = int(blk["release_time"])
            cur_tard = max(0, exit_t - due)
            cb = a["bay_id"]
            wl = blk["workload"]
            im0 = imbal(bay_loads)
            orients = [oi for oi in _unique_orients(blk)]
            done = False
            for tj in sorted((j for j in range(n_bays) if prefs[j] > prefs[cb]),
                             key=lambda j: -prefs[j]):
                loads2 = list(bay_loads)
                loads2[cb] -= wl; loads2[tj] += wl
                # budget = the strict-improvement room left for added tardiness
                budget = (w3 * (prefs[tj] - prefs[cb])
                          - w2 * (imbal(loads2) - im0))
                if budget <= 1e-9:
                    continue                 # move can't pay for itself
                bay = bays[tj]
                if not any(_orient_fits(blk, oi, bay) for oi in orients):
                    continue
                # candidate entry times: same interval first, then bay-event
                # times whose tardiness delta still fits within the budget.
                t_hi = due - proc + cur_tard + int(budget / max(w1, 1e-9))
                cands_t = {entry}
                alap = due - proc
                if rel_t <= alap:
                    cands_t.add(alap); cands_t.add(rel_t)
                for it2 in sched[tj]:
                    a2, e2 = it2[1], it2[2]
                    for tt in (int(e2), int(a2) - proc):
                        if rel_t <= tt <= t_hi:
                            cands_t.add(tt)

                def dtard(t):
                    return max(0, t + proc - due) - cur_tard

                # same-interval first; then least added tardiness, LATEST first
                # within a tardiness tier (bays drain over time -- late slots
                # near ALAP are where free space actually exists; mirrors
                # _zero_candidates' reverse order).
                times = sorted(cands_t, key=lambda t: (t != entry, dtard(t), -t))
                for t in times[:time_cap]:
                    dobj = w1 * dtard(t) - budget
                    if dobj >= -1e-9:
                        continue
                    e_new = t + proc
                    relx = _time_overlap_rel(sched[tj], t, e_new)
                    actives = [(b.block_id, b.orient_idx, b.x, b.y)
                               for b, _a2, _e2 in relx]
                    for oi in orients:
                        if not _orient_fits(blk, oi, bay):
                            continue
                        feas, cx0, cy0, occ_fp = raster.scan_scoped(
                            tj, actives, bi, oi)
                        if feas is None or not feas.any():
                            continue
                        cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                             raster.W[tj], occ_fp, True, None)
                        tried = 0
                        for (x, y) in cells:
                            nb = _mkblock(bi, blk, x, y, oi)
                            if _can_place(bay, relx, nb, t, e_new):
                                # commit: strict internal-objective improvement
                                sched[cb] = [it for it in sched[cb]
                                             if it[0].block_id != bi]
                                sched[tj].append((nb, t, e_new,
                                                  nb.bounding_rect()))
                                bay_loads[cb] -= wl; bay_loads[tj] += wl
                                a["bay_id"] = tj
                                a["x"] = int(x); a["y"] = int(y)
                                a["orient_idx"] = oi
                                a["entry_time"] = int(t)
                                a["exit_time"] = int(e_new)
                                pass_moved = True; moved_any = True
                                done = True
                                break
                            tried += 1
                            if tried >= pos_cap:
                                break
                        if done:
                            break
                    if done or time.time() > deadline:
                        break
                if done:
                    break                    # next block
        if not pass_moved or time.time() > deadline:
            break
    if not moved_any:
        return None, None
    o = _objective(cur, blocks_data, bays, bay_u, w1, w2, w3)[0]
    return cur, o


# -----------------------------------------------------------------------------
# v13 #3b: CP-SAT time-WINDOW decomposition for giant bays
# -----------------------------------------------------------------------------

def _cpsat_retime_window(bay, blocks_data, ids, new_assign, t_end,
                         cap_pairs=4000, chunk0=55):
    """Windowed retime for a bay whose full pair count exceeds the CP-SAT cap
    (v12 silently no-opped there). Retimes one time-window CHUNK of blocks at a
    time: chunk blocks are variables constrained inside [T0, T1] (their current
    span) against each other with the EXACT var-var encoding of the full model,
    and against every temporally-overlapping non-chunk block as FIXED constants
    (same crane tie rules, entry times substituted). Variables cannot leave
    [T0, T1], so no unmodeled interaction is possible. Chunks are processed
    most-tardy-first until the deadline; each accepted window strictly reduces
    its own tardiness. Mutates new_assign in place; returns True if improved."""
    from ortools.sat.python import cp_model
    improved = False

    def tard(bi):
        return max(0, new_assign[bi]["exit_time"] - blocks_data[bi]["due_date"])

    ids_sorted = sorted(ids, key=lambda bi: new_assign[bi]["entry_time"])
    chunks = [ids_sorted[i:i + chunk0] for i in range(0, len(ids_sorted), chunk0)]
    chunks.sort(key=lambda ch: -sum(tard(bi) for bi in ch))
    for ch in chunks:
        if time.time() >= t_end - 1.5:
            break
        if sum(tard(bi) for bi in ch) <= 0:
            continue

        def bounds(c):
            """[T0e, T1]: the chunk's span EXTENDED LEFT by its own width --
            tardiness wins come from pulling blocks earlier into idle gaps
            before the chunk, which a same-span window cannot express."""
            t0 = min(new_assign[bi]["entry_time"] for bi in c)
            t1 = max(new_assign[bi]["exit_time"] for bi in c)
            return max(0, t0 - max(1, t1 - t0)), t1

        def fixed_of(c, T0, T1):
            cs = set(c)
            return [bi for bi in ids if bi not in cs
                    and new_assign[bi]["entry_time"] <= T1
                    and new_assign[bi]["exit_time"] >= T0]

        T0, T1 = bounds(ch)
        fixed = fixed_of(ch, T0, T1)
        while (len(ch) > 12 and
               len(ch) * (len(ch) - 1) // 2 + len(ch) * len(fixed)
               > int(cap_pairs * 1.5)):
            ch = ch[:max(12, int(len(ch) * 0.7))]
            T0, T1 = bounds(ch)
            fixed = fixed_of(ch, T0, T1)
        before = sum(tard(bi) for bi in ch)
        if before <= 0:
            continue
        blks = {bi: _mkblock(bi, blocks_data[bi], new_assign[bi]["x"],
                             new_assign[bi]["y"], new_assign[bi]["orient_idx"])
                for bi in list(ch) + fixed}
        m = cp_model.CpModel()
        E, P = {}, {}
        terms = {}
        for bi in ch:
            blk = blocks_data[bi]
            P[bi] = int(blk["processing_time"])
            lo = max(int(blk["release_time"]), int(T0))
            hi = int(T1) - P[bi]
            e0 = int(new_assign[bi]["entry_time"])
            lo = min(lo, e0); hi = max(hi, e0)    # domain always contains hint
            E[bi] = m.NewIntVar(lo, hi, f"e{bi}")
            m.AddHint(E[bi], e0)
            T = m.NewIntVar(0, int(T1) + 10, f"t{bi}")
            m.Add(T >= E[bi] + P[bi] - int(blk["due_date"]))
            terms[bi] = T

        def outside_vv(i, off_i, j, tie_bad):
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + off_i <= E[j] - (1 if tie_bad == "left" else 0)
                  ).OnlyEnforceIf(b1)
            m.Add(E[i] + off_i >= E[j] + P[j] + (1 if tie_bad == "right" else 0)
                  ).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        def outside_vf(i, off_i, lo_c, hi_c, tie_left, tie_right):
            """E[i]+off_i outside (lo_c, hi_c) with optional boundary bans."""
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + off_i <= lo_c - (1 if tie_left else 0)).OnlyEnforceIf(b1)
            m.Add(E[i] + off_i >= hi_c + (1 if tie_right else 0)).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        abort = False
        chl = list(ch)
        for u in range(len(chl)):
            if (u & 15) == 0 and time.time() >= t_end - 0.8:
                abort = True
                break
            i = chl[u]
            A = blks[i]
            # -- var-var (exact mirror of the full model) ------------------
            for v in range(u + 1, len(chl)):
                j = chl[v]
                B = blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                if _collide(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] + P[i] <= E[j]).OnlyEnforceIf(b1)
                    m.Add(E[j] + P[j] <= E[i]).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                    continue
                if _entry_blocked(bay, B, A):
                    outside_vv(i, 0, j, "left" if j < i else "none")
                if _exit_blocked(bay, B, A):
                    outside_vv(i, P[i], j, "right" if j > i else "none")
                if _entry_blocked(bay, A, B):
                    outside_vv(j, 0, i, "left" if i < j else "none")
                if _exit_blocked(bay, A, B):
                    outside_vv(j, P[j], i, "right" if i > j else "none")
            # -- var-fixed (fixed entry times as constants) ----------------
            for j in fixed:
                B = blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                aj = int(new_assign[j]["entry_time"])
                ej = int(new_assign[j]["exit_time"])
                if _collide(bay, A, B):
                    # disjoint intervals: exit_i <= aj OR E_i >= ej
                    outside_vf(i, P[i], aj, ej + P[i], False, False)
                    continue
                # j (fixed) obstructs i's entry/exit moments:
                if _entry_blocked(bay, B, A):
                    outside_vf(i, 0, aj, ej, j < i, False)
                if _exit_blocked(bay, B, A):
                    outside_vf(i, P[i], aj, ej, False, j > i)
                # i (variable) obstructs j's fixed entry moment aj / exit ej:
                # aj outside (E_i, E_i+P_i): E_i >= aj (+1 if i<j) OR exit_i<=aj
                if _entry_blocked(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] >= aj + (1 if i < j else 0)).OnlyEnforceIf(b1)
                    m.Add(E[i] + P[i] <= aj).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                if _exit_blocked(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] >= ej).OnlyEnforceIf(b1)
                    m.Add(E[i] + P[i] <= ej - (1 if i > j else 0)).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
        if abort:
            break
        m.Minimize(sum(terms.values()))
        rem2 = min(5.0, t_end - time.time() - 0.3)
        if rem2 < 0.5:
            break
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = rem2
        solver.parameters.num_search_workers = 1
        try:
            status = solver.Solve(m)
        except Exception:
            continue
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            after = sum(int(solver.Value(t)) for t in terms.values())
            if after < before:
                for bi in ch:
                    e = int(solver.Value(E[bi]))
                    new_assign[bi]["entry_time"] = e
                    new_assign[bi]["exit_time"] = e + P[bi]
                improved = True
    return improved


# -----------------------------------------------------------------------------
# v11 CP-SAT exact time-repair (fixed geometry)  [v12: audit fixes]
# -----------------------------------------------------------------------------

def _cpsat_retime(prob_info, assign, bays, blocks_data, budget_s, hard_deadline):
    """Re-optimize ALL entry times of `assign` with bay/x/y/orient fixed,
    minimizing total tardiness (the only timing-dependent objective term).
    Bays are independent -> one CP-SAT model per bay. Pairwise relations come
    from the exact cached geometry primitives; crane tie rules mirror
    _present_at_entry/_present_at_exit. Returns a new assignments dict or None
    (ortools missing, no time, or no improvement)."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    t_end = min(time.time() + budget_s, hard_deadline - 1.0)
    if time.time() >= t_end:
        return None
    n_bays = len(bays)
    by_bay = [[] for _ in range(n_bays)]
    for bi, a in assign.items():
        by_bay[a["bay_id"]].append(bi)
    # Most-tardy bays first so the budget goes where the money is.
    def bay_tard(ids):
        return sum(max(0, assign[bi]["exit_time"] - blocks_data[bi]["due_date"])
                   for bi in ids)
    order = sorted(range(n_bays), key=lambda j: -bay_tard(by_bay[j]))
    new_assign = {bi: dict(a) for bi, a in assign.items()}
    improved = False
    for bj in order:
        ids = by_bay[bj]
        if len(ids) < 2 or bay_tard(ids) <= 0:
            continue
        # v12 fix: pair-count cap. The pairwise build is O(m^2) Shapely/cache
        # queries; a bay with hundreds of blocks can blow the whole window on
        # model construction alone. v13 #3b: such giant bays now get the
        # time-WINDOW decomposition (chunked exact retime) instead of a no-op.
        if len(ids) * (len(ids) - 1) // 2 > 4000:
            try:
                if _cpsat_retime_window(bays[bj], blocks_data, ids,
                                        new_assign, t_end):
                    improved = True
            except Exception:
                pass
            continue
        remaining = t_end - time.time()
        if remaining < 1.5:
            break
        bay = bays[bj]
        blks = {bi: _mkblock(bi, blocks_data[bi], assign[bi]["x"],
                             assign[bi]["y"], assign[bi]["orient_idx"])
                for bi in ids}
        m = cp_model.CpModel()
        H = int(2 * max(max(a["exit_time"] for a in assign.values()),
                        max(blocks_data[bi]["due_date"] for bi in ids)) + 10)
        E, P = {}, {}
        terms = []
        for bi in ids:
            blk = blocks_data[bi]
            P[bi] = int(blk["processing_time"])
            E[bi] = m.NewIntVar(int(blk["release_time"]), H, f"e{bi}")
            m.AddHint(E[bi], int(assign[bi]["entry_time"]))
            T = m.NewIntVar(0, H, f"t{bi}")
            m.Add(T >= E[bi] + P[bi] - int(blk["due_date"]))
            terms.append(T)

        def outside(t_i, off_i, bi_id, bj2, tie_bad):
            """Moment E[bi_id]+off_i must lie outside (E[bj2], E[bj2]+P[bj2]);
            tie_bad='left' also forbids == E[bj2]; 'right' forbids == exit."""
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            if tie_bad == "left":
                m.Add(E[bi_id] + off_i <= E[bj2] - 1).OnlyEnforceIf(b1)
            else:
                m.Add(E[bi_id] + off_i <= E[bj2]).OnlyEnforceIf(b1)
            if tie_bad == "right":
                m.Add(E[bi_id] + off_i >= E[bj2] + P[bj2] + 1).OnlyEnforceIf(b2)
            else:
                m.Add(E[bi_id] + off_i >= E[bj2] + P[bj2]).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        abort = False
        for u in range(len(ids)):
            # v12 fix: deadline flag INSIDE the O(m^2) build. A partially-built
            # model omits collision/crane constraints and would solve to a
            # garbage (infeasible-in-reality) schedule, so on timeout we abort
            # the bay WITHOUT solving rather than solve an incomplete model.
            if (u & 15) == 0 and time.time() >= t_end:
                abort = True
                break
            for v in range(u + 1, len(ids)):
                i, j = ids[u], ids[v]
                A, B = blks[i], blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                if _collide(bay, A, B):
                    # disjoint presence intervals (touching allowed; ties are
                    # then boundary moments, which the replay rules permit)
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] + P[i] <= E[j]).OnlyEnforceIf(b1)
                    m.Add(E[j] + P[j] <= E[i]).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                    continue
                # crane rules (mirror _present_at_entry/_present_at_exit ties):
                # j present at i's ENTRY t: E_j < t < exit_j, or t == E_j and
                # j.id < i.id. j present at i's EXIT t: E_j < t < exit_j, or
                # t == exit_j and j.id > i.id.
                if _entry_blocked(bay, B, A):   # j obstructs i's entry moment
                    outside(E[i], 0, i, j, "left" if j < i else "none")
                if _exit_blocked(bay, B, A):    # j obstructs i's exit moment
                    outside(E[i], P[i], i, j, "right" if j > i else "none")
                if _entry_blocked(bay, A, B):
                    outside(E[j], 0, j, i, "left" if i < j else "none")
                if _exit_blocked(bay, A, B):
                    outside(E[j], P[j], j, i, "right" if i > j else "none")
        if abort:
            break
        m.Minimize(sum(terms))
        # v12 fix: recompute the solver budget AFTER the (possibly slow) build,
        # and drop the >=1s floor -- the old code reserved the PRE-build
        # `remaining` and floored it at 1s, so a long build let the solve run
        # past t_end and starved the post-CP improve.
        rem2 = t_end - time.time()
        if rem2 < 0.5:
            break
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = rem2
        solver.parameters.num_search_workers = 1  # we're already 1 core/worker
        try:
            status = solver.Solve(m)
        except Exception:
            continue
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            before = bay_tard(ids)
            after = sum(int(solver.Value(t)) for t in terms)
            if after < before:
                for bi in ids:
                    e = int(solver.Value(E[bi]))
                    new_assign[bi]["entry_time"] = e
                    new_assign[bi]["exit_time"] = e + P[bi]
                improved = True
    return new_assign if improved else None


# -----------------------------------------------------------------------------
# v10 parallel portfolio (v11: + island inboxes + CP-SAT pass)
# -----------------------------------------------------------------------------

def _run_strategy(wid, prob_info, timelimit, t_start, push, inbox=None):
    """One portfolio member. Streams (internal_obj, assignments) via push();
    receives global-best broadcasts via inbox (None for the W0 anchor)."""
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    deadline = t_start + timelimit * 0.95 - reserve - 2.5  # margin for final put
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)
    window = deadline - t_start

    def iobj(assign):
        return _objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]

    def build(order, fc, gamma=0.0):
        a = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                       t_start, deadline, forced=fc, util_gamma=gamma)
        o = iobj(a)
        push(o, a)
        return o, a

    # v13: raster engine (shared masks). Every non-anchor worker gets one: the
    # dispatcher workers (W2/W3) use its occupancy for construction, and ALL
    # forced workers (incl. W1) use its scoped scan for raster-windowed repair
    # inside the improver. W0 stays byte-exact v9 and never touches a raster.
    raster = _Raster(prob_info, bays) if (_HAVE_NUMPY and wid != 0) else None

    def improve(assign, seed, until=None, repack_every=0):
        dl = deadline if until is None else min(until, deadline)
        r, o = _improve(prob_info, assign, bays, bay_u, w1, w2, w3,
                        dl, forced, seed=seed, on_best=push, inbox=inbox,
                        raster=raster, repack_every=repack_every)
        push(o, r, force=True)
        return o, r

    # round-3: structural-overload detection + fluid-target cache. targets are
    # deterministic per (c_eff, mode), so compute each grid point once.
    overload = _overload_ratio(prob_info, bays)
    _tgt_cache = {}

    def fluid_tgt(spec):
        if spec is None:
            return None
        tg = _tgt_cache.get(spec)
        if tg is None:
            tg = _fluid_targets(prob_info, bays, spec[0], spec[1])
            _tgt_cache[spec] = tg
        return tg

    def dispatch(kappa, gamma, drng=None, alpha=0.0, score_pos=True,
                 tspec=None, beam=False, dl=None):
        raster.reset()
        a = _dispatch_construct(prob_info, bays, bay_u, w1, w2, w3,
                                dl if dl is not None else deadline,
                                raster, kappa=kappa, gamma=gamma, rng=drng,
                                alpha=alpha, score_pos=score_pos,
                                targets=fluid_tgt(tspec), beam=beam)
        o = iobj(a)
        push(o, a)
        return o, a

    def polish(assign, seed, repack_every=0):
        """improve -> CP-SAT exact time-repair -> improve the winner -> Z3
        relocation endgame. The CP pass fires at a hard-latest 62% of the
        window (or immediately when the improver converges early == a stall
        gate) so the improver both feeds it a good geometry and gets time to
        exploit the re-timed schedule after. v13: the tail reserves a small
        slice for the tardiness-neutral preference-relocation pass (#3c).
        v14: `repack_every` interleaves joint-window-repack rounds inside both
        improve passes (0 == classic v13 polish)."""
        cp_at = t_start + 0.62 * window
        o1, r1 = improve(assign, seed, until=cp_at, repack_every=repack_every)
        try:
            rc = _cpsat_retime(prob_info, r1, bays, blocks_data,
                               min(30.0, 0.12 * window), deadline)
        except Exception:
            rc = None
        base, ob = r1, o1
        if rc is not None:
            oc = iobj(rc)
            push(oc, rc, force=True)
            if oc < ob:
                base, ob = rc, oc
        z3_at = deadline - (min(12.0, 0.05 * window) if raster is not None
                            else 0.0)
        if time.time() < z3_at - 2.0:
            o2, r2 = improve(base, seed + 1, until=z3_at,
                             repack_every=repack_every)
            if o2 < ob:
                base, ob = r2, o2
        if raster is not None and time.time() < deadline - 0.5:
            try:
                rz, oz = _z3_relocate(prob_info, base, bays, bay_u,
                                      w1, w2, w3, raster, deadline)
                if rz is not None and oz < ob - 1e-9:
                    push(oz, rz, force=True)
            except Exception:
                pass

    if wid == 0:
        # W0 = EXACT v9 replica (same rng streams, same two-pass improver).
        # This is the no-regression anchor: the improver is basin-sensitive, so
        # only replaying v9's exact construction sequence guarantees v10 keeps
        # every v9 result (e.g. prob_31 17.64M comes from improving a jittered
        # construction that no plain EDD/AREA basin reaches). The worker gets a
        # slightly earlier deadline than v9's own (margin for the final put).
        _v9_search(prob_info, timelimit - 2.5, t_start, push=push)
        return

    # -- W2 = dispatcher + volume-aware mini-lottery -> improver --------------
    if wid == 2 and raster is not None:
        cands = []
        if forced:
            # v13 giant/forced mini-lottery: rotate alpha (volume triage) x kappa
            # before polish. In v12 giants got exactly ONE dispatch here; raster
            # builds are cheap enough to sample the fluid-SPT basin (alpha>0).
            plan = [(0.0, 1.0, None, False), (0.5, 1.0, None, False),
                    (1.0, 1.0, None, False), (0.5, 2.0, None, False),
                    (0.0, 1.0, None, True)]        # v14: beam ticket last
            cap = t_start + 0.45 * window
            if overload > 1.05:
                # round-3: structurally oversubscribed (prob_38/27 regime) ->
                # add fluid-target ADMISSION-GATED dispatches. NOTE the honest
                # probe result: at the construction level EVERY gate variant
                # (spt/band loaders, pure-cut sacrifice; C in 0.5..1.1)
                # realized WORSE than the ungated dispatcher on both 38 and 27
                # (realization penalty ~13-22M dwarfs the fluid-SPT saving);
                # only the 3 closest variants are kept as cheap lottery
                # tickets (~1-5s each) in case the improver flips one, with
                # the plain entries first so best-of always protects. v14 adds
                # a multi-order admission-beam ticket last (attacks the first-
                # fit interlock foreclosure the gate variants could not).
                plan = [(0.0, 1.0, None, False), (0.5, 1.0, None, False),
                        (0.0, 1.0, (0.80, "cut"), False),
                        (0.0, 1.0, (1.10, "spt"), False),
                        (0.0, 1.0, (0.70, "cut"), False),
                        (1.0, 1.0, None, False), (0.5, 2.0, None, False),
                        (0.0, 1.0, None, True)]    # v14: beam ticket last
            for al, ka, ts_, bm in plan:
                try:
                    # beam tickets are capped at the lottery boundary so a slow
                    # multi-order fill can never starve the repack-heavy polish.
                    cands.append(dispatch(ka, 0.5, alpha=al, tspec=ts_, beam=bm,
                                          dl=cap if bm else None))
                except Exception:
                    break
                if time.time() >= cap:
                    break
        else:
            try:
                cands.append(dispatch(1.0, 0.5))
            except Exception:
                pass
        if cands:
            # v14: W2 is the repack-heavy worker (giants + overloaded prob_27).
            polish(min(cands, key=lambda c: c[0])[1], seed=2222, repack_every=3)
        else:  # dispatcher failed -> safe v11-style construction + improve
            try:
                _, a = build(_area_order(blocks_data) if forced
                             else _edd_order(blocks_data), forced)
                improve(a, seed=2222, repack_every=3)
            except Exception:
                pass
        return

    # -- W3 on GIANTS = repack specialist (v14) --------------------------------
    # Giants (n>=250, forced) ran only 3 workers in v12/v13 because W3's multi-
    # start dispatcher lottery cannot afford several giant builds. v14 re-adds
    # W3 as a REPACK SPECIALIST instead: seed with a cheap SPARSE construction
    # (deadline already past -> dense=False path, seconds even at n=250), then
    # run the improver with repack_every=2; the island inbox hands it W1/W2's
    # broadcast incumbent within ~a minute, so nearly the whole window is spent
    # on joint-window repacks of the real leader. RSS measured 2.87GB/3w on
    # prob_38 -> a 4th worker projects ~4GB, far under the 16GB budget. All
    # accepts obj-gated; worst case it contributes nothing (parent takes min).
    if wid == 3 and raster is not None and forced and len(blocks_data) >= 250:
        try:
            a = _construct(prob_info, _edd_order(blocks_data), bays, bay_u,
                           w1, w2, w3, t_start, t_start, forced=True)
            push(iobj(a), a)
        except Exception:
            return
        improve(a, seed=4444, repack_every=2)
        return

    # -- W3 = dispatcher lottery (kappa/gamma/jitter) -> improver -> CP-SAT ---
    if wid == 3 and raster is not None:
        drng = random.Random(9099)
        cands = []
        cap = t_start + 0.5 * window
        # v13: rotate ATC kappa x bay-spread gamma x volume-triage alpha.
        # v14: two beam tickets appended ONLY under congestion (forced or
        # overload > 0.44). Appending them unconditionally changed the lottery
        # ROTATION (gi % len(plan)) on easy non-forced instances and lost
        # v13's wrap-around basins (measured: prob_1 @60s 18,357 -> 29,665,
        # pure Z2/Z3 drift with no queues for the beam to fix). Deep admission
        # queues only form under congestion; on the train set every instance
        # with ANY v13 tardiness has overload >= 0.456 while the zero-tardy
        # easy tail tops out at 0.426, so 0.44 keeps v13's W3 lottery
        # byte-exact on the easy tail and gives the tardy class the beam
        # (measured on prob_35, overload 0.621: 2,011,342 -> 1,346,898).
        plan = [(0.5, 0.5, 0.0, None, False), (1.0, 0.5, 0.5, None, False),
                (2.0, 0.5, 1.0, None, False), (4.0, 0.5, 0.0, None, False),
                (1.0, 2.0, 0.5, None, False), (2.0, 0.0, 1.0, None, False),
                (0.5, 1.0, 0.0, None, False), (4.0, 0.0, 0.5, None, False)]
        if forced or overload > 0.44:
            plan = plan + [(1.0, 0.5, 0.0, None, True),
                           (2.0, 0.5, 0.5, None, True)]
        if overload > 1.05:
            # round-3: overloaded non-giant (prob_27 regime, nw=4) -> W3 mixes
            # in jittered target-gated dispatches (the jitter samples around
            # the gate; see W2 note -- construction-level probe says the gate
            # loses, these are cheap lottery tickets only). v14: + a beam ticket.
            plan = [(1.0, 0.5, 0.0, (0.80, "cut"), False),
                    (2.0, 0.5, 0.0, (1.10, "spt"), False),
                    (1.0, 0.5, 0.0, None, True)] + plan
        gi = 0
        while True:
            kap, gam, al, ts_, bm = plan[gi % len(plan)]
            gi += 1
            try:
                cands.append(dispatch(kap, gam, drng, alpha=al, tspec=ts_,
                                      beam=bm, dl=cap if bm else None))
            except Exception:
                break
            if time.time() >= cap or gi > 60:
                break
        if cands:
            # v14: W3 dispatcher polish gains repack rounds (non-giant density +
            # overloaded prob_27).
            polish(min(cands, key=lambda c: c[0])[1], seed=3333, repack_every=4)
        elif time.time() < deadline:  # fallback
            try:
                _, a = build(_area_order(blocks_data) if forced
                             else _edd_order(blocks_data), forced)
                improve(a, seed=3333, repack_every=4)
            except Exception:
                pass
        return

    if forced:
        if wid == 1:
            # v9's giant-winner basin with the FULL budget instead of 65% of
            # the post-construction reserve.
            _, a = build(_area_order(blocks_data), True)
            polish(a, seed=777)
        elif wid == 2:
            # Basin lottery: jittered EDD/AREA multi-start with a different rng
            # than W0's, improve the best. Samples more of the construction
            # space that produced v9's luckiest results.
            rng = random.Random(1414)
            cands = []
            cap = t_start + 0.5 * window
            gens = [lambda: _edd_order(blocks_data, jitter=rng),
                    lambda: _area_order(blocks_data, jitter=rng)]
            gi = 0
            while True:
                try:
                    cands.append(build(gens[gi % 2](), True))
                except Exception:
                    break
                gi += 1
                if time.time() >= cap:
                    break
            if cands:
                polish(min(cands, key=lambda c: c[0])[1], seed=555)
        else:
            # Congestion-aware constructions (kills Pass-A first-preferred-wins;
            # pays an anticipatory price for stuffing crowded bays). gamma=0.5
            # measured best on prob_39 (28.97M vs 29.75M plain EDD); larger
            # gammas over-spread. Jitter around it, improve the best.
            rng = random.Random(1313)
            cands = []
            cap = t_start + 0.55 * window
            # v11: rotate gamma over EDD+AREA (v10.0's varied plans found
            # basins the fixed gamma lost, e.g. prob_28 7.92M), then jitter.
            for order_fn, g in ((lambda: _edd_order(blocks_data), 0.5),
                                (lambda: _area_order(blocks_data), 0.5),
                                (lambda: _edd_order(blocks_data), 2.0),
                                (lambda: _edd_order(blocks_data, jitter=rng), 0.5),
                                (lambda: _area_order(blocks_data, jitter=rng), 0.5),
                                (lambda: _edd_order(blocks_data, jitter=rng), 2.0)):
                try:
                    cands.append(build(order_fn(), True, g))
                except Exception:
                    pass
                if time.time() >= cap:
                    break
            if cands:
                polish(min(cands, key=lambda c: c[0])[1], seed=1313)
    else:
        # Non-forced instances: v9's thorough congestion+EDD+jitter recipe,
        # seed/order-diversified across workers; W3 adds util_gamma.
        edd = _edd_order(blocks_data)
        cong = _congestion_order(blocks_data)
        plans = {
            1: ([(edd, True, 0.0), (cong, False, 0.0)], 111, 777),
            2: ([(cong, False, 0.0), (edd, True, 0.0)], 1414, 555),
            3: ([(cong, False, 0.5), (edd, True, 0.5)], 1313, 1313),
        }
        starts, jseed, iseed = plans[1 + (wid - 1) % 3]
        cands = []
        for order, fc, gamma in starts:
            if time.time() >= deadline:
                break
            try:
                cands.append(build(order, fc, gamma))
            except Exception:
                pass
        rng = random.Random(jseed)
        stale = 0
        best_so_far = min((c[0] for c in cands), default=float("inf"))
        while time.time() < deadline and stale < 4:
            try:
                o, a = build(_edd_order(blocks_data, jitter=rng), forced)
                cands.append((o, a))
                if o < best_so_far - 1e-9:
                    best_so_far = o
                    stale = 0
                else:
                    stale += 1
            except Exception:
                break
        if cands and time.time() < deadline:
            polish(min(cands, key=lambda c: c[0])[1], seed=iseed)


def _worker_main(wid, prob_info, timelimit, t_start, q, inbox=None):
    """Portfolio worker process entry point (must be module-level for spawn)."""
    try:
        _reset_caches()
        state = {"best": float("inf")}

        def push(obj, assign, force=False):
            # Push every new incumbent immediately: improvements are sparse
            # (tens per run) and a lost final put cost prob_31 1.4M in v10.0.
            if obj >= state["best"] - 1e-9 and not force:
                return
            state["best"] = min(state["best"], obj)
            try:
                q.put((obj, assign))
            except Exception:
                pass

        _run_strategy(wid, prob_info, timelimit, t_start, push,
                      inbox=None if wid == 0 else inbox)
    except Exception:
        pass


def _algorithm_portfolio(prob_info, timelimit, t_start):
    import multiprocessing as _mp
    nw = min(4, _mp.cpu_count() or 1)
    if nw < 2:
        raise RuntimeError("not enough cores for a portfolio")
    # Giant forced instances (n>=250, e.g. prob_38/39): ONE dense construction
    # takes ~180s+, so lottery workers (W2/W3, which need several builds) can
    # never contribute, while their builds steal CPU/memory bandwidth from the
    # workers that matter. Run only W0 (v9 replica -- keeps v9's exact result
    # on a clean core) and W1 (AREA basin with a full-budget improver).
    # v12: giants keep W0 (v9 replica) + W1 (AREA basin) but now ALSO run W2 =
    # the raster dispatcher, whose builds are far lighter than the Shapely
    # constructions that forced n>=250 down to 2 workers in v11 (the raster path
    # never runs the expensive per-candidate Shapely scans during construction).
    # W3's multi-start lottery still can't afford several giant builds, so it is
    # dropped. nw=3 measured for RSS safety on prob_38 (see report).
    _pre_bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    # v14: giants go back to 4 workers -- W3 is no longer a lottery (its giant
    # branch in _run_strategy is the cheap repack specialist: one sparse build
    # + inbox-seeded repack improve). RSS measured 2.87GB/3w on prob_38 ->
    # ~4GB/4w, comfortable under 16GB.
    if len(prob_info["blocks"]) >= 250 and _is_forced(prob_info, _pre_bays):
        nw = min(nw, 4)
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    search_deadline = t_start + timelimit * 0.95 - reserve
    ctx = _mp.get_context()
    q = ctx.Queue()
    inboxes = [ctx.Queue() for _ in range(nw)]  # v11 island broadcasts
    procs = []
    for wid in range(nw):
        p = ctx.Process(target=_worker_main,
                        args=(wid, prob_info, timelimit, t_start, q,
                              inboxes[wid]),
                        daemon=True)
        p.start()
        procs.append(p)

    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)

    cands = []
    # Insurance: while workers spin up, the otherwise-idle parent builds one
    # cheap non-dense EDD construction. If memory pressure ever stalls all
    # workers (seen on prob_38: 4 dense builds thrashed 16GB and the queue came
    # back empty), the parent still holds a sane solution instead of the
    # catastrophic empty-bay fallback.
    try:
        _reset_caches()
        quick = _construct(prob_info, _edd_order(blocks_data), bays, bay_u,
                           w1, w2, w3, t_start, t_start,  # deadline past->sparse
                           forced=_is_forced(prob_info, bays))
        cands.append((_objective(quick, blocks_data, bays, bay_u,
                                 w1, w2, w3)[0], quick))
        _reset_caches()  # parent doesn't search further; free the memory
    except Exception:
        pass

    gbest = float("inf")  # v11: broadcast global best to worker inboxes when
    #                       it improves enough to matter (>0.2%)
    while time.time() < search_deadline:
        try:
            item = q.get(timeout=0.25)
            cands.append(item)
            if item[0] < gbest * 0.998:
                gbest = item[0]
                for ib in inboxes:
                    try:
                        ib.put(item)
                    except Exception:
                        pass
        except Exception:
            if all(not p.is_alive() for p in procs):
                break
    # Grace drain: workers check their deadline once per improver round, and a
    # round can take seconds on n=250 -- wait briefly for the final puts.
    grace = t_start + timelimit * 0.95 - reserve * 0.55
    while time.time() < grace and any(p.is_alive() for p in procs):
        try:
            cands.append(q.get(timeout=0.25))
        except Exception:
            pass
    while True:  # final drain (before terminate: a killed mid-put corrupts pipes)
        try:
            cands.append(q.get(timeout=0.05))
        except Exception:
            break
    for p in procs:
        try:
            if p.is_alive():
                p.terminate()
        except Exception:
            pass

    import os as _os2
    _dbg = _os2.environ.get("OGC_DEBUG")
    fallback = _empty_bay_solution(prob_info, bays)
    cands.append((_objective(fallback, blocks_data, bays, bay_u, w1, w2, w3)[0],
                  fallback))
    cands.sort(key=lambda c: c[0])
    hard_stop = t_start + timelimit - 1.0
    # v13 #3c: parent-side Z3 relocation on the winning candidate. Workers run
    # the pass inside polish, but a W0 (v9-replica) win never sees it -- this
    # catches that case. Cheap (~seconds, obj-gated); the relocated candidate
    # goes FIRST in the verify order and the original stays next in line, so a
    # failed official check costs one verify, never correctness.
    if _HAVE_NUMPY and cands and cands[0][0] < float("inf"):
        try:
            z_dl = min(hard_stop - 2.0, time.time() + 5.0)
            if z_dl > time.time() + 1.0:
                rz, oz = _z3_relocate(prob_info, cands[0][1], bays, bay_u,
                                      w1, w2, w3, _Raster(prob_info, bays),
                                      z_dl)
                if rz is not None and oz < cands[0][0] - 1e-9:
                    cands.insert(0, (oz, rz))
        except Exception:
            pass
    if _dbg:
        _el = time.time() - t_start
        _objs = sorted(c[0] for c in cands)[:5]
        print(f"[parent] ncands={len(cands)} elapsed={_el:.1f} hard_stop_in="
              f"{hard_stop - time.time():.1f} best5={[f'{o:.3g}' for o in _objs]}",
              flush=True)
    _nver = 0
    # Absolute cutoff just under the contract limit. We ALWAYS verify at least the
    # single best candidate (check_feasibility is ~0.15s even for n=250): this is
    # the guard against the empty-bay catastrophe when the end-phase drain has
    # eaten past hard_stop under load, which otherwise threw away a ready 15M
    # solution for the 1.9e9 fallback.
    abs_stop = t_start + timelimit - 0.3
    for _, assign in cands:
        now = time.time()
        if now > abs_stop:
            break
        if _nver >= 1 and now > hard_stop:
            if _dbg:
                print(f"[parent] hard_stop hit after {_nver} verifies", flush=True)
            break
        _nver += 1
        sol = {"operations": _build_operations(assign)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            continue
        if res["feasible"]:
            return sol
    # Last resort: empty-bay (structurally feasible).
    return {"operations": _build_operations(fallback)}


# -----------------------------------------------------------------------------
# Required entry point
# -----------------------------------------------------------------------------

def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    try:
        return _algorithm_portfolio(prob_info, timelimit, t_start)
    except Exception:
        # Multiprocessing unavailable/broken -> v9 single-thread pipeline with
        # whatever budget remains.
        return _algorithm_single(prob_info, timelimit, t_start)
