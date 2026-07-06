# Heuristic v14 — burst-window joint repack (goal < 150M)

## Diagnosis from v13 (focus-6 121.57M; full-40 row pending, projected ~157-160M)
Three admission-timing levers are now EXHAUSTED BY MEASUREMENT on the
overloaded pair (38/27, 75.0M combined):
1. alpha-ATC volume triage (v13 r1): moved the pair −6.3M, then saturated.
2. CP-SAT retime, full + windowed (v13 r2): ZERO improvement on giants —
   post-improver schedules are retime-tight with fixed geometry.
3. Fluid-target admission gating (v13 r3): every (C_eff, discipline) variant
   LOSES at construction. Measured cause: (a) the fluid-SPT "bounds" were
   preemptive-relaxation artifacts ~40% below any loadable non-preemptive
   schedule (a correct loader at C=1.0 reproduces ~30.0M/20.7M for 38/27);
   (b) a stable ~13-22M realization penalty sits on every target schedule —
   holding big blocks back does NOT let the masses run on time; they still
   queue on fragmentation and crane blocking. "Everyone slightly late"
   dominates every realizable "few very late" plan.

The realization penalty IS the residual lever: geometry, not order. The
dispatcher and repair both place ONE block at a time into whatever concave
scrap exists; a dense interlocked cluster is only reachable by placing its
members TOGETHER. Single-block moves cannot restructure a bay ("move a
chair" vs "repack the room"). Same story at admission events: first-fit
forecloses interlocks that a jointly-chosen fill would keep open.

## THREE improvements (v14)
1. **Joint window repack (LNS-XL) — the headline.** New improver move for
   tardy instances: pick the most congested (bay, time-window) — max
   area-time in queue-overlap — DESTROY every block whose [entry,exit)
   intersects it in that bay (typ. 10-30 blocks), then REBUILD the window
   from scratch with a restricted event-driven dispatch over the destroyed
   set (raster scans, scoped occupancy including un-destroyed neighbors as
   fixed): try k orders (area-desc / ATC / due / bottom-area-first), keep
   the best internal-objective rebuild, accept if it beats the incumbent
   window. Rotate over the top congested windows within a time budget.
   Blocks that no longer fit go back through normal repair (never lost —
   force-place guarantee stands). This is the only mechanism that can
   convert poly/bbox slack (shapes fill 57-72% of their bboxes) into
   density: coordinated interlock needs coordinated placement.
2. **Multi-order admission beam at events.** In the dispatcher, when an
   event has >= m queued candidates (m~4), evaluate k greedy fills (ATC
   order, area-desc, best-fit-decreasing by scan-feasible cell count) and
   commit the fill with the best (admitted area, internal score); scans are
   cached per occupancy version so extra orders are cheap. Kills the
   "first-fit forecloses the interlock" failure at its source.
3. **Worker rebalance toward repack.** Giants (nw=3): W2's polish becomes
   repack-heavy (joint-window rounds interleaved with classic destroy/
   repair); evaluate nw=4 with W3 = pure repack specialist on W2's
   construction (RSS was 2.83GB/3w — verify 4w fits). Non-giants: W3's
   post-lottery polish gains joint-repack rounds. W0 anchor untouched; all
   accepts internal-objective-gated; parent official verify unchanged.

## Expected attack
prob_38/27: the measured ~13-22M realization penalty is the addressable
pool; capturing 25-40% ⇒ −5 to −9M. prob_39/26/33/31 (density-pure): joint
repack directly targets their remaining ~25M-over-LB ⇒ −3 to −6M. Mid-tier
tardy set echoes. Needed vs projection: ~−8 to −10M ⇒ gates below.

## Budget & mechanics
- Opus implements per goal-session protocol; file baseline/myalgorithm_14.py
  from v13 (commit f0ae5ad); W0 byte-exact; numpy-only local, ortools
  guarded; Windows spawn-safe; serial testing, quiet machine.
- Test ladder: (1) unit: repack rebuild never returns worse-than-destroyed
  window (accept-gate) + official feasibility on smoke; (2) smoke @60s
  prob_39 + prob_27 vs v13; (3) focus-6 @300s, gate < 110M (v13: 121.57M);
  (4) mid-tier spot 23/35/30/37; (5) full-40 bench_row @300s.

## Results (filled after testing)
