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
