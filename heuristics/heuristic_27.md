# Heuristic v27 — SCAN-THROUGHPUT MULTIPLIER epoch (goal < 112,500,000; v25 = 124,581,895; v26 ladder ≈ neutral)

Departure: v26 (post-ladder; W1/W3 near_k diversity measured neutral-to-marginal,
see heuristic_26.md Results). Remaining ask: ≈ −12.08M, concentrated in
prob_38 = 36.35M (≈34.1M tardiness + 2.27M preference; w1=13333, w3=300) and
prob_27 = 24.97M (≈23.0M tardiness + 1.96M preference; w1=13333, w3=400).

## Premise — the wall is THROUGHPUT, not mechanism

Measured (ledger_19): ~0.3 improver iters/s with **92% of wall-clock inside the
raster scans** (`scan()` / `scan_scoped()`, myalgorithm_26.py:2993-3113). The
hot loop is `sliding_window_view` + `einsum` — a dense O(R·C·MH·MW) integer
cross-correlation per layer, per (block, orient, bay, occupancy-version), with
no sparsity exploitation and no early termination. On 38-class giants
(masks ~40×40 in bays ~100×60) that is ~10⁷ multiply-adds per scan.

Consequences of a 5–10x scan kernel, at identical wall-clock budgets:
- every deadline-paced BUILD finishes earlier → more polish time in every
  stream (natural re-pace, no code pacing change);
- the W1 rotation completes more tickets per 0.42w/0.5w window → more basins;
- the improver runs ~2–3 iters/s instead of 0.3 → polish depth multiplies;
- deep near_k (16–64) becomes affordable where it truncated before — the exact
  failure mode that killed 26a (near_k=32 scan truncated the giant build at its
  0.22w deadline).

numba is SUBMISSION-LEGAL: ogc2026_env.yml ships numba (+ scipy, torch etc.)
on the eval server. Locally .venv_ogc lacks it → `pip install numba` (do this
on an idle machine, never mid-bench). Code must guard `try: import numba`
with the einsum path as fallback so the submission cannot die on import.

## Improvement A — fast correlation kernel for scan()/scan_scoped() (primary)

PROTOTYPED 2026-07-15 (session scratchpad, .venv_ogc + numba 0.66):
- sparse scatter numba kernel: **DEAD** — x0.3 vs einsum on giant regime (both
  operands are dense; the sparse premise fails).
- **FFT correlation (pure numpy rfft2, batched over layers): VALIDATED** —
  exact (== einsum) on 30 random regimes with an assert-guarded rint;
  x2.7 on giant (40×40 mask, 100×60 bay, 2 layers), x3.9 mid (20×20/80×50),
  x0.6 small (8×10/50×25) → HYBRID: einsum below a work-size threshold
  (R·C·MH·MW), FFT above; threshold calibrated from the real profile.
- stretch: numba BITBOARD kernel — pack union rows into uint64, precompute 64
  column-shifted packed variants per (bi,oi,layer) mask (immutable, lazily
  cached, ~40KB per combo), count = popcount(AND) summed over mask rows;
  ~R·C·MH·ceil(MW/64) word-ops ≈ 100x fewer ops than einsum on giants
  (theoretical x10-30). Only pursue if the FFT hybrid's measured end-to-end
  gain is Amdahl-capped well below the scan share.

STEP 0 (before implementing): PROFILE a real workload — patch scan()/
scan_scoped() to histogram (R,C,MH,MW,nl,#actives) and time the einsum vs the
Python-side layer assembly on ~60-120s of algorithm() on prob_38 and prob_27.
If layer assembly (the `for actives` loop, mask fetches, slicing) is a large
share of scan_scoped, the kernel must swallow it too (numba-jit the whole
scoped path or cache the actives-union stack per improver trial context),
else Amdahl caps the epoch.

Returns EXACTLY the same `total` semantics (feas = total==0; near =
0<total≤near_k) → byte-identical decisions per scan. Guard `try: import
numba` (fallback: FFT hybrid, then einsum) so the submission cannot die on
import. Compile-at-import warmup 2-5s if numba used (cache=False — eval
pycache writability unknown).

**EPOCH RESET WARNING:** faster scans shift every time-paced lottery draw and
every deadline-bounded phase in ALL streams — the v13→v14 displacement law
applies globally. v27-A is NOT spot-comparable per-ticket; it needs the full
eligible-8 spot at minimum, and a full-40 @600s row before any promotion.
Expect some per-instance regressions (displaced lucky draws) offset by
systematic depth gains. Min-wins protection does not cross code versions:
judge only the full row.

Kill: full-40 @600s ≥ 124.58M (no net gain) after the exactness harness
passes. If the kernel is exact but slower on small instances (JIT overhead,
tiny masks), gate the numba path on mask area × bay area above a threshold —
measure, don't guess.

## Improvement B — post-multiplier knob re-exploitation (the epoch's harvest)

**[SUPERSEDED by the 27a saturation finding: the eligible-8 came back
byte-identical under x3.56 scans → count caps saturate and polish converges at
600s; more draws/depth is predicted dead and risks the frozen 38 coupling.
Do not run these sweeps without a specific contrary signal. The freed wall-
clock should fund NEW MECHANISMS (C, or restart-from-perturbed-base), not
more of the same. ledger_27_diag (in flight) decides the mechanism family.]

Every tuned knob was optimized under the 0.3 iters/s regime. Once A lands,
re-sweep the cheap dimensions on {38,27} only:
- near_k in the W1 family: {32, 48, 64} tickets now complete without
  truncation (26c measured these under the OLD cost model);
- 26a-revisit: near_k=32 build1 in the W0-reclaimed deep pipeline no longer
  truncates at 0.22w — re-spot {38,27,39} once (the displacement risk stays,
  so judge vs the NEW v27-A baseline, not v25 cells);
- W1 jitter tail: more draws now fit — consider raising the ji<24 cap;
- improver repack_every / whole-bay budget on the giants.
One spot each, keep winners, standard kill (≥ −100k rule vs the v27-A row).

## Improvement C — ejection-chain admission (new mechanism family)

Carried from 26d (unrun): at admission events, for near-miss anchors blocked
by ≤2 RESIDENT blocks, test exact single-depth relocation of each blocker to
its own exact-feasible anchor in the same bay/layer (_can_place-gated both
moves, obj-gated accept, crane-path re-checked for both). near_k recovers
dilation loss; ejection recovers FRAGMENTATION loss (residual ~0.05–0.15 of
bay area in the admission loss stack). Only affordable at v27-A scan speeds —
each ejection test is ~3 extra scans. Wire as one W1 ticket first. Spot
{38,27}. Kill: flat on both after a blocker-count sweep {1,2}.

## Ladder

- 27a = A. Order: pip install numba (idle machine) → exactness harness on real
  instances (38/27/5, near_k 3 and 32, assert array-equal feas+near grids) →
  microbench speedup (target ≥5x giant-mask scans; report ms/scan) →
  full eligible-8 spot @600s → full-40 @600s row `algorithm 27`.
  Protect: prob_1 @60s (value may legitimately shift in this epoch — protect
  criterion is FEASIBLE + ≤ 18,357+noise, byte-match no longer required).
- 27b = B sweeps on the 27a baseline (only if 27a kept).
- 27c = C. Spot {38,27} vs the current epoch baseline.
- SOTA promotion: only from a full-40 row < 124,581,895; goal check < 112.5M.

## Results

### 27a — FFT/numba scan kernel (EXECUTE, 2026-07-15)

**TASK 0 profile** (single-thread `_run_strategy(wid=1)`; einsum path instrumented):
- prob_38 (90s wall 75.8s): scan() n=99,692 corr=26.14s; scan_scoped() n=52,643
  corr=9.88s **asm=13.13s**. corr = 47% of wall; scan_scoped assembly = 57% of
  (asm+corr) and 17% of wall. Instrumented total 65% of wall.
- prob_27 (60s wall 49.0s): scan() n=138,133 corr=15.58s; scan_scoped() n=30,271
  corr=5.16s **asm=9.50s** (asm = 65% of scan_scoped).
- Work sizes SMALL: wide shallow bays (p38 H~24 W~105, p27 H~19 W~58),
  masks ~14×15, nl=2, R·C·MH·MW median 60k–175k. This is BELOW the FFT
  crossover (proto: FFT loses <55k, wins >1.5M) → **FFT is the wrong kernel
  here**. Assembly ≥30% of scan_scoped → flagged for task (c).

**Kernel chosen: numba SATURATING correlation** (not FFT). For each anchor,
accumulate mask/occupancy overlap with per-anchor early-exit once the count
reaches near_cap = near_k+1; feas=(t==0), near=(0<t≤near_k) are then exact
(capping never changes either verdict). Dense giants early-exit after a few
cells. FFT-hybrid and einsum kept as guarded fallbacks (eval safety); numba
is submission-legal. Import+warmup = 0.99s (<5s). Mask-cell coords cached per
(bi,oi); union stack built per call. Applied to scan() AND scan_scoped()
correlation loops only — assembly left byte-exact (corr-only already clears
the gate; assembly accel deferred to 27b).

Microbench (real dims, 0/400 exactness mismatches): near_k=3 (default) x15–23;
near_k=32 (deep) x1.76–2.63.

**TASK 2 harness** (`v27_harness.py`; record W1 trace on {38,27,39}, replay vs
v26 einsum, assert feas+near at near_k∈{3,32}, time both):
- **Exactness: 0 mismatches over 230,448 grid checks.**
- scan() x6.43, scan_scoped() x1.61 (now assembly-bound), **OVERALL x3.56** on
  the real recorded trace (36.9s→10.4s). GATE PASS (exact + ≥1.5x).

**TASK 3 spot — eligible-8 @600s serial** (`bench.py myalgorithm_27 600 23 26
27 30 31 33 38 39`; machine quiet, foreign embedding-build process finished
before the giants; 8/8 feasible):

| prob | v27 | banked v25 | delta |
|------|-----|-----------|-------|
| 23 | 2,524,154 | 2,524,154 | 0 |
| 26 | 8,551,513 | 8,551,513 | 0 |
| 27 | 24,972,962 | 24,972,962 | 0 |
| 30 | 3,363,565 | 3,363,565 | 0 |
| 31 | 8,124,019 | 8,124,019 | 0 |
| 33 | 7,734,338 | 7,734,338 | 0 |
| 38 | 36,351,493 | 36,351,493 | 0 |
| 39 | 8,389,519 | 8,389,519 | 0 |
| **sum** | **100,011,563** | **100,011,563** | **0** |

**Every eligible-8 cell is BYTE-IDENTICAL to the banked v25 cells (delta 0).**
The predicted epoch displacement did NOT materialise: the exact faster kernel
finishes the same work sooner but the workers already converge to these optima
within the 600s budget (min-wins improver reaches a fixed point; the winning
candidate — often the W0 exact replica or a plateaued basin — is unchanged).
Extra throughput found nothing better and displaced nothing.

**TASK 4 decision:** 8-sum delta = 0, well within ±300k → **STOP for
orchestrator review; full-40 NOT run** (do not burn 6.7h when the spot is a
byte-for-byte tie). No promotion (no full-40 improvement measured). v27a is a
VALIDATED, exact, submission-safe throughput multiplier (x3.56 scan trace,
0/230,448 exactness mismatches) that is OUTCOME-NEUTRAL on the train
eligible-8. Its value is as a substrate: the 27b (near_k {48,64}, jitter tail,
repack budget) and 27c (ejection-chain admission) mechanisms were "only
affordable at v27-A scan speeds" — they now have the headroom. Kept as
myalgorithm_27.py; myalgorithm.py (SOTA) left at v25 cells.

**TASK 5 protect:** prob_1 @60s = 18,357 (feasible, 51.0s, obj1=0) — ≤20,000
and byte-identical to the banked v25 protect value. Import+warmup 0.99s (<5s).
