# jv11 — W0-reclaim pipeline replica on giants (goal <120M)

Base: jv9 (SOTA-code; composed jv9-r2 = 121,468,412 after jv10-batch banking).
Gap −1.47M.

## The insight (from jv10's death)
jv10 proved capacity must **ADD** draws, never **DISPLACE** streams — the
racer/2nd-deaf each evicted a jv9 winner and regressed. But it also isolated
WHERE the giant wins come from: leader-**following** repack draws (deaf-wid5
silenced → 27 +425k regress). Every giant replica to date clones the LIGHT
W3-repack slot = a repack of the broadcast leader. The pipeline that actually
**produces** the leaders — W0-reclaim (nk-nestle build → deep improve →
whole_bay → z3) — has NEVER been replicated.

## Three plans

### A. W0-reclaim replica (the bet)
Add a 9th giant worker (wid 8), oversubscribed onto the idle parent core
(insurance build finishes early; jv8 tie-evidence: giant contention ≈0). It
reruns the full W0-reclaim pipeline with improve seeds 1616/1617 **+ soff** —
same deterministic builds, fresh polish trajectory → attacks the leader's OWN
basin instead of repacking it. ADDS a draw (no jv9 stream removed) → min-wins
floor-safe. `OGC_GIANT_NW` caps it for RSS re-bench.

### B. RSS safety (canary, not a lever)
prob_38 @9 workers is the budget risk (36.76M cell, 8w≈9GB + reclaim
replica ~1.5GB). Smoke-canaried before the A/B; blown times/MemoryError abort.

### C. (deferred) second W0-reclaim replica with independent (deaf) basin
Only if A wins and RSS has headroom.

## Test plan
`compare.py myalgorithm_jv9 myalgorithm_jv11 750 27 38 39`
Giants only (the sole cells jv11 code touches; non-giants byte-identical to
jv9). 27 = the responsive target, 38/39 = rigid + RSS canary. Isolated
re-bench any disputed giant (two jv10-batch cells hung under multi-hour load).


## RESULTS (2026-07-20, jv11_ab.log): NEUTRAL + HANG BUG -- NOT PROMOTED

| cell | jv9 arm | jv11 arm | verdict |
|---|---|---|---|
| 27 | 24,074,569 | 24,074,569 | bit-identical TIE -- both drew the jv8 basin (27's -425k is a stochastic wid5-follower draw, NOT reproduced here); reclaim-replica added no winning draw, losing wid6-deaf cost nothing |
| 38 | 37,556,441 | 37,556,441 | TIE, but BOTH +799,909 off the 36,756,532 basin = adjacent-run load artifact on the timing-sensitive giant; bank stands, jv11 neutral |
| 39 | 8,406,071 (708s) | 1,920,819,967 (4711s) | **HANG BUG** -- reclaim replica's `while True: inbox.get(timeout=8.0)` never exits when the giant broadcasts <8s apart -> infinite drain, worker never polishes, process blew deadline 6x |

**Verdict: jv11 DEAD. Neutral where it ran (27/38 ties = reclaim-light-polish
does NOT beat W3-repack) + a deadline-blowing inbox-drain bug on 39. NOT
promoted. myalgorithm.py stays jv9.**

### Conclusions (campaign-level)
1. **Giants are draw-lotteries**: 27's -425k is stochastic (wid5-follower);
   the composed row banks the best MEASURED draw, which is optimistic for a
   single submission. 38/39 basins are rigid.
2. **The giant portfolio is saturated at nw=8** -- oversubscription pages the
   36M cell (jv9 control confirmed the 3.7B @180s is a pure budget artifact,
   any version), and reclaim-light == repack (neutral). No giant headroom.
3. **The remaining real shot at <120M is the UNMEASURED TAIL**: the composed
   row still banks jv6-era values for cells 1-20 + several mid cells never
   A/B'd under capacity. jv9's 7-worker non-giant width improves those
   (proven: 28 -64k, 29 -9k). A full-40 @750s of jv9 measures ALL 40 under
   capacity -> banks the tail. THAT is the go-forward, not more giant levers.
