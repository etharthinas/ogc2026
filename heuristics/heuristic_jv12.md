# jv12 — giant merge-tail (goal <120M) — DEAD

Base: jv9 (SOTA). Idea: the merge-tail recombination (campaign's ONLY
positive-yield mechanism, −383k non-forced) was gated off for forced giants.
The capacity campaign gave the 8 giant workers between-run diversity (27
±425k); ~49s of parent "remaining" already exists after search_deadline. So:
ungate the merge for n≥250 forced giants + route the forced branch's feasible
winner through `_merge_tail` (official-verified, min-wins, wider 6s safety).

## Build
- `_merge_tail` gate: `_giant = _forced and n≥250 and OGC_GIANT_MERGE!=0`;
  fire on giants, keep non-giant forced byte-identical.
- Parent forced branch (was TOKEN-IDENTICAL, no merge): giants now call
  `_merge_tail` on the feasible winner; non-giant forced unchanged.
- safety 2.5→6.0s on giants (250-block feasibility check headroom).

## Diagnostic runs (OGC_DEBUG, @750s)
- **prob_39**: `[merge33] fired=True rem=47.8 cands=32 gain=0`, runtime 745s
  (time-safe). `best5=[8.41e6 ×5]` — top solutions identical.
- **prob_27**: `best5=[2.36e7 ×5]` — identical; pool deduped below the k≥3
  diversity gate (merge didn't fire). Drew the good basin 23,649,558 this run.

## Verdict: DEAD — NOT PROMOTED
The 8-worker giant portfolio **converges to a SINGLE basin per run** (best5
all identical on both giants). The between-run variance (27: 23.65M vs 24.07M)
is *which* basin the collective lands in — a coordinated lottery, NOT intra-run
diversity. The merge recombines solutions *within* one run, where there is
nothing to recombine: 39 had 32 distinct signatures but gain=0 (they differ
only in objective-neutral ways, and 47s is too short for a 250-block, 32-
placement CP-SAT to search anyway). This is the absorbing-fixed-point wall
proven at the recombination level.

The mechanism is time-safe and floor-safe (gain=0 → returns winner), but
neutral, and the 745s runtime on giants is uncomfortably close to the 750s
limit (risk on the larger prob_38). Not worth shipping. myalgorithm.py stays
jv9.

## Campaign-final conclusion
Every WITHIN-RUN structural lever is now measured dead: reclaim replica (jv11
neutral), racer/deaf (jv10 dead), giant-merge (jv12 dead). Only BETWEEN-RUN
draw multiplication (capacity, jv7–jv9) moved the needle (−3.0M, the biggest
cell wins of the lineage). The giants (61% of mass) converge intra-run and
only shift via a coordinated between-run basin lottery that min-wins already
exploits. <120M is foreclosed under construct→polish→merge: the honest single-
shot is 122.73M, the best-of-draws composed row is 121.47M, and closing the
remaining gap needs a non-polish solver (multi-day, high-risk) or winning
multiple independent giant basin-lotteries in one shot (probabilistically
negligible). SOTA deliverable: jv9.
