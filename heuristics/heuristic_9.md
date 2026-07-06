# Heuristic v9 — multi-start construction for forced instances

## Diagnosis from v8 (v8 = 311.16M @ 1w/100s, 40/40 feasible)
The residual loss is dominated by a handful of instances whose objective was
**byte-identical across v3, v5, v7, v8** — prob_27 (52.40M), prob_30 (14.39M),
prob_35 (11.39M), and prob_39 (29.75M). That exact-repeat is the tell: these are
not being improved by the destroy/repair improver at all. Direct measurement
confirmed it — on prob_30 the EDD construction *alone* produces 14,387,771 in
27s, and the remaining ~70s of improver finds **zero** improvement (only ~12
rounds run; the wide-cap repair is slow). So on these "forced" instances the
result IS the deterministic EDD construction; the improver is dead weight.

## THREE improvements planned over v8
1. **Cross-bay rebalancing destroy/repair.** *Tried extensively; abandoned.* A
   destroy operator that relocates blocks from the most-tardy bay to under-loaded
   bays. It could never crack the stuck optima (prob_27/30/35/39 stayed 0) and,
   fired during the descent, it *regressed* the round-starved giants prob_38/39
   by up to ~11M by stealing their improver rounds. Every gating scheme traded
   one failure for another (see "What didn't work"). Cross-bay is the wrong lever
   because the stuck instances are construction-determined, not improver-limited.
2. **Multi-start construction (v9, SHIPPED).** Since the stuck instances' value
   is their EDD construction and the improver can't beat it, spend the otherwise-
   wasted improver time on MORE constructions. A *jittered* EDD order (ties broken
   randomly, `_edd_order(jitter=rng)`) yields a strictly better construction on
   several of them:
   | instance | EDD construction | best jittered |
   |---|---|---|
   | prob_30 | 14,387,771 | 12,945,176 |
   | prob_27 | 52,400,285 | 51,474,131 |
   | prob_35 | 11,802,456 | 11,651,843 |
   So for forced instances v9 runs EDD **plus as many dense jittered-EDD
   constructions as fit**, keeps the best (best-of, so never worse than v8's
   construction), then lets the improver polish the winner with whatever time is
   left.
3. **Deep partial-restart of the improver.** *Implemented but dormant.* Perturb
   the champion by 45% after a long tardiness-stall and re-descend. It cannot fire
   in practice because the improver only manages ~12 rounds/100s on this hardware,
   far short of the stall threshold; left in the code (gated off) for larger time
   budgets. Also added `since_o1` (rounds since obj1/tardiness improved) as the
   real convergence signal — plain `since_best` never fires because tiny
   obj2/obj3 gains keep resetting it.

## The critical safety gate (why v9 doesn't hurt the giants)
Multi-start must NOT steal time from the genuinely round-starved instances
(prob_38 94M, prob_39 30M), where the improver's long tardiness descent is
essential and every stolen round costs. v9 therefore only multi-starts when the
**first construction was cheap** — `t_first < 0.55 * search_window`:
- Construction-cheap (prob_27/30/35, first build a small fraction of the window):
  the improver is useless, so pour the budget into jittered constructions.
- Construction-expensive (prob_38/39, one dense n=250 build already eats most of
  the window): skip multi-start entirely, keep the full improver → **byte-
  identical to v8**.
The gate is a *fraction* of the window, so it is budget-adaptive: at larger time
limits a giant's build becomes a smaller fraction and multi-start switches on
only once the improver has room to spare.

## What didn't work (recorded so the next version doesn't repeat it)
- Cross-bay rebalance, eager (every ~4th round): −11M on prob_38/39 (stole
  descent rounds).
- Cross-bay rebalance, gated at `since_best>=30/50`, tardy movers: still −2.8M on
  prob_38 (it never truly converges — kicks keep finding late gains).
- Cross-bay rebalance, gated, non-tardy movers: safe but ~0 on the stuck optima
  (their most-tardy bay is fully tardy → no movers).
- Partial-restart gated on `since_best`: never fires (obj2/obj3 micro-gains reset
  it); switched to `since_o1`, but the improver is too round-starved to reach the
  stall threshold at 100s anyway.

## The AREA-order breakthrough (what finally cracked the frozen giants)
EDD-jitter alone barely moved the biggest stuck instances. Testing alternative
*base* orders for the multi-start showed the **largest-footprint-first (AREA)**
order — place the hardest-to-fit blocks while the bays are still empty — reaches a
far better geometric basin on exactly the giants (dense construction obj):

| instance | EDD | AREA | vs v8 result |
|---|---|---|---|
| prob_39 | 29.80M | **27.05M** | 29.75M → **27.05M** (−2.69M; frozen across v3..v8!) |
| prob_27 | 52.40M | **49.68M** | 52.40M → ~49.7M (−2.7M) |
| prob_26 | 22.74M | **19.43M** | 20.60M → ~19.4M (−1.2M) |

(min-slack order was worse everywhere → dropped.) So v9's multi-start rotates
**EDD + AREA + jittered EDD/AREA**, keeps the best construction, then polishes it
with the improver.

## Budget & the improver reserve
Two coupling constraints set the run budget:
- The AREA construction on the n=250 giants (prob_38/39) costs ~70s; fitting
  EDD+AREA needs the construction phase to span ~140s, which only leaves room
  for the improver at a **per-instance limit around 300s**. At 100s the giants
  fit only one construction, so their AREA gain is unreachable — this is why v9
  is run at 300s (well within the contest's "a few minutes to half an hour").
- The construction phase is capped at `CON_FRAC=0.55` of the window so the
  improver keeps a guaranteed ~45% share; this removes the 100s regressions
  (prob_20/25/31) where constructions had starved improver-dependent instances.
Also added a keep-awake (`SetThreadExecutionState`) to the bench scripts after a
machine sleep mid-run corrupted a long benchmark.

## Results
Validated at 300s (keep-awake), v9 vs recorded v8@100s on the giants:
| instance | v8 | v9@300s | delta |
|---|---|---|---|
| prob_39 | 29,747,433 | **27,053,638** | −2,693,795 |
| prob_27 | 52,400,285 | **48,919,611** | −3,480,674 |
| prob_26 | 20,604,236 | **18,925,231** | −1,679,005 |
| prob_30 | 14,387,771 | **11,136,533** | −3,251,238 |

**−11.10M on these four alone**; prob_39 in particular moved for the first time
in the project's history (byte-identical across v3..v8).

Full-40 at 300s (keep-awake, 40/40 feasible): **TOTAL = 300,400,756**
(row `algorithm 9 (1w 300s)`) — **−10.76M vs v8's 311.16M**, but 0.40M over the
300M goal. Confirmed gains: prob_27 −3.48M, prob_39 −2.69M, prob_30 −2.63M,
prob_26 −1.87M, prob_34 −0.32M, prob_23 −0.42M. The overshoot is exactly the
avoidable regressions from the multi-start choosing a jittered construction that
the improver then descends to a slightly worse local optimum than plain EDD:
prob_33 +0.55M, prob_25 +0.08M, prob_37 +0.02M (= +0.65M).

## Regression-safe two-pass improver (final v9)
Fix: on forced instances run the improver on the PLAIN EDD construction first
(35% of the reserve — enough to reach v8's value, which v8 got with little
improver time), then on the best other construction ONLY IF its RAW objective
already beats the EDD-improved result (65% of the reserve). AREA wins outright on
the giants (they keep their polished gains); on improver-dependent instances the
AREA/jitter rarely beats EDD-improved, so the EDD result stands and there is no
regression.

Validated at 300s (v9-dual vs the earlier single-improver v9 / vs v8):
| instance | single-improver v9 | dual-improver v9 | note |
|---|---|---|---|
| prob_33 | 17,773,091 | **16,666,198** | −1.11M — improving BOTH basins beats v8's 17.22M too |
| prob_37 | 8,986,762 | 8,968,772 | recovered to v8 |
| prob_25 | 822,293 | 820,769 | ~same (uncongested) |
| prob_27 | 48,919,611 | 48,919,611 | gain kept |
| prob_26 | 18,735,273 | 18,735,273 | gain kept |
| prob_38 | 94,292,570 | 94,292,570 | round-starved giant: no regression (improver early-stops) |
| prob_39 | 27,053,638 | 27,053,638 | gain kept |

Net −1.13M vs the single-improver full-40 (300,400,756). The two-pass improver
also picked up extra gains beyond the validation set (notably prob_31
18.90M->17.64M, −1.26M, and a stronger prob_30 11.14M), so the final full-40 came
in even lower.

## FINAL RESULT (results.csv row `algorithm 9`)
**Full-40 @300s = 297,827,281, 40/40 feasible** — UNDER the 300M goal, −13.33M
(−4.3%) vs v8's 311,159,140. Biggest movers vs v8: prob_27 −3.48M, prob_30
−3.25M, prob_39 −2.69M (frozen across v3..v8 until AREA), prob_26 −1.87M,
prob_31 −1.26M, prob_33 −0.55M, prob_34 −0.32M, prob_23 −0.42M; small residual
regressions prob_32 +0.37M, prob_25 +0.08M (low-w1, obj2/obj3-dominated).
Progression: v1 1.067B -> v3 442M -> v5 318M -> v8 311M -> **v9 297.8M**.
</content>
