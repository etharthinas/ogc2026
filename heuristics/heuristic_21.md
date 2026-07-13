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

### 21a spot @600s (2026-07-13)

Improvement A (improver-nm): implemented sound, measured FLAT (+0 on 31/33
at 150s from nm builds) — the repack neighborhood is exhausted on these
constructions regardless of candidate recovery. Kept wired (byte-inert
default), value ≈ 0. The 21a payload became slot economics + nm+beam family
across W0/W2/W3 on eligible instances:

| prob | v21 @600s | v20 | delta |
|---|---|---|---|
| 38 | 41,646,457 | 43,156,139 | **−1,509,682** |
| 23 | 2,955,426 | 3,010,868 | **−55,442** |
| 26 | 9,653,490 | 9,653,490 | ±0 (restored after append fix) |
| 31/39/33/27/30 | (flat) | — | ±0 |

Lesson re-learned the hard way: PREPENDING tickets to the W3 lottery
displaced prob_26's banked beam-draw winner by +374k (v17's exact lesson,
v14's exact magnitude). Fix: APPEND (W3) — original draw sequence byte-exact,
nm tickets run in leftover time only; W2's prepend kept (source of 23/38
gains, no banked winner lives there). prob_1 @60s protect: byte-exact.

**Full-40 row `algorithm 21` = 137,636,209** (−1,565,124 vs v20;
−12.0M vs v18). Remaining to <125M: −12.64M.

38's residual: obj1=2965 (39.5M of its 41.6M) vs relax@0.7 target 1219.
27 flat at 1899 obj1. 21b/21c (overhang scoring, MPC) target exactly these.

### 21c = v22 (MPC joint admission, W1 tickets) — 137,384,844 (−251k)

CP-SAT max-weight compatible-set fill (footprint-union-disjoint conflicts,
_can_place-gated commits) as a 4th beam order. Raw probe: 38 −832k
@(2.0,0.5), config-dependent elsewhere. Spot: 27 −61k, 30 −190k (through
polish), 38 flat (the mpc raw advantage never won from W1's shallow ticket).

### 21b+21c deep = v23 (mpc→deep pipeline; overhang tickets) — 135,377,106 (−2.01M)

(a) W0-reclaimed builds plain-nm AND mpc variants, deep pipeline takes the
raw-min: **27 −1,516,877**. (b) overhang-aware anchor scoring (_order_cells
penalizes upper-layer cells over empty floor) as W1 tickets: **26 −487,249**
— the previously-immovable instance. KEY LESSON: raw build quality does NOT
predict post-polish outcome; the currency is basin diversity fed into deep
polish, protected by min-wins.

### v25 (deep-nestle near_k family) — **GOAL MET: 124,581,895 < 125M**

The 38 diagnostic showed 44–51% of floor area free while 50–90 blocks
queue, and the reason: near_k=3 recovers only 3-cell mask overlaps while
38-class blocks have 40+ cell perimeters — deeply-nestled exact-feasible
anchors were invisible. near_k ∈ {16, 24, 32} tickets (nm cap nk+8) heading
the W1 rotation produced raw builds BELOW every fully-polished banked cell,
and polish compounded:

| prob | v25 | v24 | delta |
|---|---|---|---|
| 38 | 36,351,493 | 41,646,457 | **−5,294,964** |
| 39 | 8,389,519 | 10,253,072 | **−1,863,553** |
| 31 | 8,124,019 | 9,038,459 | **−914,440** |
| 27 | 24,972,962 | 25,647,585 | **−674,623** |
| 33 | 7,734,338 | 8,376,814 | **−642,476** |
| 26 | 8,551,513 | 9,166,241 | **−614,728** |
| 23 | 2,524,154 | 2,955,426 | **−431,272** |
| 30 | 3,363,565 | 3,722,720 | **−359,155** |

Net −10,795,211 in one rung. Full-40 = **124,581,895** (row `algorithm
25`), prob_1 @60s protect byte-exact, myalgorithm.py = v25, commit c407ac1.
Campaign total v18 → v25: −25.25M, all downstream of refuting ledger_19's
footprint-density artifact. v26 candidates: near_k upgrade inside the W0/W3
deep pipelines (still building at near_k=3); per-instance nk adaptation.

### v24 (ovh into deep pipelines) — NET FLAT, one displacement lesson

All cells flat except 27 REGRESSED +939k: shifting the W0 build deadlines
(0.22/0.38 → 0.18/0.30/0.42 to fit a third build) changed the mpc build and
raw-min fed polish a worse input. BUILD-BUDGET PACING IS LOAD-BEARING.
Reverted to v23 timing verbatim; W3-giant ovh variant + W1 weight-4 ticket
kept (measured no-harm). Standing law: never re-pace a winning deep
pipeline's build phase to make room for new variants — add variants only in
min-wins ticket space.
