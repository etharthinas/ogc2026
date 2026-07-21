# MOONSHOT PLAN — global nester / Gurobi packing (goal: total < 120M)

**Authorized 2026-07-21.** Start with the bounded 1–2h Gurobi prototype (below)
BEFORE any multi-day build. New chat picks this up.

## RESULT 2026-07-21 — PROTOTYPE RAN, ZERO YIELD, FORECLOSURE AIRTIGHT

Probe: `baseline/probe_gurobi_nfp.py` (true-shape NFP MIP; run
`python probe_gurobi_nfp.py dumps/prob_39.myalgorithm_jv9.json --bay B`).
Verdict on jv9's prob_39 (obj 8,406,071, Z1=553, per-bay 143/182/228):
**on ALL THREE bays the exact optimum equals the incumbent, PROVEN**
(bound == incumbent; bay0 D=12: 123→123, bay1 D=11: 154→154, bay2 D=6:
132→132; spliced solutions re-verify byte-identical objectives). Gurobi
finds nothing = the plan's decision rule fires: report and stop.

Two structural discoveries that outlive the probe:
1. **The checker evaluates INTEGER coordinates only.** `check_feasibility`
   rebuilds every Block with `x=int(round(x))` (utils.py:1154/1334). The
   "continuous non-overlap NFP" angle — the one differentiator this plan
   called genuinely new — does not exist as a degree of freedom. Any nester,
   global or local, plays on the same integer grid the raster engine already
   searches. (Measured the hard way: float solutions placed 5e-3 outside the
   NFP boundary round INTO overlap and fail stage 2.)
2. **Gurobi's license is size-restricted: 2000 vars / 2000 constraints**
   (hits at 2001; expiry 2027-11-29 is real but the cap is what binds).
   Whole-bay exact models are impossible on this machine; Xpress is a dead
   network license (error 998). Model budget forces (bay, window) locality:
   D<=14 movers, radius 6, ~1500-1900 vars.

Probe model (sound, checker-validated end-to-end): movers = most-tardy
non-interlocked blocks of the worst window; integer (x,y) in a radius-6 box
x integer entry times; per-pair disjunction [time-disjoint] OR [relative
vector outside EVERY convex piece of the true union-footprint NFP]
(ear-clip + Hertel-Mehlhorn decomposition, piece-pair Minkowski, unioned +
re-decomposed, reachability-pruned big-M edges). Conservatisms: union
footprint (forbids the layer-order interlocks the incumbent DOES use — the
model literally cannot represent some jv9 placements, they had to be
pre-banned from the mover set), orientation fixed, NFP holes filled.

Why this closes the moonshot rather than just narrowing it: the exact
optimizer was given MORE freedom than the dead CP-SAT menus (full ~169-cell
integer neighborhood per mover, jointly, plus free retiming) and proved the
heuristic's packing locally optimal on every giant hot window; the only
untested regime is whole-bay/global scale, which (a) has no solver vehicle
under the license caps, and (b) lost its claimed differentiator with the
integer-grid discovery — a global exact nester would be searching the same
lattice the portfolio already saturates, with the same interlock semantics
CP-SAT already encodes exactly. <120M stays foreclosed under everything
tractable on this machine.

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
