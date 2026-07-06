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

Implemented in baseline/myalgorithm_13.py (from v12). W0 byte-exact anchor
untouched. Correctness: dispatcher byte-reproduces v12 at alpha=0/score_pos off
(0/250 diffs, prob_39); scan_scoped sound (0/1503 exact-check violations);
every reported solution passes the parent's official check_feasibility
(stage=5). Peak python RSS on prob_38 (3 workers) = 2.83 GB. Env: .venv_ogc,
serial @300s, quiet machine.

Focus-6 @300s (v12 -> v13, obj):
| prob | v12         | v13         | delta       |
|------|-------------|-------------|-------------|
|  38  | 49,420,035  | 45,806,839  | -3,613,196  |
|  27  | 31,929,802  | 29,198,468  | -2,731,334  |
|  39  | 15,300,889  | 13,979,218  | -1,321,671  |
|  31  | 12,880,039  | 11,305,550  | -1,574,489  |
|  26  | 12,689,104  | 11,368,821  | -1,320,283  |
|  33  | 11,055,920  |  9,921,419  | -1,134,501  |
|total | 133,283,789 | 121,580,315 | -11,703,474 |
-8.78% overall. GATE (<112M) NOT met -- short by 9.58M.

Smoke @60s: prob_26 13,148,749 -> 11,471,802 (-12.8%); prob_39 15,300,889 ->
13,979,218 (-8.6%). (v12 prob_39 @60 == @300: v12 was frozen at the AABB
density ceiling; v13 raster repair breaks it -- direct evidence of lever #1.)

Regression @300s (easies, all Z1=0 preserved -> NO tardiness regression; all
IMPROVED via the dispatcher's contact-scoring on w3):
| prob | v12     | v13     |
|------|---------|---------|
|  1   | 64,891  | 27,969  |
|  5   | 105,279 | 97,253  |
|  20  | 209,325 | 198,806 |

Lever attribution (analytic, from Z-splits -- per-worker winner logging NOT
instrumented): #1 raster repair drove the Z1 (density) drops everywhere,
starkest on prob_39 (v12 frozen -> -1.3M) and prob_31 (Z1 10.09M -> 8.55M,
-15%). #2 volume-aware alpha triage + giant W2 mini-lottery drove the giant
Z1 wins (38 -3.6M, 27 -2.7M). #1's contact scoring in the dispatcher drove the
easy-instance Z3 wins (prob_1 Z3 64.8k -> 26.8k). #3a throughput caches gave
~5% faster dispatcher builds (byte-repro run 5.5 -> 5.2s), feeding more
rounds/builds everywhere.

## Round 2 (coordinator follow-up): #3c + wider repair gate + #3b

Added in the same file: (1) `_z3_relocate` -- preference-relocation endgame,
run at the tail of every polish AND parent-side on the winning candidate;
generalized beyond tardiness-neutral: same-interval move first, then
alternative entry times gated by the EXACT objective delta
(w1*d_tard + w2*d_imbal - w3*gain < 0), candidate times latest-first within a
tardiness tier (bays drain over time). (2) Raster-repair gate widened from
forced-only to forced OR best_tardy > 0 (zero-tardiness easies keep AABB
repair). (3) `_cpsat_retime_window` -- CP-SAT time-window decomposition for
bays over the 4000-pair cap: chunks of <=55 blocks by entry time, variables
confined to a LEFT-EXTENDED window, temporally-overlapping outsiders as fixed
constants with exact crane-tie encodings, most-tardy chunks first.

Micro-validation: relocated prob_31 solution passes official check (stage=5),
obj1 invariant on the same-interval path; windowed CP-SAT model solves without
error on prob_39/38 giant bays (var-fixed encodings verified against the
_present_at_entry/_present_at_exit tie rules).

Focus-6 @300s FINAL (serial, quiet):
| prob | v12         | v13 final   | delta       |
|------|-------------|-------------|-------------|
|  38  | 49,420,035  | 45,806,839  | -3,613,196  |
|  27  | 31,929,802  | 29,198,468  | -2,731,334  |
|  39  | 15,300,889  | 13,978,536  | -1,322,353  |
|  31  | 12,880,039  | 11,293,179  | -1,586,860  |
|  26  | 12,689,104  | 11,367,852  | -1,321,252  |
|  33  | 11,055,920  |  9,921,419  | -1,134,501  |
|total | 133,283,789 | 121,566,293 | -11,717,496 |
GATE (<112M) NOT met; also above the ~115M projection bar. Round-2 passes
added only -14k on focus-6.

Mid-tier @300s (the wider-gate + endgame targets -- BIG wins):
| prob | v12       | v13       | delta    |
|------|-----------|-----------|----------|
|  23  | 4,584,164 | 3,819,621 | -16.7%   |
|  35  | 2,347,358 | 2,011,342 | -14.3%   |
Easies: prob_1 @60s = 18,357 (v12 @300s: 64,891; Z1=0 kept) -- the Z3
relocation pass works where free space exists.

HONEST NEGATIVE RESULTS (measured, not speculation):
* The "8.5M recoverable Z3" hypothesis is FALSE on the forced/congested
  instances: preferred bays are space-saturated across the entire usable
  horizon (that is WHY blocks went off-preference), and w1 >> w3-per-block
  (budget/w1 ~ 1 tardiness unit) leaves no timing room. Measured: prob_31
  -12k of 2.74M, prob_38/27/33 zero moves. The Z3 money on forced instances
  is structural, not endgame-recoverable by single-block relocation.
* CP-SAT retime (full AND windowed) finds ZERO improvement on the giants'
  post-improver schedules (prob_38: 30s budget, 3.3k raw tardy units, no
  window improved) -- with geometry fixed and prompt exits the dispatcher/
  improver schedules are already retime-tight. #3b stays (harmless, budget-
  bounded, may fire on other instances) but is not a giant lever.

Full-40 projection: measured deltas sum to ~-12.9M on the 9 measured
instances; if the unmeasured mid-tier tardy instances (21/28/30/32/37/22...)
improve like 23/35 (-14..17%), full-40 lands ~157-160M -- under v12's 174.6M
but likely ABOVE the 150M goal. The residual is prob_38/27's structural
overload (75M together vs fluid-SPT bound ~29M+22M): closing THAT needs a
tardiness-aware triage that abandons whole blocks' due dates strategically
(fluid-SPT basin), not more geometry.

## Round 3: fluid-target admission gate (structural-overload lever) — NEGATIVE

Implemented in full: `_overload_ratio` (area*time demand / capacity*time over
the due horizon; prob_38=1.14, prob_27=1.19, all other train <=0.94 ->
threshold 1.05 isolates the pair), `_fluid_targets` (deterministic greedy
step-profile loader; disciplines: 'spt' small-a*p-first, 'band' due-banded
SPT, 'cut' pure sacrifice = hold back only the largest-a*p volume excess and
earliest-fit it into the post-burst tail), dispatcher `targets` param (event
seeding, admission gate `t < target -> skip`, ATC urgency keyed on
max(due-slack-point, target) so un-sacrificed blocks keep exact v12 urgency).
Byte-repro invariant preserved (targets=None: 0/250 diffs vs v12).

Construction-level probe (kappa=1, gamma=0.5, alpha=0, deterministic; realized
= internal obj of the raw dispatch):

prob_27 (plain 29.20M): spt C=0.60/0.66/0.72 -> 56.7/49.6/44.0M; spt C=1.00/
1.10 -> 34.3/30.6M; band C=1.10 -> 33.6M; cut C=0.50..0.80 -> 34.6..30.5M.
prob_38 (plain 45.86M): spt C=0.66 -> 53.1M ... cut C=0.80 -> 46.6M; best
gated variant 46.6M. EVERY gate variant loses to plain on BOTH instances;
monotone in C with plain as the limit.

Why the diagnostic bounds (38: 28.8M @C=0.66, 27: 19.2M @C=0.62) don't
realize: (a) the non-preemptive greedy loader is ~40% tighter than the
preemptive fluid bound at equal C (my C=1.00 fluid Z1 = 30.0M/20.7M ~= the
reference bounds); (b) the realization penalty on top of ANY target schedule
is a stable ~13-22M: holding the big blocks back does NOT let the masses run
on time -- they still queue on fragmentation + crane blocking, so the
schedule pays the sacrifice AND most of the original queue. The ungated
"everyone slightly late" equilibrium dominates every "few very late + masses
on time" schedule we could realize.

Wiring kept (cheap lottery tickets, best-of-protected): W2 forced plan on
overload>1.05 adds (0.80,cut)/(1.10,spt)/(0.70,cut) after the plain entries;
W3 prepends 2 jittered gated entries. Bench @300s serial (3.9GB free RAM,
quiet): prob_38 = 45,806,839, prob_27 = 29,198,468 -- BYTE-IDENTICAL to
round-2 (gated candidates never won best-of; no regression, no gain).

Coordinator target (pair <= ~68M) NOT met: pair stays 75.0M. Verdict: the
overload residual is not reachable by admission-order/timing levers over
fixed one-shot geometry. What the evidence points at instead: the ~15M
realization penalty IS the lever -- burst-window packing density (deeper
geometric search during the backlog: e.g. multi-position lookahead per
admission event, or re-packing the standing queue's bay jointly) rather than
WHO gets admitted WHEN.
