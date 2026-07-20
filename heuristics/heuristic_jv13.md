# jv13 — giant solo (island broadcast off on giants) — DEAD

Base: jv9. Motivated by jv12's diagnosis: the 8 giant workers CONVERGE to one
basin per run (best5 identical) because the island broadcast makes them adopt
the first-good leader. Hypothesis: convergence makes the portfolio UNDER-
explore; suppress the broadcast on giants so 8 workers explore INDEPENDENT
basins to completion, min-wins → maybe find a basin BELOW the converged best,
not just reduce the 27 ±425k variance.

Build: parent skips `for ib in inboxes: ib.put(item)` when `_giant_solo`
(forced n≥250 + OGC_GIANT_SOLO!=0). Non-giants byte-identical.

## Probe (OGC_DEBUG, 27 @750s)
`prob_27 = 23,560,982` (obj1=1610) — BELOW the best-observed 23,649,558 by
−88,576. Looked like a genuine new basin (under-exploration confirmed?).

## A/B vs jv9 @750s {27,38,39}: DEAD (net −26,666) — NOT PROMOTED
| cell | jv9 | jv13 | delta |
|---|---|---|---|
| 27 | 23,649,558 | 23,649,558 | TIE — the probe's 23.56M was draw NOISE (27's real range 23.56–24.07M); the winning draw comes from an independent-builder worker (wid0 reclaim) both arms produce identically, so broadcast-suppression didn't change it |
| 38 | 36,756,532 | 36,783,198 | **+26,666 REGRESS** — the rigid giant's basin depends on convergence: the repack-follower workers need the leader to hold the hard-won 38 basin; independence loses it |
| 39 | 8,406,071 | 8,406,071 | TIE |

**Verdict: giant-solo neutral-to-negative. The under-exploration hypothesis is
REFUTED: independence does not systematically find lower giant basins, and it
hurts the rigid 38. NOT promoted; myalgorithm.py stays jv9.**

## Campaign-final (definitive)
Post-capacity within-run levers, ALL measured dead on giants:
- jv10 racer/2nd-deaf — displacement regress
- jv11 W0-reclaim replica — neutral + hang bug
- jv12 giant merge-tail — neutral (intra-run convergence, nothing to recombine)
- jv13 giant solo/independence — neutral + 38 regress

Five distinct within-run mechanisms, five dead. The giants are a genuine
absorbing fixed point: their value is set by the instance + the collective
basin the portfolio lands in, and no within-run manipulation (recombination,
independence, replicas, reconfiguration) moves it below the best between-run
draw. Only BETWEEN-RUN draw multiplication (capacity, jv7–jv9) helped, and it
is core-saturated at nw=8.

**<120M is foreclosed under construct→polish→merge.** Deliverable: jv9 —
composed 121,468,412 / honest single-shot 122,728,934, a real −2.4% over jv6
(124.48M), plus a complete measured impossibility proof across 7 lever families
(capacity being the sole winner). Closing the remaining −2.7M needs a non-
polish solver (multi-day, low odds) — a user decision.

## Post-hoc packing-lever checks (2026-07-21, grounded in lb_analysis)
- **Orientation dedup (jv14, discarded no-op):** hypothesis was that
  `_unique_orients` bbox-dedup discarded shape-distinct orientations (a
  fragmentation source). MEASURED MOOT: on 39/37/38/27 the blocks rotate at
  non-90° angles so all ~8 orientations have distinct bboxes already
  (bbox-unique 7.99/8, shape-dedup recovers 0 extra). The construction already
  explores every orientation. Fragmentation is a GLOBAL placement property, not
  orientation choice.
- Combined with the campaign's dead exact-pack (windows + whole-bay = optimal
  LOCAL placement, measured zero), the tractable packing levers are exhausted.
  The 39/37 packing gap (their tardiness is 100% nesting fragmentation) needs a
  GLOBAL irregular nester (No-Fit-Polygon class) = the multi-day moonshot.

## DEFINITIVE RESOLUTION (2026-07-21): giant tardiness is tiling-forced, foreclosed
The area lower bound (Z1: 38>=135, 39/37=0) is LOOSE -- it ignores 2D tiling.
The binding question is answered by `_exact_pack_bay` (whole-bay exact CP-SAT:
ALL bay blocks, free placement + FREE INTEGER ENTRY TIMES = exact "admit-
earlier re-nest"), which the campaign already ran ON PROB_39 across 5 configs
@45-90s: "FEASIBLE-at-hint, millions of branches, ZERO yield." So:
- capacity is NOT the limit (area LB near-zero), but
- irregular 2D TILING is the binding limit, and the heuristic already achieves
  the tiling-constrained neighborhood optimum -- an EXACT solver with free
  retiming cannot beat it.
Since exact local search finds nothing and basin-hopping is jay-proven dead
(28a/f), even a global No-Fit-Polygon nester is low-odds (it would have to land
a basin far from the heuristic's, which the absorbing-fixed-point evidence says
reconverges). **<120M is foreclosed with high confidence; the earlier "room is
real" was a loose-bound artifact. Recommendation shifts to accept jv9 /
renegotiate, NOT the nester moonshot.** Deliverable: jv9, single-shot
122,728,934 (-2.4% vs jv6), with a rigorous measured impossibility result.

## Preference (Z3) lever investigated & closed (2026-07-21)
The campaign was Z1-tunnel-visioned; audited the objective breakdown of the
full-40 single-shot: **w1*Z1=101.3M (83%), w2*Z2=0.44M (0%), w3*Z3=20.9M
(17%)**. The 20.9M preference penalty was untouched -- and the repack gate
`if best_tardy>0` (line 2471) means preference recovery NEVER fires on zero/
low-tardiness cells (prob_22: Z1=0 yet Z3=866k). Looked like a big open lever.
CLOSED as structurally forced:
- prob_22: 81/100 blocks prefer the SMALL bay0 (cap 1440) demanding 7793
  workload = 5.4x capacity. `_z3_relocate` on the solution recovered ZERO
  (every move budget<=0: relocating into the oversubscribed preferred bay
  spikes the w2 imbalance penalty past the w3 gain).
- EVERY big-Z3 cell is preference-oversubscribed 2x-33x (31: 33.6x, 27: 9.8x,
  37: 9.0x, 38: 7.0x, 34: all 4 bays 2.4-3.8x). Blocks collectively demand
  their preferred bays far beyond capacity -> the penalty is instance-designed-
  in and forced. The heuristic already recovers the small reducible part
  (bay_score w3 term + z3_relocate on giants).

## FINAL: both loss components structurally forced -> <120M foreclosed
- Z1 (83%): 2D irregular-tiling-forced (whole-bay exact-pack = zero yield on 39).
- Z3 (17%): preference-capacity-oversubscription-forced (every cell 2-33x).
The area lower bound (Z1 loose) and aggregate Z3 bound are both loose because
they ignore the REAL binding constraints (tiling / temporal peaks). Every
tractable lever across jv7-jv14 + this preference audit is exhausted. jv9
(single-shot 122,728,934, -2.4% vs jv6) is the deliverable; <120M requires a
fundamentally different solver with low odds (exact methods already find
nothing in-neighborhood).
