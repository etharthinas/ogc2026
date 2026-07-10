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

| run | prob | start | explore | iters | accepts | best | verdict |
|---|---|---|---|---|---|---|---|
| v0.1 naked R&R (avg ruin 10, caps 40/30, L=1000) | 31 | v18 @120s = 10.93M | 300s | 124 | 0 | =start | throughput FAIL + 0 accepts |
| v0.2 small ruin (avg 6, caps 18/14, L=300) | 31 | 10.93M | 300s | 230 | 0 | =start | ≥200 iters OK; 0 accepts |
| v0.2 fresh start (raw EDD build 58.1M) | 31 | fresh | 300s | 522 | 463 (92%) | 39.15M | mechanism works; repair far too weak to reach the basin |
| ILS mode (ruin → 2s `_improve` burst) | 31 | 10.93M | 300s | 93 | 0 | =start | descent can't recover the ruin loss either |
| delta probe (ILS, 120s) | 31 | 10.93M | 120s | 37 | 0 | =start | **min candidate delta = +13,600** (≈1 tardiness unit), then +40k/+67k/+253k |
| naked R&R | 39 | v18 @120s = 12.89M | 300s | 345 | 2 (ties) | =start | min deltas 0, 0, +141k |
| RRT 2% (linear→0) | 31 | 10.93M | 300s | 306 | 8 | =start | wanders to 11.13M and back; nothing better found |
| RRT 5% (linear→0) | 31 | 10.93M | 300s | 288 | 7 | =start | wider band (cur to 11.42M), still flat |
| RRT 2% | 39 | 13.98M (BUILD CONTAMINATED — co-running session load; ≠ clean 12.89M) | 300s | 343 | 1 | =start | measurement INVALID; rerun on quiet machine |

**Diagnosis (three findings).**
1. From the polished incumbent, (almost) every ruin+rebuild candidate is
   strictly worse — v18's improver already exhausted this neighborhood, and
   LAHC's uphill tolerance never activates when nothing is ever accepted
   (history stays pinned ⇒ degenerates to hill climbing). Published LAHC
   successes (GDRR) start from construction, not a foreign polished incumbent.
2. The barrier is a **sill, not a cliff**: best candidate deltas are tiny
   (+13.6k on 31; exact ties on 39). RRT does walk over it — but at ~1 it/s
   (raster placement cost on forced instances) a 300s trajectory is ~100×
   too short to find a different deep basin. The literature's LAHC/SISR wins
   run 10³–10⁶ iterations.
3. Fresh-start trajectories improve monotonically but from 5× worse starts.

**Consequence for Improvement 5**: acceptance-rule novelty alone is NOT the
unlock at current iteration costs. Either (a) wire Improvement 7 first
(numba/vectorized placement → 10–100× iterations, exactly the plan's noted
fallback "if iterations are too slow"), or (b) make the *move* stronger
instead of more frequent — final variant under test: `_repack_window` (v18's
strongest joint move) as the perturbation with RRT acceptance on top
(`--repack --rrt 0.02`), which v18 itself only ever accepts downhill.

**Sweep status vs the plan's kill criterion** ("31 AND 39 flat after L/ruin
sweep"): prob_31 is now flat across naked L∈{50,300,1000} × ruin{6,10,strip} ×
caps{18/14,40/30} × ILS-2s × RRT{2%,5%} — the acceptance-rule side of the
sweep is effectively exhausted at ~1 it/s. prob_39 still needs a CLEAN RRT
rerun and the repack-move variant before invoking the kill. Do NOT record
Improvement 5 dead yet; record "flat at current throughput, unlock candidates
= Improvement 7 speedup or joint-move perturbation."

## FIRST SIGNAL — repack-move + RRT (`--repack --rrt 0.02`), 2026-07-10

The joint-move-perturbation unlock candidate WORKS on prob_31: perturbation =
`_repack_window` (v18's strongest joint move, which v18 only ever accepts
downhill), acceptance = linear RRT (T0 = 2% of start, →0). Mac, build 120s +
explore 300s, seed 1234:

| prob | start (Mac @120s) | explorer best | delta | iters | accepts |
|---|---|---|---|---|---|
| 31 | 10,927,585 (clean value reproduced) | **10,876,303** | **−51,282** | 108 | 54 |
| 39 | 13,978,536 (CONTAMINATED build — co-load) | 13,969,364 | −9,172 | 73 | 25 |

First negative candidate deltas of the whole sweep (−25.9k/−25.3k on 31,
−9.2k on 39): an RRT-wandered `cur` exposes congested windows the
deterministic v18 trajectory never repacks. prob_31 moved after being
byte-flat across v14→v18; vs the banked Windows 600s row its Mac total is now
−391,940 (−340,658 pacing/basin + −51,282 explorer). CAVEATS: both runs
co-ran with another session's experiments (see bench-hygiene note) — prob_31's
start value reproduced the clean basin so the improvement is likely real but
needs a quiet-machine rerun; prob_39's build was contaminated outright.
Confirmation in flight: 2 × (build 120s + explore 900s) on prob_31, seeds
42/7, rrt 0.02/0.03, run serially on a quiet machine.

Next per the plan's "any movement on 31" rule: sweep rrt fraction ×
win_scale × max_destroy × seeds, rerun prob_39 clean, then validate on the
Windows bench machine before wiring a quarantined explorer slot into
`myalgorithm_19.py` (19b).

**Bench-hygiene reminder** (bit us twice today): concurrent runs on this
machine corrupt builds (prob_39 build 12.89M → 13.98M under co-load; earlier
prob_38@300s → fallback). One experiment at a time, check `ps` first.
