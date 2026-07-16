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

### 28a spot (2026-07-16, quiet machine, serial)

prob_1 @60s guard: 18,357 = banked exactly (51.1s, feasible). Giants @600s:

| inst | 28a | v25 banked | delta |
|---|---|---|---|
| prob_38 | 36,351,493 | 36,351,493 | 0 (byte-flat) |
| prob_27 | 24,972,962 | 24,972,962 | 0 (byte-flat) |
| prob_39 | 8,389,519 | 8,389,519 | 0 (byte-flat) |

**Byte-flat everywhere** — restarts+rebalance either never fire (gate
since_o1 >= 75 unreached) or fire and never beat the incumbent (best is
monotone, so flat is the guaranteed floor). Distinguishing via OGC_DEBUG
n_restart counters piggybacked on the 28b spot run (same constants in that
file). FRAC-sweep decision deferred until then. NOTE: the header-advertised
"every 2nd restart uses volume-normalized-ATC rebuild order" variant is NOT
in the code (restarts always shuffle) — spare knob if debug shows restarts
fire-but-lose; n_rebal debug counter also still never incremented.

### 28b spot (2026-07-16) — KILLED, regressive

myalgorithm_28b.py (blocker-informed tardy swap destroy, SWAP_EVERY=4,
BLOCKER_CAP=3, single-bay, near-anchors only). prob_1 @60s guard: 18,357 =
banked. Giants @600s:

| inst | 28b | v25 banked | delta |
|---|---|---|---|
| prob_38 | 38,247,522 | 36,351,493 | **+1,896,029** |
| prob_27 | 25,403,468 | 24,972,962 | **+430,506** |

obj1 rose on both (38: 2569→2694; 27: 1726→1754). Mechanism: the swap fires
every 4th round from round 4 — on round-starved improver slices (see debug
below) it STEALS descent rounds from the classic destroy modes; the move
itself rarely lands (saturated bays). Cap sweep {2} skipped — the failure is
cadence/round-stealing, not blocker-set size. Same mechanism class as the v9
eager-plateau hazard. LAW reinforced: on giants, every improver round is
descent-critical; any new move must ADD rounds' value, not replace them.

### 28c spot (2026-07-16) — flat

myalgorithm_28c.py (rollout admission B=3/H=15/QDEPTH=8 in W3 giant first
seed). prob_1 @60s guard: 18,357 = banked. prob_38 = 36,351,493, prob_39 =
8,389,519 — both byte-flat. Second consecutive byte-flat modification of
this slot (after 26b): the W3 first seed NEVER wins the obj-gated race —
"free real estate" is free because it is WORTHLESS. Do not deliver
mechanisms there again; a rollout test that can actually bank must run in a
winning pipeline (W1/W2 giant) under explicit obj-gating.

### OGC_DEBUG improver telemetry (from 28b run; same restart constants as 28a)

prob_38 improve slices: rounds = 3–17, since_o1 <= 16 → the since_o1>=75
restart gate is STRUCTURALLY UNREACHABLE on 38 (round-starved slices, even
at x3.56 scan speed). prob_27 slices: rounds = 76–127, n_restart = 1–2 per
slice → restarts DO fire on 27-class and always lose (fire-and-lose).
n_rebal counter was never incremented (bug) so rebalance telemetry is
unknown. Consequence: improver-level escapes can never touch 38; 28f
calibration variant (RESTART_AFTER=30/EVERY=15 + ATC rebuild order on every
2nd fire + n_rebal fix) spot-tested on 27 only.

### 28f spot (2026-07-16) — flat; v28 series CLOSED

prob_27 @600s = 24,972,962 (byte-flat). Telemetry: n_restart up to 18 per
slice, slices up to 291 rounds with since_o1 = 291 — restarts fired densely
under BOTH rebuild orders (shuffled and volume-normalized-ATC) and not one
ever improved obj1. n_rebal = 0 with the fixed counter: cross-bay rebalance
NEVER fires (since_best plateau of 80 is never reached — tiny obj2/obj3
gains keep resetting it). VERDICT: improver-level basin-hopping cannot
escape these optima, period. The v25 giant incumbents are locally optimal
against 0.45-fraction randomized rebuilds; the sequencing lever must be
pulled at CONSTRUCTION (admission order), not in the improver → heuristic_29.

### Final: v28 == v25 cells (124,581,895). No promotion. Files kept:
myalgorithm_28.py (28a, byte-neutral), myalgorithm_28b.py (KILLED, do not
revive the cadence), myalgorithm_28c.py (flat), myalgorithm_28f.py (flat).
