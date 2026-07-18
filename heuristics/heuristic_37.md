# Heuristic v37 — JOINT ORDER+GEOMETRY EPOCH (goal < 110,000,000)

User directive (2026-07-18): "loss < 110M... The current solution is a local
optimum; try radical, multi-axis changes in order to break out. (Don't be
greedy)."

Frontier: v36 = 124,141,498 (@900s row). Ask: −14.15M.

## Why this epoch exists

Every prior campaign closed with the same sentence: "joint order+geometry is
the only remaining escape class for 38/27 and no tractable mechanism is
known" (v29 ledger). This epoch BUILDS three such mechanisms. The measured
ground truth they stand on (ledger_27_diag + diag{26,31,33,37,39}.json):

- The 7 heavy instances {38,27,26,39,31,33,37} carry ~99.8M of the 124.1M;
  ~87.5M of that is pure obj1 = burst entry-queue delay (100% attribution,
  dwell 0, no by-construction tardiness).
- During the burst, feasible-placement fraction for queued blocks is
  0.0%–0.6% (admission search is essentially perfect); layer-0 density runs
  0.63–0.71 mean / ~0.80 peak; the residual ~30% floor is fragmented or
  crane-poisoned.
- Relaxation targets (relax@0.7): 38 obj1 1219 vs realized 2569; 27: 615 vs
  1726 → theory gap ~33M on the two giants alone. The gap is ORDERING +
  fragmentation, not missed anchors.
- The build dispatcher is TIME-MONOTONE: at each admission moment it picks
  the best block for the hole that exists NOW. It can never (a) slot a
  later-released block into an earlier gap it already passed, (b) push a
  slack-rich resident later to admit two tight blocks earlier, (c) shape
  today's packing so tomorrow's exits open contiguous holes. All prior
  order-forcing (29a/c/d) kept the greedy time-monotone decoder and only
  changed its input order — the certificates were geometry-blind mirages.

All three arms below are OFFLINE / STANDALONE-FIRST (zero displacement risk
to the frozen v36 race), champion-capture-seeded, official-checker-gated.
Winners integrate exactly like the proven tails (post-race, min-wins,
elapsed-guarded) — the v36 overflow-tail architecture was built for this.

## 37a — Space-time reservation LNS (nonmonotone joint repack) [FLAGSHIP]

Operate on the full (x,y,t) reservation volume of a COMPLETE solution
instead of simulating time forward. State: assignment {bi: (bay, oi, x, y,
entry)}; exit = entry + proc always (dwell 0 is measured-optimal).

- Insertion primitive `earliest_feasible(bi, resv)`: candidate entry times =
  release, then event times (exits) ascending; per candidate window
  [t, t+proc): union per-layer occupancy over the window's event slices →
  raster scan + near-miss anchors (near_k up to 16) → exact _can_place gate
  vs interval-overlapping residents → crane entry check at t and exit check
  at t+proc vs blocks present at those ticks. This is NONMONOTONE: any
  block can take any time slot, before or after its current one.
- Destroy operators (adaptive roulette, 8–30 blocks): D1 time-band × bay
  slab; D2 tardy-chain (a tardy block + residents overlapping its release
  window in its target bay region); D3 exit-cohort defrag (blocks whose
  exits scatter inside a band of one bay); D4 random.
- Repair: 2–3 insertion orders per destroy (ATC, min-slack, regret-random);
  anchor tie-break = contact/perimeter score + DEATH-TIME CLUSTERING bonus
  (prefer anchors adjacent to residents with similar exit times — vacate
  together ⇒ contiguous holes ⇒ effective density above the 0.7 ceiling).
- Accept: exact internal objective strictly improves; official
  check_feasibility before an incumbent is banked; keep best-verified.
- Multi-axis by construction: one move changes entry order, geometry, bay
  assignment and timing simultaneously.

Why prior deaths don't cover this: LAHC/SA ruin-recreate (v19) reinserted
through the time-monotone dispatcher at 0.3 iters/s pre-numba; 29a permuted
the realized order fed to the same decoder; window repack (_repack_window)
re-places at fixed/nearby times. None had a nonmonotone earliest-slot
insertion over a reservation table.

Kill: after one operator-mix sweep, best verified improvement < 30k
objective on BOTH {38, 27} @600s offline.

## 37b — Death-time-clustered defrag construction ("die together, pack
together")

Attack the 0.7 effective-density ceiling at BUILD time: current anchor
scoring optimizes the immediate fit, so space vacates in scattered
pinholes. New build scoring term: cluster blocks whose exits are close
(cohort = exit-time bucket) into the same spatial region; secondary term:
minimize free-space perimeter growth. Standalone probe = single-process
build+polish (v25 machinery) on {38, 27, 39}; compare RAW and POLISHED vs
banked. Integration only if it wins outright (26c law: appended W1 tickets
displace 38's coupling; a displacing ticket must beat the banked cell, not
the fallback).

Kill: raw builds never beat banked raw analogues on all of {38, 27, 39}.

## 37c — Replay-order-aware windowed CP-SAT (fix the measured
inexpressibility)

The merge model rejects the champion as its own hint on prob_26 because
pairwise space-time-crane compatibility cannot express dense REPLAY ORDER
(3-way: crane feasibility of A's entry at tick t depends on which same-tick
operations precede it). Fix: add intra-tick sequence literals — per tick,
exits before entries (official semantics), and order variables among
same-tick ops; crane constraints become conditional on sequence position.
Scope: time-band windows of 20–40 blocks over champion captures of
{26, 38, 27}, positions from candidate pools (champion + raster anchors),
warm-started from champion.

GATE 0 (cheap, decisive, run first): the champion window must be ACCEPTED
as a feasible hint by the new model. If still rejected → the abstraction is
still lossy → kill immediately without tuning.

Kill: Gate 0 fails after the ordering fix, or zero improvement on every
window tried on {26, 38}.

## Protocol

- Substrate: champion captures v25_{38,27,26,39,31,33,37}.json (obj1
  bit-identical to banked on 38/27/26/31/33; 39/37 marginally stale — all
  deltas measured vs the capture's own recomputed objective).
- Probes SERIAL on a quiet machine (16GB law; prob_38 is memory-heavy).
- Spot ladder: {38, 27} first (61.3M mass). Any arm ≥ −100k on a giant →
  extend to all 7 targets.
- Integration shape for winners: new post-race tail stage after
  _tail35_cpsat in the v36 overflow architecture (elapsed-guarded,
  official-check gated, forced-path token-identity preserved). Full-40 row
  @900s convention only after spot wins.
- Don't-be-greedy rule (user directive): arms are allowed to accept
  interim regressions inside their own search (LNS restarts from perturbed
  incumbents; 37b explores foreign basins); only INTEGRATION is min-wins.

## Results

### Calibration (2026-07-18, from captures — new numbers)

- Ordering-only obj1 floors (perfect redistribution of the realized total
  delay onto slack, throughput unchanged): prob_38 = 1939 (realized 2569),
  prob_27 = 1297 (realized 1726) → ordering-only ceiling ≈ −14.1M combined.
  The relax@0.7 targets (1219/615) are BELOW these floors → reaching them
  requires density/defrag gains on top of ordering.
- Slack-waster census (champion captures): prob_38 has 120 blocks holding
  527 units of unused slack (~7.0M transferable at w1), prob_27 has 72
  blocks / 348 units (~4.6M). The currency for slack-transfer trades exists.

### 37a stochastic LNS — KILLED at its criterion (2026-07-18)

st_lns.py sound (drift 0.0 vs official checker; nonmonotone insertion
validated — re-placed a tardy block 52 ticks earlier after clearing its
blockers). But @600s: prob_38 945 iters / prob_27 1823 iters, ZERO accepts
on both (also 0 on prob_26 smoke). LAW: at this saturation, stochastic
destroy + greedy sequential earliest-feasible repair cannot assemble the
coordinated multi-block trades — every single-chain move strands its
displaced set at a net loss. The joint lever needs EXACT repair.

### 37c order-aware windowed CP-SAT — ALIVE: first prob_38 improvement
since v25

- GATE 0 PASSES on prob_26 AND prob_38 (all 10 windows tried): the
  champion is representable once intra-tick order literals exist. The
  historical "pairwise model inexpressibility" (heuristic_32) is REFUTED —
  the missing piece was same-tick op ordering, not 3-way sweep geometry
  (utils.check_entry/check_exit are purely pairwise given the presence
  set).
- Burst sweep on prob_38 (9 windows @120s, narrow v1 pools): window
  [48,58] banked a VERIFIED −13,333 (obj1 −1; official 36,322,548) — the
  first accepted improvement on prob_38 by any mechanism since v25.
  8/9 windows champion-optimal-within-pool, all proved in 0.0s → POOLS,
  not solver capacity, are binding.
- prob_26 burst window: champion-optimal within pool (consistent with the
  locked-mass verdict).
- One lossiness found and fixed: frozen↔window same-tick order was baked
  at block_id order → one window's alternate rejected by official replay
  (gate caught it). v2 realizer topo-sorts same-tick ops crane-aware +
  lazy no-good-cut repair.
- v2 (sweep mode): overlapping bands, apply-and-continue passes,
  asymmetric slack-aware pools (tardy → earlier times down to release;
  slack-rich → free later times within slack; cross-bay menus; 39.5
  cand/block vs 18.5 in v1). MEASURED: prob_27 sweep → single −13,333 then
  converged; prob_38 W=30 sweep → the SAME single −13,333. Champion is
  window-optimal at every entry-band granularity.

### PRESENCE-WINDOW CERTIFICATES (2026-07-18) — champion-anchored repair
class CLOSED at −13,333/giant

Entry-band windows freeze the actual floor-holders (residents entering
before t1). v3 presence mode frees every block whose [entry,exit)
intersects the band, WITH slack-shifted time menus and cross-bay
candidates for residents too:
- prob_38 [38,48]: 110 blocks free, 3,248 candidates, 467k pair-combos,
  built 28s, GATE0 PASS, solved OPTIMAL → delta +0.
- prob_38 [48,58]: 105 blocks free → OPTIMAL, the same single −13,333
  (verified, saved cpsat_order_38.json → 36,322,548).
- prob_38 [0,135] (window cap 140 blocks): OPTIMAL, +0.
- prob_27 [42,52]: 65 blocks free → OPTIMAL, single −13,333 (verified,
  saved cpsat_order_27.json → 24,959,629); [20,32]: 75 blocks → +0.
VERDICT: at every scope 20→140 blocks, exact joint (order × geometry ×
bay × time) repack of the champion proves optimal-within-pool except for
exactly ONE tardiness unit per giant. The slack-transfer chains the
ordering bound permits (−630/−429 units) are NOT reachable from the
champion's packing at any tractable neighborhood scope — the remaining
headroom, if it exists, requires a globally different packing dialect
(pools are champion-shaped; 8 anchors/bay×orient around realized
geometry). Total harvest of the repair class: −26,666.

Consequences: (1) 37b (construction-time defrag basin change) is the only
live arm; (2) integration of the order-tail (−26,666 + generic in-tail
presence repack of whatever champion emerges) proceeds as v37 regardless;
(3) if 37b dies, the honest conclusion is that ~124.1M is the effective
optimum of this architecture, now backed by exact certificates rather
than exhausted-mechanism induction.

### v37 INTEGRATED AND VERIFIED IN-PIPELINE (2026-07-18)

myalgorithm_37.py = myalgorithm_36.py byte-copy + vendored `_tail37_order`
(self-contained presence-window order-CP-SAT tail; gate: forced/w1≥6000,
remaining ≥120s; top-2 queue-peak bands width 10, window cap 110; strict
official-check min-wins accept; hard deadline discipline). Verified @900s
serial, quiet machine:
- prob_38 = 36,322,548 (633.0s, feasible, obj1 2568) — v36 cell was
  36,351,493 → **−28,945** (race lands the 36,335,881 basin, tail −13,333).
- prob_27 = 24,959,629 (600.7s, feasible, obj1 1725) — v36 cell
  24,972,962 → **−13,333**.
Total verified so far: **−42,278**; projected v37 row ≈ 124,099,220
(< v36 124,141,498; other cells byte-identical by construction — tail is
post-race, forced-gated, additive-only). Remaining eligible cells
{23,26,30,31,33,39,37} to spot-measure for further tail wins before the
row is recorded. 37b DTC ladder (fixed harness: w=0 ≡ stock byte-identical,
Stage-5 reorder rescue, INFEASIBLE reporting with stage attribution) in
flight on prob_38.
