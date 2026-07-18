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

### Probe results (raw dispatch ablations, 2026-07-17 14:13–)

**probe_steal** (steal m∈{2,4} vs off, min-over-lottery lens):
| prob | best Δ within-cfg | new-raw-min vs off-min | note |
|---|---|---|---|
| 37 | **−170,703** (m2, k0.5) | −83,568 | design target fires; m2 > m4 |
| 27 | −93,418 (m4, k1.0) | −93,418 | mostly harmful (+0.8..1.5M others) |
| 38 | −2,004,353 (m4, k1.0) | −492,227 | k0.5 harmful; chaotic margins |
| 39 | −332,403 (m4, k0.5) | −71,498 | chaotic |
→ steal = lottery-diversity-like; clean signal only on 37. Deployed: W2 head
ticket steal2/k0.5 gated {37}.

**probe_nmc** (nm_compete on/off × nk{3,32}):
| prob | nk3 Δ | nk32 Δ | verdict |
|---|---|---|---|
| 38 | **−2,674,658** / −2,345,442 | +555M/+1118M (grid explodes, unfinished) | nk3 only |
| 39 | −578,814 / −544,847 | **−910,389** and k1.0: **−2,493,941 → raw 8,067,980 = −321k BELOW banked** | nk32 the star |
| 27 | +1.1M..+2.3M | explodes | cmp DEAD on 27 (as everything) |
| 31 | −143,985 (partial) | (pending) | mild |
→ cmp ≫ steal on giants; v25's deep-nestle did NOT subsume 20b-2. Deployed:
W0-reclaim 4th build @0.46w, gated n≥250 (excludes 27), overload>1.05 → nk3-cmp
(38-class), else nk32-cmp k1.0 (39-class).

**probe_nmc final** — prob_31: nk3-cmp k1.0 −1,372,611; nk32-cmp explodes; and
the **plain nk32/k1.0/a0.0 off-build = 7,772,243 = −628k BELOW banked
8,400,210** (a family config the production rotation apparently never runs —
W2 mid-tier ticket candidate, needs spot A/B on {23,26,30,31,33}).

**probe_cap**: 38 −1,459,277 within-config (k1.0,nk3) but 43.65M > the nk32
family min 41.06M → cap widening is SUBSUMED by the deep-nestle family; drop.

### jv6b deployed diff (vs jv6) — all gates verified byte-inert elsewhere
1. W2 forced lottery HEAD ticket steal2/k0.5, gate `steal37` = {37}.
2. W0-reclaim 4th build @0.46w (cmp), gate nm_elig ∧ reclaim ∧ n≥250 = {38,39}:
   overload>1.05 → beam/nm8/nk3/cmp k0.5a0.5; else beam/nm8/nk32/cmp k1.0a0.0.
3. `steal`/`nm_compete` kwargs default-off; 27 and all other 37 cells byte-exact.

### jv6b A/B @750s {38,39,37} — ALL TIES (2026-07-17 15:49–17:05)

| prob | jv6 | jv6b | note |
|---|---|---|---|
| 38 | 36,756,532 | 36,756,532 | bit-identical |
| 39 | 8,406,071 | 8,406,071 | bit-identical (@750s draw = banked+16,552) |
| 37 | **5,699,640** | 5,699,640 | bit-identical; **both arms −107,407 vs 600s banked — pure 750s time gain** |

Smoke: jv6b prob_1@60s = 1,499 byte-exact (all levers inert off-gate). PASS.

**Post-mortem**: the W0 4th build gets only the 0.38w→0.46w residual (~60s) —
a giant beam+nm8 build needs ~100–150s (probe budget) → truncated → force-
placed garbage → loses min-wins → tie. Also production builds are UNJITTERED
(drng=None) while probes jitter with seed 9099 — probe draws don't transfer
verbatim. The W2 steal ticket on 37 either never won its intra-worker race or
its stream lost the portfolio race (bit-identical output = the winning worker
was untouched in both arms). **Raw signal real, delivery slots lost — 30a's
fate.** Next insertion attempt must give the cmp build a FULL slice with the
probe's rng: 39-only ladder-head restructure (0.20w slice, jittered, existing
builds shifted +0.08w — v24 pacing risk confined to {39} by gate), and W0-
trace (OGC_DEBUG) to see whether the steal/cmp builds fire and what they
produce in situ.

### full-40 jv6 @750s — landed 22:53, feasible 40/40, TOTAL 125,474,905 (raw)

```
CSVROW jv6 (4w 750s; v33 x jv5 stack),8849,5840,61010,16916,70531,78558,77431,
11252,58395,79940,38108,94773,78343,99935,43137,44836,73755,54317,67227,185445,
1380772,873789,2494797,578751,334062,8093323,24972962,3565230,557994,3363565,
8400210,3881748,7869639,1978590,1688817,175641,5807047,37574186,8389519,
2245665,125474905
```

**vs jv5 row (@600s, this machine): +658,578 raw — but the delta decomposes:**
- **Non-forced merge-tail re-harvest: −383,875 across 21 cells** (12 −62,531,
  9 −46,485, 18 −39,613, 16 −32,177, 13 −26,522, 5 −25,519, 22 −24,950,
  4 −18,650, 19 −16,986, 10 −15,750, 24 −15,105, 11 −10,955, 6 −10,482,
  1 −9,508, 20 −9,845, 3 −5,180, 15 −5,072, 17 −4,309, 7 −3,364, 2 −780,
  36 −92). The Phase D × merge-tail synergy is REAL and banked.
- **Forced-cell draw shifts @750s**: 33 +179,066, 27 +39,999, 14 +5,902.
- **prob_38 = 37,574,186 = +817,654 off the basin reproduced 5× today**
  (36,756,532 across jv5's 4 runs + today's 2 A/B arms). 37/39/40 landed
  bit-exactly on their 600s bank values → tail-of-run load/draw artifact
  suspected. Isolated re-bench of 38 and 37 launched 22:54 (jay's algorithm-23
  re-bench precedent).
- prob_1 @750s = 8,849 (not the 1,499 @60s draw — merge pool differs by
  budget; the 1,499 basin exists but isn't the 750s attractor).

### Isolated re-bench (23:54–23:18) — row corrected

| prob | full-40 tail | isolated @750s | verdict |
|---|---|---|---|
| 38 | 37,574,186 | **36,756,532** (702s) | 6th reproduction of the basin — tail value was a load artifact; corrected |
| 37 | 5,807,047 | 5,807,047 | two 750s draws exist {5,699,640 ×2 (A/B), 5,807,047 ×2}; conservative kept |

**Corrected full-40 @750s = 124,478,185** (results.csv; second correction:
the night2 A/B re-measured 33 @750s isolated = 7,690,573 in BOTH arms → the
full-40's 7,869,639 was another tail artifact, −179,066). Net vs jv5 row:
**−338,142**. New SOTA row, this machine, 40/40 feasible.
⚠️ Protocol law: full-40 TAIL values for timing-sensitive forced cells are
unreliable on this machine — 38 (+817,654) and 33 (+179,066) both corrected by
isolated re-bench. Future rows: always isolated-re-bench the forced cells.

### Night2 (2026-07-17 23:18 – 07-18 01:15)

**probe_tall — DEAD.** Hard tall-orientation forcing on 26-class:
26 +3.83M/+13.2M (frac .75/.9), 23 +1.66M/+3.19M, 30 +1.79M/+3.13M.
Orientation freedom is essential; with 30a/b (soft steering) this CLOSES the
26 height-frag family entirely — the fragmentation is real but no orientation
policy exploits it. Do not re-propose.

**Mid-tier A/B (r2, APPENDED nk32j ticket, {31,33,26,23,30}) — 5/5 bit-
identical ties.** The appended ticket NEVER RAN: W2's existing 7 tickets
already exhaust the 0.45w cap on mid-tier. **Law: W2-append is structurally
dead on nm_elig cells** (same budget-exhaustion as W1-append, 30a lesson).
→ r3: ticket moved to HEAD, gate narrowed to exactly {31} (overload≤0.72),
A/B {31}+protect{33} running.

### ★ PROBE CACHE-CONTAMINATION BUG (found 2026-07-18 02:30) ★

Night3 r3 A/B tied bit-identically on 31 → offline reproduction of the
"7,772,243" build in a clean process gave **11,380,559** → root cause: the
module caches `_BLK/_CC/_CE/_CX/_MREL` are keyed by `(block_id, oi, x, y)` —
**instance-agnostic**. Production resets them per instance (`:2853`); the
probe scripts did NOT, and ran multiple instances per process. **Every
cross-instance probe number from 07-17 is garbage** (placements chosen with
another instance's geometry, evaluated without a feasibility check):
- probe_steal: only 37 (first) clean → **−170,703 stands**; 27/38/39 garbage.
- probe_nmc: only 38 (first) clean → **nk3-cmp −2,674,658 stands**; the
  39 "8,067,980 below banked" and 31 "7,772,243 below banked" miracles = FAKE.
- probe_cap: only 38 clean (−1,459,277, but above family min → still drop).
- probe_tall: only 26 clean (+3.83M → still DEAD).
- **Retroactively explains jv4-era w3nm**: probe_w3nm ran 31 first (control,
  clean, reproduced jay) then {32,34,37,22,29} contaminated → the "−562k on
  32" that "polished away" in the real A/B was never real. The probe-vs-A/B
  discrepancy pattern of that whole campaign is now explained.
All four probe scripts patched (`_reset_caches()` + `_MREL.clear()` per
instance). jv6b r4: nk32j ticket and the W0 39-branch (garbage premises)
REMOVED; 38's nk3-cmp W0 build (clean premise, tied-harmless) kept.
Clean re-probe of {39,27,31} nmc + {27,38,39} steal running.

### Night3 r3 A/B {31,33} — both bit-identical ties (pre-bug-discovery)
31: 8,400,210 ×2, 33: 7,690,573 ×2 — consistent with the ticket premise
being fake; 33 protect re-confirms the corrected row value a third time.

### CLEAN re-probe (02:05–02:20, cache bug fixed) — final verdicts

nm_compete (relative to same-config control / absolute vs family best):
| prob | best rel Δ (nk3) | cmp best abs | family best abs | verdict |
|---|---|---|---|---|
| 38 | −2,674,658 | 41,700,612 | **41,063,457** (nk32-off) | family still wins |
| 39 | −1,247,139 | 10,481,935 | ~10,301,276 | family still wins |
| 31 | −1,650,781 | 9,575,466 | ~10,301,276* | close, but raw ≫ bank 8.40M |
| 27 | −99,009 | — | — | locked as always |

steal: 38 −912,757 rel (abs 45.7M vs family 41.1M), 39 −2,197,484 rel
(abs 12.5M vs family 10.3M), 27 flat — all abs-uncompetitive.

**FAMILY VERDICT — nm_compete and steal are CONFIG-RESCUE levers, not
frontier advances.** They lift weak configs by 1–2.7M raw but their best
absolute builds never beat the tuned deep-nestle family's best. That is
exactly why every full-pipeline A/B tied bit-identically: the winning
worker's stream was never improved. Both families are DEAD at portfolio
level (jv6b keeps the two harmless clean-premise deliveries as sandbox).
nk32+cmp grid explosion reproduces cleanly (borderline on 39: k1.0 ok,
k0.5 explodes) — the merged-grid cost is structural, do not revisit.

### ★ TEMPORAL ZONING — new family, breaks the absolute frontier (2026-07-18)

Mechanism (absent from both graveyards): re-rank the top-`zone` contact cells
to prefer cells whose resident spatial NEIGHBORS exit near the new block's
exit_t. Co-locating exit cohorts makes each exit wave free ONE LARGE contiguous
region instead of scattered nibbled holes (the measured fragmentation source;
100% of giant obj1 is entry-delay). Not a better-scoring greedy — a
structurally more *drainable* layout, the one axis the polish-away meta-law
may not cover.

**probe_zone (clean harness) — SIGNAL ×4**: 38 −2.97M, 27 −489k, 39 −1.40M,
31 −1.99M (best rel Δ). **probe_zonecombo abs-best per cell**:
| prob | winning config | raw | vs family best | vs 750s bank |
|---|---|---|---|---|
| **39** | nk32+z24 k0.5/a0.5 | **9,872,219** | **−429k** (10.30M) | +1.48M (8.39M) |
| **31** | cmp+z24 k0.5/a0.5 | **9,091,978** | **−1.21M** (10.30M) | +0.69M (8.40M) |
| 38 | cmp+z12 k1.0/a0.0 | 41,057,861 | −6k (tie) | +4.30M | frontier unbroken |

39 and 31 are the **first absolute-frontier breaks since v25's deep-nestle**.
Raw is still above the polished bank (expected — raw is the seed), so the
decisive question is whether the zoned seed SURVIVES polish. r5 wires it into
the real deep pipelines: 39 → W0-reclaim raw-min seed (feeds improve→whole_bay
→z3); 31 → restoration-lottery cand (feeds polish_v13's improve→cpsat→whole_bay
→z3). Both use drng=9099 (probe-matched). A/B @750s {39,31,38} running.
One degenerate: 38 k1.0/z12 timed out in probe (203M) — zone re-rank cost;
guarded by giving the build its own 0.46w slice, not the residual.

### Campaign state after night 1
jv6 = 124,478,185 @750s stands. Live yield sources measured this campaign:
Phase A bug-repair (−799,909), merge-tail × Phase D re-harvest (−383,875),
750s draw shifts (net ≈ +46k after corrections... 37 −107k bimodal vs 33/27
artifacts corrected). Everything else (steal, cmp, cap, tall, mid-tier
tickets, W2/W1 appends): dead or delivery-blocked. This mirrors jay's
v26–v34 closed-epoch conclusion on the forced mass.
