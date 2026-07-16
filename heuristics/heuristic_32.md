# Heuristic v32 — RADICAL EPOCH: four parallel architecture rewrites (goal < 110,000,000)

User directive (2026-07-16): "ideate radical changes, multi-axis thinking or
completely rewriting the architecture... multiple different strategies as
starting points, working in parallel."

Diagnosis the strategies share: v25's incumbents are JOINT fixed points of
(admission order x placement x bay assignment x timing) under a forward-
greedy decoder + local search. Ten single-axis mechanisms died in v28-v30.
The four arms below each change the PARADIGM, not a knob. Each is a
standalone `algorithm(prob_info, timelimit)` file (baseline/radical_*.py),
benched directly against banked cells — integration under min-wins only for
winners, so no displacement laws apply during exploration. All may reuse
v25's raster/scan/objective machinery via `import myalgorithm_25`.

## S1 — BRKGA: evolve the DECODER INPUTS (biased random-key GA)

The v29 lesson: forced foreign orders realize catastrophically because only
the greedy decoder knows geometry. So search the space the decoder maps
well: genome = (priority-key vector over blocks, bay-bias matrix, small
decoder-policy genes); decode via the existing event-driven dispatcher
(keys replace ATC priority; bay bias tilts bay-choice economics); fitness =
true internal objective. Population ~30, elite-biased crossover, warm-start
elites from perturbed v25-champion keys (extract the champion's realized
order once, rank-encode). Every genome realizes FEASIBLY by construction —
no realization gap, co-adaptation emerges from selection. Giants: builds
1-3s -> ~200-500 decodes/600s; mid-tier: thousands.
Kill: after tuning one generation-budget knob, best-ever < banked on both
{26,27}.

## S2 — BACKWARD (due-date-anchored) construction

All 30 versions construct forward from releases (tardiness = what's left
over). Backward instead: process blocks in DESC due order, place each at
its LATEST feasible entry (exit = due where possible), building the
schedule right-to-left in time; then a forward legalization pass fixes
release violations by left-shifting. The fixed point of backward-greedy is
a different basin family than forward-greedy's — the cheapest true
paradigm flip available. Crane checks must run in reverse-time semantics
(entry of A after exit of B in real time = the reverse in build order).
Then one v25-style improve pass on the legalized result.
Kill: < banked on all of {26,27,33} after one ordering-variant sweep.

## S3 — PARTITION-FIRST: bay assignment as a first-class search level

Currently bay choice is a local economic decision inside dispatch; the
partition of blocks across bays is an emergent accident. Rewrite: solve an
assignment-level CP-SAT (blocks -> bays; capacity = calibrated area-time
budget per bay from v25's realized densities; objective = preference +
balance + a congestion proxy) and enumerate K=5 DIVERSE partitions via
no-good cuts; for each, run the v25 dispatcher CONSTRAINED to the
partition (bay_preferences overridden to lock assignment); polish the best
two. Searches the one axis no mechanism ever touched: WHICH BLOCKS COMPETE
for the same floor.
Kill: all K partitions realize worse than banked on {27,31}.

## S4 — SOLUTION MERGE: cross-candidate recombination (path relinking)

The portfolio already produces 20-30 diverse full solutions per run whose
UNION contains better mixtures — never recombined (min-wins keeps exactly
one). Standalone: run v25 to harvest all worker candidates (on_best/inbox
streams exist); build a placement POOL per block (its placement in every
candidate + entry/exit); solve a recombination CP-SAT: pick one placement
per block from its pool, pairwise space-time-crane compatibility from
rasterized checks, minimize true objective. Restricted to pools of ~5-15
per block this is a large but sparse binary model; warm-start = best
candidate; even a few hundred improved picks = a new basin. This is the
only arm that does true JOINT order+geometry moves.
Kill: CP-SAT finds nothing better than warm start on {26,27} within budget.

## Shared protocol

- prob_1 is NOT a guard here (standalone files replace the whole
  algorithm); instead every arm must return feasible on prob_1 and {26,27}
  (check_feasibility gate inside the file, fallback = v25 delegation).
- Spot queue (serial, detached): each arm {26,27} @600s vs banked
  (8,551,513 / 24,972,962). Any win >= -100k -> extend to {38,39,31,33,37}.
- Winners integrate as an extra portfolio arm under min-wins (post-race,
  sub-second gating per the displacement laws) -> full-40 row.
- 31a (epoch reset, prior plan) continues in parallel as a fifth thread.

## Results

(pending)
