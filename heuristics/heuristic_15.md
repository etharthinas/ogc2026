# Heuristic v15 — cross-bay repack + basin-diversity harvest (goal < 150M)

## Diagnosis from v14 (validation −3.56M vs v13; full-40 row pending ~152M)
1. **Joint repack works exactly where geometry is the binding constraint**
   (39 −1.60M, 26 −1.71M, 23 −0.43M) but v14 windows are SINGLE-BAY: the
   move can re-interlock a bay but cannot rebalance across bays, recover
   preference (Z3 needs bay changes), or relieve one bay by exporting a
   block. prob_31 (Z3 2.82M, 25% of obj), 33, 30, 34 sit exactly there.
2. **The lottery noise band is real money.** Measured run-to-run spreads at
   identical code: prob_35 1.35M vs 1.75M (400k), prob_31 ±255k, prob_33
   ±277k, 30/34/28 ±80-100k. Across the ~10 noisy instances the good-tail
   vs bad-tail spread is ~1-1.5M. v14 takes ONE long polish per worker —
   one draw per worker per instance. Nobody harvests the tail.
3. **CP-SAT retime is measured-zero on all forced instances** (v13 r2:
   zero moves, full and windowed) yet still burns its 0.12·window budget
   inside every forced polish. Dead weight to refund.
4. 38/27 saturated across four lever families; only genuinely new
   mechanisms (cross-bay is one) get a shot; no more variant-tuning there.

## THREE improvements (v15)
1. **Cross-bay window repack.** Extend `_repack_window` with a cross-bay
   mode: pick a time window (congestion- or Z3-scored), destroy
   intersecting blocks across ALL bays (cap ~40, prefer tardy + off-pref),
   rebuild with FREE bay choice (restricted dispatch over destroyed set,
   all bays open, k orders as in v14, bay economics w1/w3-aware). Alternate
   single-bay and cross-bay modes round-robin. New capability: inter-bay
   rebalancing + Z3 recovery inside one obj-gated move. Targets 31/33/30/34
   (+1 fifth-family shot at 38/27; expectations low there).
2. **Basin-diversity harvest.** Restructure worker polish from one long
   improve into 2-3 independent cycles: cycle = improve(seed_i, budget/k) +
   repack rounds; each cycle starts from the best-so-far assignment but a
   DIFFERENT rng stream; every cycle-best is pushed to the parent (min
   wins). Rotate repack window width in {1, 2, 3}·pbar across cycles.
   Directly harvests the measured 250-400k per-instance spread instead of
   praying on one draw.
3. **Budget refund + Z3-scored windows.** (a) Skip CP-SAT retime entirely
   on forced instances (measured zero twice); refund the ~0.12·window to
   repack/cycles. (b) Window selection gains a Z3 term: score += w3 ×
   (recoverable preference gap of off-pref blocks in window) so cross-bay
   repack aims at preference-dense regions (prob_31's 2.82M).

## Expected attack
Noise-band set (31/33/30/34/35/28): harvest + cross-bay ⇒ −1 to −2M.
Z3 recovery on 31 (+37's 2.8M Z3): −0.3 to −1M. Density echo on 21/22/24
(unmeasured in v14): −0.3 to −1M. 38/27: 0 expected (bonus if any).
Total −2 to −4M from ~152M ⇒ 148-150M. Tight but reachable.

## Budget & mechanics
- Opus implements; file baseline/myalgorithm_15.py from v14 (commit
  3e1dc13); W0 byte-exact; same env rules; machine shared with the running
  v14 full bench — PHASE A (code, no execution) until bench14_full.log
  contains CSVROW, then Phase B.
- Test ladder: (1) units: cross-bay rebuild feasibility + accept-gate;
  byte-repro with new features off; (2) spot @300s: {31,33,30,34,35} —
  gate: sum < 30.5M (v14 draws: 11.27+10.20+4.30+2.14+1.75 = 29.66M...
  gate = beat the SUM of v14's five draws by >= 0.5M net, i.e. < 29.2M);
  (3) protect: {39,26} within noise of v14 (12.38M/9.65M); (4) shot: 38
  once; (5) prob_1 @60s byte-check; (6) full-40 bench_row @300s.

## Results (filled after testing)
