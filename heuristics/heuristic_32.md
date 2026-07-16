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

### Smokes (agent-run, short budgets, prob_1 banked = 18,357)

S4 merge 4,035 (43s) / S1 BRKGA 13,514 (30s) / S3 partition 41,465 (37s) /
S2 backward 144,372 single-thread 30s (vs 166,743 M25-single reference).

### S4 prob_1 @60s official bench (2026-07-16) — CONFIRMED NEW CELL LEVEL

**prob_1 = 4,035** (35.9s, feasible, obj1=0.0 obj2=5 obj3=20) vs banked
18,357 = **−14,322 (−78%)**. Harvest 9 distinct portfolio candidates,
pool_avg 6.4 placements/block, 33,180 pairwise checks → 4,439 incompatible
pairs, CP-SAT merged the union into a zero-tardiness mixture. First
sub-banked cell of the campaign since v25. The portfolio has been
discarding this recombination value on every instance for 25 versions.

### S4 {26,27} @600s — merge gain ZERO on forced; harvest split costs

prob_26 = 8,551,513 (warm = banked; merged_gain=0 from 14 candidates,
pool_avg 8.1). prob_27 = **25,532,585 (+559,623)** — the 70% harvest
produced a degraded champion (27's race sensitivity; near the fallback
basin) and merge gained 0 on top. VERDICT: on saturated forced instances
the harvested candidates share the same structural queue — their union
spans no better mixture. S4's value concentrates on non-forced,
low-tardiness instances. INTEGRATION SHAPE (strictly-safe): full v25
portfolio unchanged (100% budget), harvest streamed candidates for free,
merge ONLY in leftover tail budget on instances that converge early;
skip on forced (measured gain 0). Estimated yield: −1M to −4M across the
non-forced cells (1-20, 24/25/29/32/34/35/36/40 class).

### S1/S2 standalone spots — both KILLED on forced

S1 BRKGA @600s: 26 = 11.14M (+2.58M), 27 = 30.5M (+5.5M) — 95-120 decodes
can't match the portfolio. Also prob_1 @60s = 34,511 (high variance, 6
gens). S2 backward @600s: 26 = 44.3M, 27 = 198.2M — due-anchoring leaves
massive tardiness on burst instances. LAW: no standalone single-process
constructor competes with the 4-worker portfolio+polish; radical arms'
value = post-race recombination (S4) and diversity feeding, not
replacement.

### v33 (v25 + self-gating merge tail) — BANKS on prob_1 @600s

myalgorithm_33.py: v25 byte-identical + candidate retention (read-only on
the existing stream) + post-race merge in the leftover tail (gate:
not-forced, ≥3 candidates, ≥6s tail; CP-SAT warm-started, official-check
accepted). prob_1 @600s (row conditions): **8,849 vs banked 18,357 =
−9,508 (−52%)**, merge fired with 41.3s tail, 10 candidates. @60s the
tail is only ~8s and the merge finds nothing (gain 0, harmless). Mid-tier
spot {21,28,32,34,40}: 21/28/34 fired-gain-0, 32 initially +191k from a
forced-path displacement (FIXED: forced path made token-identical to v25;
prob_32 verified restored), 40 flat. Non-forced sample {20,24,25,29,35}:
29 banked −201, rest fired-gain-0. v33 PROMOTED: row `algorithm 33` =
124,572,186 (−9,709), myalgorithm.py = v33.

### Pool-diversity ceiling experiment (exp_pool_diversity.py, 2026-07-17) — CLOSED

Control (champion + 14-15 v25 candidates) vs FULL (+ 9-10 diverse solutions
from S1/S2/S3; pool 18.2/18.1 avg placements per block, ~1,500
diverse-exclusive), 300s CP-SAT, offline:
- **prob_27: control = full = champion exactly.** Hint accepted, rich pool,
  generous solve → ZERO recombination value.
- **prob_26: the model cannot represent the champion** — full merge's best
  (10.44M) is WORSE than its own hint (8.55M), meaning the pairwise
  space-time-crane compatibility abstraction excludes the true schedule
  (crane feasibility on dense instances depends on 3-way replay ORDER that
  pairwise constraints cannot capture).
VERDICT: cross-paradigm recombination on forced instances is dead — by
absence of value (27) and by model inexpressibility (26). S4's scope is
final: non-forced tail only.

### v34 (obj1-frozen obj2/3 tail on forced) — flat; ~7M obj2/3 mass LOCKED

myalgorithm_34.py: post-race time-frozen relocation/rebalance, exact
accept, double obj1-freeze guards. Spot {38,27,31} @600s: tail fired on
all three (40-50s windows) with ZERO accepted moves — no off-preference
block has ANY feasible time-frozen relocation (preferred bays
space-saturated at those intervals), no rebalance move nets positive.
The forced obj2/obj3 mass is structurally locked. v33 stays promoted.

### 1800s budget probe — prob_38 byte-flat at 3x budget

bench.py myalgorithm_33 1800 38 → 36,351,493 (1701s), bit-identical
objective components. The giant basin is time-invariant; budget scaling
is closed (extends the v18-era 2x finding to 3x on v25 machinery).

### FINAL EPOCH STATE (2026-07-17)

Frontier: v33 = 124,572,186 (row `algorithm 33`, myalgorithm.py).
Goal <110M: every constructible route measured closed on the forced mass
(~103M): 10 single-axis mechanisms (v28-30), fresh epochs (31a), 4
paradigm rewrites (S1-S4 standalone), cross-paradigm recombination,
obj2/3 relocation, 3x budget. Remaining live work: v33 merge-tail
harvest on the 20 never-measured non-forced cells (sweep running) —
expected yield 10k-100k. The evidence supports renegotiating the goal.
