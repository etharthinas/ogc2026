# Heuristic v12 — raster geometry engine + time-ordered dispatcher (break the density ceiling)

## Diagnosis from v10 (289.10M @4w/300s; goal now < 200M — need ~89M off)
Fresh instrumented runs of v10 on prob_38/27/39/31 (solutions replayed, per-block
tardiness + bay-utilization timelines measured):

1. **Objective is 96-98% Z1 (tardiness), and tardiness is 100% entry-queue delay.**
   No block has negative slack; every tardy block simply entered long after its
   release (waits of 66-116 on prob_38/27). Z2 is negligible everywhere; Z3 only
   matters on prob_31 (15%).
2. **Universal density ceiling: bays peak at 55-70% area utilization and average
   33-48% while 55-132 blocks queue.** All instances have a compressed release
   burst (every block released by t≈47, median slack 2-5); the bays never absorb
   it because the AABB-contact-point candidate generator cannot find the
   interlocking placements irregular polygons allow, and fragmentation leaves
   the median-97-area block unplaceable in 45% "free" space (prob_39).
3. **Per-instance mechanisms:**
   - prob_38 (91.3M): CAPACITY-limited (peak queued footprint 1.77x total bay
     area) + density headroom. Optimal *triage* matters: due-max 85 vs horizon
     182, tardiness diffuse over 198/250 blocks — blanket-delaying everyone is
     the worst possible triage under sum-tardiness.
   - prob_27 (48.9M): SEQUENCING/THROUGHPUT: 82 timesteps had a fitting queued
     block but zero entries; the big bay (72% of capacity) idles 24% of the
     horizon at 31% mean utilization because 100/150 blocks prefer the small
     bay and the greedy honors it. Preference costs 400/unit vs tardiness
     13,333/unit — the trade is free.
   - prob_39 (27.1M): pure PACKING density (burst is exactly at capacity 1.01x,
     slack median 2, crane nearly never idle — it just can't pack past 55%).
   - prob_31 (18.0M): SEQUENCING/PACKING (queued footprint only 0.56x bay area!)
     + real Z3 share.
4. **Code audit findings (myalgorithm_11):** `_cpsat_retime` double-overruns its
   window (no deadline check in the O(m^2) pair build loop; solver budget
   computed BEFORE the build with a >=1s floor) — this is what starved v11's
   post-CP improve and dropped final queue puts. Construction hook points for an
   external target schedule identified (order list + `lb`/candidate-time seeding
   in `_place_block`). Positions are integer and bays are ~1000-2000 cells, so
   an exact-or-conservative raster occupancy engine is cheap and sound as a
   pre-filter (numpy only — scipy absent from local venv).

## THREE improvements (v12)
1. **Raster geometry engine (numpy).** Precompute per (block, orient, layer) a
   conservative boolean footprint mask on the unit grid (Shapely rasterization,
   once; mask covers every cell the polygon touches; also an "exact-interior"
   variant marking cells fully inside). Maintain per-bay, per-layer occupancy
   grids for the currently-present set. Then:
   - **Full-position scan**: for a candidate (bay, orient) at time t, compute
     ALL feasible integer positions at once with a sliding-window AND
     (numpy sliding_window_view; no scipy). Conservative-mask disjoint =>
     provably feasible spatially AND for the crane rule (test against the union
     of layers >= k for entry clearance) — no Shapely needed. Cells where the
     conservative test fails but the exact-interior test passes go to Shapely
     verify (rare). This replaces "a handful of AABB contact points" with "every
     placeable cell in the bay", which is the direct fix for the fragmentation /
     55% ceiling, and it is FASTER than the current per-candidate Shapely path.
   - Final safety unchanged: parent still verifies with official
     check_feasibility best-first; raster bugs can only waste a candidate.
2. **Time-ordered dispatcher construction ("the pump").** Replace block-ordered
   construction with event-driven admission: walk event times (releases, exits);
   at each event, admit queued blocks greedily in priority order using the
   raster full-scan, as long as anything fits. Never leave a fitting block
   queued (kills prob_27's 82 idle steps; drains every burst as fast as geometry
   allows). Details:
   - **Priority = ATC-style triage** (Apparent Tardiness Cost: slack- and
     proc-aware exponential urgency), not plain EDD — under oversubscription
     (prob_38) sum-tardiness needs deliberate sacrifice of long/far-due blocks,
     and WSPT/ATC is the principled rule. Rotate kappa + tie jitter as lottery.
   - **Placement scoring within feasible cells**: prefer deep/perimeter cells
     (leave the entry corridor open), prefer positions minimizing exit-blocking
     of earlier-due present blocks (raster prism overlap vs their exit order),
     small bonus for touching occupied cells (compactness).
   - **Bay choice**: score = w1*expected tardiness + w3*pref penalty (+ tiny
     w2 term); with w1 dominant this auto-front-loads prob_27's starved big bay.
   - **Prompt exits**: schedule EXIT at entry+proc unless crane-blocked; retry
     blocked exits at each event.
3. **Portfolio rewire + CP-SAT retime fix.** Keep the 4-worker portfolio and
   island broadcasts; keep W0 = v9 replica anchor and W1 = v10's AREA+full-
   improver (giants' proven basin). Re-point W2 = dispatcher construction →
   improver; W3 = dispatcher lottery (rotate ATC kappa, scoring weights, jitter;
   multi-start) → improver → CP-SAT retime with the audit fixes (pair-count cap
   ~4000/bay; deadline flag inside the pair loop, abort => skip solve; recompute
   solver budget after build, drop the 1s floor; gate CP-SAT on improver stall
   instead of the fixed 62% mark). Giants keep nw gating only if tests show the
   raster path is still memory-heavy; the raster engine should make dispatcher
   builds far cheaper than Shapely builds, so try nw=4 first on n>=250.

## Expected attack per instance
prob_39/31/30/35/23/21 (density/sequencing, under-capacity): dispatcher + full
scan should recover most of the queue delay. prob_27: bay-choice economics +
never-idle admission. prob_38: density first, ATC triage second; fluid LB is
24.2M so a 91->~50M move is the swing target. Mid-tier (26/33/28/37/32) should
inherit wins from the same levers.

## Budget & mechanics
- Implementation delegated to Opus agent; Fable plans/reviews only (goal-session
  directive). Single self-contained file baseline/myalgorithm_12.py, signature
  algorithm(prob_info, timelimit=60), numpy+shapely only (ortools try/except).
- Windows spawn-safe as before; caches per worker; 16GB budget.
- Test ladder: (1) smoke prob_39+prob_27 @60s vs v10 same-budget; (2) focus
  {38,27,39,31} @300s serial; (3) extended focus {21,23,26,28,30,32,33,35,37}
  @300s; (4) full-40 bench_row @300s on a QUIET machine.
- Success gate to proceed to full-40: focus-4 total < 160M (v10: 185.0M).

## Results (results.csv row `algorithm 12 (4w 300s)`)
**Full-40 @300s serial, quiet machine = 174,587,763, 40/40 feasible — new SOTA,
−114,512,770 (−39.6%) vs v10's 289,100,533. GOAL (<200M) MET.**

| inst | v10 | v12 | delta |
|---|---:|---:|---:|
| prob_38 | 91,317,838 | **49,420,035** | **−41.90M** |
| prob_27 | 48,919,611 | **31,929,802** | **−16.99M** |
| prob_39 | 27,053,638 | **15,300,889** | **−11.75M** |
| prob_35 | 9,308,547 | **2,347,358** | **−6.96M** |
| prob_33 | 16,731,780 | 11,055,920 | −5.68M |
| prob_30 | 10,830,851 | 5,927,780 | −4.90M |
| prob_31 | 17,770,214 | 12,880,039 | −4.89M |
| prob_28 | 8,834,745 | 4,445,588 | −4.39M |
| prob_26 | 16,816,061 | 12,689,104 | −4.13M |
| prob_21 | 4,464,913 | 2,227,144 | −2.24M |
| prob_23 | 6,613,919 | 4,584,164 | −2.03M |
| prob_29 | 1,869,891 | 631,617 | −1.24M |
| prob_37 | 8,863,080 | 6,748,895 | −2.11M |
| prob_34 | 3,488,961 | 2,527,479 | −0.96M |
| prob_40 | 3,647,003 | 2,454,184 | −1.19M |
| prob_24 | 2,034,701 | 1,235,206 | −0.80M |
| prob_32 | 5,321,212 | 4,578,158 | −0.74M |
| prob_25 | 739,136 | 353,558 | −0.39M |
| prob_20 | 544,247 | 209,325 | −0.33M |
| prob_22 | 1,281,391 | 1,053,879 | −0.23M |
| prob_36 | 490,447 | 259,010 | −0.23M |
| prob_1..19 | 2,145,753 | 1,728,629 | −0.42M (all obj1=0; only prob_5 +5.8k / prob_10 +2.8k lottery noise) |

## Analysis
- Every forced/giant instance moved massively; the dispatcher construction
  (event-driven ATC admission over the raster full-position scan) is the
  winning basin nearly everywhere the improver then polishes.
- The raster engine's empirical soundness held: 0 violations over ~5,200
  checked cells; official checker passed 40/40 first-verify.
- prob_38 (49.4M vs fluid LB 24.2M) and prob_27 (31.9M vs LB 17.1M) still
  carry ~2x LB — remaining headroom is triage quality + burst density.
- Only regressions: prob_5 +5,829, prob_10 +2,842 (basin-lottery noise).
- Runtime healthy: many instances converge and stop early (47-115s on small
  ones); giants use the full window at ~1.15GB/worker RSS (nw=3).
