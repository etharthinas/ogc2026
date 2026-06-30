# Heuristic v6 — enriched candidate positions (FAILED EXPERIMENT)

## Hypothesis
The ~8 congested instances that v5's improver can't move (prob_23/27/31/39/26/
28/30/32) are packing-limited. Adding LEFT and BOTTOM edge-contact candidate
positions (block-right-against-placed-left, block-top-against-placed-bottom, plus
left/bottom alignment) to `_candidate_positions` should enable denser coexistence
in the congested window and lower tardiness.

## Result — REGRESSION, discarded
Probe @150s/3w on the stuck instances:

| instance | v5      | v6 (enriched) |
|----------|---------|---------------|
| prob_23  | 8.67M   | 22.07M        |
| prob_27  | 52.40M  | 124.22M       |
| prob_31  | 19.21M  | 43.85M        |

v6 is ~2.4× WORSE everywhere. Why:
- ~3× more candidate positions per block ⇒ each placement is much slower ⇒
  construction self-throttles to the cheap path earlier AND the improver does far
  fewer rounds in the same wall-clock.
- The position list is tried bottom-left-first up to a cap (24 construction / 14
  improver). The new low-coordinate contacts front-load the list, so the cap now
  cuts off BEFORE reaching the positions the tuned v5 set relied on ⇒ it explores
  different, worse spots within budget.

## Takeaway
The v5 bottom-left + right/top-contact set is already well-tuned; naive
enrichment backfires on both speed and the cap. The real geometric lever (if
pursued) needs a *careful* dense packer (skyline / free-rectangle with a good
candidate ranking, not raw contact enumeration) plus crane-aware placement, and
must stay fast enough to preserve improver round count. High effort, uncertain
payoff, and bounded below by the forced-tardiness floor (~100M+ total; see
results.csv relaxed LB). **Best version remains v5 (`myalgorithm_5.py`, 350M).**
</content>
