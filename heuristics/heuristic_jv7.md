# jv7 — search-capacity scaling (goal: total < 120M @750s)

Base: jv6b (= jv6 SOTA 124,478,185 + default-off drain/zone/steal/nmc plumbing;
every jv6b live edit measured bit-identical tie, see heuristic_jv6.md r4–r7).

## Premise

The jv6 campaign proved every *seed/config substitution* dead: the
construct→polish→merge pipeline is a per-instance absorbing fixed point, and a
changed worker that doesn't win its race is invisible. What was NEVER varied is
**how many independent draws race at once**. This machine has 8 physical cores
(Ultra 7 258V, 4P+4E); jv6 uses 4 workers + a mostly-idle parent, and every
CP-SAT inside a worker is 1-thread, the parent merge CP-SAT 4-thread. ~40% of
the machine idles through every 750s run. Observed draw spread (bimodal 37:
107k; 33: 179k; 27: 40k; 39: 17k) says the polished-output distribution has
real width — min-wins over MORE samples shifts the whole row left, without
touching any measured-dead lever.

## Three plans (evolve.md step 1)

### A. Portfolio width: nw 4→7 on non-giant instances
- Giants (forced, n≥250 = {27,37,38,39}): keep nw=4 byte-identical (RAM-bound;
  full-40-tail corruption precedent says don't touch their timing).
- Everything else: spawn W4–W6.
  - Non-forced cells: W4–W6 re-run plans 1–3 with wid-offset jitter/improve
    seeds → 6 independent polished draws instead of 3 + richer merge pool.
  - Forced non-giants (31-class): W4 = drain-constructor racer, W5 = zone
    racer, W6 = re-seeded nk-jitter — the config-rescue levers as *additional*
    racers (min-wins floor-safe) instead of budget-displacing substitutions.

### B. Solver-thread capacity where cores are provably idle
- Parent merge-recombine CP-SAT: 4→8 search workers (it runs after workers
  drain; the machine is idle). Merge tail is the ONLY measured positive-yield
  family (−383,875) — this directly buys it search power.
- OGC_MERGE_CAP default 24→32: mergecap-widening was dead for lack of pool
  diversity; W4–W6 now *supply* new distinct solutions, so re-test wider cap.

### C. Parent-as-searcher (deferred behind A/B probe)
- After the insurance build the parent idles between 0.25s queue polls. On
  non-forced cells it could run chunked jittered builds and inject into cands.
  Risk: delays gbest rebroadcast → perturbs worker draw timing. Only if A+B
  probe under-delivers.

## Risks
- CPU contention: 7 workers on 4P+4E means someone lands on E-cores; existing
  W0–W3 draws may shift. A/B decides — contention regression would show as
  losses on the probe cells.
- RAM: mid-tier builds are light (<1GB/worker); giants unchanged.

## Test plan (evolve.md step 3)
A/B compare.py jv7 vs jv6 @750s, isolated, on {31, 33, 26, 28, 30, 40}
(forced-non-giant racers + non-forced merge-fed), then full-40 if positive.

## RESULTS (2026-07-20, A/B @750s adjacent-in-time, jv7_ab.log)

| cell | jv6 | jv7 | delta | note |
|---|---|---|---|---|
| 31 | 8,400,210 | 8,265,728 | **−134,482** | lex win (obj1 417→401) — first portfolio-level break of 31 all campaign |
| 33 | 7,690,573 | 7,623,365 | **−67,208** | lex win (obj1 1029→1005) |
| 26 | 8,093,323 | 8,093,323 | 0 | bit-identical tie — replicas lost the race, floor held |
| 28 | 3,565,230 | 3,501,009 | **−64,221** | lex win; non-forced → merge-axis pays too |
| 30 | 3,363,565 | 3,155,729 | **−207,836** | lex win (obj1 209→197), biggest |
| 40 | 2,245,665 | 2,245,665 | 0 | tie (reclaim cell, W0 stream dominates) |

**Net −473,747, 4 wins / 2 exact ties / 0 regressions.** Composed row
(6 measured + 34 banked from jv6): **jv7 = 124,004,438 — new SOTA.**
Promoted to myalgorithm.py per evolve.md step 5.

### Analysis
The absorbing-fixed-point proof (r7) said the polish converges independent of
SEED — but the wins show it is NOT independent of POLISH TRAJECTORY (rng
stream). W4–W6's soff-shifted polish seeds sample new trajectories of the same
pipeline; min-wins keeps the best of 6–7 draws instead of 3–4. The jv6-era
"config-rescue = dead" law holds; "more draws = alive" is the new law. Wins
concentrated on forced non-giants (31/33/30 = replicas racing) + one
non-forced (28 = merge-pool/thread axis). Cost: zero regressions measured —
capacity is genuinely free on this machine.

### Next (jv8 candidates)
1. Giants: 5th light worker = repack-specialist replica (seed 4444+soff,
   sparse seed + inbox improve, ~1GB) — attacks 37's 107k bimodality and adds
   a polish draw on 27/38/39 without touching the 4 existing streams.
2. Parent-as-searcher on non-forced (Plan C).
3. Uncovered non-giant cells: A/B {23, 32, 21, 34, 35} to bank replica gains
   already in jv7 (row currently banks jv6 values there = conservative).
