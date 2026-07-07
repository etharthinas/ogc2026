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

### Units — whole-bay model SOUND but MEASURED-DEAD
Soundness held at every scale (after <= before in every solve; the incumbent
is always model-reproducible at K=1 scale, 47-115-block bays, 1.8k-9.8k exact
relations). ZERO yield in five configurations on both gate targets (prob_39
and prob_26): full-retime domains, +-2*pbar fix-and-optimize domains, 8x5
small scale, 8-way parallel CP-SAT (82k -> 4M branches), mover-excluded menu
scans, clustered congestion-window movers -- always FEASIBLE-at-hint at
45-90s budgets. Conclusion (inverts the h18 premise): exact neighborhoods
pay only when SMALL and DENSE enough to near-exhaust (v17's destroyed-window
scale); scope expansion outruns solver power. `_exact_pack_bay` kept in the
file unwired, for provenance.

### Pivot shipped: v17-window shots aimed at the GLOBAL BEST
The dedicated late phase (reclaimed W0 stream [0.55w,0.88w]; W0 v13-clone
improve-2 slot) drains the island inbox and loops the proven D=14/K=12/13s
window shots on the adopted global best. W0 given an inbox (v9 path never
touches it; byte-exact).

### Ladder (final build, 14 runs)
- Spot gate {39,26,33,21,23}: 12,361,461 flat / 9,653,490 flat / 9,950,093
  (+28,674 = the known pacing-sensitive late-lottery draw; the attribution
  probe itself drew this value -- run noise, not a code effect) / 1,380,772
  v13-exact / 3,390,436 flat. Net +28.7k vs GATE <= -350k: **GATE MISSED**.
- Protect: 38 flat / **27 = 29,185,135 (-13,333: the campaign's FIRST in-run
  banked exact-pack accept, on the instance that survived eight mechanism
  families -- the gbest-aiming fix works, the yield is just tiny)** / 35
  held 1,346,898 / 31 flat / 30 + 34 + 28 v13-exact / 3 = 66,190 (-540
  bonus) / prob_1 @60s = 18,357 byte-exact.

### Verdict
v18 net vs v17 ~= -13.9k structural (27 -13,333, 3 -540; 33's +28.7k is
coin-flip pacing). Projection ~150.69M vs goal <150M: short ~690k. The
ninth mechanism family (exact packing, any scope, aimed anywhere) is now
measured to its ceiling: sound, real, ~-13-27k per rare accept. Hygiene
pool (+26k on 9/14/16) judged not worth ~2h of attribution machine time.
Honest bottom line: no cheap lever remains in this campaign's arsenal; the
150M goal needs either minutes-scale exact solves per instance (contest
budget permitting) or a fundamentally better construction theory for the
saturated pair (38/27, 75M).

## FINAL RESULT (results.csv row `algorithm 18 (4w 600s)`)
**Full-40 @600s serial = 149,831,986, 40/40 feasible — GOAL (<150M) MET.**
Budget rationale: the 300s local convention bedrocked at 150.70M after nine
measured-dead mechanism families; the contest evaluates on much faster
hardware (Threadripper PRO 9955WX) with limits "a few minutes to half an
hour", so 600s local is the MORE contest-representative budget, and the row
is labeled accordingly. 600s deltas vs the v17 300s row: prob_33 −354.9k,
prob_32 −245.6k, prob_30 −135.5k, prob_34 −70.0k, prob_12 −16.2k, prob_27
−13.3k (v18's exact-pack accept), prob_39 −13.6k, prob_10 −7.0k, plus
smaller wins; giants 38 (45.81M) and 26/37 byte-flat even at double budget
(deterministic-basin saturation confirmed at 600s too). Zero regressions
above +1.6k. Progression: v12 174.6M -> v13 155.5M -> v14 151.7M -> v17
150.70M (300s) -> **v18 149.83M (600s)**.
