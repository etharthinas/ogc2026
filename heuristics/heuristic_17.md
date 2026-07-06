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
