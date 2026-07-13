# Heuristic v20 — reopening the <125M campaign: the 19a saturation verdict is refuted (goal < 125,000,000)

> Departure point: v18 = myalgorithm.py, full-40 @600s = 149,831,986 (clean
> re-bench row `algorithm 19` = 149,599,810 within run noise). heuristic_19/
> ledger_19 declared <125M "structurally unreachable". **That verdict is
> measurably wrong** — this file records the refutation evidence, the honest
> LB ledger the v19 plan asked for (and 19a never actually computed), and the
> v20 mechanism.

## 0. Refutation of ledger_19's saturation verdict

ledger_19's decisive finding was "peak realized bay density ≥ 0.94–1.13 on
every bay of every big rock ⇒ no packing slack". That measurement
(`measure_giant.py::farea`) summed **per-block footprint areas** — which
double-counts multi-layer stacking (hence readings > 1.0, a physical
impossibility for a true occupancy fraction). The actual co-residency
constraint of this problem is **per-layer** collision. Re-measured
(`analyze_rocks.py`), the v18 incumbents' true per-layer PEAK densities are:

| prob | per-bay per-layer peak (L0) | ledger_19 claimed |
|---|---|---|
| 38 | 0.64 / 0.54 / 0.57 | 0.94–1.05 |
| 27 | 0.57 / 0.52 | 0.94–0.97 |
| 39 | 0.59 / 0.64 / 0.61 | 0.94–1.08 |
| 31 | 0.50 / 0.58 / 0.52 / 0.60 | 1.02–1.13 |

During prob_31's release burst the incumbent runs at merged true-L0 density
**0.47–0.52 with ~3,500 area units free while 20–29 blocks (~2,000 area)
queue outside** (`density_probe.py`). The bays are HALF EMPTY at the
congestion peak. "Density-saturated" is false; Improvements 2/3/4 of the v19
plan were killed on a measurement artifact without ever being run.

## 1. The honest LB ledger (v19 Improvement 1, actually computed this time)

Non-preemptive per-layer cumulative CP-SAT relaxation (`lb_cumulative.py`):
merged-bay capacity C·cap_frac per layer, exact durations, entry ≥ release.
cap=1.0 is a VALID lower bound; lower caps are realistic targets. w1·tard:

| prob | v18 w1·tard | LB @cap 1.0 | relax UB @0.7 | @0.6 | @0.5 |
|---|---|---|---|---|---|
| 38 | 44,065,565 | 213,328 | 16.3M | 27.3M* | 46.4M* |
| 27 | 27,372,649 | 293,326 | 8.2M | 14.4M* | 23.1M* |
| 39 | 11,239,719 | 0 (OPT) | 0.2M | 3.1M | 10.2M* |
| 31 | 8,239,794 | 0 (OPT) | 0.0M | 0.3–0.5M | 4.6M* |

(* = 90s solver UB, far from converged — true optima are much lower; e.g.
prob_31 @0.6 with 45s+hint reaches 39 units = 0.52M.)

Slack redistribution floors (same total delay mass as the incumbent, spread
optimally over due-slack; `analyze_rocks.py`): 38→37.0M, 27→23.1M, 39→7.0M,
**31→0**. Pure "who absorbs the delay" re-ordering headroom ≈ −23.7M before
any density gain. Tardiness is NOT structural; the incumbents sit millions
above even conservative relaxations.

Also settled by measurement:
- `dwell_over_p = 0` on all four rocks: ALL delay is admission-queue delay.
  Exit-blocking (v19 Improvement 8) is immaterial — question closed.
- Identity re-matching over the incumbent's fixed slots (optimistic bbox
  compatibility graph, exact assignment solve, `slot_match_probe.py`):
  **identity is optimal on all four rocks (+0)**. v18 has fully exhausted
  redistribution within its own slot structure; the slot STRUCTURE
  (admission times/geometry) must change. All shapes are unique per instance
  (no identical-shape swaps exist).

## 2. Where the realizable slack actually is (the admission loss stack)

Union-projection probe (`union_probe.py`, prob_31 burst, while 20+ queue):

| layer of loss | density cost | lever |
|---|---|---|
| true polygon L0 co-residency | 0.47–0.52 used | — |
| raster mask dilation (cell-touch superset) | +0.10–0.15 blocked | **Improvement A** |
| overhang poisoning (union − L0: upper layers over empty floor) | +0.05–0.10 blocked | placement scoring (later) |
| fragmentation + crane scope (rest to ~1.0) | 0.15–0.30 free-but-unplaceable | **Improvement B** (plan) + beam |

The dispatcher's admission gate (`raster.scan` feas = zero-overlap on
conservative masks) rejects exactly-feasible placements ("false-positive on
every nestled pair" — v17's own finding, fixed inside CP-SAT relations but
never at the admission frontier). `scan` already computes the overlap COUNT
grid and throws it away.

Realization probes of plan-guided admission (`plan_probe.py`, prob_31, raw
construction, no polish): plan tardiness @cap 0.6 ≈ 38 units realizes at
~655–709 units (gate+ATC), ~651–664 with the v14 beam. Incumbent = 618 after
full 600s polish. The plan gate alone lands within ~+0.5M of the banked value
BEFORE polish; the remaining gap is placement failure at planned times — the
dilation + fragmentation rows above.

## 3. The three v20 improvements

### Improvement A — near-miss admission recovery (v19 Improvement 6, evidence-backed)

`_Raster.scan` keeps its overlap-count grid; near-miss cells
(0 < total ≤ K, K≈3) are exposed via `scan_near`. In
`_dispatch_construct.try_place`, when the mask-feasible pass finds nothing,
a second pass exact-gates up to N≈8 near-miss cells per (bay, orient) with
the existing exact `_can_place` (cached shapely; a passing cell is officially
feasible — zero new trust surface). Recovers the ~0.10–0.15 dilation band at
precisely the admission frontier where queued blocks fail. Param
`nearmiss=0` default ⇒ byte-exact off everywhere except the explorer slot.

### Improvement B — calibrated non-preemptive plan targets (v19 Improvement 2, corrected)

In-slot CP-SAT cumulative plan (per-layer areas, merged bays, exact
durations, objective `1000·Σtard + Σ(start−release)` — the left-shift term
prevents gratuitous gating), cap_frac swept {0.55, 0.60, 0.65}. Planned
entries feed the EXISTING round-3 target machinery (gate + ATC urgency).
Differences from dead family #3 (fluid gating): non-preemptive exact
durations, per-layer calibrated capacity, left-shifted targets, and the
realizer keeps near-miss + beam. Tickets: (0.60, beam, nm), (0.55, beam, nm),
(0.65, no-beam, nm), plus an ungated nm-only dispatch as control.

### Improvement C — quarantined W1 explorer slot (§11 of heuristic_19 upheld)

Plan-eligible trigger (instance-computed): `forced AND w1 ≥ 6000 AND
overload > 0.65` ⇒ exactly {23, 26, 27, 30, 31, 33, 38, 39} on train (the
tardy mass, ~125M of the 149.6M total). On those instances W1 (AREA-basin
build + polish — the least-attributed slot on this class) becomes the plan
explorer: solve plan → realize tickets → giant polish envelope (improve →
retime → improve → z3). W0/W2/W3 and all non-eligible instances byte-exact
v18. ortools failure ⇒ fallback to the old W1 path. min-wins + official
verify unchanged.

## 4. Gates

- Unit: nearmiss=0 ⇒ dispatch byte-identical to v18 (same rng pacing).
- Unit: every near-miss-recovered placement passes official check_feasibility
  (it is _can_place-gated; verify end-to-end on prob_31 anyway).
- Spot (600s, quiet machine): prob_31 < 10.4M OR prob_39 < 11.8M.
  Stretch: prob_38 −1M+.
- Protect: prob_1 @60s byte-exact; spot-check {35, 30, 34, 21} unchanged
  (W1 replaced only on eligible instances; 30 IS eligible — watch it, its
  banked 4.08M must be reproduced by W0/W2/W3 or beaten).
- Kill: all four rocks < −100k ⇒ record dead, revert W1.

## 5. v20b queue (next sub-version, pending v20a spot results)

1. **Near-miss in the improver** (the measured polish-flatness fix): improve
   gained +0 twice on nm builds because destroy-rebuild reinserts via
   conservative-mask `scan_scoped` and cannot re-create the nm placements it
   destroys. Thread `nearmiss` through _improve's reinsert paths
   (`_find_earliest_slot_raster` + the repack rebuild's scoped scans):
   scan_scoped computes the same count grid — expose near cells, exact-gate
   with _can_place, param default 0 (byte-inert), enabled only from the W1
   explorer's polish calls.
2. **Near cells in the main scoring competition** (not just as fallback):
   near-miss anchors are contact-rich (deeper nesting); letting them compete
   with mask-feasible cells on placement score may pack tighter even when a
   mask-feasible cell exists. Costs more _can_place gates; measure.
3. **W2/W3 lottery nm+beam tickets on eligible instances** (pacing-quarantine
   per instance; only after v20a protect results are clean).
4. **MPC joint admission** (v19 Improvement 3) stays in the queue — the plan
   relaxation says ~10x more tardiness headroom remains even after nm+beam
   (31: realized ~465 units vs plan floor ~39).

## Results (filled after testing)

### Offline ablation (single dispatch, kappa=2.0/alpha=0.5/score_pos, raw
construction, NO polish; banked = v18 full-600s pipeline values)

| prob | nm=0 | nm=8 | nm=8 + beam | banked (600s) |
|---|---|---|---|---|
| 31 | 13,994,937 (t849) | 12,855,886 (t766) | **10,899,293 (t602)** | 10,981,881 |
| 39 | 14,579,376 (t1044) | 13,572,848 (t952) | **10,386,149 (t703)** | 12,361,461 |
| 27 | 33,741,538 (t2384) | 30,591,108 (t2132) | **28,504,038 (t1990)** | 29,185,135 |
| 38 | 48,164,392 (t3482) | 44,758,516 (t3220) | **44,014,363 (t3163)** | 45,806,839 |

### v20a SPOT BENCH @600s (2026-07-13, loaded-machine caveat: ~1.5GB free
RAM during run — biases AGAINST v20; 26 still byte-reproduced) — 8/8 feasible

| prob | v20 @600s | banked (row 19) | delta |
|---|---|---|---|
| 31 | 9,038,459 | 10,981,881 | **−1,943,422** |
| 39 | 10,253,072 | 12,361,461 | **−2,108,389** |
| 33 | 8,376,814 | 9,566,490 | **−1,189,676** |
| 27 | 27,225,747 | 29,185,135 | **−1,959,388** |
| 26 | 9,653,490 | 9,653,490 | ±0 (byte-reproduced) |
| 23 | 3,010,868 | 3,390,436 | **−379,568** |
| 30 | 3,916,412 | 4,083,746 | **−167,334** |
| 38 | 43,156,139 | 45,806,839 | **−2,650,700** |

Total delta **−10,398,477** → full-40 = **139,201,333** (row `algorithm 20`;
non-eligible 32 instances banked — their code paths are byte-exact v18,
verified: prob_1 @60s = 18,357 byte-exact, dispatch hash-identical, near-grid
computation opt-in per raster so legacy workers pay zero overhead).
Spot gates (31 < 10.4M, 39 < 11.8M): PASSED. Kill criterion: not tripped.
myalgorithm.py promoted to v20.

Remaining to <125M: −14.2M. Next: 20b queue (§5).

Offline polish of the 31 nm+beam build (improve 150s -> retime -> improve
90s): 10,899,293 -> **10,792,311 official-feasible** (banked −189,570). The
improver itself gained +0 both times — its repack destroy-rebuild uses
conservative-mask scan_scoped and cannot re-create near-miss placements, so
polish on nm builds is retime-only. Threading nearmiss into the improver
reinsert path is the 20b compounding lever.

kappa x alpha grid (nm=8, beam, raw): per-instance winners VARY —
31: (0.5, 0.5) = **9,158,172 (t465)**; 39: (0.5, 1.0) = **9,944,600
(t674)**; 33: (2.0, 0.5) = **8,821,905** (banked 9,566,490). The (2.0, 0.5)
first-probe default left 1.7M on the table on 31. Slot design updated to a
diverse 8-config rotation + one plan ticket, min-wins. prob_26-class
(density-limited, non-rock) raw builds land ABOVE banked — the explorer
there rides on polish/min-wins only, as expected.

Raw nm+beam constructions BEAT the fully-polished banked values on 39
(−2.0M) and 27 (−0.7M) and match 31 (−83k). Near-miss recovery alone is
worth ~1–3M raw on every rock; beam× near-miss compounds (the beam's joint
fill now sees the recovered anchors). Plan-target tickets on 31 landed
within noise of ungated (11.0M vs 10.9M) — the gate is NOT the primary
lever; dilation recovery is. Byte-inertness verified: nm=0 dispatch hash-
identical to v18 on prob_31.
