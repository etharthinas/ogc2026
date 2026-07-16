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

### 30a/30b spots (2026-07-16) — KILLED (fired-and-lost), plus a wiring law

myalgorithm_30.py (height-utilization contact scoring HMATCH_W=4 + tallfirst
tie-break, appended W1+W2 trios). prob_1 guard byte-exact. Spots byte-flat:
prob_26 = 8,551,513, prob_37 = 5,807,047. Sweep myalgorithm_30s.py
(HMATCH_W=12 + fire diagnostics) on 26: byte-flat again, with the decisive
telemetry:

- **W1-APPEND IS STRUCTURALLY DEAD on 26-class: `[w1 trio] ji=0
  rem=-0.3s`** — the W1 explorer's entire ticket budget is consumed by the
  v25 rotation before even the jitter tail runs (0 of 24 jitter draws!).
  Append-only tickets in W1 can never fire there. (The v25 near_k family
  won by HEADING the rotation — a promotion-time displacement, not an
  append.)
- W2 trio fired 3/3 (~13s/build, 153s spare) at both HMATCH_W=4 and 12 and
  LOST min-wins both times → anchor-level height steering, delivered
  through W2 dispatch+polish, cannot beat the incumbent basin.

Reading: under saturation pressure the dispatcher admits whatever fits
wherever it fits; marginal anchor-score nudges do not preserve tall bands
(every admission immediately consumes the best gap). Defragmentation likely
needs a RETROSPECTIVE move (eject the guillotiners) → 30c, or joint
restructuring beyond single-axis perturbation.

### 30c spot (2026-07-16) — flat; v30 series CLOSED

myalgorithm_30c.py (band-repair destroy: deterministic guillotiner ejection
at peak-queue t*, tallest-first hmatch reinsertion, gate = 26-only via area
ratio 3.62 vs cut 3.85; prob_27 byte-identity verified under deterministic
clock). prob_26 @600s = 8,551,513 byte-flat. The diagnostic-aimed
retrospective ejection also cannot beat the incumbent basin: destroyed
guillotiners re-place into the same shredded structure (or the repair's
obj-gate rejects the intermediate). prob_26's 48%-free-but-blocked
structure survives every move shape available to the improver.

### Final: v30 == v25 cells (124,581,895). No promotion.

Height-fragmentation is REAL (measured) but UNEXPLOITABLE with single-axis
moves: prospective anchor steering fired-and-lost (30a/b), retrospective
ejection flat (30c). The fragmentation is an emergent property of the
whole admission trajectory under queue pressure — like the giants'
sequencing, it resists everything short of joint restructuring.

Day tally (v28+v29+v30, 2026-07-16): TEN mechanisms measured across every
available axis — admission order (3 forms), improver escapes (2 calibs),
improver moves (2 aimed destroys), polish depth/pacing, seed slots,
placement scoring (2 weights) — ALL flat or regressive-reverted. The v25
incumbents on the eligible set are locally optimal against every
single-axis perturbation family known to this codebase.
