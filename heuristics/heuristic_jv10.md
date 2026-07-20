# jv10 — seed-diversity racer + 2nd deaf replica + sweep (goal <120M)

Base: jv9 (SOTA 121,596,816, gap −1.60M).

## Three plans (evolve.md step 1)

### A. W7 = seed-diversity racer (nm_elig forced non-giants {23,26,30,31,33})
The zone/drain constructions BROKE the raw frontier (31 −1.21M, 39 −429k,
mid-tier drain −0.1..−0.5M raw) but died at portfolio under a SINGLE polish
trajectory (r5/r6). The capacity law says trajectories decide — so give those
seeds their own worker: W7 heads its window with 4 deterministic zone/drain
builds, then jitters around both families, and polishes the raw-min under a
fresh trajectory (2077+soff). Replaces W7's second-W1-replica role there only.

### B. Giants: wid 5 goes deaf too (2 deaf + 2 followers)
27 yielded twice to added draws; independence is the candidate active
ingredient. Followers collapse onto the leader's basin — a second independent-
basin polish stream doubles the true basin diversity. Floor-safe: 38/39/37
ties came from W0–W3 draws, so follower removal can't regress them.

### C. Sweep the never-measured mid cells {22, 24, 25}
~1.79M banked mass still carries jv6 values; jv7's non-giant replicas already
race there (code byte-identical jv9→jv10 on these), so measuring banks them.

## Test plan
`compare.py myalgorithm_jv9 myalgorithm_jv10 750 27 37 31 26 33 30 23 22 24 25`
{27,37,39-class giants + all nm_elig cells} = every cell jv10 code can touch,
plus the sweep trio. 39/38 excluded: rigid, and follower-removal is
regression-proof there (winners come from W0–W3).

## RESULTS (2026-07-20, jv10_ab.log): BOTH PLANS DEAD -- NOT PROMOTED

| cell | jv9 bank | jv10 arm | verdict |
|---|---|---|---|
| 27 | 23,649,558 | 24,074,569 | **+425k REGRESS** -- deaf-wid5 was jv9's 27 winner; 2nd-deaf silenced it (Plan B DEAD) |
| 37 | (bad-mode tie) | -- | jv9 arm drew GOOD mode 5,699,640 -> BANKED -107,407 |
| 31 | -- | -- | jv9 arm HUNG 7787s (system stall) -> invalid, isolated re-bench pending |
| 26 | 7,908,663 | 8,199,987 | +291k regress -- racer displaced W7's jitter winner (Plan A DEAD) |
| 33 | 7,623,365 | 7,589,514 | -34k vs bank (only racer win; jv9 arm +246k draw noise) |
| 30 | 3,081,819 | 3,155,729 | +74k regress |
| 23 | 2,494,797 | tie | 0 |
| 22 | 873,789 | 897,767 tie | +23,978 -- capacity modules shift SOME non-forced cells up; banked honestly |
| 24 | 578,751 | -- | jv9 arm 559,336 -> BANKED -19,415 |
| 25 | 334,062 | (hung) | jv9 arm 308,502 -> BANKED -25,560 |

**Verdict: jv10 code DEAD (displacement, same class as jv6 substitution
levers). NOT promoted -- myalgorithm.py stays jv9.** But the A/B's jv9 arm
banked 4 new draws (37 good-mode + 22/24/25): composed **121,468,412**
(jv9-r2 row). Gap -1.47M.

### The jv11 lead (crystallized here)
Every replica so far clones the LIGHT W3 slot (giants) or W1/W2/W3
(non-giants). The streams that actually PRODUCE the giant leaders -- the
W0-reclaim pipeline (nk-nestle build -> deep improve -> whole_bay -> z3) --
have NEVER been replicated. 27 yielded to leader-FOLLOWING repack draws
(jv8/jv9); a W0-reclaim replica with a shifted improve/whole_bay trajectory
attacks the leader's OWN basin, not a repack of it. This is the untried
high-value stream. jv11 = jv9 + W0-reclaim replica (giants) under fresh
trajectory. Also: two batch cells hung (31,25) under sustained multi-hour
load -> add an isolated re-bench pass for any capacity-touched giant.
