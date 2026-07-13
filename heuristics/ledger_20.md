# ledger_20.md — honest capacity ledger (v19 Improvement 1, actually computed) + refutation record

> Produced 2026-07-13 by the v20 campaign. Supersedes ledger_19.md's frontier
> verdict. Method and scripts: `baseline/lb_cumulative.py` (valid LBs and
> capacity-swept relaxation targets), `baseline/analyze_rocks.py` (per-layer
> density + slack redistribution), `baseline/density_probe.py` /
> `baseline/union_probe.py` (burst profiles), `baseline/slot_match_probe.py`
> (identity re-matching ceiling).

## 1. Why ledger_19's verdict was wrong

ledger_19 measured "peak realized bay density >= 0.94-1.13" and concluded no
packing slack. That metric (`measure_giant.py::farea`) sums per-block
FOOTPRINT areas: any multi-layer stacking is counted twice, which is exactly
why values exceeded 1.0. The problem's true co-residency constraint is
per-layer collision. The same incumbents measured per-layer:

| prob | per-layer peak per bay (L0) | burst-time merged L0 | free area while blocks queue |
|---|---|---|---|
| 38 | 0.64/0.54/0.57 | ~0.5 | large |
| 27 | 0.57/0.52 | ~0.5 | large |
| 39 | 0.59/0.64/0.61 | ~0.5 | large |
| 31 | 0.50/0.58/0.52/0.60 | 0.47-0.52 | ~3,500 units vs ~2,000 queued |

The bays are roughly HALF EMPTY at the congestion peak while 20-29 blocks
queue outside. There was never a density saturation.

## 2. Valid lower bounds and relaxation targets (w1 * tardiness)

Non-preemptive per-layer cumulative CP-SAT, merged bays. cap=1.0 rows are
VALID lower bounds; cap<1.0 rows are relaxation targets at that packing
density (solver UB, not converged — true optima lower).

| prob | v18 w1*tard | LB cap=1.0 | UB @0.7 | UB @0.6 | UB @0.55 |
|---|---|---|---|---|---|
| 38 | 44,065,565 | 213,328 | 16,252,927 | 27,279,318* | — |
| 27 | 27,372,649 | 293,326 | 8,199,795 | 14,439,639* | — |
| 39 | 11,239,719 | 0 (OPTIMAL) | 213,328 | 3,053,257 | — |
| 31 | 8,239,794 | 0 (OPTIMAL) | ~0 | 519,987 | 1,959,951 |

(* 90s single-run UBs, far from converged.)

Slack-redistribution floors (incumbent delay mass optimally re-spread over
due slack): 38 -> 37.0M, 27 -> 23.1M, 39 -> 7.0M, 31 -> 0. Combined
re-ordering headroom ~= -23.7M before any density gain.

## 3. Closed questions (measured, do not revisit)

- **Exit blocking**: dwell_over_p = 0 on all four rocks; every block exits at
  entry+processing. All delay is admission-queue delay. (v19 Improvement 8
  answered: immaterial.)
- **Identity re-matching over fixed slots**: with an OPTIMISTIC bbox
  compatibility graph (avg degree 24-42), the exact optimal assignment is
  the identity on all four rocks (+0). v18 exhausted redistribution within
  its slot structure; only different slot structures (construction) can move
  tardiness. All 40 instances have unique shapes (no identical-shape swaps).
- **Admission loss stack** (union probe, prob_31 burst): true L0 polygon
  density ~0.5; raster mask dilation blocks another ~0.10-0.15 of bay area
  (recovered by v20 Improvement A); overhang union-poisoning ~0.05-0.10;
  the rest is fragmentation/crane scope (plan realization gap).

## 4. v20 measured recoveries (raw single dispatch vs fully-polished banked)

Near-miss recovery (nm=8) + v14 beam, best grid config per instance:

| prob | best raw (config) | banked 600s | delta (raw vs polished bank) |
|---|---|---|---|
| 31 | 9,158,172 (0.5, 0.5) | 10,981,881 | −1,823,709 |
| 39 | 9,944,600 (0.5, 1.0) | 12,361,461 | −2,416,861 |
| 33 | 8,821,905 (2.0, 0.5) | 9,566,490 | −744,585 |
| 27 | 28,504,038 (2.0, 0.5) | 29,185,135 | −681,097 |
| 38 | 44,014,363 (2.0, 0.5) | 45,806,839 | −1,792,476 |

Full-portfolio smoke (prob_31 @90s, loaded machine): 9,038,459 feasible.

## 5. Frontier verdict

<125M is NOT proven unreachable — the 19a proof rested on a measurement
artifact. It is also not yet proven reachable: the remaining gap after v20's
first iteration is still large (need ~-24.6M total; raw recoveries sum
~-7.5M before polish/portfolio effects). The honest statement: the
admission-frontier levers (dilation recovery, joint fill, plan gating,
improver-side near-miss, MPC joint admission) are ALIVE and compounding,
and the relaxation targets say multi-million headroom remains on every rock
(31: realized ~465 tardiness units vs ~39 plan floor at the same density).
Iterate per evolve.md until the ledger targets or the levers exhaust.
