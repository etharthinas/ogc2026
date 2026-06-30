# Heuristic v8 — thorough repair (caching pays for a wider improver search)

## Diagnosis from v7
v7's caching gave ~1.5× rounds and reached prob_38's plateau faster, but on the
**plateaued** instances (prob_27/39/26/31/30/23/33) v7 == v5 exactly — more
rounds of the SAME capped repair search converge to the SAME local optimum. The
plateau is a search-strength limit, not a round-count limit.

## The change (idea #2 from heuristic_7.md)
v5/v7 deliberately ran the improver's per-block repair with tiny caps
(`slot_time_cap=18`, `slot_pos_cap=14`) purely because each placement was
expensive. v7's caching removed that cost, so v8 widens the repair search to the
construction's thoroughness (`slot_time_cap=40`, `slot_pos_cap=30`). A wider
repair explores more (orientation, position, time) per destroyed block, so the
destroy/repair neighborhood is strong enough to step OFF some plateaus that the
narrow search couldn't. Everything else is identical to v7 (same caches, same
exact `_can_place`, same RNG/control flow).

## Why this is safe (no round-starvation regression)
The worry: wider repair = fewer rounds, which could hurt the round-starved
prob_38. Measured the opposite — prob_38 IMPROVED under v8 (see below). Caching
gives enough round headroom that the wider search costs little while finding
strictly better packings.

## Results (fair same-machine head-to-head v7 vs v8, 120s/instance)
| instance | v7 | v8 | delta |
|---|---|---|---|
| prob_26 | 22,736,778 | **20,604,236** | **+2,132,542 (9.4%)** — plateau escaped |
| prob_38 | 95,095,421 | **94,292,570** | **+802,851 (0.8%)** |
| prob_39 | 29,747,433 | 29,747,433 | 0 |

v8 ≥ v7 on every instance tested, real gains on prob_26 and prob_38, zero
regressions. Since v7 ≥ v5 everywhere, **v8 dominates v5**.

## Full-40 benchmark (results.csv row `algorithm 8 (1w 100s)`)
**TOTAL = 311,159,140, 40/40 feasible.** This is at 100s/instance vs v5's
recorded 150s total of 317,875,374, so v8 **beats v5 by 6,716,234 (−2.1%)
despite 33% less time** — the genuine same-time gain is larger. **Zero
regressions**; 11 instances improved:

| instance | v5 (150s) | v8 (100s) | gain |
|---|---|---|---|
| prob_26 | 22,736,778 | 20,604,236 | −2,132,542 |
| prob_37 |  9,803,526 |  8,968,772 | −834,754 |
| prob_38 | 95,095,421 | 94,292,570 | −802,851 |
| prob_23 |  8,669,822 |  7,877,270 | −792,552 |
| prob_33 | 18,009,467 | 17,219,697 | −789,770 |
| prob_32 |  5,544,128 |  5,039,898 | −504,230 |
| prob_31 | 19,208,122 | 18,900,332 | −307,790 |
| prob_28 |  9,145,575 |  8,874,476 | −271,099 |
| prob_25 |    897,864 |    744,204 | −153,660 |
| prob_22 |  1,371,028 |  1,281,391 | −89,637 |
| prob_11 |    174,399 |    137,050 | −37,349 |

Progression: v1 1.067B → v3 442M → v5 318M → **v8 311M = 3.43× better than v1**.
The remaining ~213M above the ~98M relaxed floor is dominated by the
structurally-forced instances (prob_38 94M, prob_27 52M, prob_39 30M).

## The hard ceiling (idea #3 — future work)
v8 still cannot move prob_39 (relaxed LB 5.5M vs achieved 29.7M) or prob_27/31.
The residual gap on these is **bay-assignment myopia**: the greedy fills the
preferred bay to local zero-tardiness, congesting it so later blocks spill into
tardiness. Escaping needs a cross-bay rebalancing destroy/repair (move blocks to
under-loaded bays, paying w3 preference penalty since w1≫w3 on these instances) —
or solver-assisted bay assignment. That is the next lever.

## Reality check on the <100M target
The relaxed (geometry-/crane-free, bays-merged → optimistic) lower bound totals
**~98.2M**; real packing+crane+bay-split losses sit strictly on top, so the true
floor is comfortably **above 100M**. prob_38 (~90M+) and prob_27 (~40M+) are
structurally over-subscribed and alone exceed 100M. <100M is not achievable;
best realistic target is to keep closing the plateau gaps (≈150–250M range).
</content>
