# Heuristic v28 — POST-CONVERGENCE ESCAPES + SEQUENCING MOVES (goal < 112,500,000; frontier = v25 cells 124,581,895; v27a substrate x3.56 scans)

Departure: v27a (baseline/myalgorithm_27.py, commit 0b4a202 — byte-neutral,
3.56x faster scans). Remaining ask: −12.08M, mass in prob_38 (36.35M) and
prob_27 (24.97M).

## The two verdicts this plan stands on (2026-07-15)

1. **SATURATION, not throughput** (heuristic_27 Results): under x3.56 scans the
   eligible-8 reproduced v25 byte-for-byte → every stream converges within
   600s and then spins; count caps saturate; marginal depth finds nothing.
   The wasted post-convergence rounds are the budget to spend.
2. **SEQUENCING, not packing** (ledger_27_diag, commit 2542ced): ≥99.7% of
   queued-block-moments in the burst had NO exact-feasible placement anywhere
   (admission search is essentially perfect); burst layer-0 density 0.63–0.71
   ≈ the fluid cap already; 100% of obj1 is burst entry-queue delay; the 2x
   obj1 gap vs relax@0.7 (38: 2569 vs 1219; 27: 1726 vs 615) is ORDERING —
   which blocks occupy the saturated bays, in what sequence.

## Improvement A — re-enable deep partial restart + rebalance (primary)

`_improve()` (myalgorithm_27.py:2420) already contains DEEP PARTIAL RESTART
(rebuild RESTART_FRAC=0.45 of the champion in randomized order, accept-even-
if-worse into `cur`, `best` monotone) and CROSS-BAY REBALANCE — both DISABLED
since v9 (`RESTART_AFTER = REBAL_AFTER = 10**9`) because "the round-starved
giants NEVER reach convergence" and an eager plateau trigger once cost 38
−11M of descent rounds. Both premises are dead: v27a multiplied rounds/sec
~2-3x AND proved the giants converge with budget to spare (byte-flat under
extra depth). The v9 hazard (stealing DESCENT rounds) cannot recur because
the gate is `since_o1 >= RESTART_AFTER` — it fires only after obj1 has been
stalled for RESTART_AFTER rounds, i.e. exactly in the measured-wasted regime.

Safety by construction: (i) pre-gate rng stream is untouched (the restart
branch consumes rng only when it fires) → pre-convergence behavior
byte-identical; (ii) `best` is monotone → returned solution can only improve
or tie; (iii) the only real risk is wall-clock (restart rebuilds are big) —
spent from provably-wasted rounds.

Calibration: RESTART_AFTER = 60, RESTART_EVERY = 25 (fires at since_o1 = 75,
100, ...), sweep RESTART_FRAC ∈ {0.30, 0.45}; REBAL_AFTER = 80 (its v9 gate
comment says converged instances get "pure upside"). Restart rebuild order:
keep the randomized rotation, PLUS one variant biased to tardiness sequencing
(removed set reinserted in volume-normalized-ATC order — the fluid-order
blend without gating). Global constants → affects every instance; everything
is monotone-gated, so spot the giants first, then eligible-8 before recording.

Spot {38,27,39}. Keep if any ≥ −100k. Kill: all flat after the FRAC sweep →
record that post-convergence basin-hopping cannot escape these optima and
move mass to B/C.

## Improvement B — blocker-informed tardy swap destroy (sequencing move)

The existing `_destroy_tardy` removes tardy blocks alone — re-inserting into a
saturated schedule cannot move them earlier (no space). New destroy mode: for
a sampled tardy block i, use the raster near-miss machinery to identify the
RESIDENT blocks that block an earlier placement of i (overlap-count anchors at
entry times in [release_i, entry_i)), pick an anchor whose blocker set is
small (≤3) and whose blockers have due-slack; destroy {i} ∪ blockers; repair
with i FIRST at the earlier slot, blockers after (they can afford later/other
placements). This is the resident↔queued 2-exchange the sequencing verdict
calls for — an informed ejection at the improver level (subsumes the 26d/27c
ejection-chain idea with the diagnostic's guidance). Affordable only at v27a
scan speeds. Wire as one more destroy mode in the rotation (fires only when
tardy blocks exist, obj-gated accept as usual). Spot {38,27}. Kill: both
flat after a blocker-cap sweep {2,3}.

## Improvement C — rollout admission in the free W3-giant seed slot

At deep-queue events during giant construction, score the top-B admission
candidates by a short greedy ROLLOUT (simulate admitting the candidate plus
greedy continuation for H events, take projected obj1) instead of the myopic
score. B=3, H=15 to start. Deliver ONLY in the W3 giant specialist's first
seed build (26b proved this slot is free real estate: obj-gated, byte-flat
worst case, zero displacement) — NOT in W1/W0 (frozen 38 coupling). If it
banks on 38/39 raw, consider a W2-giant variant next version. Spot {38,39}.
Kill: both flat.

## Ladder

- 28a = A. Spot {38,27,39} @600s; FRAC sweep only if first spot flat; then
  eligible-8 @600s before recording. Protect prob_1 @60s (feasible, ≤ banked
  + noise; byte-match not required since restarts may legitimately fire).
- 28b = B on top of surviving 28a. Spot {38,27}.
- 28c = C. Spot {38,39}.
- Full-40 @600s row `algorithm 28` after whichever rungs land; promote
  baseline/myalgorithm.py if < 124,581,895; goal check < 112,500,000.

## Results

(pending)
