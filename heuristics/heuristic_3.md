# Heuristic v3 — EDD-earliest packing + multi-start best-of (no-regression)

## Diagnosis from v1/v2 + floor analysis

- v1 (congestion-ALAP) total **1.067B**; v2 (EDD-name-but-actually-congestion +
  dense + LNS) **REGRESSED to 1.658B**. v2's dense packing + LNS made the
  congested high-w1 instances worse and was non-monotone in time.
- Objective is dominated by **w1·Z1 (tardiness)** on the 12–20 congested
  instances prob_21–40 (w1 up to 29k). Uncongested prob_1–20 are already near
  their floor in both v1 and v2.
- **Relaxed tardiness LB** (merge all bays into one cumulative resource of area
  C = Σ bay area, ignore geometry/crane, EDD list-schedule — strictly EASIER
  than the real problem): every uncongested instance → 0 tardiness; congested
  Σ w1·tardyLB ≈ **98M**. Per instance e.g. prob_38 tardyLB=2963 (×13333=39.5M)
  vs v1's ~35,000 (472M). **⇒ ~90% of the tardiness on prob_38/27/39/33/31 is
  AVOIDABLE.** Realistic achievable total ≈ 100–200M (real > relaxed), not 1.5M.
- The relaxed schedule reaches 0 tardiness everywhere it's possible **using EDD
  order + earliest-feasible placement**. That is the lever v1/v2 both miss
  (v1 ALAP-anchors → late clustering; v2 packs in congestion order → late-due
  blocks steal early slots from early-due blocks).

## Three improvements planned for v3

### 1. EDD-earliest construction (PRIMARY)
Order blocks **earliest due date first** (tie: shortest processing, then largest
area, then most layers). Place each at the **earliest feasible slot ≥ release**
that packs spatially (bottom-left over the blocks present in that window) and
passes crane entry/exit. Early-due blocks claim early time → later-due blocks
fall into later windows → co-presence spreads across the horizon instead of
bunching late. This directly reproduces the relaxed schedule's tardiness win
under the real constraints. Applied to forced/congested instances; the
uncongested path keeps v2's zero-slot Pass A (already optimal there).

### 2. Multi-start best-of incumbent (anti-regression + robustness)
Per instance, build with several constructors and **keep the best VERIFIED-
feasible** solution: {EDD-earliest, congestion-ALAP (=v1 behavior), and a few
seeded EDD tie-break/bay-order perturbations within the time budget}. Guarantees
v3 ≤ min(strategies) ≤ v1 on every instance — the regression v2 introduced is
structurally impossible. Multi-start greedy is the low-risk lever CONTEXT.md
explicitly recommends.

### 3. Safe tardiness-pull improvement (replaces v2's broken LNS)
Spend remaining time on moves that can only help: take the worst-tardy blocks
and re-search a full earliest-slot placement across ALL bays/orientations;
accept only if it lowers that block's exit time AND the re-checked full solution
objective improves (verified feasible). Monotone — never worsens the incumbent
(v2's LNS could and did). Also run extra multi-start rounds as time allows.

## Reuses from v2 (correct, keep verbatim)
`_can_place`, `_present_at_*`, `_find_zero_slot`, `_find_earliest_slot`,
`_candidate_positions`, `_orient_*`, `_unique_orients`, `_objective`,
`_build_operations`, `_force_place`, empty-bay safety net, incumbent discipline.

## Results (benchmarked 2026-06-29, 90s/instance, 40/40 feasible)

**TOTAL = 442,472,883** — 2.4× better than v1 (1,066,850,978 @120s), 3.7× better
than v2 (1,658,139,513). See results.csv row `algorithm 3`.

### Wins
- EDD-earliest crushed the dominant tardiness: prob_38 472M→211M, prob_27
  174M→52M, prob_39 79M→30M, prob_31 43M→19M, prob_33 43M→18M, prob_37 28M→10M,
  prob_35 40M→15M, prob_32 9.5M→5.5M. Best-of made the uncongested instances
  better too (prob_8 174k→12k, prob_6 1.01M→235k, prob_18 390k→144k, prob_15/17/19
  all ~halved) — the EDD + perturbation candidates beat v1/v2's single pass.
- No regression except **prob_1: 166,743 vs v2 108,561** (obj1=2 residual vs v2's
  obj1=0). The improver didn't mop up the last 2 units of tardiness that v2's
  random-neighbor LNS happened to fix. Minor (+58k) vs the ~600M gained overall.

### Where the cost now lives (v4 targets)
Total is dominated by a few forced instances; obj1 (tardiness) still far above
the relaxed area-only LB, so much is still avoidable:
- **prob_38: 210,670,582 = 48% of the whole total.** obj1=15,630 vs relaxed LB
  2,963 (×13333 ⇒ ~39.5M floor). ~170M still avoidable here alone.
- prob_27: 52.4M, obj1=3801 (LB 2031 ⇒ 27M). prob_39: 29.7M, obj1=2143 (LB 414).
  prob_26: 22.7M, obj1=1650 (LB 687). prob_31/33/35/30 each ~14-19M.
The lever for v4: drive obj1 on these forced instances toward the relaxed LB —
better time-spreading / a real LNS that reschedules the congested window, and
fixing prob_1's residual.
</content>
