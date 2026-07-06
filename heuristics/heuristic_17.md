# Heuristic v17 — basin restoration + exact packing windows (goal < 150M)

## Diagnosis from v16 (projected ~151.28M; need ~1.3M)
1. **~0.6M of the gap is displaced v13 basins, recoverable deterministically.**
   Per-instance best-known across v13..v16 rows sums to 150.69M. v13's full
   row beats the current state on {21: 1,380,772, 28: 3,565,230, 29: 557,994,
   30: 4,219,267, 33: 9,921,419, 34: 2,048,624} — v14's polish changes
   (repack rounds altering rng pacing, v15's harvest cycles replacing
   improve-2) displaced those winners as side effects. Within-version
   determinism (v15/v16 finding) means reconstructing v13's exact polish
   paths in dedicated worker slots reproduces those draws exactly.
2. **The remaining ~0.7M needs a NEW mechanism.** Seven ordering/portfolio
   families are dead on the saturated set. The one untried family: EXACT
   simultaneous multi-block placement — CP-SAT over candidate menus
   (CONTEXT.md's candidate-placement MIP, never attempted). Greedy rebuild
   orders (v14 repack) reach some interlocks; exact selection over K
   raster-feasible placements per block reaches provably better ones.
   Targets: 39 (12.36M vs 1.3M fluid LB — biggest ratio), 26 (9.65M vs
   5.1M), 23, 33.

## THREE improvements (v17)
0. (diagnostic precursor, do first) **Winner attribution probe**: patched
   parent (probe only, not the module) logging which worker/phase produced
   the verified winner, run on {21,28,29,30,33,34} under v13 code — tells
   exactly which slot/plan/seed to reconstruct.
1. **v13 basin restoration.** Per attribution: dedicate slots/plan entries
   reproducing the winning v13 paths byte-exactly (v13's polish = improve →
   cpsat → improve, no repack, no cycles, original seeds/pacing) on
   non-forced instances while the v15/v16 paths keep their own slots on the
   instances THEY win. Where slots collide, split by instance-computed
   regime only if a clean rule exists (forced/non-forced already separates
   most); otherwise prefer covering the larger objective mass.
2. **Exact packing window (CP-SAT matheuristic).** New polish move for
   density-limited instances: select congested (bay, window) as in repack;
   destroy set D (cap ~18 for model size); for each block in D enumerate up
   to K (~25) raster-feasible candidate placements (position x orientation,
   scoped occupancy of undestroyed neighbors); precompute pairwise
   compatibility via raster mask intersection + entry/exit prism rules
   (cached, same soundness contract as v12 raster); CP-SAT model: exactly-one
   placement per block, no incompatible pairs co-selected with overlapping
   time, integer entry times, minimize w1*tardiness (+ small w3 term);
   time-budgeted (~10-20s per window), obj-gated accept, official-verify
   safety unchanged. ortools guarded (env-optional): if absent, fall back to
   v14 greedy repack. Wire into the reclaimed giant/overload slots (v16's
   free compute) and W2/W3 polish on density-limited non-forced.
3. **Full-40 assembly check.** After 1+2, projected best-known union +
   exact-window gains must clear 150M on the spot sets before the full
   bench: gate = {21,28,29,30,33,34} reproduce v13 values exactly AND
   {39,26} improve by >= 300k combined.

## Budget & mechanics
- Same rules; file baseline/myalgorithm_17.py from v16 (commit db9a782).
- Ladder: (0) attribution probe (6 x 300s under v13); (1) units: restored
  paths byte-match v13 draws on 2 probe instances; exact-window soundness
  (every CP-SAT-selected placement passes _can_place + official check);
  (2) spot @300s: {21,28,30,33,34} vs v13 values + {39,26} vs v16; (3)
  protect: {38,27,35,31,1}; (4) full-40 bench_row @300s.

## Results (filled after testing)

### Step 0 — attribution probe (m13a, fixed spawn-guard driver bug: first
### pass silently fell back to v9 — caught because prob_21 == v9's exact value)
- 21: W3 polish improve(s3333, no repack) -> CPSAT (1,380,772 reproduced)
- 28: W3 raw lottery build, t=80.3 (3,565,230 reproduced)
- 29: W3 raw lottery build #4, t=10.7 (557,994 reproduced)
- 30: W3 raw lottery build, t=72.1 (4,219,267 reproduced; forced instance)
- 33: W3 raw lottery build, t=116.9 (9,950,093 vs row 9,921,419 -- late-
  lottery build, pacing-sensitive +-30k)
- 34: W2/W3 Z3-relocation endgame (2,048,624 reproduced)
Displacement mechanism: v14's beam tickets changed the lottery ROTATION
(len 8 -> 10) and v14's repack_every changed polish improve-1 pacing.

### Restoration (ladder pass 1) — ALL FIVE SPOT TARGETS BYTE-MATCH v13
21 = 1,380,772 / 28 = 3,565,230 / 30 = 4,219,267 / 33 = 9,921,419 /
34 = 2,048,624  (sum -562,184 vs v16 basis; 29 untested but same slot,
projected -20,577).

### Gate {39,26} — MISSED on pass 1
39 = 12,361,461 (flat vs v16; exact-pack netted zero there in full runs).
26 = 10,027,385 (+373,895 REGRESSION): giving W3-forced the v13 rotation
recovered 30/33 but destroyed 26's banked winner (a W3 polish on a
BEAM-build input). REPAIR (build B): W3-forced beam rotation restored
verbatim; the v13 rotation clone moved to W0's forced-non-giant slot (v9
replica is provably valueless there: 1.5-5x worse on every such instance in
results.csv). Repair re-run of {26,30,33,23,31} pending at report time.

### Exact packing window — sound, real but small
Three debugging iterations: (1) pair_cap bail -> adaptive menu shrink
(K 25->12->6->4); (2) empty menus (clearance vs the whole widened span is
impossible in congested bays) -> window-limited actives + var-fixed timing
constraints for EVERY candidate; (3) decisive: conservative mask relations
false-positive on every nestled pair, making the incumbent interlock
infeasible in-model (best 411 > incumbent 345 on prob_26) -> two-tier
relations (mask prefilter + exact cached geometry, _cpsat_retime's audited
encodings). Final config D=14, K=12, ~15s/shot, top-8 window rotation.
Measured: officially-feasible -26,666 accepts on BOTH prob_39 and prob_26
units (~1/8 shots); many windows prove OPTIMAL at the incumbent. In full
runs the accepts did not beat the portfolio best on the gate pair ->
net contribution ~0 measured. Soundness: zero exact-validation failures,
zero official-check failures across all accepts.

### Protect (pass 1)
38 = 45,806,839 flat / 27 = 29,198,468 flat / 35 = 1,346,898 held /
31 = 11,268,243 flat / 23 = 3,390,436 flat / prob_1 @60s = 18,357 exact.

### Repair re-run (final build) — 5/5 CLEAN
26 = 9,653,490 RESTORED (rotation was the whole story; exact-shot pacing
innocent) / 30 = 4,219,267 v13-exact via the W0 clone slot / 33 = 9,921,419
v13-exact via W0 (even the pacing-sensitive late-lottery draw landed) /
23 = 3,390,436 flat / 31 = 11,268,243 flat.

### Projection (all restoration numbers measured on the final build)
v16 basis 151,286,060 - 562,184 (measured restoration) - 20,577 (29,
projected, same slot probe-reproduced) ~= 150.70M. Goal <150M NOT reached:
the exact-pack prong underdelivered its ~0.7M (real mechanism, ~-27k per
accepted window, too few accepts inside the portfolio). Remaining honest
levers: none cheap -- the saturated pair (38/27) has now survived eight
mechanism families; the next escalation would be exact packing at whole-bay
scale (minutes-class solves).

## FINAL RESULT (results.csv row `algorithm 17 (4w 300s)`)
**Full-40 @300s = 150,701,580, 40/40 feasible — new SOTA, −1,004,134 vs
v14's recorded 151,705,714 (v15/v16 unbenched interims).** Projection hit
exactly (150.70M). myalgorithm.py promoted to v17. Surprise row wins:
prob_3 66,730 (−23.5k, first move since v3), prob_13 −8.8k, prob_25 −6.6k,
prob_8 −1k. Row-hygiene targets for v18: prob_9 +11.2k / prob_14 +10.6k /
prob_16 +4.1k (v14-era draws displaced), prob_39 +13.6k (spot draw
12,361,461 not reproduced in full run — pacing). Gap to <150M: 701,580.
