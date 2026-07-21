# heuristic_41 — Deadline guarantee + the density frontier (v41, design for v42)

## Context (2026-07-21, after row 40 = 120,123,174)

Gap to <115M: −5.12M. Two work items this iteration: (a) fix the v40 timelimit-overrun
defect (prob_26 ran 2104s @TL=1800 — contest-compliance risk), (b) locate where the
remaining 5.12M can actually come from.

## v41 = v40 + hard return-by-deadline guarantee

Audit found 10 unbounded post-race sites; the smoking gun for the +304s overrun was
`_t37_build_pool` (no deadline parameter at all: ≤110 blocks × raster scans × `_can_place`
gates ≈ 50-80s/band on this half-speed mac, k=6 bands compounding). Fixes: deadline params
threaded into every tail build loop (checked every N iterations), CP-SAT
`max_time_in_seconds` recomputed immediately before every Solve, every post-stage official
verify gated on a measured `cf_cost` (the instance's own check_feasibility cost), unverified
candidates discarded in favor of the prior verified champion. Fast-path behavior identical;
guards collapse to v40 constants when `cf_cost <= ~0.4s`.
Validation: prob_26 @1800 (the overrunner) + prob_23 @900 — must return within TL and
land the known basins.

## LB analysis — the "forced tardiness" belief is dead

`lb_cumulative.py` (all-bays-merged per-layer cumulative relaxation, valid tardiness LB)
at cap_frac=1.0, 120s: **every top cell except 38/27 has LB=0**, and
prob_38 w1·LB = 226,661 / prob_27 w1·LB = 279,993 — vs current cells 36.3M / 23.6M.
Aggregate capacity is NOT binding. The binding constraint is realized packing density.

Density calibration (cap_frac = assumed effective density; w1·LB / w1·UB, 90s):

| cap_frac | prob_38 | prob_27 |
|---|---|---|
| 0.5 | 26.3M / 42.6M | 13.7M / 22.9M |
| 0.6 | 14.3M / 26.8M | 9.4M / 13.2M |
| 0.7 | 8.1M / 15.7M | — |
| 0.8 | 4.4M / 8.8M | — |

Current cells sit at ≈0.5-0.55 effective density on both giants. Each +0.05 density is
worth roughly −5M on prob_38 and −3M on prob_27. **The entire path to <115M is packing
density on the two giants.**

## v42 design — budget-gated depth scaling (from the read-only audit)

@1800s the giant path gets 2.5× more time but every depth constant is 600s-era; observed
rounds are plentiful (~168) with best_o1 plateauing → coordination radius binds, not round
count. Three knobs (all obj-gated min-wins, giants only, no-ops when <200-300s remain):
1. Deep xpack shots: alternate proven (D=14,K=12,13s) with deep (D=22,K=16,30s) in
   `whole_bay_phase` on the W0 reclaim-giant path.
2. Joint-repack radius: 5th rotation entry ws=6.0·pbar, md=70 when >300s remain.
3. Repair caps 40/30 → 64/48 when >300s remain (v8 precedent: the 18→40/14→30 widening
   escaped plateaus for −2.13M on prob_26).
Rejected for now: deaf-replica xpack (8GB memory risk), bigger kicks (28a evidence:
accept-worse moves fire-and-lose).
Known deviation: on forced cells at TL=900 the >300s gates CAN pass early — 900s forced
cells need re-measurement if v42 is promoted (no banking).

Measurement: v42 vs v41 paired @1800 on {38, 27, 26} (38/27 have deterministic basins
today: 36,322,548 / 23,560,982 — attribution is clean).

## v42 RESULT (2026-07-21): FLAT — depth-scaling family dead

All three paired cells byte-identical to v41: prob_38 36,322,548 / prob_27 23,560,982 /
prob_26 7,721,350. Deep xpack shots, wider joint-repack radius, and 64/48 repair caps all
converge to the same optimum. v42 NOT promoted (kept in tree for provenance).

Accumulated fixed-point evidence on the giants: tails ≈0, merge-on-forced 0, depth
scaling 0, seed replicas 0 (jv8/9 measured), re-pacing lottery ±14k — the ONLY lever that
has ever moved prob_38/27 is total wall-clock into the same deterministic W0-reclaim
pipeline (−1.87M / −0.51M per 900→1800 doubling). Hence the v43 question: is the pipeline
compute-starved (slope persists at 3600s → speed engineering pays) or density-saturated
(slope collapses → <115M needs a new packing paradigm)? 3600s probe running.
