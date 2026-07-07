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

## Results (validation @300s vs v14 full-bench row)
Units PASS (xbay officially feasible + real bay moves; features-off
byte-repro exact vs v14). Round 1: prob_35 1,346,898 (−406k — good draw
banked); 31/33/30/34/26/39 byte-flat; 38 +53k slip from envelope shift;
prob_1 exact. Round 2 (harvest re-seeded from runner-up CONSTRUCTIONS via
pick_alts; giants reverted to exact v14 envelope; xbay Z3-targeted):
38 restored to 45,806,839 exact; 31/37/33 STILL byte-flat; 35 kept.
Net vs v14: −406,058. Projected full-40 ≈ 151.3M.

## Analysis — two measured-dead hypotheses, one live insight
1. **The "lottery noise band" was code-version variance, not run variance.**
   Within one version, per-instance draws are nearly deterministic (byte-flat
   reproductions everywhere, even from distinct construction seeds). Harvest
   (both improve-seed and construction-seed variants) is measured-dead as a
   lever. prob_35's −406k was a one-off code-shift capture.
2. **xbay / Z3 recovery is dead on the Z3-heavy pair (31/37):** preferred
   bays are space-saturated across the horizon; no window/bay-choice scheme
   found a single accepted move. Sixth dead family on the saturated set.
3. **Live insight for v16:** on prob_38/39 (giant gate) and prob_27, the W0
   v9-replica anchor core produces ~2x-worse candidates that can never win
   (94.3M/29.8M/52.4M-class vs current 45.8/12.4/29.2M) — a full CPU core
   of provably wasted compute on the three instances holding 87.4M (58% of
   total). Reclaiming it for productive streams is the largest untried lever.
   Feasibility safety is unaffected (parent insurance build + empty-bay
   fallback + official verify remain).
