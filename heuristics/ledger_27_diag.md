# ledger_27_diag — v25 giant-burst diagnostics: packing vs sequencing

Date: 2026-07-15. Measurement session on dev/jay; machine quiet, serial 600s runs.
Scripts: `baseline/capture_v25.py` (runs the real `algorithm()` from `baseline/myalgorithm.py` = v25 and saves ops→assignment JSON), `baseline/diag_v25.py` (raster + exact `_can_place` diagnostic). Fresh captures `baseline/v25_38.json`, `baseline/v25_27.json`; full per-sample timelines in `baseline/diag38.json`, `baseline/diag27.json`.

## Task 1 — capture & reproduction

| inst | captured objective | banked | delta | obj1 (tardiness) | runtime |
|---|---|---|---|---|---|
| prob_38 | 36,335,881 | 36,351,493 | **−15,612** (obj1 identical at 2569; delta entirely obj2/obj3 tie-break) | 2569 | 562.4 s |
| prob_27 | 24,972,962 | 24,972,962 | 0 (exact) | 1726 | 549.6 s |

Both verified feasible via `utils.check_feasibility`. w1 = 13,333 for both.

## Task 2(b) — THE KEY NUMBER: feasible-placement fraction during the burst

At each of ~200 grid samples over [0, horizon], for every released-but-not-entered block, we asked whether ANY exact-feasible placement existed in ANY bay: conservative raster `scan()` anchors + near-miss `scan_near()` anchors (near_k=3, dilation cannot fake infeasibility), each exact-gated by `_can_place` (up to 400 scan + 400 near anchors per bay×orient, all unique orients, all bays).

Two obstacle sets: **strict** = full realized schedule (future entrants immovable); **lenient** = only blocks resident at t (pure instantaneous geometric/crane room, ignoring all future entries).

| inst | queue-block-moments | feasible existed (strict) | fraction (strict) | fraction (lenient) | saturated (strict) |
|---|---|---|---|---|---|
| prob_38 | 3162 | 8 | **0.25 %** | 1.01 % (32) | 3154 (99.75 %) |
| prob_27 | 2093 | 6 | **0.29 %** | 0.57 % (12) | 2087 (99.71 %) |

Even ignoring every future entrant (lenient), ≥ 99 % of queue-block-moments had NO exact-feasible placement anywhere. The admission machinery is not leaving placements on the table.

## Task 2(a) — burst window & per-layer collision-true density

Densities are per-layer occupied-cell fractions from the conservative raster (NOT footprint sums; no multilayer double-count). Stats over burst samples (queue > 0).

**prob_38** (bays 68×16=1088, 156×16=2496, 109×27=2943; horizon 135):
burst window t∈[8, 105] (98/200 samples), peak queue 78 blocks at t=43 (qrem_proc 1854 vs 76 resident).

| bay | layer-0 dens min/mean/max | layer-1+ dens min/mean/max |
|---|---|---|
| 0 | 0.307 / **0.665** / 0.779 | 0.412 / 0.630 / 0.816 |
| 1 | 0.589 / **0.713** / 0.793 | 0.482 / 0.617 / 0.705 |
| 2 | 0.474 / **0.691** / 0.801 | 0.409 / 0.627 / 0.813 |

**prob_27** (bays 52×20=1040, 168×16=2688; horizon 132):
burst window t∈[10, 106] (97/200 samples), peak queue 47 blocks at t=47.

| bay | layer-0 dens min/mean/max | layer-1+ dens min/mean/max |
|---|---|---|
| 0 | 0.488 / **0.634** / 0.759 | 0.308 / 0.537 / 0.837 |
| 1 | 0.402 / **0.642** / 0.759 | 0.423 / 0.576 / 0.677 |

The bays are NOT half-empty during the burst: layer-0 runs 0.63–0.71 mean and 0.76–0.80 peak, and per (b) the remaining ~25–35 % floor is fragmentary/crane-poisoned — effectively zero admittable anchors. The 19a "half-empty bays" picture does not hold for v25 incumbents.

## Task 2(c) — tardiness attribution

Per-tardy-block identity: tardiness = entry_delay + max(0, rel+proc−due) + dwell_excess.

| inst | n_tardy | obj1 | from queued blocks (entry>release) | from never-queued | Σ entry_delay (tardy) | Σ floor | Σ dwell_excess |
|---|---|---|---|---|---|---|---|
| prob_38 | 111/250 | 2569 | **2569 (100 %)** | 0 | 3059 | 0 | 0 |
| prob_27 | 66/150 | 1726 | **1726 (100 %)** | 0 | 2012 | 0 | 0 |

Every unit of obj1 comes from blocks that queued during the burst; entry delay is the sole driver (no block is tardy "by construction", no dwell loss).

Distribution — broad, not few-huge:

| inst | tardiness histogram [1,2)/[2,4)/[4,8)/[8,16)/[16,32)/[32,∞) | mean | median | max | top-10 % tardy hold | top-25 % hold |
|---|---|---|---|---|---|---|
| prob_38 | 15 / 11 / 16 / 18 / 18 / 33 | 23.1 | 14 | 79 | 29.5 % of obj1 | 61.4 % |
| prob_27 | 6 / 6 / 6 / 8 / 18 / 22 | 26.2 | 20 | 77 | 24.6 % of obj1 | 54.7 % |

Many-medium-plus-fat-tail: no single block dominates (max block = 79/2569 ≈ 3 %); halving the tail alone cannot reach the relaxation target (~1219 / ~615), the whole queue must drain faster.

## Task 2(d) — exit-side check

dwell_excess = exit − entry − processing: **0 blocks > 0 in both instances** (max excess 0). Exit side stays clean, as historically.

## Caveats

- Anchor enumeration caps at 400 scan + 400 near anchors per bay×orient per moment; scan anchors are the full conservative-clear set so undercount risk is confined to exotic exit-blocking patterns — the lenient column (still ≤1 %) bounds it.
- prob_38 capture is 15,612 below the banked total (obj2/obj3 lottery tie-break); obj1 is bit-identical, so all tardiness diagnostics apply to the banked solution unchanged.

## Verdict (5 lines)

1. **SEQUENCING, not packing**: feasible placements existed in only **0.25 % (38) / 0.29 % (27)** of queue-block-moments — admission is finding essentially every placement that exists; the queue is not caused by missed anchors.
2. Bays are effectively saturated during the burst at layer-0 density 0.63–0.71 mean / ~0.80 peak; the residual ~25–35 % floor is fragmented or crane-poisoned (lenient residents-only check still ≤ 1 % feasible).
3. 100 % of obj1 comes from burst-queued blocks via entry delay; dwell over processing is exactly 0; distribution is many-medium with a fat tail (top-25 % of tardy blocks ≈ 55–61 % of obj1).
4. Therefore the lever toward the relaxation target (~1219 / ~615) is WHICH blocks occupy the saturated bays and in what order (weighted-tardiness sequencing / swap of queue positions), and/or packings that raise EFFECTIVE density past ~0.7 by cutting fragmentation — not more lookahead at fixed packings.
5. Any next mechanism should manipulate the entry ORDER (e.g. tardiness-aware queue priority, block-swap between resident and queued) or restructure the packing to defragment; pure admission-search improvements are exhausted (0.25 % headroom).
