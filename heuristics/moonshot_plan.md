# MOONSHOT PLAN — global nester / Gurobi packing (goal: total < 120M)

**Authorized 2026-07-21.** Start with the bounded 1–2h Gurobi prototype (below)
BEFORE any multi-day build. New chat picks this up.

## Where we are (don't re-derive — it's measured)
- SOTA = **jv9** (`baseline/myalgorithm_jv9.py` = `myalgorithm.py`), honest
  full-40 single-shot **122,728,934** (−2.4% vs jv6 124.48M). Composed
  best-of-draws 121,468,412.
- Goal <120M is FORECLOSED under construct→polish→merge (7 lever families
  dead: capacity jv7–9 won −3M, jv10–13 within-run all dead, packing +
  preference audits both structurally forced). See heuristic_jv7–jv13.md,
  [[jv7-capacity-law]], [[jv6-campaign]].
- Objective split (full-40): **w1·Z1 = 101.3M (83%)**, w2·Z2 = 0.44M,
  **w3·Z3 = 20.9M (17%)**. Z3 is preference-oversubscription-forced (every
  cell 2–33× over capacity) — NOT the moonshot target.
- **Moonshot target = Z1 tardiness on the giants.** Area lower bound
  (`baseline/lb_analysis.py`): **prob_39 and prob_37 have Z1 area-optimum = 0**
  (their block area fits with ZERO tardiness) yet the heuristic achieves
  Z1 = 553 (39) / 899 (37) → 39 (8.41M) + 37 (5.76M) = **14.2M of loss that
  is theoretically packing-fragmentation, not capacity**. 38 (139% cap) and
  27 (141% cap) have SOME forced tardiness; 39/37 are the pure-nesting cells.

## The prototype question (1–2h, bounded)
Can a global/exact nester find a materially-lower-tardiness packing on a giant
than the heuristic + OR-Tools whole-bay pack (which measured ZERO yield on 39,
"millions of branches, feasible-at-hint")?

### Design
1. Pick **prob_39** (area-LB Z1=0, so a zero-tardy packing SHOULD exist if
   tiling allows). Load `train/prob_39.json`.
2. Get jv9's solution for 39 (run once @750s or reuse a saved dump) → its
   per-bay block sets, placements, entry/exit, and Z1.
3. Gurobi model on the SINGLE most-tardy bay (or a peak-congestion time
   window): binary grid-occupancy or No-Fit-Polygon pairwise non-overlap +
   integer entry times, minimize tardiness, WARM-START from jv9's placement.
   - grid model = same as OR-Tools whole-bay but Gurobi's presolve/cuts may
     search differently; NFP model = genuinely new (continuous non-overlap).
4. Timebox Gurobi to ~20–40 min. Compare its best tardiness vs jv9's on that
   bay.

### Decision rule
- Gurobi beats the heuristic packing by a real margin → the moonshot is
  justified; scale to all giants + integrate with the schedule (multi-day).
- Gurobi finds nothing (matches OR-Tools) → foreclosure is airtight; report
  and stop. (This is the likely outcome — same model class as the dead
  whole-bay pack; the NFP formulation is the one real differentiator worth
  trying.)

## Env / gotchas (from the campaign)
- Solvers: **Gurobi available, license OK to 2027-11-29**; Xpress importable.
  OR-Tools CP-SAT is what the heuristic uses.
- Python: `C:\Users\user\anaconda3\envs\ogc2026\python.exe` (conda not on PATH).
- Bench: `bench.py <mod> <tl> <k>`; a 180s LIMIT on a giant always returns
  3.7B empty-fallback (one dense build takes >180s — NOT a bug). Use ≥600s or
  reuse a saved solution dump. NO other CPU work during benches.
- Feasibility oracle: `utils.check_feasibility` (do not modify utils.py).
- `_exact_pack_bay` / `_exact_pack_window` in myalgorithm_jv9.py = the existing
  OR-Tools packers (the ones that found zero) — read them first to avoid
  rebuilding the dead model; the NFP/Gurobi angle is what's new.

## New-chat kickoff
Reference this file + [[jv7-capacity-law]]. First action: read
`_exact_pack_bay` in myalgorithm_jv9.py + `lb_analysis.py`, dump jv9's prob_39
solution, then build the Gurobi/NFP probe on 39's worst bay.
