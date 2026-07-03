# Heuristic v13 — raster-repair improver + volume-aware triage (goal < 150M)

## Diagnosis from v12 (174.59M @4w/300s; need −24.6M)
Instrumented v12 runs on the six biggest losers (38: 49.4M, 27: 31.9M, 39:
15.3M, 31: 12.9M, 26: 12.7M, 33: 11.1M = 133.3M of 174.6M):

1. **Residual is DENSITY — specifically concavity waste.** Tardiness is still
   100% entry-wait, diffuse. During the backlog window bays run only 45-53%
   mean / 52-59% peak area density, yet **bounding-box density is 0.73-1.01 —
   the layouts are bbox-saturated.** The missing floor is INSIDE the bboxes:
   shapes fill only 57-72% of their own bounding boxes (prob_26 worst: 0.57).
   Concave interlock placements are structurally unreachable because the
   IMPROVER still enumerates only AABB-corner candidates
   (`_candidate_positions`); the raster full-position scan exists only in the
   dispatcher construction. An exhaustive crane-feasibility probe on prob_38's
   idle steps found 0-3 admissible placements despite 500-1600 free area units
   — free space is fragmented concave scrap.
2. **Triage on the oversubscribed pair (38/27).** At v12's own effective
   density, v12 ≈ the fluid-EDD bound (triage near-optimal *given EDD
   discipline*), but EDD is the wrong discipline under overload: fluid-SPT
   (sacrifice few LARGE area×proc blocks instead of democratic lateness) cuts
   the fluid bound ~40% on 38 (48.0→28.8M) and ~33% on 27. The dispatcher's
   ATC uses 1/proc only — blind to footprint area, i.e. to the real
   space-time volume a block consumes.
3. **Fragmentation is unmanaged:** adjacent blocks' exit times are
   uncorrelated (|Δexit| = random baseline), so holes open scattered, one at
   a time, each concave. Zero exit-delay anywhere (prompt exits work).
4. **Code audit findings:** cand_cap=12 cliff (block rejected though a 13th
   cell fits); no scan cache, footprint recomputed per bay-sort key, sched
   never prunes exited blocks (O(n^2) on giants); ATC jitter mis-scaled
   (additive 0.15 dominates small indices — randomizes instead of perturbs);
   giants (nw=3) never run the kappa/gamma lottery (W2 = single kappa=1
   build); CP-SAT retime silently no-ops on giant bays (>4000-pair cap);
   Z3 on prob_31 = 2.77M (21.5% of its objective), 143/200 blocks off-pref.
   NOTE: a diagnostic claim that "W0 wins the giants / raster contributed
   nothing" was traced to a clobbered comparison file and is FALSE — the
   dispatcher produced the v12 giant wins (objective arithmetic: 49.4M vs
   W0-replica's ~91M level).

## THREE improvements (v13)
1. **Raster-windowed repair in the improver (all six targets).** Give the
   worker's `_Raster` to `_improve`: for each candidate entry time in
   `_find_earliest_slot`/`_find_zero_slot`, build occupancy from only the
   time-overlapping blocks, full-position scan, enumerate feasible cells
   (contact/BL-ordered), keep `_can_place` as the exact gate. Gate to
   forced/congested instances (raster repair costs more per move but reaches
   packings AABB corners never propose — that is the density lever). Adaptive
   cand_cap: 12 → 48 when the entry queue is deep. Position quality upgrade
   used by BOTH dispatcher and raster-repair: prefer cells maximizing contact
   with occupied+wall cells (perimeter match), tie-break toward neighbors
   with similar exit times (exit-cohort zoning) so holes coalesce instead of
   scattering.
2. **Volume-aware triage + giant lottery (38/27, plus 33).** Generalize the
   ATC index to space-time volume: priority ~ 1/(a_i^alpha · p_i) ·
   exp(-max(0,slack)/(kappa·pbar)), alpha rotated in {0, 0.5, 1.0} (alpha=0 =
   v12's ATC; alpha>0 deliberately strands large-footprint long blocks under
   overload, mirroring fluid-SPT). Fix jitter to multiplicative. Give giants
   the lottery: inside W2's slot on nw=3 instances run 3-4 dispatches
   (alpha/kappa rotation) before polish — raster builds are cheap (audit) and
   giants currently get exactly one. W3's lottery gains the alpha dimension
   everywhere else.
3. **Throughput + endgame fixes.** (a) Perf: scan cache per
   (bay,bi,oi,ver), footprint/util cache per (bay,ver), prune exited blocks
   from dispatcher sched, exit-time set instead of O(n) heap membership,
   drop zeroed occupancy layers. These multiply dispatcher builds and
   improver rounds everywhere. (b) CP-SAT giant fix: time-window
   decomposition — retime only blocks whose [entry,exit) intersects a
   sliding window (pairs under cap), iterate windows most-tardy-first.
   (c) Z3 endgame pass: after the improver, for each off-preference block
   try a tardiness-neutral move to its preferred bay (raster scan for a
   feasible same-interval slot); pure Z3 profit, targets prob_31 (+38/27
   small). Never touch W0 (byte-exact anchor stays).

## Expected attack
prob_38 −10-20M (density + alpha-triage), prob_27 −6-12M, prob_39 −4-8M,
prob_31 −3-5M (density + Z3 pass), prob_26 −4-7M (worst poly/bbox, gains most
per density point), prob_33 −3-6M, mid-tier inherits raster-repair/perf wins.
Need −24.6M overall; plan headroom ~2x that.

## Budget & mechanics
- Implementation by Opus agent (goal-session directive); single file
  baseline/myalgorithm_13.py from myalgorithm_12.py; numpy+shapely only
  (ortools guarded); Windows spawn-safe; W0 untouched.
- Test ladder: (1) smoke prob_39+prob_26 @60s vs v12 same-budget; (2)
  focus-6 {38,27,39,31,26,33} @300s serial (v12 = 133.28M; gate: < 112M);
  (3) regression spot-check prob_1/5/20 @300s (raster-repair must not hurt
  the zero-tardiness easies); (4) full-40 bench_row @300s quiet machine.

## Results (filled after testing)
