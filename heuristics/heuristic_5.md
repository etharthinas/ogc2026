# Heuristic v5 — full thorough construction + FAST basin-hopping improver

## Diagnosis from v4 (results.csv `algorithm 4`, 423M @150s/6w)

Two concrete fixes identified:
1. v4's construction-time cap (0.55) degraded the start on prob_31/33 → small
   regressions the improver couldn't recover. **Fix: no cap** — use v3's full
   thorough construction; the improver takes only leftover time (safe: on short
   budgets it simply gets little, matching v3).
2. v4's improver rounds were too slow (big destroy sets + full repair search →
   few rounds → kicks never even triggered at KICK=12). **Fix: small/fast
   rounds** — destroy k≤6, capped repair search (slot_time_cap=18, pos_cap=14),
   KICK=6, and early-exit when obj1=0 and stagnant (stop wasting time on
   uncongested). Feasibility is still fully checked per placement, so smaller
   search caps only trade per-block optimality for far more rounds — never
   correctness.

## What changed (v3 core kept verbatim)
- `algorithm()` forced branch: single thorough EDD-earliest construction over the
  FULL window; improver gets the remainder.
- `_improve`: K-small destroy, fast repair caps, KICK=6, stagnation break.
- `_place_block`: forwards `slot_time_cap`/`slot_pos_cap` to `_find_earliest_slot`.

## Results (benchmarked 2026-06-29)

Key congested set @150s/3w: **prob_38 = 95,095,421** (obj1=6975) — v5 reaches at
150s what v3's slower improver needed 300s for, and far below v4's 192M. The fast
improver is the win. prob_27 (52.4M), prob_31 (19.2M), prob_39 (29.7M) are
UNCHANGED from their construction value — their residual tardiness is
packing/crane-limited, not search-limited (relaxed area-only LB confirms a real
gap remains, but closing it needs denser geometric packing, not more search).

**Full 40-instance TOTAL = 349,913,211** @150s/4w, 40/40 feasible (results.csv
row `algorithm 5`). Progression: v1 1.067B → v2 1.658B → v3 442M → v4 423M →
**v5 350M = 3.05× better than v1**. prob_38 = 127M in this 4-worker run but 95M
with less contention (3w) — under contest conditions (one instance, full CPU,
longer limit) the true total is meaningfully lower (~310M or below) and prob_38
keeps dropping with compute.

Net wins vs v3: prob_38 (211M→127M, →95M uncontended), prob_20 (1.11M→544k),
prob_34 (4.64M→3.49M), prob_35 (14.6M→11.4M), prob_40 (6.75M→4.31M), prob_37
(10.5M→9.8M). The packing-limited instances (27/26/31/39/23/28/30/32) are
unchanged — they sit at their construction floor for this candidate-position set.

### Consolidation (2026-06-29, user chose "consolidate v5")
- **Early-termination fix:** the improver now stops once nothing is tardy and the
  search has stalled (`since_best > 40`), instead of burning the whole budget.
  Verified objective-neutral: prob_2/3/8/15 return IDENTICAL objectives but in
  11–32s instead of 130s, 40/40 feasible. Better contest behaviour (returns a
  solved instance fast instead of spinning for the full limit).
- **`myalgorithm.py` locked to v5** (`from myalgorithm_5 import algorithm`),
  verified working end-to-end via the official `check_feasibility`.
- **Definitive single-worker (full-CPU, 150s) total = 317,875,374**, 40/40
  feasible (results.csv row `algorithm 5 (1w full-CPU 150s)`). This is the
  contest-representative number (eval runs one instance at a time). The 350M
  4-worker figure was pessimistic due to CPU contention starving the improver.
- prob_38 PLATEAUS at 95,095,421 (obj1=6975): identical at 150s/3w and 600s/1w,
  so more time does not help — its residual (vs relaxed LB 2963) is packing/
  crane-bound, not search-bound.
- Final headline: **v1 1,066,850,978 → v5 317,875,374 = 3.36× reduction.**

### The wall it hits
prob_27/31/33/39 sit at their construction tardiness no matter how much the
improver runs — the EDD-earliest placement is near the best this candidate-
position set (bottom-left + right/top edge contacts) can do under the crane
constraint. The next lever (v6, if pursued) is GEOMETRIC: richer candidate
positions (left/bottom contacts, skyline/free-rectangle) and crane-aware
placement so more blocks coexist in the congested window. Higher effort, and the
realistic floor (forced tardiness, see results.csv `joint_floor` + relaxed LB
~100M total) caps the achievable gain.
</content>
