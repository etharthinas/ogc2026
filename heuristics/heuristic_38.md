# Heuristic v38 — TAIL COVERAGE + LOTTERY + DIALECT EPOCH

Loop directive (2026-07-20): "Critique the current SOTA model, and find
inefficiencies. Then implement radical changes via evolve.md protocol in
order to drop loss. Think broadly, and not greedily."

Frontier: v37 = 124,149,848 (@900s row, myalgorithm.py). The v37 epoch closed
with exact joint-neighborhood optimality certificates on the giants (38/27):
the remaining ~14M ordering+density gap is unreachable from the champion
basin at any tractable scope. So this epoch does NOT re-attack the certified
giants' neighborhoods; it attacks what the certificates DON'T cover.

## Critique of v37 (the inefficiencies found)

1. **The order tail's non-forced gate is DEAD CODE.** `_tail37_order` contains
   a non-forced gate (w1 >= 6000 + tardy present), but its only call site is
   inside the `if _forced:` branch of the verify loop. The non-forced path
   (merge tail) never calls it. Consequence: the 8 non-forced cells in 21-40
   — {21, 22, 24, 28, 29, 34, 35, 36}, combined banked mass ~10.6M, six of
   them at w1 = 13,333/unit — have NEVER been touched by the only mechanism
   that has produced verified wins since v25.
2. **Forced cells 25 and 40 were banked from v36 without ever being measured
   under v37.** Both are forced (w1=667), so the tail WOULD fire there; the
   row simply carries stale cells. prob_40 = 2,300,281 banked.
3. **Band coverage is top-2 only** (`_t37_pick_bands` k=2), while the offline
   mid-tier presence sweeps that found prob_37 = −41,190 needed 3 accepts
   across bands (apply-and-continue). Forced giants leave ~250s of the 900s
   budget unused (prob_38 finished at 633s).
4. **The w1 >= 6000 gate points the wrong way.** Measured: LOW-w1 instances
   hold MORE reachable order units (prob_37, w1=3333: 12 units; prob_33,
   w1=6667: 1 unit). The gate should be "tardy queue exists", not "units are
   expensive".
5. **Session-lottery variance is harvested by nobody.** prob_37 basin swing
   +107k, prob_32 −54k across sessions; v37 epoch flagged an in-algorithm
   second seeded race as the one untested legitimate lever.

## Arms

### 38a — Tail coverage completion [THIS ITERATION]

myalgorithm_38.py = myalgorithm_37 (== myalgorithm.py) + three changes:
- Call `_tail37_order` on the NON-FORCED path, after `_merge_tail`, on the
  post-merge champion, with a fresh official check as base. Min-wins,
  official-gated, post-race: zero displacement risk by construction.
- Drop the `w1 < 6000` refusal in the non-forced gate (keep "tardy present"
  and "remaining >= 120s").
- Widen bands k=2 → k=6 (per-band budget sharing already deadline-guards;
  on the certified giants extra bands prove +0 and cost only idle overflow).

Spot plan @900s serial (mass-ordered): 28, 40, 34, 21, 35, 22, 24, 29, 25,
36, then 37 (band-widening bonus check). Non-forced cells are historically
byte-deterministic → any strict improvement is bankable; unchanged cells
must come back byte-identical (regression guard).

Kill: no cell improves → coverage closes with byte-identity certificates.

### 38b — Overflow second-seeded race (lottery harvest)

Offline probe FIRST: standalone capped race (~240s, distinct seed) on
prob_37/32 vs banked. Only if a short race ever lands within/below the
banked basin does an in-algorithm overflow race make sense at 900s.
Kill: 3 seeds on both instances, never within −0 of banked.

### 38c — Admission set-packing dialect [RADICAL ARM]

The dispatcher admits ONE best block per free hole; the certificates say the
champion's realized geometry is the binding constraint. Attack the dialect at
its source: at each burst admission event, solve a small exact set+position
CP-SAT over the queued cohort for the CURRENT free region (admit k blocks
jointly, e.g. two smalls over one medium). Standalone single-worker ladder on
38/27 (37b harness pattern: w=0 ≡ stock byte-identity check first).
Kill: raw single-worker build never beats the stock analogue on both giants.

## Results

### 38a spot bench (2026-07-20, @900s serial; machine 17% load, no foreign
memory hogs; bash wrapper externally killed mid-run after 7 cells)

| cell | banked (v37 row) | v38 measured | delta | note |
|---|---|---|---|---|
| 28 | 3,565,230 | 3,565,230 | 0 | tail ran (obj1=198 units), no wins — coverage certified |
| 40 | 2,300,281 | 2,299,885 | **−396** | first-ever v37-tail measurement (was banked from v36) |
| 34 | 1,978,590 | 1,978,590 | 0 | byte-equal |
| 21 | 1,380,772 | 1,355,109 | **−25,663** | biggest 38a win; first tail contact ever on this cell |
| 35 | 1,346,898 | 1,346,898 | 0 | byte-equal |
| 22 | 918,798 | 918,798 | 0 | obj1=0 → tail correctly gated out |
| 24 | 643,943 | 643,943 | 0 | byte-equal |
| 22 | 934,883 | 918,798 | **−16,085** | obj1=0 → TAIL GATED OUT (see below) |
| 29 | 557,496 | 557,793 | **+297** | obj1=0 → TAIL GATED OUT (see below) |
| 25 | 338,322 | 336,988 | **−1,334** | forced, first v37-tail measurement |
| 36, 37 | | | | still running |

(Correction: an earlier interim note compared prob_22 against the
"algorithm 33 final" row instead of the v37 row. Numbers above are all
vs the v37 row.)

Raw net over the 9 measured cells: **−43,181**.

### THE ATTRIBUTION PROBLEM (2026-07-20) — non-forced cells are NOT
deterministic, and the two biggest swings are unattributed

prob_22 (−16,085) and prob_29 (+297) BOTH have obj1 = 0, so the order
tail's tardy-present gate refuses them: **the 38a mechanism never ran on
either cell**. Their deltas are therefore pure session-lottery variance,
not mechanism. This falsifies the epoch-open assumption that "non-forced
cells are historically byte-deterministic → any strict improvement is
bankable". It also means prob_21's −25,663 (obj1=73, tail COULD have
fired) is not yet attributable either — it needs a same-day v37 control,
exactly as the v36 prob_37 nonreproducible-cell episode taught.

LAW (extends the v37 reproducibility discovery): session-state basin
sensitivity is NOT confined to forced instances. Non-forced cells with a
merge tail swing too. Cross-version cell comparison requires a same-day
control on ANY cell that moved, forced or not.

Next: same-day v37 controls on the 5 moved cells {21, 22, 29, 25, 40} to
separate mechanism from lottery before anything is recorded as a v38 row.
Cells that came back byte-identical (28, 34, 35, 24) need no control —
identity is self-certifying.

### Bench completion + CONTROL VERDICTS (2026-07-20)

Final two v38 cells: prob_36 = 188,270 (byte-equal), prob_37 = 5,807,047
(row banked 5,770,494 → +36,553). Note 5,807,047 is EXACTLY the number
heuristic_37 recorded as v36's honest same-day control for prob_37 — the
cell the v37 epoch already flagged as the nonreproducible one. Band
widening k=6 bought nothing there; the session simply landed the honest
basin. This is a third independent sighting of the same value on that
cell and reinforces that the v37 row's 5,770,494 is a lucky roll, not a
reproducible cell.

HARNESS BUG (recorded so it isn't repeated): the control script guarded
with `while pgrep -f "_v38_verify.py"` — `pgrep` does not match the
Windows python process list under git-bash, so the guard fell through
immediately and controls for prob_21/22 ran CONCURRENTLY with the v38
prob_36/37 runs. Machine-load law violated. Both affected controls are
still usable (load can only hurt a control, and both reproduced exactly),
but 29/25/40 controls run clean after the bench drained.

| cell | v37 control (same-day) | v38 | verdict |
|---|---|---|---|
| 21 | 1,380,772 (= banked exactly) | 1,355,109 | **−25,663 ATTRIBUTED to 38a** — control reproduces the banked cell to the unit, v38 beats it |
| 22 | 918,798 (= v38 exactly) | 918,798 | **stale row artifact.** Both versions land 918,798 today; the v37 row's 934,883 is not reproducible. Real gain vs the recorded row, zero mechanism credit |
| 29, 25, 40 | running clean | | pending |

Standing verdict: 38a's dead-gate fix has ONE hard-attributed win
(prob_21, −25,663, on a cell no tail had ever touched) plus a recorded-row
correction on prob_22. The epoch's more durable output is methodological:
two of the three "wins" a naive read would have banked were row staleness
or lottery.
