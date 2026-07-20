# jv9 — full-width portfolio + independent-basin giant replica (goal <120M)

Base: jv8 (SOTA 122,663,634). Facts driving this iteration:
- jv8 proved adding workers leaves incumbent draws bit-identical (37/39/38/23/
  32 exact ties) → CPU contention from further widening is ~measured-zero.
- 27 responded −858k to replica repack draws; 31/33/30/35/28 responded to
  replica racers. 38/39/26 are locked basins (bit-identical under +3 workers).
- The parent still idles ~95% of every run (0.25s queue polls); one core is
  reserved for it on non-giants, and giants leave it a whole core too.
- Every giant replica currently improves the INBOX LEADER — they all collapse
  onto the same basin. True basin independence is untested at replica scale.

## Three plans (evolve.md step 1)

### A. 8th worker — use every core (nw min(7,cpu−1) → min(8,cpu))
Non-giants: W7 = second W1-slot replica (soff = 10007·4). Giants: 4th light
repack replica. Parent poll loop is near-free; jv8's tie evidence says
oversubscription risk ≈ 0. Expected: +1/7 draw capacity everywhere.

### B. DEAF giant replica — independent basin polish
On giants, ONE replica (original wid 6) gets inbox=None: it polishes its OWN
sparse-seed basin to the deadline instead of adopting the leader. The r7
"seed-independence" proof was for the SAME trajectory; 27 just showed
trajectories matter — a deaf replica is a new trajectory AND a new basin,
the one combination never tried. Floor-safe via min-wins.

### C. Parent-as-searcher (still deferred)
9th stream on non-giants. Broadcast-latency risk to the merge tail; only if
A+B stall short of goal.

## Test plan
`compare.py myalgorithm_jv8 myalgorithm_jv9 750 27 31 33 30 35 28 26 38`
— the responsive set + two locked canaries (26 contention canary, 38 RAM
canary: 8 workers on the 36.76M cell, projected ~9GB).

## RESULTS (2026-07-20, jv9_ab.log): −1,064,445, 4 wins / 4 ties / 0 regress

| cell | jv8 arm | jv9 | delta | note |
|---|---|---|---|---|
| **27** | 24,074,569 | **23,649,558** | **−425,011** | second consecutive strike (obj1 1669→1628); cumulative −1.32M |
| **31** | 8,265,728 | **7,884,864** | **−380,864** | obj1 401→378 |
| 33 | 7,623,365 | 7,623,365 | 0 | tie |
| 30 | 3,155,729 | 3,081,819 | −73,910 | weighted win (lex prefers jv8: obj1 197→199; goal metric is weighted) |
| 35 | 1,343,575 | 1,343,575 | 0 | tie, both arms −2,373 below banked |
| 28 | 3,501,009 | 3,501,009 | 0 | tie |
| **26** | 8,093,323 | **7,908,663** | **−184,660** | the twice-bit-identical cell BREAKS at 8 workers (obj1 545→534) |
| 38 | 36,756,532 | 36,756,532 | 0 | canary clean: 8 workers, no RAM/contention harm |

**Composed row: jv9 = 121,596,816 — new SOTA.** Cumulative capacity yield
−2,881,369. Goal <120M: −1.60M to go.

### Analysis
Width keeps paying past the point every substitution lever died. 26's break
shows "locked" cells are just draw-starved at different depths. 27 has now
yielded twice to added independent draws — its basin structure is shallow-
multimodal, not deep. 38/39 remain the only truly rigid cells.

### Next (jv10)
- W7 → seed-diversity racer on forced non-giants: polish the ZONE/DRAIN raw-
  frontier builds under fresh trajectories (their r5/r6 deaths were single-
  trajectory).
- Giants: second deaf replica (independence is the candidate active
  ingredient behind 27).
- Sweep {22, 24, 25, 20, 36} (~2.1M mass) + re-measure 37 under 8w.
