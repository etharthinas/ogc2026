# Heuristic v2 — EDD Temporal Leveling + Thorough Placement

## Why v1 loses (diagnosis from results.csv row `algorithm 1`)

v1 (`myalgorithm_1.py`, congestion-first + ALAP) totals **~1.23B at 60s/instance**.
The cost is almost entirely **obj1 (tardiness)** on instances prob_21–40, and these
runs are NOT timeout-bound (prob_38 finishes in 55s, prob_27 in 19s) — the tardiness
is **algorithmic**.

Two oracles computed over the 40 train instances:

- **ALAP peak/cap** (everyone exits at due date): up to 2.75 — looks hopeless.
- **MANDATORY peak/cap** (area that MUST co-exist for any zero-tardy schedule,
  using `[due-proc, release+proc]` overlap windows): only **12 of 40 instances
  exceed 1.0**. The other **28 can reach ~zero tardiness** if entries are spread
  within each block's slack window and packed reasonably.

Key identity: a block entering at `release` and exiting at `release+proc` has
tardiness `max(0, -slack) = 0` whenever `slack ≥ 0` (true for most blocks). So
tardiness is fundamentally a **spatial-packing-over-time failure**, not a temporal
one. v1's ALAP anchoring piles every block at its due date, overflows the bay, and
dumps the overflow into serialized empty-bay windows (`_find_tardy_slot` fallback)
→ massive avoidable tardiness even on instances whose MAND peak/cap < 1.

Evidence of avoidable slack: prob_31 MAND=1.04 but v1 obj1=3047; prob_28 MAND=0.89
but obj1=824; prob_21 MAND=0.93 but obj1=408; prob_38 MAND=1.77 but obj1=33228
(floor is far lower).

## Three improvements planned for v2

### 1. EDD ordering instead of congestion ordering (PRIMARY)
Process blocks **earliest-due-date first** (tie: largest area, then least slack).
Placing earliest-due blocks first at ALAP makes them claim the *earlier* time
windows; later-due blocks naturally fall into *later* windows → co-presence is
spread across the horizon instead of bunched at the late end. This is the classic
EDD result for tardiness and it directly attacks v1's clustering.

### 2. Thorough min-tardiness placement (drop the "first zero slot" shortcut)
v1's `w1_dominant` path takes the *first* zero-tardiness slot in the most-preferred
bay and stops. v2 instead, for each block:
  - scans candidate positions across **all** bays/orientations (richer BL +
    edge-contact set, larger cap),
  - for each, finds the feasible interval with **minimum tardiness** (zero if any
    slot fits), and among zero-tardy options prefers the one that **wastes least
    space / keeps the bay flattest** (skyline top-y), so later blocks still fit.
  - falls back to least-tardy (not empty-bay serialization) only when no zero slot
    exists anywhere.

### 3. Time-budgeted improvement loop (LNS-lite)
After a feasible construction, repeatedly **destroy** the most-tardy blocks (and a
few spatio-temporal neighbors) and **repair** them with the same thorough
placement, in a different order. Keep the best VERIFIED-feasible incumbent. Spend
the remaining time budget here. Directly drives obj1 down on the forced-tardy
instances and mops up residual tardiness on the rest. (obj2/obj3 reassignment is
deferred to v3.)

## Reuses from v1 (correct, keep verbatim)
`_can_place`, `_present_at_entry/_exit`, `_find_zero_slot`, `_candidate_positions`,
`_orient_bbox/_orient_fits/_unique_orients`, `_build_operations`, the empty-bay
safety net, and the always-return-feasible incumbent discipline.

## Results (benchmarked 2026-06-29)

**TOTAL = 1,658,139,513 — a REGRESSION vs v1 (1,066,850,978).** 40/40 feasible.
See results.csv row `algorithm 2`.

### What happened
- v2 drove obj1=0 on ~16 uncongested instances (prob_1–19) and shaved obj2/obj3
  there (e.g. prob_1 108k vs v1 508k, prob_4 83k vs 659k). Good.
- But on the congested high-w1 instances (prob_21–40) it got WORSE, and these
  dominate the total. **prob_38: 777,913,924 (v2, 3109s) vs 472,513,932 (v1).**
  EDD/dense packing + LNS *increased* tardiness on the worst instances despite
  being given huge time budgets (3000s+).
- Root cause: dense earliest-slot packing fills bays greedily early, then the
  tail of congested blocks has nowhere to go and gets serialized into empty-bay
  windows → enormous obj1. The LNS destroy/repair re-inserts with the same
  greedy and can't escape. More time made it worse, not better (non-monotone).

### FLOOR ANALYSIS (decisive)
Joint assignment-only relaxation (geometry/time dropped, **obj1=0 assumed
everywhere**, multi-start SA minimizing w2·Z2 + w3·Z3) → **SUM = 1,305,792**.
- This is an *optimistic* estimate of the absolute best total: it assumes ZERO
  tardiness on all 40 instances, which is provably impossible on the 12
  instances with mandatory peak/cap > 1 (prob_21,23,24,25,26,27,28,30,31,32,33,
  35,37,38,39,40 — peak/cap up to 2.75). Any real schedule adds w1·Z1 on top.
- Net: the achievable floor is **≈1.3M (optimistic) to ~1.5–2M (realistic)**.
  **A total under 1,000,000 is below the floor — not attainable.** The lever
  that matters is collapsing the ~1.6B of avoidable tardiness on the congested
  instances down toward that floor, not chasing a sub-1M number.
