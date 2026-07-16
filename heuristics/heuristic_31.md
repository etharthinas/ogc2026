# Heuristic v31 — EPOCH RESET + RESERVATION SHUFFLE + OBJ2/3 POST-PASS (goal < 110,000,000; frontier = v25 cells 124,581,895)

Departure: v25 (= v28 = v29 = v30 cells). Remaining ask: −14.6M.

## Where the remaining mass demonstrably is

1. **Wasted post-convergence budget on 27-class** (28f telemetry): prob_27's
   improve slices run 76–291 rounds with since_o1 == slice length — hundreds
   of seconds of converged spinning. 26/31/33 similar (converge within
   600s). Incumbent-perturbation escapes are dead (28a/f); a FRESH epoch is
   the one diversity source never tried.
2. **prob_37's future-commitment blocking** (diag37): strict feasible 0.27%
   vs lenient 2.42% — a 9x gap unique to 37. ~10% of blocked moments have
   geometric room NOW that is only claimed by a not-yet-entered block's
   reservation. No mechanism has ever displaced a reservation.
3. **obj2/obj3 mass ≈ 12.4M across the eligible-7** (38: 2.10M, 27: 1.96M,
   31: 2.83M, 37: 2.81M, 26/33/39: ~2.7M). Historically "Z3 relocation
   saturated on forced" — but that pass was TOTAL-objective-gated. An
   obj2/3-ONLY post-pass with obj1 FROZEN as a hard constraint (retime/
   relocate moves that cannot touch any entry-queue-critical block) was
   never tried.

## Improvement A — epoch reset on convergence (primary)

Portfolio-level: when a worker's improve stream has stalled on obj1 for
EPOCH_AFTER rounds (reuse since_o1, the proven signal) AND ≥ EPOCH_MIN_REM
seconds remain, abandon incumbent perturbation entirely: re-run the
worker's ENTIRE construction phase with a shifted seed base (seed + 7777,
fresh drng, same ticket structure), then polish the new champion with the
remaining budget; final result = min(old best, new epoch best). Full-
solution min-wins → floor-safe by construction; fires only in measured-
wasted budget (the 28f regime). Round-starved giants never reach the gate
(38-safe by the same telemetry that killed 28a there). Spot {27,26,31,33}.
Keep if any ≥ −100k. Kill: all flat → converged-instance budget is simply
exhausted value and the eligible set is closed at 600s.

## Improvement B — reservation shuffle at admission (37-aimed)

Dispatcher-level, new move: when a released block b cannot place anywhere
(strict) but COULD place ignoring not-yet-entered reservations (the lenient
check — machinery exists in diag form), find the future entrant r whose
reservation blocks b; if r's slack (due_r − (t_now + proc_r)) exceeds b's
by MARGIN, STEAL the reservation: place b now at the freed anchor, re-queue
r (r re-enters the admission queue and gets re-placed at its next feasible
moment). One steal per event, deterministic tie-breaks, gated to instances
with a measured lenient/strict gap ≥ 3x (statically: 37-class — gate on
the instance signature n≥250 ∧ w1≤3400 like 37, or add ratio conditions;
verify 38/39 excluded). Deliver as an APPENDED W2 ticket variant
(steal=True) — sub-second per event, no solver. Spot {37}. Kill: flat
after a MARGIN sweep {2, 4}.

## Improvement C — obj2/3-only post-pass with obj1 frozen

After the portfolio settles (post-race, respects the race-displacement
law), run a final pass on the champion: identify blocks with preference
penalty (obj3) or in the max-imbalance bay (obj2); try relocation to a
preferred/lighter bay or retime WITHIN slack (entry may move later only if
exit ≤ due and no queued block wanted that slot — conservative: only moves
that provably keep obj1 IDENTICAL block-by-block); accept per-move iff
obj2/obj3 strictly improve. Cheap (seconds), full check_feasibility gate
at the end, min-wins vs pre-pass champion. Runs everywhere (obj1-frozen →
cannot regress tardiness anywhere). Spot {37,31,38} (largest obj2/3 mass).
Kill: < −50k total across all three.

## Ladder

- 31a = A. prob_1 guard; spot {27,26,31,33} @600s.
- 31b = B. Spot {37} @600s.
- 31c = C. Spot {37,31,38} @600s.
- Combine survivors → eligible-8 → full-40 row `algorithm 31`; promote if
  < 124,581,895; goal check < 110,000,000.

## Results

### 31a spot (2026-07-16) — fully byte-flat; killed

myalgorithm_31.py (epoch reset on convergence: W1/W2/W3 armed with +7777
seed shifts, EPOCH_AFTER=120/EPOCH_MIN_REM=90; W0 unarmed anchor). Spot
{27,26,31,33} @600s: 24,972,962 / 8,551,513 / 8,124,019 / 7,734,338 —
all byte-flat. Even a completely fresh construction epoch spent in the
measured-wasted post-convergence budget cannot beat the incumbent basins.
Closes the "fresh diversity" family: the eligible-8 are at the
architecture floor at 600s. 31b (reservation shuffle) and 31c (obj2/3
post-pass) superseded by the heuristic_32 radical epoch; 31c's obj2/3
target is being captured by v33's merge tail instead (prob_1 −9,508 was
entirely obj2/obj3).
