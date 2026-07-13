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

## Results (filled after testing)

(pending)
