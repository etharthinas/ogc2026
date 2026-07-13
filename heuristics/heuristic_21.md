# Heuristic v21 — deepening the admission-frontier levers (goal < 125,000,000; v20 = 139,201,333)

Departure: v20 (myalgorithm.py, commit 53f564d). Remaining ask: −14.2M.
Where it must come from (v20 spot obj1 vs relaxation targets, w1·tard):

| prob | v20 w1·tard | relax UB @0.7 | headroom |
|---|---|---|---|
| 38 | 41,025,641 (t3077) | 16.3M (t1219) | ~−24M |
| 27 | 25,318,467 (t1899) | 8.2M (t615) | ~−17M |
| 39 | 9,279,768 (t696) | 0.2M (t16) | ~−9M |
| 31 | 6,146,513 (t461) | ~0 (t23 @1.0) | ~−6M |
| 33 | 15,093,556/w1=6667 (t1132) | (unmeasured) | ? |

Measured-dead this campaign (do not retry): plan-target gating in ALL forms —
fluid (family #3), calibrated non-preemptive (v20: 10.8–12.3M vs 9.16M
ungated on 31 even with the strong realizer), self-calibrating fixed-point
(9.48M vs 9.16M). The nm+beam greedy out-admits every gated realization.
Also: near_k=5 (worse than 3), nm cap 16 (no change), slot-identity
rematching (optimal at identity), SA/LAHC (v19), exit-lane discipline
(dwell=0). Jitter draws around the lottery: ±0.4M spread, small.

## Improvement A — near-miss in the improver (fix the measured polish flatness)

_improve gained +0 on nm builds twice: its repack destroy-rebuild reinserts
via conservative-mask scan_scoped and cannot re-create the nm placements it
destroys, so every rebuild loses and is rejected. Thread near-miss recovery
through the reinsert path:
- `_Raster.scan_scoped(..., want_near=False)`: also return near anchors
  (0 < scoped count <= near_k) when asked.
- `_find_earliest_slot_raster(..., nearmiss=0)`: near pass per (t, orient)
  after the mask-feasible pass, exact-gated by _can_place (same soundness
  contract as v20 Improvement A).
- `_repack_window(..., nearmiss=0)` -> pass through; `_improve(...,
  nearmiss=0)` -> pass to repack; explorer polish calls with nearmiss=8.
Default 0 everywhere = byte-inert on legacy paths.
Unit: nm=0 improve byte-identical. Spot: any eligible instance −300k.

## Improvement B — overhang-aware cell scoring (attack union-poisoning)

union_probe measured 0.05–0.10 of bay area poisoned by upper layers hanging
over EMPTY floor (blocks later entries; the entry rule tests the union of
present layers >= k). _order_cells currently scores footprint contact only.
Add, in explorer paths only (flag, default off): penalize candidate cells by
the count of currently-empty floor cells newly covered by the block's
layer>=1 masks; prefer positions whose overhangs align over existing
occupancy. Cheap: one windowed sum per candidate over the already-built
occupancy grids. Spot: 38 or 27 −500k (their co-residency is extreme).

## Improvement C — MPC exact joint admission (the heavy hitter)

The v14 beam (3 greedy orders, commit/rollback) bought +1.7M on 31; exact
joint choice should buy more where queues are deep (38: 126 queued blocks).
At events with queue >= m (m~6) inside the explorer build: menu of K~8
raster/near candidate cells per queued block (top-scored), pairwise
compatibility from mask/near overlap + exact `_can_place` gates on accept,
CP-SAT exactly-one-or-none per block, objective = admitted area − w1·(horizon
tardiness) as in v19 Improvement 3, 2–4s budget per solve, commit re-gated by
_can_place (zero trust surface). Fall back to beam on any failure/timeout.
Spot gate: 38 ≥ −800k or 27 ≥ −500k. Kill: both < −200k after a θ/K sweep.

## Slot economics

W1 explorer (v20): drop the plan-target ticket (measured dead), spend the
whole ticket window on the nm+beam config rotation + jittered draws; polish
with Improvement A active. W2/W3 nm+beam lottery tickets on eligible
instances: HOLD until v21a protect results are clean (pacing risk on the
eligible set's W2/W3 banked contributions is now low — v20 owns those cells —
but one change at a time).

## Ladder

- 21a = A + slot economics (drop plan ticket). Spot {31, 33, 39}. Protect
  {26 byte, prob_1 @60s byte}.
- 21b = B. Spot {38, 27}.
- 21c = C. Spot {38, 27, 39}. Full-40 row after whichever lands.

## Results

(pending)
