# heuristic jv6 — v33(jay) × jv5(jiyun) stack + 750s budget campaign (goal < 110M)

> Base: **v33** (`origin/dev/jay` 162375a, `algorithm 33 final` = 124,336,687 on
> jay's machine) merged with **jv5-r2** (our Phase A dispatch-repair + deep-nestle
> W0/W3, −799,909 on prob_38 this machine; Phase D `_scoped_union` memo).
> 3-way merge, base = v25 c407ac1; only textual conflict was the header.
> Deadline 2026-07-28 14:00 KST; freeze 07-27. **New bench standard: 750s**
> (goal directive "max search capacity within 750s"), 4w, same-machine A/B only.

## 0. Evidence base (do not re-litigate)

- Jay's v26–v34 epoch: **every single-axis family on the forced mass is measured
  dead** (admission order, improver escapes/moves, polish depth, seed slots,
  placement scoring, fresh epochs, BRKGA/backward/partition rewrites,
  cross-paradigm merge, obj1-frozen obj2/3 pass, 3× budget). Total epoch yield
  = −245,208, all from the **S4 self-gating merge tail on non-forced cells**.
- v33 1800s probe on prob_38: bit-identical → budget scaling closed **for v33**.
  (jv6 re-opens the question: v33's W0/W3 second builds were dead code — jv5
  repaired them. 750s A/B on {38,27} re-measures time-convertibility.)
- Relaxation "headroom" on 38/27 (obj1 1219/615 vs 2569/1726) is a
  **geometry-blind mirage** (29d): realizable orders live ±1 unit from the
  champion's. The only named-open escape: **joint order+geometry** (no tractable
  mechanism known) and **31b reservation-steal** (designed, never benched).
- Laws in force: same-machine A/B only; min-wins protects the bank not the race
  (race-displacement law — tail additions must be sub-second or post-race);
  W1-append is structurally dead on 26-class (tickets must HEAD the rotation);
  W1↔W0 coupling frozen on 38; every improver round on giants is descent-critical.

## 1. Plan — three routes (per evolve.md)

### Route A — the jv6 stack itself (banked levers, verify the merge)
v33's merge tail + jv5's Phase A/D have disjoint code paths except that
**Phase D (faster scan_scoped) feeds the merge tail a richer candidate pool**
— expected ≥ additive. Gates: prob_1@60s, hot A/B vs v33 @750s {38,27},
protect spot, full-40 @750s.
- Early signal (07-17): jv6 @30s prob_1 = **1,499 = the obj1=0 joint floor**
  (v25 18,357 / v33-banked 8,849 @600s / standalone-S4 4,035). Synergy real.

### Route B — 31b reservation-steal (jay-designed, never benched; 37-aimed)
When a released block b is strictly blocked but has room vs residents-only
(lenient), find the future entrant r whose realized reservation claims that
room; if slack_r − slack_b ≥ MARGIN, steal: place b now, re-queue r. Appended
W2 ticket (sub-second, no solver), gated to 37-class signature
(lenient/strict gap ≥ 3×; verify 38/39 excluded). Kill: flat after MARGIN {2,4}.
Prior tempered by w3nm's measured tie on 37 (deeper admission search polished
away) — but steal ≠ search-harder: it *displaces* a committed future claim.

### Route C — 750s budget exploitation
All pacing is w-proportional (tick_dl≈0.55w, W0→0.38w, W3→0.40w), so 750s
gives every stage +25% wall. Two sub-bets:
1. **Repaired deep pipelines convert time** (Phase A builds were dead code in
   v33's 1800s probe → that probe does not bind jv6). Measured by the 750s hot A/B.
2. **Merge-tail re-harvest at 750s**: the S4 gate (non-forced ∧ tail ≥ 6s ∧ ≥3
   cands) opens wider with +150s; the harvest family is the only one with
   measured nonzero yield. Full-40 @750s captures it.

### Route D (stretch) — post-convergence burst-slab joint re-solve (27-class)
The one shape not literally tried: scoped **order+geometry LNS on the burst
subwindow** executed only in measured-wasted spin budget (since_o1 conv gate;
38 never reaches the gate → 38-safe). Destroy = all blocks entering t∈[a,b] of
the burst; re-insert by exact replay under permuted admission order (not
CP-SAT — the pairwise-compat model provably cannot express champions).
Prior LOW (28a/f: "improver-level basin-hopping cannot escape, period") —
attempt only if A–C leave budget before freeze.

## 2. Gates

```
# quiet machine, cwd=baseline/, serial:
bench.py myalgorithm_jv6 60 1                                    # ≤18,357 (merge tail may better it)
compare.py myalgorithm_v33_ref myalgorithm_jv6 750 38 27         # hot
compare.py myalgorithm_v33_ref myalgorithm_jv6 750 23 26 30 31 33 39   # spot rest
bench_row.py myalgorithm_jv6 750 "jv6"                           # full-40 row
```
Adopt: spot Σdelta < 0 ∧ protect byte-exact/noise ∧ 40/40 feasible.

## 3. Results

### Gate prob_1 — PASS, and a synergy discovery (2026-07-17)

| run | value | note |
|---|---|---|
| jv6 @30s | **1,499** (obj1=0, obj2=157, obj3=2) | = the `joint_floor_obj1=0` row value |
| jv6 @60s | **1,499** (56.9s) | deterministic reproduction |
| v25 @60s (convention) | 18,357 | |
| v33 banked @600s | 8,849 | its merge finds nothing @60s (tail ~8s) |
| standalone S4 @60s | 4,035 | needed a 35.9s CP-SAT |

**Mechanism**: jv5 Phase D (`_scoped_union` memo) accelerates the improver →
workers converge earlier → the post-race tail v33's merge gate needs (≥6s)
opens much wider → richer candidate pool + longer recombination solve. The
stack is **super-additive** on non-forced cells: jv6 @60s beats v33 @600s by
−7,350 on prob_1. Expect the full-40 @750s to re-harvest the ~20 non-forced
cells beyond v33's banked values.

### Route B implemented — `myalgorithm_jv6b.py` (pending smoke + A/B)

`steal` (int = MARGIN, 0=off) threaded `dispatch()` → `_dispatch_construct`;
`try_steal()` evicts a **same-tick** admission r (entry == t, zero elapsed →
pure reservation, no bay-time waste) with `slack_r − slack_b ≥ MARGIN`, retries
the blocked b, keeps eviction only on success; r re-queues. ≤2 attempts/event,
≤4 evictions/attempt, deterministic, no solver. W2 forced lottery gains two
APPENDED tickets `steal∈{2,4}` gated `steal37 = forced ∧ n≥250 ∧ w1≤3400 ∧
overload≤1.05` = exactly {37} on train. Risk noted: at n=250 the 5 base
tickets may exhaust the 0.45w cap → appended tickets inert; measure fire rate
with OGC_DEBUG before the A/B.

### hot A/B v33 vs jv6 @750s {38,27} — 38 landed (2026-07-17)

| prob | v33 @750s | jv6 @750s | delta | z1 |
|---|---|---|---|---|
| **38** | 37,556,441 | **36,756,532** | **−799,909** | 2673 → 2598 |

- v33 @750s = v25 @600s **bit-identical** → 750s buys the unrepaired code
  nothing (time-invariance now confirmed at 600/750/1800).
- jv6 @750s = jv5 @600s **bit-identical** → Phase A survives the v33 merge
  intact; its basin is also time-invariant. The −799,909 is banked on the
  stack.

| prob | v33 @750s | jv6 @750s | delta |
|---|---|---|---|
| 27 | 24,972,962 | 24,972,962 | ±0 (tie, z1/z2/z3 all equal) |

**GATE: PASS** (Σ −799,909, 0 regressions, lex 1W/1T). Note: 27 @750s gives
24,972,962 in BOTH arms vs the 600s-era 24,932,963 draw (+39,999) — the
extra 150s shifts the race draw slightly; fair across arms, noise-scale.
