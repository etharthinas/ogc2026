# jv17 — SUBCELL RESCUE (the architectural fix), 2026-07-23

Base: jv9/jv15. Trigger: user revealed the team is ~130th → the campaign's
"foreclosed / dead lever" verdicts were statements about THIS ENGINE's basin,
not about the problem. Audit the engine itself.

## The leak (measured, not theorised)

`_Raster.mask()` marks a unit cell occupied when a layer polygon merely
**touches** the closed unit square. Every fractional-vertex block is therefore
dilated by up to one cell per edge, and legal edge-touching placements are
rejected. Measured TRUE polygon co-resident density at the peak moments that
force all tardiness:

| cell | true peak polygon density / bay | engine's bbox-measure |
|---|---|---|
| 31 | 0.667 / 0.687 / 0.648 / 0.662 | 1.16 / 1.14 / 1.27 / 0.99 |
| 37 | 0.580 / 0.634 / 0.639 | 1.03 / 0.93 / 0.89 |
| 38 | 0.696 / 0.686 / 0.700 | 1.01 / 1.03 / 1.19 |
| 32 | 0.572 / 0.484 / 0.509 | 1.00 / 0.94 / 0.93 |
| 39 | 0.660 / 0.658 / 0.653 | 1.12 / 1.12 / 1.09 |

Bays are 48–70% full in real area while the engine reports "full". Since 100%
of measured tardiness is ENTRY DELAY (both giants and mids — verified from the
dumps: `tard_from_linger = 0` everywhere), blocks were queueing against
**phantom occupancy**. w1·Z1 is 83% of the total loss.

## jv16 (rejected): rasterise everything at 1/q

Full fine raster (q=4, FFT-correlation scan). Sound and it worked on a small
cell (prob_37 W0 @420s: 6,481,834 → 5,661,219, −12.7%), but scans cost 2.53 ms
vs 0.39 ms (6.5×) and the giant collapsed: **prob_38 A/B = 198,342,182 vs
36,756,532**. Throughput is load-bearing on giants. Kept as
`myalgorithm_jv16.py` for reference only.

## jv17 (adopted): rescue only at the admission frontier

The unit scan stays **verbatim jv9** (same code path, same cost, same numbers).
A parallel 1/4-subcell occupancy is maintained incrementally, and when a
block's unit scan yields fewer than `_RESCUE_MIN` (8) anchors — i.e. the block
is starving, which is exactly when tardiness is decided — the cheapest
unit-rejected anchors (unit overlap ≤ `_RESCUE_MAX`=12, at most
`_RESCUE_CAP`=96) are re-tested against the 1/4 mask and flipped to feasible
when genuinely clear. Same rescue in `scan_scoped` for the repair windows.

Soundness is unchanged in kind: the subcell mask is still a closed-cell
superset of the polygon, so subcell-disjointness proves no positive-area
overlap and no crane-path conflict; every commit still passes exact
`_can_place`. Verified empirically: 16 rescued anchors re-checked with the
official `utils.check_entry` → **0 violations**.

Cost: **0.66 ms/scan** (jv9 0.39, jv16 2.53). Env knobs `OGC_RASTER_Q`,
`OGC_RESCUE_MIN/MAX/CAP`; `OGC_RASTER_Q=1` ⇒ byte-exact jv9.

## Measured (this machine, A/B vs jv9 @750s unless noted)

| cell | jv9 | jv17 | delta |
|---|---|---|---|
| 38 | 36,756,532 | **36,546,634** | **+209,898** (z1 tie, z3 7042→6344; no fallback) |
| 31 | 7,884,864 | **7,179,261** | **+705,603** (z1 378→333) |
| 37 (W0 probe @420s) | 6,481,834 | **5,486,611** | −15.4% (single worker below the jv9 portfolio's 750s record 5,699,640) |
| 1 / 5 / 20 @200s | 15,751 / 77,765 / 183,494 | 1,499 / 74,971 / 132,393 | +14,252 / +2,794 / +51,101 |
| 12 @200s | 84,350 | 134,015 | −49,665 (z1=0 both; z3 510→896 — Z3-endgame draw, recheck) |

Small-cell battery net +18,482 (3W/1L). No feasibility failures anywhere.

## Consequence

Every pre-jv17 impossibility verdict (whole-bay exact-pack zero yield, drain
lookahead erased by polish, Z3 geometrically locked, "tiling-forced",
"<120M foreclosed") was measured on the dilated engine and must be re-tested
before being believed.
