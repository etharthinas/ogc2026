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

## Rescue width: swept, unimodal, and SIZE-DEPENDENT

Every rescued anchor buys density but costs scan throughput, and on a giant
throughput is what finds the basin. prob_38 @750s A/B vs jv9:

| MIN/MAX/CAP | delta |
|---|---|
| 8 / 12 / 96 | +209,898 |
| 32 / 24 / 192 | +1,787,358 |
| **128 / 48 / 512** | **+2,575,535** |
| always-on (∞ / 64 / 1024) | +1,729,439 |

But prob_31 (n=200) reverses it: 8/12/96 → +705,603 vs 128/48/512 → +425,869.
Big instances are admission-starved (every extra legal anchor pays); smaller
ones already have anchors and need the scan budget for polish depth. Hence
**size-adaptive width in `_Raster.__init__`**: n ≥ 250 → 128/48/512, else
8/12/96 (env vars override for probes).

## Measured (this machine, A/B vs jv9 @750s unless noted; adaptive width)

| cell | n | jv9 | jv17 | delta |
|---|---|---|---|---|
| 38 | 250 | 36,756,532 | **34,180,997** | **+2,575,535** (z1 2598→2419) |
| 26 | 150 | 7,908,663 | **7,184,621** | **+724,042** (z1 534→477) |
| 31 | 200 | 7,884,864 | **7,179,261** | **+705,603** (z1 378→333) |
| 37 | 250 | 5,699,640 | **5,291,045** | **+408,595** (z1 916→769) |
| 39 | 250 | 8,389,519 | **8,013,678** | **+375,841** (z1 553→530) |
| 27 | 150 | 23,649,558 | 23,651,026 | −1,468 (tie; z1 1628→1626, lex win) |
| 33 | 200 | 7,623,365 | 7,705,521 | −82,156 (z1 1005→1023 — recheck at wide width) |
| 1 / 5 / 20 @200s | | 15,751 / 77,765 / 183,494 | 1,499 / 74,971 / 132,393 | +14,252 / +2,794 / +51,101 |
| 12 @200s | | 84,350 | 134,015 | −49,665 (z1=0 both; z3 510→896 — Z3-endgame draw, recheck) |

**Measured-cell total: +4,710,940** vs jv9 (which single-shots 122,728,934) →
projected ≈ 118.0M with 31 cells still unmeasured. Aggregate z1 falls on every
class, which is the mechanism working as diagnosed. No feasibility failures
and no empty-fallbacks anywhere. Full-40 single-shot running to confirm.

## Consequence

Every pre-jv17 impossibility verdict (whole-bay exact-pack zero yield, drain
lookahead erased by polish, Z3 geometrically locked, "tiling-forced",
"<120M foreclosed") was measured on the dilated engine and must be re-tested
before being believed.
