# ledger_19 — 19a target ledger (v0, 2026-07-10)

Tool: `analysis/ledger_19.py` (CP-SAT non-preemptive area-cumulative
relaxation; NOT in the submission path). 60s/solve, Mac dev machine, quiet.
Model: exactly-one bay per block, exact durations (exit = entry + p),
per-bay `AddCumulative` over floor(min-orientation base-layer area) with
capacity ceil(cap_frac · Area_k); objective w1·ΣT. Deviations from the
heuristic_19.md Improvement-1 spec: no time bucketing needed (cumulative is
exact-in-time and still a relaxation); `d_k` calibration from v18 incumbents
replaced for now by fixed density scenarios cap ∈ {0.6, 0.5} bracketing the
measured best effective density (eta* = 0.48 on prob_38); Z3 term omitted
(floor row covers Z2+Z3). The v18-incumbent-replay calibration remains TODO.

Cell format: `provenLB/incumbentUB` of the relaxation (w1·Z1 units).
cap=1.0 is a mathematically valid lower bound; 0.6/0.5 are realistic-target
scenarios, not bounds.

| prob | v18 | floor(Z2+Z3) | cap=1.0 LB/UB | cap=0.6 LB/UB | cap=0.5 LB/UB |
|---|---|---|---|---|---|
| 21 | 1,380,772 | 80,470 | 0/0 OPT | 0/0 OPT | 0/199,995 |
| 22 | 934,883 | 36,937 | 0/0 OPT | 0/0 OPT | 0/0 OPT |
| 23 | 3,390,436 | 4,579 | 0/0 OPT | 13,559/94,913 | 81,354/1,816,906 |
| 24 | 643,943 | 24,755 | 0/0 OPT | 0/0 OPT | 0/0 OPT |
| 25 | 338,322 | 5,547 | 0/0 OPT | 9,338/146,073 | 14,674/272,803 |
| 26 | 9,653,490 | 74,172 | 0/0 OPT | 0/26,666 | 0/1,546,628 |
| 27 | 29,185,135 | 31,156 | 0/733,315 | 146,663/14,119,647 | 266,660/23,652,742 |
| 28 | 3,565,230 | 17,238 | 0/0 OPT | 0/0 OPT | 0/2,866,595 |
| 29 | 557,994 | 34,782 | 0/0 OPT | 0/0 OPT | 0/0 OPT |
| 30 | 4,083,746 | 16,252 | 0/0 OPT | 26,666/293,326 | 79,998/3,586,577 |
| 31 | 11,268,243 | 178,971 | 0/0 OPT | 0/506,654 | 0/5,906,519 |
| 32 | 3,881,748 | 28,565 | 0/0 OPT | 0/0 OPT | 0/93,324 |
| 33 | 9,566,490 | 19,080 | 0/0 OPT | 0/4,186,876 | 0/9,187,126 |
| 34 | 1,978,590 | 20,986 | 0/0 OPT | 0/0 OPT | 0/379,962 |
| 35 | 1,346,898 | 22,945 | 0/0 OPT | 0/0 OPT | 0/2,106,614 |
| 36 | 188,270 | 25,379 | 0/0 OPT | 0/0 OPT | 0/134,067 |
| 37 | 5,807,047 | 63,004 | 0/0 OPT | 0/1,099,890 | 0/3,709,629 |
| 38 | 45,806,839 | 17,678 | 0/2,546,603 | 0/28,119,297 | 0/45,332,200 |
| 39 | 12,361,461 | 25,594 | 0/0 OPT | 0/3,413,248 | 0/11,826,371 |
| 40 | 2,300,281 | 25,677 | 0/0 OPT | 0/594,297 | 0/1,278,639 |

## Readings

1. **cap=1.0: proven OPTIMAL 0 on 18/20 instances** (27/38 unproven-0 at 60s).
   Even non-preemptively, with whole-block bay assignment and exact durations,
   raw area volume forces zero tardiness. Every objective point above the
   Z2+Z3 floor is geometric/crane packing loss — confirming the fluid analysis
   with a stronger model. The <125M question is entirely about achievable
   packing density.
2. **Density scenarios quantify the prize.** If effective density 0.6 became
   achievable, the relaxation's own incumbents suggest ballpark targets of
   ~14.1M on 27 (now 29.2M) and ~28.1M on 38 (now 45.8M) — −33M on the two
   giants alone; prob_38's cap=0.5 UB (45.3M) ≈ v18's value, consistent with
   eta* ≈ 0.48 (v18 already extracts ~0.5-density performance there).
3. **prob_31 has huge non-density headroom**: even at 0.5 density the
   relaxation reaches 5.9M vs v18's 11.27M (LB 0). Its cost is preference/
   ordering structure, not packing capacity — consistent with the
   preference-concentration diagnosis (pinned rho 4.48).
4. **Verdicts**: all 20 remain CHASE by the valid-LB criterion (the valid LB
   is simply too loose to prove saturation). The *useful* stop-lines come from
   the density scenarios: e.g. treating cap=0.5 UB as "reachable without a
   density breakthrough" says 31 (→ ~6.1M incl. floor), 33 (→ ~9.2M), 39
   (→ ~11.9M) still have room, while 38 at 0.5 is already exhausted (45.3M ≈
   v18) — 38 moves ONLY with >0.5 effective density (Tier-C machinery).
5. TODO for ledger v1: replay v18 incumbents to calibrate true per-bay d_k
   (Improvement 2 step 1); longer budgets on 27/38 to settle their cap=1.0
   bounds; feed failed exact-pack windows back as no-good cuts (LBBD-style,
   see research_survey_v19.md §5).

## Improvement-5 (LAHC explorer) unit-test log — standalone driver `baseline/explorer_lahc.py`

Mac dev machine, prob_31, internal-objective comparisons (Mac basin @120s =
10,927,585, budget-flat to 420s — the same "deterministic basin" shape as the
Windows 600s row at 11,268,243):

| run | start | explore | iters | accepts | best | verdict |
|---|---|---|---|---|---|---|
| v0.1 naked R&R (avg ruin 10, caps 40/30, L=1000) | v18 @120s = 10.93M | 300s | 124 | 0 | 10.93M (=start) | throughput FAIL + 0 accepts |
| v0.2 small ruin (avg 6, caps 18/14, L=300) | v18 @120s = 10.93M | 300s | 230 | 0 | 10.93M (=start) | ≥200 iters OK; still 0 accepts |
| v0.2 fresh start (raw EDD build 58.1M) | fresh | 300s | 522 | 463 (92%) | 39.15M | LAHC mechanism works, repair too weak to reach the basin |

**Diagnosis.** From the polished incumbent, EVERY ruin+greedy-rebuild
candidate is strictly worse — v18's own improver already exhausted this exact
neighborhood, and LAHC's uphill tolerance only activates once something gets
accepted (history stays at the incumbent value otherwise: with an always-worse
repair, LAHC degenerates to hill climbing). The published LAHC successes
(GDRR) start from construction, not from a foreign polished incumbent. From a
fresh start the trajectory works mechanically but the naked greedy repair is
~4-5× weaker than v18's polish stack — 300s is nowhere near the banked basin.

**Consequence for Improvement 5**: the payload must be ILS-shaped —
(SISR ruin as perturbation) → (bounded `_improve` burst as local search) →
(LAHC/RRT acceptance on the resulting local optima) — not naked ruin-recreate.
Implemented as `--ils <burst_s>` in the driver; first measurement pending.
