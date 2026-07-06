# Heuristic v18 — whole-bay exact packing on the global best (goal < 150M)

## Diagnosis from v17 (projected ~150.70M; need ~0.7M)
1. **The exact-pack mechanism is proven sound but starved of scope and
   placement.** v17 measured: officially-feasible −26.7k accepts (~1/8
   shots), zero soundness failures across every accept — but D=14/K=12
   windows on WORKER incumbents never beat the portfolio best, and windows
   on polished incumbents often prove optimal at that scale. Conclusion:
   the yield exists at LARGER scope, applied to the GLOBAL best.
2. Eight mechanism families dead on 38/27; 39 still 11M over fluid LB;
   the density set (39/26/33/23/21/30/32/37) collectively holds ~5-8M of
   over-LB mass where per-instance −50-150k from exact optimization is
   plausible and sufficient (need only ~0.7M across 8 instances).

## THREE improvements (v18)
1. **Whole-bay exact model.** Scale exact-pack from (window, D=14, K=12) to
   a full bay: every block of the bay gets a menu — the ~20 most valuable
   movers (tardy/central/off-pref) get K~8 raster-feasible alternatives,
   the rest keep their current placement as their only candidate (K=1, so
   pairwise blowup stays bounded: pairs with both-K=1 reuse the incumbent's
   known relations); full retime of all bay blocks (v13-audited encodings);
   objective w1*tardiness + w3 preference of movers. Solve budget 45-90s,
   1-2 bays per instance (most-tardy first). Two-tier relations and exact
   _can_place validation carry over from v17 verbatim.
2. **Aim at the global best, late.** Run the whole-bay model in a dedicated
   slot AFTER island adoption of the global best (last ~35% of window):
   worker adopts gbest, exact-packs its worst bay(s), pushes. Also a
   parent-side micro-pass if reserve allows (skip if tight). This fixes
   v17's placement error (exact-pack on weak incumbents).
3. **Coverage sweep + row hygiene.** (a) Run the mechanism on the wide
   density set {39,26,33,23,21,30,32,37,35}; keep per-instance only if the
   spot measures a win (obj-gated anyway — min-wins). (b) Whatever the v17
   full-40 row reveals as regressed vs best-known (e.g. 22/24/25 v14-era
   W3-beam paths if displaced by the v17 rotation surgery), restore via the
   attribution-probe playbook (measured, byte-exact, slot-cloned).

## Budget & mechanics
- baseline/myalgorithm_18.py from v17 (commit 1b26e75); same env rules; W0
  byte-exact outside reclaimed slots; PHASE A (no execution) while the v17
  full-40 bench runs (bench17_full.log lacks CSVROW).
- Ladder: (1) units: whole-bay model reproduces incumbent as feasible
  (relations sound at K=1 scale) + one measured improving accept on prob_39
  in isolation; (2) spot @300s {39,26,33,21,23}: GATE combined <= −350k vs
  v17 values (12,361,461 / 9,653,490 / 9,921,419 / 1,380,772 / 3,390,436);
  (3) protect {38,27,35,31,30,34,28} + prob_1 @60s byte; (4) row-hygiene
  restorations per the v17 full row; (5) full-40 bench_row @300s.

## Results (filled after testing)
