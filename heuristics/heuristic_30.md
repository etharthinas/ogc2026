# Heuristic v30 — HEIGHT-AWARE ANTI-FRAGMENTATION PACKING (goal < 110,000,000; frontier = v25 cells 124,581,895)

Departure: v25 (= v28 = v29 cells). Remaining ask: −14.6M.

## The measurement this plan stands on (2026-07-16, diag_gaps26 + mid-tier diags, commit e673d7f)

1. **prob_26 is FRAGMENTATION-bound, height-wise** (diag_gaps26.py): burst
   layer-0 free fraction 0.481 (bays half empty) yet 87.5% of burst
   (sample,bay) moments have largest-free-rect < EVERY queued bbox. Median
   largest free rect = 23w x 7h vs median queued bbox 22w x 14h — width
   matches, HEIGHT collapses to half. Bays are shallow strips (168x16,
   132x21, 89x18); near-full-height residents guillotine them into thin
   horizontal bands. Crane-only blocking = 0.0% (38 collision vs 0 crane).
   Sliver mass (runs narrower than min queued width) = 26% of free cells.
2. Mid-tier classification: 31/33/39 saturated at dens0 0.64-0.72
   (giant-class, dead to current levers); 37 intermediate (0.57-0.63,
   lenient/strict gap 9x); 26 the half-empty anomaly (0.50-0.53).
3. ledger_27_diag on the GIANTS: "the residual ~25-35% floor is fragmentary
   or crane-poisoned" — the same fragmentation mechanism plausibly caps
   their effective density at ~0.7. Every bay in the eligible set is a
   shallow strip (16-27 tall).

Mechanism class never tried in 29 versions: PLACEMENT-SHAPE discipline that
minimizes the fragmentation an entry/exit leaves behind (all prior packing
levers were about FINDING anchors — near_k, exact scan — not about which
anchor leaves the healthiest residual space).

## Improvement A — height-utilization contact scoring (ticket family, primary)

Add a position-scoring variant to the dispatcher's anchor ranking
(`_order_cells` / score_pos): on shallow-strip bays, add
  frag_penalty(anchor) =
    alpha * (bay_H - block_h - neighbors_matched_h)   [height-waste at the top]
    + beta * (left/right contact height mismatch)     [guillotine misalignment]
i.e. prefer anchors where the block's TOP edge aligns with adjacent residents'
top edges (or the bay ceiling), and where short blocks nest beside
equally-short residents instead of cutting a tall free column. Deliver as
APPENDED W1/W2 lottery tickets (near_k-family pattern, the v25 playbook;
min-wins + append-only + sub-second scoring so no race displacement). Spot
{26,37} first (the anomaly class), then {38,39,27,31,33}. Keep if >= −100k
anywhere. Kill: flat on 26 after an alpha/beta sweep — then fragmentation is
not steerable at placement time and 30B/30C take over.

## Improvement B — height-class admission tie-break (cheap, composable)

Within the ATC admission order, break near-ties by HEIGHT DESC (taller
blocks first): full-height blocks claim wall/flush positions early; short
blocks fill the leftover bands late. Zero-cost reorder, dispatcher-side,
appended ticket variant (tspec-free). Spot {26,37}. Kill: flat both.

## Improvement C — band-repair destroy mode (improver-side, 26-class gate)

New destroy mode gated to LOW-DENSITY-burst instances only (burst dens0
mean < 0.60 measured at runtime is not available — gate statically on the
26-class signature: shallow bays AND w1-forced AND n<=200): pick the bay
with the most sub-height free bands at the peak-queue moment; destroy the
SHORT residents bordering the widest band (the guillotiners), repair with
height-matched reinsertion order. This is 28b's ejection idea but aimed by
the fragmentation diagnostic instead of tardiness, and gated off the
giants/round-starved instances entirely (28b's regression mechanism cannot
recur: prob_26's improve slices converge — it is not round-starved).
Spot {26} alone @600s. Kill: flat after one aim-policy sweep.

## Ladder

- 30a = A. prob_1 @60s guard; spot {26,37} @600s; if either banks, extend
  spot to {38,39,27,31,33}.
- 30b = B (independent ticket). Spot {26,37}.
- 30c = C. Spot {26}.
- Combine survivors -> eligible-8 @600s -> full-40 @600s row `algorithm 30`;
  promote if < 124,581,895; goal check < 110,000,000.

## Results

(pending)
