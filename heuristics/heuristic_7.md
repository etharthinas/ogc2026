# Heuristic v7 — pairwise geometry caching (speed → more improver rounds)

## Diagnosis from v5/v6 (v5 = 317.9M @1w/150s; v6 enrichment FAILED)

v5 sits at a **structural ceiling**, not a time limit, on most instances:
- A relaxed lower bound (all bays merged into one cumulative resource, geometry
  and crane ignored — strictly optimistic) totals **~98.2M** across the 40
  instances. So the realistic floor is *above* 100M; the contest target of
  <100M is below it. prob_38 and prob_27 are **structurally over-subscribed**:
  total area-time DEMAND exceeds total capacity-time over the entire horizon
  (114% and 119%); their large tardiness is largely forced.
- The 318M→98M gap is concentrated in two regimes:
  (a) **round-starved** instances — large n, slow per-round (prob_38, n=250):
      v5 hasn't converged at the time limit.
  (b) **plateaued** instances — v5's improver reaches a local optimum it cannot
      escape regardless of round count (prob_27/39/26/31/30/23/33).

v6 (naive candidate-position enrichment) failed because more positions made each
placement slower → fewer rounds and the bottom-left cap cut off before the
positions v5 relied on.

## THREE planned improvements over v5

1. **Pairwise geometry caching (v7, this file).** v5 rebuilds Shapely
   intersections on every placement check. Memoize the three pairwise
   feasibility primitives — collision, crane-entry obstruction, crane-exit
   obstruction — keyed by the two placements `(block_id, orient, x, y)`. These
   are pure geometry (time-independent) and SEPARABLE per existing block (a
   crane path is blocked iff ANY single present block blocks it), so the cache
   is EXACT. Target: many more rounds/sec → directly attacks regime (a).
2. **Thorough repair enabled by caching (→ v8).** With placements cheap, widen
   the improver's per-block search caps (v5 kept them tiny only for speed) to
   try to escape regime (b) plateaus.
3. **Bay-assignment-aware destroy/repair (future).** Hypothesis for regime (b):
   the greedy takes local zero-tardiness placements in *preferred* bays,
   congesting them so *later* blocks become tardy. A destroy/repair that
   rebalances blocks across bays (accepting w3 preference penalty when w1≫w3,
   which holds on the congested instances) could escape these. Not yet built.

## What changed in v7 (vs v5)
- New module-level caches `_BLK/_CC/_CE/_CX`, cleared per instance in
  `algorithm()` (`_reset_caches()`).
- `_can_place` rewritten to route every Shapely call through the pair caches;
  Block construction routed through `_mkblock`. **Algorithm logic, RNG, control
  flow unchanged** — at infinite speed v7 ≡ v5; at finite time v7 does more
  rounds.

## Correctness
Direct equivalence test: 24,000 random `(sched, new_block, entry, exit)` cases
across prob_1/9/27/38/31/35 — v5 `_can_place` and v7 `_can_place` agree on
**every** case (0 mismatches). The decomposition is exact because
`check_entry/exit` loop over each existing block independently and
`check_collisions` is pairwise; all are bay-independent (bay only matters for the
boundary self-check, excluded via `bay.contains_block` first).

## Results (fair same-machine head-to-head v5 vs v7, 100s/instance)
| instance | v5 | v7 | delta |
|---|---|---|---|
| prob_38 (round-starved) | 103,013,583 | **95,095,421** | **+7,918,162 (7.7%)** |
| prob_35 | 11,385,884 | 11,385,884 | 0 |
| prob_28 | 9,145,575 | 9,145,575 | 0 |
| prob_27 | 52,400,285 | 52,400,285 | 0 |
| prob_39 | 29,747,433 | 29,747,433 | 0 |
| prob_26 | 22,736,778 | 22,736,778 | 0 |
| prob_33 | 18,009,467 | 18,009,467 | 0 |

v7 reaches prob_38's plateau (95.1M) at **100s** that v5 needs **150s** for
(~1.5× effective rounds). Everywhere else both reach the same plateau within
budget → identical. **v7 is strictly ≥ v5, never worse.** It is a safe speedup
(more robust under tight limits) but does NOT lower v5's converged total at
generous limits — the plateaus require a stronger SEARCH, which v8 attacks.
</content>
