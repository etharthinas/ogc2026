# ledger_19.md — Tier-T honest capacity measurement (heuristic_19 Improvement 1 + 8A)

> Deliverable the plan (§2, §13, Improvement 1) says to produce FIRST, because
> every downstream decision — which rock to push, whether <125M is reachable at
> all — depends on capacity-honest numbers we did not have. Produced 2026-07-08.
> Method: run the REAL v18 4-worker `algorithm()` on the instance (300s, clean
> machine), convert the returned operations back to an internal assignment
> (`run_v18_save.py`), then measure realized bay density, admission delay, and
> tardiness (`measure_giant.py`). All incumbents reproduce the banked value
> (27=29,185,135; 38=45,806,839; 39=12,361,461 exactly; 31=11,055,999, i.e.
> −212k under the loaded-machine 600s bench row — see run-variance note).

## The four big rocks are DENSITY-SATURATED (the decisive finding)

| prob | v18 obj | w1·tardiness | peak realized bay density | n_tardy | queued (entry>rel) |
|---|---|---|---|---|---|
| 38 | 45,806,839 | 44,065,565 | 0.941 / 0.974 / **1.048** | 100/250 | 126/250 |
| 27 | 29,185,135 | 27,372,649 | 0.939 / **0.972** | 70/150 | 87/150 |
| 39 | 12,361,461 | 11,239,719 | **1.026** / 0.944 / **1.077** | 100/250 | 131/250 |
| 31 | 11,055,999 | 8,239,794 | **1.065 / 1.133 / 1.025 / 1.023** | 47/200 | 70/200 |

Peak realized density ≥ 0.94 on every bay of every big rock; values > 1.0 mean
the incumbent is already exploiting **multi-layer stacking** (blocks share (x,y)
footprint on different layers). **There is no packing slack left to exploit.**

### Why this refutes the plan's payload (Improvements 2, 3, 4)

Improvements 2/3/4 (calibrated flow-plan, rolling-horizon MPC constructor,
layout-book column generation) ALL rest on one premise: that a smarter
constructor can pack the bays DENSER during the release burst, drain the entry
queue faster, and thereby cut tardiness. The measurement shows the premise is
false — v18's incumbent **already** packs to ≥94–100%+ realized density at the
congestion peak. Improvement 4's own cheap kill test is stated in the plan:
"if exact density-max cannot beat accidental density, kill early." The accidental
density is already ≥0.94–1.13; exact density-max cannot beat it. The over-floor
"mass" the plan hoped to recover (e.g. 38: 21.6M vs fluid LB 24.2M) is a
**preemptive fluid mirage** — the fluid LBs are ~40% loose exactly because they
permit preemption and fractional packing the real (non-preemptive, integer,
crane-constrained) problem forbids. The realistic non-preemptive floor sits
near the incumbent, not near the fluid LB.

### Why tardiness is structural (not schedulable away)

Tardiness = Σ max(0, exit − due). Under saturation, the total resident
area·time demand during the burst exceeds bay capacity, forcing a fixed minimum
total exit-delay. The only schedule freedom is WHICH blocks absorb the delay
(push slack/late-due blocks, rush early-due blocks). That is precisely what the
v18 dispatcher's ATC priority + `_improve` + exact `_cpsat_retime` already
optimize. Re-ordering admissions only "shuffles who is tardy, not total queue
delay" (the plan's dead family #1). Confirmed dead by direct measurement.

## Improvement 5 (acceptance-rule diversification) — MEASURED DEAD (19b)

The one genuinely-untried family (non-greedy acceptance: SA / LAHC
ruin-and-recreate), tested from the TRUE banked incumbents:

| instance | greedy (obj-gated) 200-250s | SA (uphill) | LAHC (multiple configs) |
|---|---|---|---|
| 31 | 11,030,700 (−25,299) | 11,030,700 (identical) | flat (+0), 0–43 accepts, never < start |
| 39 | 12,361,461 (**+0**) | — | flat (+0), 56 accepts, never < start |

- `sa=True` (the improver's wired-but-never-used uphill path) explores uphill
  and returns the SAME basin as greedy → no better basin reachable by these
  moves.
- LAHC with seeded history (`hist=inf`) DOES accept uphill moves (43/56 accepts
  on 31/39) and wanders, but best-seen NEVER drops below the incumbent.
- prob_39 greedy control is FLAT from the banked incumbent: the giant is NOT
  round-starved once converged; v18 already extracts everything the improver
  reaches.
- **Throughput wall:** ruin-recreate runs at ~0.2–0.7 iters/s. Profiling
  (`prof_recreate.py`) pins 92% of time in `_Raster.scan_scoped`
  (einsum + sliding-window mask scan, ~300 scans per block placement).
  numba is NOT importable in `.venv_ogc` (verified), so Improvement 7 (the
  throughput multiplier the plan counted on) is unavailable — iteration-heavy
  metaheuristics are structurally infeasible on this hardware/env.

Kill criterion from the plan ("31 AND 39 flat < −100k after the L/ruin sweep")
is MET. Improvement 5 is the **tenth measured-dead family**.

## Frontier verdict — does the realistic target sum clear 125M? NO.

- The four big rocks (96.6M, 65% of the 149.83M total and the plan's ENTIRE
  targetable mass) are density-saturated → realistic floor ≈ incumbent.
- The mid-band {26,33,37,30,32,28,23,21,35,40,…} totals ~26.6M with a joint
  floor ~0.5M, but the plan itself budgets only −1…−3M combined there, and it
  is the same saturated/scheduling regime.
- Even conceding the ENTIRE mid-band optimistically (−3M) leaves ~146.8M —
  still **21.8M above the 125M goal**, because the required −18…−24M must come
  from the big rocks, which are measured immovable.

Budget escalation (§13b) is a proven zero: v18 measured the giants byte-flat at
2× budget, and the giants are saturated, so more time cannot create resident
space that does not exist.

**Conclusion: <125,000,000 is not reachable at the 600s (or any) convention
with any mechanism in this campaign's arsenal. The 149.83M frontier is a
structural space-time-saturation floor, not a search-effort artifact.** This is
the §13 case. Per §13 and the campaign law "do NOT silently bench-shop
budgets," the decision (renegotiate the goal to the measured frontier / escalate
with a fundamentally new *time-responsive* mechanism / accept 149.83M) is
surfaced to the user rather than papered over.
