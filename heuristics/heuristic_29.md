# Heuristic v29 — SEQUENCING IN THE RIGHT SPACES (goal < 110,000,000; frontier = v25 cells 124,581,895)

Departure: v25 (= v28 cells; 28a/28c flat, 28b regressive). Remaining ask:
−14.6M. Mass: prob_38 36.35M + prob_27 24.97M = half the total; relax@0.7
obj1 headroom alone is ~18M (38) + ~14.8M (27) at w1=13,333.

## What v28 proved (2026-07-16, heuristic_28.md Results)

1. **Improver-level escapes can NEVER touch prob_38**: its improve slices are
   round-starved (3–17 rounds, since_o1 ≤ 16) even at x3.56 scan speed. On
   27-class, escapes fire and lose. The improver is the WRONG LAYER for the
   sequencing lever on giants.
2. **Round-stealing regresses** (28b: +1.9M on 38): every giant improver round
   is descent-critical.
3. **The W3 first-seed slot is free-but-worthless** (26b + 28c byte-flat
   twice): its seed never wins the obj-gated race. Test mechanisms in winning
   pipelines or not at all.
4. Sequencing verdict stands (ledger_27_diag): 0.25–0.29% placement headroom,
   100% of obj1 is burst entry-queue delay; the lever is admission ORDER.

Therefore v29 moves the sequencing search OUT of the improver and INTO the
spaces that own the order: the dispatcher's admission sequence (A, C) and the
polish-budget allocation that decides how deep each basin descends (B).

## Improvement A — order-forced replay search over the realized admission sequence (primary)

New search space: the winning giant build's REALIZED entry order (the sequence
in which blocks were actually admitted). Mechanism:
1. Run the current W1/W2 giant pipeline unchanged; capture the champion's
   realized admission sequence S (block ids in entry order).
2. Add an ORDER-FORCED dispatch mode: `_dispatch_construct(order=S')` admits
   strictly in the order of S' — at each event the next unadmitted block in S'
   is tried first (full scan + near-miss); bounded skip-ahead k≤3 if it cannot
   place anywhere (skipped block retried next event; hard fallback to ATC if
   the forced queue stalls > k).
3. Perturb: S' = S with targeted swaps — pick a tardy block i (tardiness-
   weighted), move it earlier past predecessors j whose due-slack exceeds
   their tardiness gain (the resident↔queued 2-exchange at the ORDER level,
   where 28b tried it at the placement level and lost to round-starvation);
   also try block-of-8 reversals around burst peaks.
4. Each replay is a full cheap build (x3.56 scans; a giant dispatch is ~1-3s);
   accept by objective, min-wins with the portfolio as usual. Budget: replace
   the proven-worthless W3 first-seed slot (finding 3) with a replay-search
   stream seeded from the inbox champion.
Spot {38,27}. Keep if ≥ −100k. Kill: flat/regressive after a swap-policy
sweep (adjacent-swap vs pull-to-release).

## Improvement B — pooled deep polish for giants (top-k basins)

The 3–17-round slices on 38 mean DESCENT ITSELF is truncated — not just
escapes (since_o1 ≤ 16 says the last improvement was still recent when the
deadline hit). Keep every build byte-identical; change only polish-budget
allocation on giants (n ≥ 250): instead of improving each lottery candidate
briefly, rank candidates by raw objective and pool the polish budget into the
top-2 (e.g. 70/30), giving slices of 100+ rounds. Min-wins portfolio gating
is unchanged — worst case the pooled polish returns the same best. Tension
with the "feed basin diversity to deep polish" law is acknowledged: on 38
there IS no deep polish today, so the law's premise (deep polish exists) is
unmet; this creates it. Spot {38,39,27}. Kill: flat/regressive → giants'
polish depth is not the binding constraint, record and stop re-pacing polish
forever.

## Improvement C — fluid-order dispatch (relaxation order as the seed sequence)

The relax@0.7 experiment produced obj1 ≈ 1219 (38) / 615 (27) — its entry
ORDER is a certificate of a much better sequencing. Recompute the fluid
relaxation (area-capacity bays at 0.7 density, no geometry), extract its
entry order, and run ONE order-forced dispatch (mechanism from A) per giant
with that order, as an extra lottery ticket in the W2 giant rotation
(APPEND, never prepend — ticket law). Distinct from the failed v22/23 tspec
experiments: those gated admission TIMES (blocks waited for targets); this
forces only relative ORDER and still admits greedily-early. Spot {38,27}.
Kill: flat → the fluid order is not realizable under true geometry/crane
constraints; record the realized-vs-fluid order edit distance for the ledger.

## Ladder

- 29a = A. Implement order-forced mode + replay stream in the W3 slot.
  Spot {38,27} @600s vs banked; prob_1 @60s guard.
- 29b = B alone (independent file). Spot {38,39,27} @600s.
- 29c = C on top of surviving A-machinery (shares the order-forced mode).
  Spot {38,27} @600s.
- Combine survivors; eligible-8 @600s; full-40 @600s row `algorithm 29`;
  promote if < 124,581,895; goal check < 110,000,000.

## Results

### 29a spot (2026-07-16) — flat, with a signal

myalgorithm_29a.py (order-forced dispatch + replay-search stream in the W3
slot; ORDER_LOOKAHEAD=3, ORDER_STALL=8, rng 9291). prob_1 @60s guard:
18,357 = banked. prob_38 = 36,351,493, prob_27 = 24,972,962 — both
byte-flat totals. BUT the OGC_DEBUG telemetry shows prob_27 polish slices
reaching **obj1 = 1725** (banked = 1726) three times — the first sub-banked
tardiness basin ever sighted on 27 — losing the min-wins race on obj2/obj3.
Reading: the order-forced machinery soundly realizes perturbed admission
sequences at competitive quality, but LOCAL perturbations of the realized
order move single tardiness units (same local-optimum wall as the improver,
one level up). The escalation is a GLOBALLY different order → 29c
(fluid-relaxation order), which the 1725 sighting de-risks. Bench-ops note:
two background-task kills orphaned one 29a spot run (parent dead, workers
spinning, empty log ~45 min); benches now launch detached via Start-Process
(see env memory).

### 29b spot (2026-07-16) — flat; polish depth is NOT the binding constraint

myalgorithm_29b.py (pooled 70/30 top-2 polish on giants, re-anchored slice
boundaries — v28's absolute cp_at=0.62w left late-finishing giant builds a
near-empty first improve leg). prob_1 @60s guard: 18,357 = banked.
prob_38 = 36,351,493 and prob_39 = 8,389,519 byte-flat (prob_27 leg is
gate-excluded, coupling check only). Even with real descent rounds in leg 1
and a fresh 30% slice on the runner-up basin, nothing moved. Combined with
28a/28f: the v25 giant incumbents are locally optimal against BOTH deeper
descent AND randomized basin-hops — per the ledger_27 verdict the residual
mass is reachable only through a globally different admission SEQUENCE.
Record instruction honored: stop re-pacing polish forever.

### 29c spot (2026-07-16) — flat; experiment invalid (loader, not hypothesis)

myalgorithm_29c.py (fluid-order W2 ticket from a NEW greedy ATC area-
capacity loader @0.7). prob_1 guard: 18,357 = banked. Totals byte-flat
(38: 36,351,493 / 27: 24,972,962). Telemetry says WHY, and it is not the
certificate hypothesis: the greedy loader's own relaxation tardiness is
4439 (38) / 3163 (27) — WORSE than the banked realized obj1 (2569/1726)
and nowhere near the CP-SAT certificates (1219/615, from `_plan_targets`,
which was never wired to an ORDER — v22/23 only ever gated TIMES with it).
Forcing a bad order realized bad builds (48.0M / 32.1M; mean_rank_delta
30.8 / 21.6) that min-wins correctly discarded. 29c tests the loader, not
the certificate → 29d re-derives the forced order from `_plan_targets`
(cap_frac=0.7, ≤6s CP-SAT budget, skip ticket on timeout).

### 29d spot (2026-07-16) — 38 flat, 27 REGRESSED to the fallback basin; ORDER-FORCING FAMILY DEAD

myalgorithm_29d.py (plan-order ticket from `_plan_targets` @0.7, ≤6s).
prob_38 = 36,351,493 flat; telemetry plan_obj1=2736 (6s CP-SAT can't reach
the 1219 certificate), realized_obj=63.0M, rank_delta=50.8. prob_27 =
**25,403,468 (+430,506)** — EXACTLY 28b's regression value; telemetry
plan_obj1=1334 (genuinely better-sequenced than banked 1726!),
realized_obj=35.2M (+41%), rank_delta=26.8.

Two conclusions:
1. **Order-forcing is dead.** Realizable admission orders live in a narrow
   neighborhood of the champion's order (29a: ±1 obj1 unit, competitive);
   geometry-blind orders — even ones the relaxation scores better (1334 <
   1726) — realize 30–75% worse because co-resident geometric compatibility
   is what the champion's order encodes. The relax@0.7 sequencing
   certificates (1219/615) are geometry-free mirages, same species as the
   19-era fluid LBs. Joint order+geometry is the only remaining escape
   class for the giants, and no tractable mechanism for it is known.
2. **NEW LAW — cross-worker race displacement:** prob_27 has two attractor
   basins: 24,972,962 (banked, W-race won) and 25,403,468 (fallback; 28b
   and 29d land there through UNRELATED mechanisms). Any latency added
   inside a worker's loop (29d's ≤6s CP-SAT solve; 28b's swap scans) shifts
   its island-inbox push timing and can flip the race. Min-wins does NOT
   protect against this. W2/W1 tail additions must be effectively free
   (sub-second, 29c-class) or run after the race is settled.

### Final: v29 == v25 cells (124,581,895). No promotion. Order-space,
polish-depth, and improver-escape families all measured dead in v28+v29.
Next: measure-first on the mid-tier {26,31,33,37,39} (~38.6M mass, never
diagnosed) — packing-bound or sequencing-bound? (mid_diag_driver.py)
