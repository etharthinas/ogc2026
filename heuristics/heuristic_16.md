# Heuristic v16 — reclaim wasted anchor compute (goal < 150M)

## Diagnosis from v15 (projected ~151.3M; need ~1.3M)
1. **A full CPU core is provably wasted on exactly the instances that hold
   58% of the loss.** On prob_38/39 (giant gate nw=3) and prob_27 (nw=4),
   W0 runs the v9-replica anchor whose candidates are ~2x worse than the
   dispatcher-side winners (94.3M/29.8M/52.4M-class vs 45.8/12.4/29.2M) —
   it has not won a single verify on these instances since v12. The anchor's
   feasibility-safety role is fully covered by the parent's insurance build,
   the empty-bay fallback, and official best-first verification.
2. Six lever families measured-dead on the saturated set (triage, retime,
   target gating, xbay/Z3, harvest x2). What HAS worked on giants since v12:
   more productive search streams (portfolio width) and joint repack
   (prob_39 −1.6M, prob_26 −1.7M). prob_39 still sits at 12.4M vs 1.3M fluid
   LB; prob_26 at 9.7M vs 5.1M — repack is proven there but round-limited.
3. Within-version determinism (v15 finding): re-rolls don't pay; only NEW
   search capacity or NEW mechanisms do.

## THREE improvements (v16)
1. **Anchor reclaim.** On instances where the v9-replica is provably
   non-competitive — rule: giant gate (n>=250 forced) OR overload ratio
   > 1.05 (isolates 38/39/27 on train; both criteria computed from the
   instance, no name lookups) — W0's core runs a PRODUCTIVE stream instead:
   dispatcher construction with a kappa/alpha variant not covered by W1/W2
   (e.g. kappa=2, alpha=0.5) → full v14-envelope polish (improve → retime
   (non-forced only) → improve → Z3 endgame). W0 stays byte-exact everywhere
   else. Safety unchanged (insurance + empty-bay + official verify).
2. **Repack deepening on the density-proven set.** Spend part of the
   reclaimed capacity on repack power where it measurably pays: destroy cap
   30 → 45, window-scale rotation gains a 4*pbar entry, and on giants the
   W3 specialist alternates single-bay/cross-bay windows (xbay accepts were
   zero on Z3 targets but untested as a DENSITY move on giants at depth).
3. **prob_27-class parity.** Non-giant overloaded instances (overload >
   1.05, n < 250: prob_27) get the giant treatment they never had: W2 runs
   the forced mini-lottery + interleaved repack (currently giant-only paths)
   and the reclaimed W0 stream doubles as their second dispatcher basin.

## Expected attack
38: second full-budget dispatcher basin + deeper repack (45.8M; even 1-2%
= 0.5-0.9M). 39: reclaimed core + deeper repack vs 11M headroom (0.3-1M).
27: mini-lottery + repack parity + reclaimed stream (29.2M; 0.3-0.8M).
Total −1.1 to −2.7M from ~151.3M ⇒ 148.6-150.2M.

## Budget & mechanics
- Opus implements baseline/myalgorithm_16.py from v15 (commit e123955); W0
  byte-exact on ALL non-reclaimed instances (that includes every current
  W0-winning basin); same env rules; serial quiet-machine testing.
- Test ladder: (1) units: reclaim-rule isolation check (compute rule over
  all 40 train instances — must select exactly {27, 38, 39}); byte-repro on
  a non-reclaimed forced instance (31) and an easy (1); (2) spot @300s:
  {38, 39, 27} — GATE: sum < 86.0M (current 87,440,435 = 45,806,839 +
  12,375,057 + 29,198,468... wait 45.81+12.38+29.20 = 87.38M; gate 86.0M);
  (3) protect @300s: {26, 35, 31} flat-or-better; (4) prob_1 @60s byte;
  (5) full-40 bench_row @300s.

## Results (filled after testing)

### Units
- Reclaim-rule isolation: rule as specced selects {27, 37, 38, 39, 40}, NOT
  the expected {27,38,39} — prob_37 (n=250 forced, overload 0.782) and
  prob_40 (n=250 forced, overload 1.222, higher than 38's 1.142) are also
  giants. results.csv proves W0-v9 non-competitive on them too (v9 vs v14:
  37 = 9.03M vs 5.81M, 40 = 3.79M vs 2.30M), so the five-instance selection
  was kept (min-wins-safe on all five). Unit PASS with corrected expectation.
- Byte-repro v15 vs v16 (deterministic clock): PASS on prob_31
  (dispatch+improve, forced non-reclaimed) and prob_1 (easy).

### Ladder @300s (two passes: first under mild stale load ~3% of one core,
### rerun on clean machine — every number byte-identical across both passes)
- GATE {38,39,27}: 45,806,839 (flat) + 12,361,461 (−13,596) + 29,198,468
  (flat) = 87,366,768 vs gate < 86.0M → GATE MISSED (net −13.6k).
- Reclaim extras: 37 = 5,807,047 (flat), 40 = 2,300,281 (flat).
- Protect: 26 = 9,653,490 (flat), 35 = 1,346,898 (holds v15 band),
  31 = 11,268,243 (flat); prob_1 @60s = 18,357 byte-exact.

### Analysis
The anchor reclaim is SAFE (zero regressions anywhere in the ladder) but
bought almost nothing: the kappa=2/alpha=0.5 full-budget W0 stream + deep
repack (cap 45, {2,1,3,4}·pbar rotation, giant-specialist sbay/xbay) never
beat the incumbent v14 winners on the saturated set. Only prob_39 moved, a
reproducible −13,596. Both passes byte-identical per instance ⇒ outcomes on
this set are fully deterministic under the current portfolio; the seventh
lever family (portfolio width / reclaimed compute) is now measured ≈ dead on
38/27. Projected full-40 if promoted: ~151.28M (v15 −13.6k) — far from the
~1.3M needed. The remaining headroom (39: 12.36M vs 1.3M fluid LB; 27:
29.2M vs ~20.7M loadable bound) points at geometry-at-scale mechanisms
(exact/simultaneous multi-block packing subproblems), not further
ordering/portfolio levers.
