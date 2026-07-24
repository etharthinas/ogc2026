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

- **jv18 wide-retry A/B: REJECTED 07-24** (restarted after the 07-23 kill;
  paired @750s, quiet machine, ab_jv18_wide.log): 38 EXACT TIE
  (34,180,997 both), 27 weighted +15k but lex-WORSE (z1 1620 vs 1618),
  31 **-343,025**. Total jv17 65,024,818 vs jv18 65,352,863 (-328k), lex
  2-0-1 for jv17. Wide-retry opens the rescue when admission fails, and it
  either changes nothing (38) or trades z1 up for z2 down at a loss (31).
  Consistent with the audit's "frontier near-exact" verdict: failures are
  real fullness, not phantom. jv18 is DEAD; jv17 stays SOTA base.
- **deferral audit 38/27: DONE 07-24 — VERDICT: FULL** (jv17 750s dumps,
  --cap=20 --probe-entry; audit_jv17_38.log / audit_jv17_27.log):
  - prob_38: FULL 19/20 audited tardy blocks = **99.9%** of audited
    weighted tardiness; the single OPEN was 1 tick late (13k). True max-bay
    density at FULL moments: min 0.59 / med 0.65 / max 0.69.
  - prob_27: FULL 17/20 = **97.9%**; OPENs = 2×1-tick + blk 113 (20 ticks
    late, 293k — the one real frontier miss, unexplained).
  - Tardy blocks wait 55-85 ticks release→entry with the bay genuinely FULL
    the whole stretch at true density only ~0.6 — **a third of the bay area
    is trapped in unusable fragments for 3-4 residency generations.**
  - CONCLUSION: finer/exact frontier machinery is DEAD (jv16 already died on
    throughput; jv18 wide-retry died -328k; audit now shows there is ~nothing
    to see). The giant pool is 100% FRAGMENTATION + WHO-IS-RESIDENT →
    Route A (drain shaping, measured next), Route B (make-room; its audit
    precondition "long FULL stretches at density <=0.65" is MET), Route C
    (triage).
- Reasoned-dead (no build): within-event "failed-block look-set" (add the
  just-deferred block to later placements' look) — zero score
  differentiation: space only shrinks within an event, so a block FULL
  everywhere at t stays FULL for every candidate, cnt contribution is 0
  either way. The temporal version of this idea is the already-shipped
  exit-cohort zone sort. Preserving holes for a FAILED block needs future
  exits modeled → that is exactly Route B's make-room, not a look-set tweak.
- **Tardy-block anatomy (07-24, jv17 dumps)**: top-20 tardy blocks are
  1.96x/1.82x mean bbox area (38/27); on-time blocks are 0.74x/0.75x. Tardy
  larges enter at t=70-108 while the release stream ends at t=47 — they are
  fully starved until drain-down. The engine's triage already sacrifices
  them; the loss is that NOTHING reserves the freed fragments for them.
- **probe_dm_giants 07-24 (single-worker raw, drain=8 base, 120s/arm)**:
  - prob_27: rlook additive **-1,765,971 SIGNAL** (d8 27,351,666 ->
    d8r2 25,585,695); drain itself +47k flat vs d0 at this config.
  - prob_38: drain **-1,024,379 SIGNAL** vs d0; rlook +446M is a BUDGET
    ARTIFACT (d8 needs 107s of the 120s budget; +50% look cost overran ->
    force-placed tail, o1 36,346). NOT a quality verdict -> re-probe with
    headroom + cost-neutral BLEND mode (probe_rlook.py, _RLOOK_MODE=1:
    imminent replaces the look tail, cost == plain d8).
- **probe_dm_mid 07-24 (partial)**: prob_26 drain **-1,155,571 SIGNAL**
  (Route A2 alive on mid-cells); rlook additive +526k flat there.
- **STARVATION GUARD built (OGC_HOLD, default OFF)** in myalgorithm_jv19.py:
  when a late large (anorm >= 1.4) block fails admission, slack-rich blocks
  (slack >= 1.0*pbar) are skipped for the rest of the event, banking freed
  space across exit waves until the claimant fits. Self-limiting (skipped
  blocks re-enter as their slack burns). Untested: probe_hold.py ready
  (arms h0/h1 conservative/h1a aggressive, cells 38 27).
### *** THE BUG (07-24): the drain build NEVER RAN, in any shipped version ***

`_run_strategy`'s local `dispatch()` wrapper has NEVER had a `drain`
parameter — not in jv6b, jv9, jv17, jv18, nor in the promoted submission
entry point `myalgorithm.py`. The jv6b-r7 "FORCE drain seed" call
(`dispatch(1.0, 0.5, alpha=0.0, beam=True, nearmiss=8, nk=32, drain=8, ...)`)
sits inside `try: ... except Exception: pass`, so every invocation since
2026-07-18 raised `TypeError: dispatch() got an unexpected keyword argument
'drain'` and was silently swallowed. Verified by signature inspection across
all four modules plus a direct call reproduction.

This is the SAME defect class the v25 mpc bug had (and whose fix the jv5
header brags about) — a dead kwarg behind a bare except. Consequences:
- Every "drain" verdict in the campaign record is VOID. jv6b r6/r7's
  "absorbed by polish", and this session's own memory note "drain=8 is
  ALREADY SHIPPED in W0 reclaim on {27,38,39}", measured a no-op.
- Route A2 ("drain never runs on mid-cells") was accidentally right for the
  wrong reason: drain never ran ANYWHERE.
- LESSON (evolve.md "compare what the code BELIEVES against ground truth"):
  a mechanism gated behind `except Exception: pass` must assert it ran.

### jv19 bundle (all three legs measured as raw signals, A/B pending)

1. **drain forwarding FIX** — `dispatch()` takes and forwards `drain`; the
   r7 giant seed-force now actually fires, bounded by `_o3 <= 1.3 * _o0`
   (r7's intent was "structure over ~10% worse raw", not "any complete
   assignment": an over-budget build force-places its tail and would feed
   the deep pipeline garbage). Fires on reclaim cells {27,38,39,37,40}.
2. **rlook additive** (`_RLOOK=2, _RLOOK_K=4, _RLOOK_MODE=0`) — probe_rlook
   07-24 with budget headroom, vs plain drain=8: **38 -1,696,368**,
   **27 -1,765,971** (both SIGNAL). The cost-neutral BLEND mode is WORSE
   (38 +212k, 27 -1.29M) → additive adopted, blend kept behind MODE=1.
   Combined with the drain fix, raw giants: 38 40.12M→37.40M (-2.72M),
   27 27.30M→25.59M (-1.72M).
3. **mid-cell drain tickets** (`_MIDDRAIN=1`) — one drain=8 ticket heading
   the W2 forced lottery (fires {26,31,33,30,23,32,25}), plus one on the
   contended non-forced branch (overload>0.55 → {28,35,34,36,21}).
   probe_drain_mid raw: 26 -1,155,571, 28 -1,394,238, 30 -477,712,
   31 -115,993, 33 -17,715.

REJECTED into default-off: **starvation guard** (`OGC_HOLD`, built + probed).
h1 (K=1.0,AMIN=1.4) never fires (bit-identical on both giants); h1a
(K=0.5,AMIN=1.2) is 38 -377,482 / 27 +0. One-cell weak signal, no bundle.

Smoke: jv19 runs end-to-end feasible; A/B on 28 @120s is a bit-identical TIE
(the polish there reaches 2,551,624, BELOW every raw construction 2.64M+, so
W2's construction change is invisible — the jv6b "absorbed by polish" law is
real on cells where W2 is not the winning worker).

- **jv19 BUILT 07-24 (Route A1, release lookahead)**: `myalgorithm_jv19.py` =
  jv17 + imminent releases in the drain look-set. Blocks releasing in
  (t, t+OGC_RLOOK] (default 2 ticks) join `look` at both admission sites
  (plain loop + beam fill), most-urgent-first, capped at OGC_RLOOK_K=4 extra
  entries. OGC_RLOOK=0 restores byte-equal jv17 drain behavior. Rationale:
  median release gap on 38/27 is 1 tick, bursts of 5-11 blocks, residency
  ~21 ticks — the old look-set (queued-only) let a placement at t foreclose
  the burst at t+1. Compiles; functional smoke + paired A/B pending (machine
  busy with jv18 A/B). UNMEASURED — do not promote.
