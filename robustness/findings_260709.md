# Robustness findings — 2026-07-09 (Mac dev machine, v18 = myalgorithm.py)

Machine: macOS arm64, 10 cores, 16GB RAM, conda env `ogc2026`
(`ogc2026_env_local.yml`; python 3.12.13, shapely 2.1.2, ortools 9.15.6755 —
same versions as the eval server). Numbers are robustness signals, NOT
performance rows (those stay on the Windows bench machine).

## 1. Cross-platform determinism sanity check — PASS

`prob_1 @60s = 18,357` on this Mac = the Windows byte-protect value exactly.
Also reproduced from the extracted submission zip at T=30s. The solver's
banked basins are not Windows-specific at short budgets on easy instances.

## 2. Timelimit scaling (`bench_scaling.py`, probs {1,27,31,38} × T {60,120,300}) — 1 FAILURE

| prob | T=60 | T=120 | T=300 |
|---|---|---|---|
| 1 | 18,357 (50.9s) | 18,357 (102.9s) | 18,357 (272.0s) |
| 27 | 29,198,468 (50.1s) | 29,185,135 (100.4s) | 29,185,135 (261.9s) |
| 31 | 11,548,288 (53.7s) | **10,927,585** (103.7s) | 10,927,585 (263.6s) |
| 38 | 45,806,839 (57.2s) | 45,806,839 (108.1s) | **FAIL: 3,729,926,244 @ 997.3s** |

**Finding A: prob_38 @T=300 blew its own deadline 3.3× (997s wall) and
returned the empty-bay fallback (3.73B) — but only under machine load.**
The failing run co-ran with the stress test + other heavy processes; a
standalone rerun (§4) is clean: feasible 45,806,839, peak RSS 1.39 GB.
So this is NOT intrinsic solver memory bloat. What it demonstrates is the
failure MODE: under resource starvation the cooperative deadline discipline
(time.time() checks in workers, parent drain/terminate) can collapse, and the
result is a would-be timeout ⇒ −1 on the eval server. Takeaways:
1. Bench hygiene on dev machines is not optional (matches the campaign law:
   quiet machine, check load first) — co-run numbers are garbage.
2. The eval server is dedicated but throttled via cpulimit (400%); the safe
   posture is a **parent-side hard watchdog**: at `T − ε` return the best
   verified incumbent unconditionally (kill workers, don't join them), so
   even a starved run degrades to "insurance solution" instead of overrun.
   Worth a small v19 hardening item (submission path, so protect-gated).

**Finding B: prob_31 @120s on this machine = 10,927,585, i.e. −340,658 BELOW
the banked Windows 600s value (11,268,243).** Same code, same instance —
different CPU pacing lands a better basin. This directly supports the
heuristic_19.md Improvement-5 premise that prob_31's basin is escapable (its
"stuck" value is an artifact of one deterministic trajectory, not a structural
floor). Cheap follow-up on the Windows machine: reproduce with small pacing
perturbations (or bank via an explorer slot); the assignment itself could be
harvested from a Mac run and verified/banked through min-wins if we add a
cross-machine solution-import path (`operations` JSON is machine-independent).

Other observations: prob_27 needs >60s for its exact-pack accept
(29,198,468 → 29,185,135 at 120s) — graceful. All wall-time margins healthy
(algo returns 8–13% before T) except the prob_38@300 failure.

## 3. Instance perturbation stress (`stress_test.py`, {1,27,38} × 7 variants @60s) — 21/21 PASS

bay_grow / bay_shrink / due_tight / release_jitter / w1_low / drop10 / dup10
all returned feasible solutions in time, including n=275 (dup10 on prob_38,
above the n≥250 giant gate) and n=110/135/165/225 variants that cross
overload/branch thresholds. No crashes, no hangs, no infeasibles.
Objective sanity: bay_grow helps (prob_38 45.8M → 29.2M with +10% bay area —
more evidence that density is the binding constraint), bay_shrink/due_tight
hurt, w1_low collapses the objective as expected.

Known gap: the branch-flag introspection (`ovl/frc/rcl` columns) printed `?`
— `myalgorithm`'s private helpers take different arguments than guessed.
Cosmetic only; fix when next touching the script.

## 4. Memory profile (prob_38 @300s, standalone) — PASS

```
CHILD_RESULT feasible=True objective=45806839.0
prob_38 @300s: peak RSS = 1.39 GB across 6 processes (533 samples)
timeline (max GB per decile): 1.0 1.4 1.4 1.3 0.6 0.9 1.0 0.8 0.9 1.0
OK: peak 1.39 GB vs 16 GB server limit (alert at 85%)
```

Ample headroom for the v19 CP-SAT components (~14.6 GB to the alert line),
and the standalone rerun reproduces the banked 45,806,839 — confirming
Finding A's failure was load-induced, not a T=300 code path bug.

## Recommended standing gate before every submission

```bash
conda run -n ogc2026 python robustness/bench_scaling.py && \
conda run -n ogc2026 python robustness/stress_test.py && echo SAFE
```
plus one `mem_profile.py` run on prob_38 whenever a CP-SAT-heavy component
lands (v19c/19d).
