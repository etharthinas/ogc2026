# jv8 — capacity scaling on the GIANTS (goal: total < 120M @750s)

Base: jv7 (SOTA 124,004,438). jv7 proved the capacity law on non-giants
(−473,747, 0 regressions); the giants {27,37,38,39} = 76.0M (61% of total)
still run nw=4. jv8 extends the law to them.

## Three plans (evolve.md step 1)

### A. Giant light-replica workers (the iteration's bet)
Giants capped at nw=4 for RAM (dense builds thrashed 16GB in v1x era; current
4w ≈ 4GB measured on 38). The W3-giant REPACK SPECIALIST path is light
(~sparse seed, seconds + inbox-seeded improve ≈ ~1GB): spawn W4–W6 on giants
too (nw min(7, cpu−1)), all mapped to the W3-giant slot with soff ≠ 0:
- soff>0 replicas SKIP the nm_elig heavy seed builds (nk24/nk32/ovh, would
  duplicate W3's deterministic builds) → v14 sparse seed + improve(4444+soff,
  repack_every=2, xbay=True) = an independent repack-polish draw of the inbox
  global leader.
- Attacks: 37's measured bimodality {5,699,640 / 5,807,047} (−107k in
  expectation), plus fresh polish draws on 27/38/39 where every historical
  win was admission-frontier/polish-draw shaped.
- RSS projection: 4w ≈ 4GB + 3 × ~1.2GB ≈ 8GB < 16GB.

### B. Bank jv7's uncovered non-giant cells (measurement, no code)
jv7's row banks jv6 values on ~10 unmeasured non-giant cells. A/B the biggest
{23, 32, 34, 35, 21, 29} — replicas already race there in jv7/jv8.

### C. Parent-as-searcher (still deferred)
Held for jv9: giant A/B must stay unconfounded, and the parent's rebroadcast
latency is load-bearing on giants (inbox-seeded repack replicas).

## Risks
- Giant timing shifts from added contention (full-40-tail corruption
  precedent): the A/B measures exactly this; disputed cells → isolated
  re-bench (jay's algorithm-23 law).
- 38 RSS: monitored via A/B runtime sanity (a thrash shows as blown times).

## Test plan
One batch (adjacent-in-time, no concurrent CPU work):
`compare.py myalgorithm_jv6 myalgorithm_jv8 750 37 39 27 38 23 32 34 35 21 29`
Giants first (highest information), then plan-B cells. vs jv6 = the banked-row
basis, so deltas add directly onto the composed row.

## RESULTS (2026-07-20, jv8_ab.log): −1,300,805, 5 wins / 5 ties / 0 regress

| cell | jv6 arm | jv8 | delta | note |
|---|---|---|---|---|
| 37 | 5,807,047 | 5,807,047 | 0 | tie — both arms drew the bad bimodal mode |
| 39 | 8,389,519 | 8,389,519 | 0 | bit-identical tie |
| **27** | 24,932,963 | **24,074,569** | **−858,394** | ★ the giant NO lever ever moved; replicas found a new basin (obj1 1723→1669, z2 502→96). vs banked 24,972,962 = −898,393 |
| 38 | 36,756,532 | 36,756,532 | 0 | the 6×-reproduced basin holds |
| 23 | 2,494,797 | 2,494,797 | 0 | tie |
| 32 | 3,881,748 | 3,881,748 | 0 | tie (lottery-sensitive cell unharmed) |
| 34 | 1,978,590 | 1,898,254 | −80,336 | jv7-axis banking win |
| 35 | 1,688,817 | **1,345,948** | **−342,869** | 20% cell cut, obj1 99→76 |
| 21 | 1,380,772 | 1,371,049 | −9,723 | |
| 29 | 557,994 | 548,511 | −9,483 | obj1=0 cell, z2/z3 polish win |

**Composed row (10 measured here + 6 from jv7 A/B + 24 banked jv6):
jv8 = 122,663,634 — new SOTA.** Promoted to myalgorithm.py per evolve.md.
Cumulative capacity-campaign yield: −1,814,551. Goal <120M: −2.66M to go.

### Analysis
The capacity law extends to the giants: 27's −858k is the single largest
portfolio-level cell win of the entire jv lineage, from three ~free light
repack replicas racing shifted-rng polish draws of the inbox leader. 38/39
are genuinely locked (bit-identical under +3 workers — their basins are
deep). 37's bimodality didn't flip this draw (both arms bad mode; the good
mode remains a ~50% lottery — a DETERMINISTIC capture needs the replicas to
finish their draw before deadline, worth a jv9 look). Non-forced small cells
(29: obj1=0) still yield to replica draws → the remaining 24 unmeasured
cells likely hide more.

### Next (jv9)
1. Parent-as-searcher (Plan C) — the last idle core-fraction.
2. A/B-sweep the remaining unmeasured cells (bank latent replica wins).
3. 37 bimodal capture: replicas already add draws; consider one giant
   replica seeded from the SPARSE path with early-finish + re-improve loop.
