# jv15 — Z3-pool reopening + draw-recapture (campaign start 2026-07-22)

Goal (user /goal): **loss < 115M** @750s bench standard. Base = jv9
(honest single-shot 122,728,934). Gap = −7.73M.

## Loss decomposition of jv9 single-shot (full40_jv9.log × weights)
- w1·Z1 = 101.29M (83%) — 38: 34.6M, 27: 22.3M, 39: 7.4M, 26: 7.1M, 33: 7.0M,
  31: 5.3M, 37: 3.1M, 28: 2.6M, 30: 2.6M, 40/23: 2.1M each …
- w3·Z3 = 20.96M (17%) — 31: 2.94M, 37: 2.64M, 38: 2.11M, 32: 1.92M,
  27: 1.82M, 34: 1.32M, 39: 1.02M, 28: 0.90M, 22: 0.87M, 33: 0.86M …
- w2·Z2 = 0.47M (0%).

## Plan (three ways, per evolve.md)
1. **Z3 joint-reassignment** (Ahuja–Orlin cyclic-exchange class): the jv13
   "structurally forced" closure only tested SINGLE relocations (w2-spike
   blocked). CP-SAT screen `z3_floor.py` (same-Z2, no-new-tardiness area-time
   capacity): floor ≪ current on every big cell, optimistic pool 13.5M/11 cells
   (all CP-SAT-OPTIMAL). Attack: fixed-times post-pass (`z3_reassign.py`) +
   construction-membership bias (`z3_target.py` + jv15 bay_score hook).
2. **Draw recapture**: single-shot vs composed gap = 1.26M on variance cells
   (27/31/33/30/32/37/39). jv9 deaf-GIANT replica banked this class on giants;
   non-giant deaf replica untested (jv13 killed broadcast-off for giants only).
   jv15 `OGC_NG_DEAF` hook: wid-7 replica goes deaf on non-giants.
3. **Mid-cell Z1 classification**: area-LB Z1 = 0 (OPTIMAL) for ALL of
   26/33/31/30/28/21/23/35/40 → their ~31M w1·Z1 is geometry-caused, and the
   whole-bay exact-pack "zero yield" proof exists ONLY for prob_39. Overnight:
   `_exact_pack_bay`-class runs on 26/33/31 hot bays at 10–20 min budgets.

## Measured so far (2026-07-22)
- `z3_floor.py` screen: pool 13.5M optimistic (Z2-capped, capacity-capped).
- `z3_reassign.py` post-pass, fixed times (Z1 provably unchanged), checker-
  verified: prob_39 **−27,908** (2 moves); prob_37 0 moves after time-flex
  (fail_geom=57) → DENSE cells' pool needs membership-at-construction or time
  co-opt; slack cells (22/29/24/21/32/34, z1≈0) still untested (dumps cooking).
- Construction bias (hard, 1e9) single-worker probes:
  - 37 W0-dispatcher: **6,339,796 vs 6,481,834 control = −142,038**, z3
    4945→4785, z1 1054→1040 (dominates — real structural shift).
  - 31 W1-explorer: −194,660 total but z3 10570→10683 (WORSE) — gain was a z1
    draw shift, polish will erase. Bias moves z3 only where admission pressure
    allows (37-class).
- LP targets (bucketed release-window capacity, relaxation ladder):
  37 Z3→644@cf1.3, 32→270@cf1.6, 34→68@cf1.1, 31→6131@cf1.3.

## jv15 module state
Copy of jv9 + three env-gated default-off hooks (env unset ⇒ jv9-identical):
- `OGC_Z3_TARGET`/`OGC_Z3_BONUS`: bay_score (+dispatch) & _place_block score
  non-target-bay penalty + target-first bay_order.
- `OGC_NG_DEAF`: wid-7 replica deaf on non-giants.
