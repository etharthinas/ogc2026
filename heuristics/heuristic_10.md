# Heuristic v10 — 4-core parallel portfolio (radical: use ALL allowed compute)

## Diagnosis from v9 (v9 = 297.83M @ 1w/300s, 40/40 feasible; goal < 250M)
Fresh per-instance fluid lower bound (bays merged, geometry/crane ignored —
optimistic) vs v9:

| inst | v9 | fluid LB | headroom | dem/cap | note |
|---|---:|---:|---:|---:|---|
| prob_38 | 94.29M | 24.2M | 70.0M | 1.14 | over-subscribed, round-starved |
| prob_27 | 48.92M | 17.1M | 31.8M | 1.19 | over-subscribed |
| prob_39 | 27.05M | 1.3M | 25.7M | 0.87 | NOT over-subscribed — packing/bay-split loss |
| prob_31 | 17.64M | ~0 | 17.6M | 0.68 | pure heuristic loss |
| prob_33 | 16.67M | 2.6M | 14.0M | 0.94 | |
| prob_26 | 18.74M | 5.1M | 13.7M | 0.87 | |
| prob_30/35 | 11.1/11.4M | ~0 | ~11M each | 0.77/0.62 | |
| prob_28/37/23/32/21 | 8.9/9.0/7.5/5.4/4.5M | ~0 | ~35M total | 0.57-0.80 | prob_21 frozen since v3 |

Two structural observations drive v10:
1. **The algorithm uses 1 of the 4 allowed CPU cores.** The eval server grants
   4 cores; v9 is pure single-threaded Python. Measured in v7: a mere 1.5×
   round-rate moved prob_38 by −8M. v9's worst compromises are *time-splitting*
   compromises: the 35/65 two-pass improver split, the CON_FRAC=0.55 cap, the
   construction-cheap gate — all exist because one thread must ration one
   budget across constructions and improvement. 4 workers dissolve the rationing.
2. **Bay-assignment myopia is a construction-time bug, not an improver gap.**
   In `_place_block` Pass A, when w1 dominates, the FIRST preferred bay with a
   zero-tardiness slot wins outright (`if bay_zero and w1_dominant: break`).
   The greedy fills the preferred bay while zero-slots remain, congests it, and
   later blocks spill into tardiness (prob_39: LB 1.3M vs 27M achieved!).
   v9's improver-level cross-bay rebalance failed (heuristic_9); the lever must
   be applied DURING construction, when spreading is still free.

## THREE improvements planned over v9
1. **Parallel portfolio (multiprocessing, min(4, cpu) workers).** Each worker
   runs an independent full-budget search strategy with its own RNG; workers
   stream their best-so-far assignments to the parent via a queue; the parent
   verifies best-first with the official checker at the deadline and returns
   the first feasible. Strategies (forced instances):
   - W0: plain EDD construction → full-budget improver (v8-like; safety anchor).
   - W1: AREA construction → full-budget improver (the v9 giants' winner, now
     with ~3x the improver time it got under the 65% split).
   - W2: congestion-aware construction (fix #2 below) + jitter multi-start →
     improver on best.
   - W3: jittered EDD/AREA multi-start until 0.55 window → improver with
     simulated-annealing acceptance (fix #3 below) — the explorer.
   Parent keeps v9's single-thread path as fallback if multiprocessing is
   unavailable. Never worse than v9's best member modulo seed noise; W0/W1
   are supersets of v9's two passes.
2. **Congestion-aware zero-slot scoring (kills the Pass-A break).** In W2's
   construction, Pass A evaluates ALL bays (no first-preferred-wins break) and
   adds a window-utilization penalty `gamma * w1 * util` where util = committed
   area-time overlapping the block's [entry, exit) window / (bay_area * proc).
   This makes the greedy pay a small anticipatory price for stuffing an
   already-crowded bay, spreading load while it is still free (target:
   prob_39/31/26/30/35 — all far above LB with dem/cap < 0.9).
3. **Simulated-annealing acceptance in W3's improver.** v9's improver is strict
   descent + deterministic kicks; the byte-identical-across-versions instances
   show it re-lands in the same basin. W3 accepts worse repairs with
   probability exp(-delta/T), T ~ a small fraction of current tardiness cost,
   geometric cooling, reheats on long stalls. Pure exploration upside since W0
   anchors the portfolio.

## Budget & mechanics
- Windows spawn-safe (worker fn at module level; grader imports module → child
  re-imports fine; Linux grader uses fork). Worker deadline = search_deadline −
  1s; parent drains queue, sorts by internal objective, official-verifies
  best-first within the reserve (12s @300s), falls back to empty-bay solution.
- Cache cap lowered per worker (4 processes share 16GB).
- Non-forced instances: same portfolio structure with the v3-style
  congestion+EDD+jitter strategies spread across workers.
- Bench: same-machine comparison vs results.csv v9 row @300s; iterate on the
  focus set {38,27,39,26,31,33,30,35,23,28,37,32} (≈277M of 297.8M), then
  full-40.

## Debugging journey (v10.0 -> v10.2) — what broke and why
**v10.0** (W0 EDD-improve / W1 AREA-improve / W2 gamma / W3 SA-jitter):
focus-set was net −3.3M (prob_26 −1.79M, prob_35 −1.10M, prob_28 −0.95M,
prob_23 −0.85M, prob_33 −0.69M) BUT three failures:
- prob_31 +1.45M / prob_30 +0.66M, byte-identical under serial re-run: v9's
  17.64M/11.14M came from improving a *jittered* construction from its exact
  rng stream (rng_c=2026). The improver is fiercely basin-sensitive — measured
  on prob_31: EDD+improve plateaus at 19.09M after ONE improvement in 175s,
  while v9's jittered basin reaches 17.64M. No v10.0 worker replayed v9's
  streams → the basin lottery was lost. FIX (v10.1): W0 = exact v9 replica
  (_v9_search shared by fallback and worker).
- prob_38 = 3.73B — the EMPTY-BAY FALLBACK. 4 workers x dense n=250 builds +
  Shapely Block caches thrashed the 16GB machine (worker RSS >1.2GB each,
  free RAM 2.6GB): zero constructions finished in 273s → empty queue.
  FIX (v10.1): bounded caches, parent-side cheap insurance construction,
  grace drain for final puts (an improver round takes seconds on n=250; the
  final forced push was landing after the parent stopped reading).
**v10.1**: prob_30 10.83M (−0.31M vs v9), prob_31 17.99M (recovered 1.09M,
still +0.36M), but prob_38 106.1M / prob_27 49.68M (= raw AREA construction —
the improver did NOTHING). Root cause measured: one dense prob_38 EDD build
needs 192k Block objects and >1M crane-entry pair-checks; my tight caps
(_BLK 100k / bools 1M) re-introduced the Shapely cost v7's caching removed →
builds ~180s+, improver round-starved, and 4 simultaneous builds contend.
FIX (v10.2): caps 250k/2.5M, and giants (n>=250 forced) run only nw=2
(W0 v9-replica on a clean core + W1 AREA-improve) — lottery workers can never
finish enough builds there to matter; they only steal cycles.
**Congestion-gamma diagnostic (prob_39)**: gamma=0.5 improves the EDD basin
(29.75M→28.97M) but HURTS the AREA basin (27.05→31.1M); nothing beats plain
AREA 27.05M, which the improver cannot move. The bay-myopia fix at
construction time is NOT the giants' lever; their floor is the construction
basin itself. Kept as W3's lottery on smaller forced instances only.
**SA acceptance**: inconclusive (confounded by the push race); parked.

## Results
v10.2 validation @300s, serial, vs v9 (results.csv `algorithm 9`):
| inst | v9 | v10.2 | delta | note |
|---|---:|---:|---:|---|
| prob_38 | 94,292,570 | **91,317,838** | **−2,974,732** | first move since v8! W1 = AREA basin + FULL-budget improver — v9 never even built AREA on prob_38 (its t_first gate skipped multi-start), so this basin was unexplored |
| prob_27 | 48,919,611 | 48,919,611 | 0 | replica anchor restored it |
| prob_39 | 27,053,638 | 27,053,638 | 0 | = raw AREA construction; no improver/gamma moves it |
| prob_31 | 17,638,531 | 17,770,214 | +131,683 | basin-lottery timing residue |
| prob_1 | 166,743 | 166,743 | 0 | non-forced path intact |
| prob_21 | 4,510,988 | 4,464,913 | −46,075 | frozen since v3, lottery paid |
| prob_25 | 820,769 | 739,136 | −81,633 | beats v8's best too |
| prob_40 | 3,788,423 | 3,647,003 | −141,420 | nw=2 giant gate works |
Plus v10.0/v10.1 measurements that carry over (same or weaker code than final):
prob_26 −1.79M, prob_35 −1.10M, prob_28 −0.95M, prob_23 −0.85M, prob_33
−0.69M, prob_30 −0.31M.

## FINAL RESULT (results.csv row `algorithm 10 (4w 300s)`)
**Full-40 @300s = 289,100,533, 40/40 feasible** — new SOTA, **−8,726,748
(−2.9%) vs v9's 297,827,281**. Biggest movers vs v9: prob_38 −2.97M (94.29→
91.32M, AREA basin + full improver budget), prob_35 −2.08M (11.39→9.31M),
prob_26 −1.92M, prob_23 −0.85M, prob_24 −0.29M, prob_30 −0.31M, prob_37
−0.17M, prob_40 −0.14M, prob_32 −0.09M, prob_25 −0.08M, plus broad small wins
on the easy instances (prob_11 137k→83k, prob_5/9/10/12/13/14/15/18/19).
Small residual regressions: prob_31 +0.13M, prob_33 +0.07M (basin-lottery
noise; v10.0's different seeds had found 15.97M on prob_33 and 7.92M on
prob_28 — worker-plan seeds matter, motivating v11's island model).
Progression: v1 1.067B -> v3 442M -> v5 318M -> v8 311M -> v9 297.8M ->
**v10 289.1M**.

## Lessons for v11
- The portfolio's biggest single win (prob_38 −2.97M) came from giving a KNOWN
  basin a FULL improver budget on its own core — not from new heuristics.
- Workers are isolated; nobody polishes another worker's winner. An island
  model (parent broadcasts global best back to workers) is the natural next
  step.
- prob_39/31/35/30 have fluid-LB ≈ 0 yet ~10-27M objectives: schedule-limited
  with fixed geometry. CP-SAT time-repair (fix bay/x/y/orient, re-optimize all
  entry times exactly) is the targeted lever; ortools is in the official env
  (NOT in local .venv_ogc — pip install needed locally).
