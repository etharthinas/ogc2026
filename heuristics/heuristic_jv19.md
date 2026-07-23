# heuristic_jv19 — after the dilation fix: where the next 8.3M lives

**Goal UPDATED (user /goal 2026-07-24): total train loss < 105M @750s (was
<110M). SOTA jv17 = 118,297,918 full-40 single-shot. Deadline 07-28 14:00
KST. Standing 130th.**

## Where the money is (jv17 full-40 row)

| cell | loss | n | note |
|---|---|---|---|
| 38 | 36.79M | 250 | over-subscribed 1.14; old fluid LB ~24.2M → pool ≈ 12.6M |
| 27 | 23.62M | 150 | over-subscribed 1.19; old fluid LB ~17.1M → pool ≈ 6.5M |
| 39 | 8.01M | 250 | |
| 26 | 7.97M | 150 | area-LB Z1=0 (CP-SAT proven, jv15) |
| 33 | 7.71M | 200 | area-LB Z1=0 |
| 31 | 7.18M | 200 | area-LB Z1=0 |
| 37 | 5.29M | 250 | |
| 32 | 3.69M | 250 | |
| 30 | 3.21M | 150 | area-LB Z1=0 |
| 28/23/21/35/34 | ~10.4M | | mostly area-LB Z1=0 |

Mid-cells with proven area-LB 0 sum to ~34M — their z1 is 100%
geometry/sequencing. 38+27 = 60.4M with ~19M of relaxed-bound headroom.

## Diagnosis round (this session)

1. **jv18 wide-retry paired A/B @750s {38, 27, 31}** — the built-but-unmeasured
   arm from jv17b. RUNNING (ab_jv18_wide.log).
2. **Deferral audit** (`probe_deferral_audit.py`, NEW, official checker
   primitives, exhaustive integer anchors × orientations × bays): for the top
   tardy+deferred blocks in a jv17 dump, did an EXACT legal placement exist at
   release / at sampled times before actual entry?
   - First datapoints (prob_37 jv17 w0 dump): top-3 tardy blocks **FULL** at
     release; block 240 FULL at release, mid-times AND entry−1 — the engine
     admitted it at the first physically possible tick, at true polygon
     density only **0.61**. If this pattern holds on 38/27: the admission
     frontier is already near-exact; tardiness is caused by FRAGMENTATION
     (no contiguous hole at 60% density) and by WHAT is resident, not by
     phantom occupancy anymore.
   - jv17 dumps for 38/27 + audit: pending (after the A/B frees the machine).

## Stale verdicts that must be re-tested on the fixed engine

- "Drain lookahead absorbed by polish" (jv6b r6/r7) — measured on the DILATED
  engine; jv17's own frontier gain survived the polish, so absorption is not
  a law. drain=8 kwarg is built and default-off.
- "0% ejection-recoverable / only global constructor" (w1 probe, July 13).
- "SBEC closures yield 0 at full budget" (old engine incumbents).
- Exact-pack mid-cells 0-yield (re-confirmed 07-23 on jv15-era dumps — but
  those seeds predate jv17).

## Candidate routes (pick after diagnosis; three per evolve.md)

### Route A — queue-drain preservation, generalized (construction-side)
CODE AUDIT 07-23: drain=8 is ALREADY ACTIVE in the shipping W0 reclaim
stream on nm_elig {27,38,39} — the drain build's seed is FORCED into the
deep pipeline (myalgorithm_jv18.py:5416-5426, jv6b r7 kept). So "re-test
drain" is moot for giants. The genuinely untried extensions:
  A1. RELEASE LOOKAHEAD: extend the look-set beyond the current queue to
      imminent releases (release ∈ (t, t+Δ], high w1 urgency) so a placement
      at t cannot foreclose the burst arriving at t+1..t+Δ. ~10-line change
      to the look-list builder in the admission loop + beam path.
  A2. DRAIN ON MID-CELLS: the drain build never runs on 26/31/33/30/28
      (reclaim gate = giants/overload>1.05 only) — the ~34M area-LB=0 pool.
      Single-worker probe first (~120s per cell), then a jv19 worker-config
      arm if it moves raw z1.

### Route B — make-room at the deferral frontier (retroactive, bounded)
When a top-urgency block is deferred while true density is ~0.6, a resident
set blocks every anchor. Bounded retroactive repositioning: pick the cheapest
ejection set among residents whose OWN placement can be revised without
violating any placement committed in [their entry, now] (SBEC-style exact
pair closure, but ONLINE and tiny: ≤2 residents, same bay, position-only).
Expensive per fire; gate on the exact trigger (deferral of a block whose
w1·expected-wait exceeds a threshold). Build cost: high. Only if Route A
measures dead AND the audit shows long FULL stretches with density ≤0.65.

### Route C — admission triage on the over-subscribed pair (who eats the wait)
On 27/38 the queue exceeds capacity by construction; z1 is decided by WHO
waits. CAVEAT (code audit 07-23): the worker lotteries already sweep
kappa ∈ {0.5,1,2,4} × gamma ∈ {0,0.5,1,2} × alpha ∈ {0,0.5,1} per run and
take the min — plain ATC re-tuning is covered ground. A live Route C must
change the priority FAMILY: (a) explicit sacrifice — the round-3 fluid
`targets` machinery exists (gate a chosen loser set until their fluid
target), was built pre-jv17 and never re-tested on the fixed engine; or
(b) WSPT-rate ordering (w1-per-occupied-area·tick) at saturation moments
only. The 60.4M pool means even 3% pays 1.8M.

## Measurement discipline

Paired adjacent A/B only (compare.py); 750s; quiet machine; repeat
decision-sized deltas. Every new mechanism behind a default-off env switch.

## Results (running log)

- jv18 wide-retry A/B: RESTARTED 07-24 (first attempt 07-23 was killed with
  zero pairs banked; ab_jv18_wide.log confirmed 0 bytes before restart).
- deferral audit 38/27: PENDING (queued after the A/B frees the machine:
  bench_dump myalgorithm_jv17 750 38 27, then probe_deferral_audit
  --cap=20 --probe-entry on both dumps).
- **jv19 BUILT 07-24 (Route A1, release lookahead)**: `myalgorithm_jv19.py` =
  jv17 + imminent releases in the drain look-set. Blocks releasing in
  (t, t+OGC_RLOOK] (default 2 ticks) join `look` at both admission sites
  (plain loop + beam fill), most-urgent-first, capped at OGC_RLOOK_K=4 extra
  entries. OGC_RLOOK=0 restores byte-equal jv17 drain behavior. Rationale:
  median release gap on 38/27 is 1 tick, bursts of 5-11 blocks, residency
  ~21 ticks — the old look-set (queued-only) let a placement at t foreclose
  the burst at t+1. Compiles; functional smoke + paired A/B pending (machine
  busy with jv18 A/B). UNMEASURED — do not promote.
