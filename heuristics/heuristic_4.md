# Heuristic v4 — Budget rebalance + basin-hopping improver

## Diagnosis from v3 (results.csv `algorithm 3`, 442M @90s)

- v3's monotone destroy/repair improver is EFFECTIVE and scales with time:
  prob_38 210M@90s → **95M@300s** (obj1 15630→6975). Unlike v2 it is monotone, so
  more time only helps. Contest allows minutes–30min, so this matters a lot.
- BUT at 90s the single 250-block construction eats ~78s → the improver barely
  runs on big instances. And the improver **plateaus** on some: prob_39 30M@90s →
  29.2M@300s (obj1 2143→2105, ~2%). Pure hill-climbing with EDD-only reinsertion
  gets stuck in a local structure (relaxed LB says obj1 could be ~414, not 2100).
- prob_1 still +58k vs v2 (residual obj1=2 the improver won't clear).

## Three improvements planned for v4

### 1. Budget rebalance — cap construction, feed the improver (PRIMARY)
Cap the primary construction to ~55% of the search window and DROP the secondary
full construction on forced instances (it rarely wins the best-of and wastes the
budget). Everything left goes to the improver, which is where the gains are. At
long limits construction is a small fraction anyway; at short limits this is what
lets the improver run at all on 250-block instances.

### 2. Basin-hopping improver (escape plateaus)
Replace strict hill-climbing with destroy→repair + occasional escape "kicks":
- Maintain `cur` (working) and `best` (returned). Always track best; return best
  ⇒ still monotone in the RESULT (never worse than the construction).
- Each round: destroy a set, repair, accept if better; if no improvement for K
  rounds, do a larger disruptive destroy and accept it (a kick) to jump basins,
  then resume hill-climbing. This is what prob_39 needs to break its plateau.
- Diversify REPAIR ordering per round (EDD, EDD+jitter, due-then-proc,
  release-then-due) instead of EDD-only — different orderings unlock different
  packings.

### 3. Window-destroy mode (structural rescheduling)
Add a destroy mode that removes ALL blocks active in a sampled peak-congestion
time window of one congested bay (not just the worst-tardy blocks), so the
bottleneck window is re-packed wholesale. Alternate this with the tardy-focused
destroy across rounds. Targets the root cause (a jammed congested window) rather
than nibbling individual late blocks.

## Reuses from v3 (correct, keep verbatim)
All placement/feasibility helpers, `_construct`, EDD/congestion orders,
`_objective`, `_build_operations`, empty-bay net, best-first final verification.

## Results (benchmarked 2026-06-29, 150s/instance, 6 workers, 40/40 feasible)

**TOTAL = 422,961,696** — only ~4% better than v3 (442M@90s) despite 1.67× time.
Mixed; two lessons:

1. **The construction cap (0.55) was a mistake.** It degraded the starting point
   on prob_31 (20.6M vs v3 19.5M) and prob_33 (18.7M vs 18.1M) and the improver
   couldn't recover within budget → small regressions. The thorough v3
   construction is worth its full time; the improver should take only LEFTOVER
   time. v5 removes the cap.
2. **The benchmark is CPU-contention-noisy.** prob_38 = 146M in a 4-instance/
   4-worker smoke test but 192M in the 40-instance/6-worker full run at the same
   150s — the wall-clock deadline fires after less actual compute when 6 heavy
   processes share the cores. The official eval runs ONE instance at a time with
   the full machine, so true single-instance numbers are materially better than
   this 6-worker benchmark. The improver scales with real compute (prob_38:
   210M→146M→95M as effective compute grows).

### Where v4 helped vs hurt
- Helped: prob_38 (211M→192M, more w/ CPU), prob_35 (14.6M→11.6M), prob_20
  (1.11M→0.77M), prob_36, several uncongested (improver mopped obj2/obj3).
- Hurt (cap): prob_31, prob_33. Neutral: prob_26/27/28/30/32 (improver found
  little in contended time).

### v5 plan
- Remove the construction cap (guarantee v5 construction == v3's strong start).
- Faster, smaller improver rounds (smaller destroy sets, capped repair search)
  + lower KICK threshold → many more rounds per second → actually bites on the
  congested instances where v4's slow rounds found nothing.
- Benchmark with fewer workers to reflect real single-instance CPU.
</content>
