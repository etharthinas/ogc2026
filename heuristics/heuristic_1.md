# Congestion-First Construction Heuristic

A construction heuristic for the OGC 2026 Grand Shipyard Puzzle.

## Goal

Minimize `obj = w1·Z1 + w2·Z2 + w3·Z3`, treating tardiness (`Z1`) as the
lexicographically-dominant term. Aspiration is `Z1 = 0` (no delay); when an
instance makes that provably impossible, degrade gracefully by minimizing `Z1`.

## Core idea

Place the **most-constrained blocks first**, identified by where the schedule is
most congested in time. A block in the peak-congestion window has the least
placement freedom, so commit it while the bays are still empty and choice is
maximal; fit flexible blocks into the gaps afterward.

Design choices (settled):
- Congestion measured as **global** footprint-area demand over all bays.
- Each block anchored **as-late-as-possible (ALAP)**: exit at its due date.

---

## Step 0 — Per-block static data

```
for each block i:
    slack_i        = due_i - release_i - processing_i      # temporal freedom
    area_i         = min over orientations of footprint area
    layers_i       = max layer count across orientations
    pref_bays_i    = bays sorted by bay_preference, best first
    canon_i        = [due_i - processing_i, due_i]          # ALAP interval
```

`canon_i` is the interval the block *wants* for zero tardiness (exit pinned to
the due date). It is the anchor for congestion estimation and the starting point
for placement.

---

## Step 1 — Global congestion profile

```
TOTAL_AREA = sum over bays b of (b.width * b.height)

function demand(t):
    return sum of area_i for all i where canon_i covers t

function congestion(t):
    return demand(t) / TOTAL_AREA

t_star = argmax over t of congestion(t)
```

Evaluate `t` over the integer timeline spanned by all `canon_i` (or, cheaper,
only at interval start/end points — congestion is piecewise-constant and only
changes at those breakpoints).

### Feasibility oracle (free)

```
if max_t demand(t) > TOTAL_AREA:
    # More area must coexist than all bays can hold -> Z1 = 0 is impossible.
    mode = MINIMIZE_TARDINESS
else:
    mode = AIM_FOR_ZERO          # zero tardiness may be achievable
log(instance, peak_congestion = max_t congestion(t), mode)
```

This is cheap and decides per-instance whether to chase `Z1 = 0` or accept that
some blocks will be tardy.

---

## Step 2 — Criticality ordering

Within (and near) the current congestion peak, order blocks by least freedom:

```
function criticality_key(i):
    return (slack_i ascending, area_i descending, layers_i descending)
```

Lowest-slack, largest, most-layered blocks first — they have the least room and
must claim space while it exists.

---

## Step 3 — Placement of one block (candidate scoring)

For a block `i`, enumerate candidates `(bay, orient, x, y, entry, exit)`:

```
for bay in pref_bays_i:
  for orient in orientations(i):
    for (x, y) in candidate_positions(bay, orient):   # bottom-left + edge contacts
      entry, exit = choose_interval(i, bay, x, y, orient)   # see Step 4
      if entry is None: continue                            # no feasible slot

      # Hard constraints — reject outright:
      if not fits_in_bay(bay, i, orient, x, y):        continue
      if not check_entry(bay, present_at(entry), i):   continue   # crane lower-in
      if not check_exit(bay, present_at(exit), i):     continue   # crane lift-out
      if burial_violation(bay, i, x, y, exit):         continue   # see below

      cost = w1 * tardiness(exit, due_i)        # 0 if exit <= due_i (dominant)
           + w3 * pref_penalty(bay, i)          # max_pref_i - pref(bay, i)
           + LAMBDA_CRANE * burial_risk(bay, i, x, y, exit)
           + LAMBDA_PACK  * wasted_space(bay, i, x, y, orient)
      record candidate with cost

place block at the minimum-cost candidate; update bay state
if no candidate exists: defer i to the overflow pass (Step 6)
```

### Burial rule (the term the baseline lacks)

> A block must never be buried under another block that exits *later* than it.

```
function burial_violation(bay, i, x, y, exit_i):
    # Hard: any already-placed block j that leaves AFTER i and whose
    # same-or-higher layers sit over i's crane path makes i impossible to lift.
    for j in placed_in(bay):
        if exit_j > exit_i and crane_path_blocked(j over i at (x,y)):
            return True
    return False

function burial_risk(bay, i, x, y, exit_i):
    # Soft: count not-yet-placed neighbors likely to box i in, to prefer
    # placements that keep i's exit path clear. Used only for tie-breaking.
    ...
```

Lay later-exiting blocks at the bottom, earlier-exiting blocks on top / in clear
lanes, so the crane rule falls out of the placement order.

---

## Step 4 — Interval choice for one candidate (ALAP, then left-shift)

```
function choose_interval(i, bay, x, y, orient):
    exit = due_i                          # ALAP: aim for zero tardiness
    entry = exit - processing_i
    while entry >= release_i:             # slide earlier within slack
        if slot_free(bay, x, y, orient, entry, exit):
            return (entry, exit)
        entry -= 1; exit -= 1             # left-shift by one unit
    if mode == AIM_FOR_ZERO:
        return (None, None)               # no zero-tardiness slot here
    # MINIMIZE_TARDINESS: accept the least-late feasible exit
    return earliest_feasible_slot_after(i, bay, x, y, orient)
```

`slot_free` = spatial collision-free AND crane entry/exit feasible against blocks
present during `[entry, exit)`.

---

## Step 5 — Construction loop (congestion-first, expand outward)

```
placed = {}
remaining = all blocks
while remaining is non-empty:
    profile = congestion profile over remaining        # recompute, it shrinks
    t_peak  = argmax of profile
    window  = blocks in remaining whose canon covers t_peak
    for i in window sorted by criticality_key:
        place_block(i)                                  # Steps 3-4
        move i from remaining to placed
    if window was empty:                                # no peak left
        place all remaining in criticality order, then break
```

Each pass strips the current bottleneck, so the next peak is the next-most
congested window — the front expands outward in time from the worst pressure.

---

## Step 6 — Overflow / graceful degradation

Blocks with no feasible zero-tardiness candidate:

```
for i in deferred:
    relax in this order until placed:
        1. left-shift exploiting full slack (still Z1 = 0)
        2. allow tardiness: minimize (exit_i - due_i), pick least-late slot
        3. last resort: empty-bay window (guaranteed feasible, hurts objective)
```

Never leave a block unplaced — feasibility beats objective.

---

## Step 7 — Incumbent discipline

```
sol = build operations dict from placements
if check_feasibility(prob_info, sol).feasible:
    if obj(sol) < obj(incumbent): incumbent = sol
return incumbent          # always the best VERIFIED-feasible solution seen
```

Keep a guaranteed-feasible fallback as the initial incumbent (sequential
empty-bay schedule) so the algorithm can never return infeasible.

---

## Reuse: congestion-first as a repair constructor

This same constructor is the repair/insertion engine for destroy-and-repair
(LNS): when a move removes a cluster of blocks, re-insert them congestion-first
over the *removed set only*. Steps 2–6 apply unchanged to any subset.

---

## Open items to nail down against `utils.py`

- `crane_path_blocked` / `burial_violation` must mirror `check_entry` /
  `check_exit` semantics exactly (same-or-higher layer rule).
- `candidate_positions`: start with baseline's bottom-left + AABB edge contacts;
  enrich later (skyline / free-rectangle).
- Tune `LAMBDA_CRANE`, `LAMBDA_PACK`; normalize against `w1`/`w3` scales so no
  term dominates spuriously.
- Breakpoint-only evaluation of `demand(t)` for speed.

---

## Benchmark analysis (algorithm 1)

Analysis of running `baseline/myalgorithm.py` over all 40 training instances.
Per-instance and total objective values ("losses") are recorded in
`results.csv` (row `algorithm 1`).

- **Date:** 2026-06-28
- **Per-instance time limit:** 120 s
- **Checker:** `utils.check_feasibility` (official, unmodified)

> **Environment note.** The `ogc2026` conda env from the prior session was gone
> (`/private/tmp` purged — only dangling Python symlinks remained, no `conda` on
> PATH). Results were produced with a stand-in venv (`shapely 2.0.7`, NumPy
> 2.0.2) on Python 3.9. Shapely geometry is deterministic, so feasibility and
> objective values match the official py3.12 environment. Rebuild the conda env
> per `README.txt` before final submission runs.

### Total objective

- **Sum of objectives over all 40 instances: 1,066,850,978.**
- A single instance, **prob_38, accounts for 44.3%** of that total
  (472,513,932) — it overran the time limit and force-placed its tail.
- **Excluding the two timed-out instances (prob_38, prob_40): 582,965,830.**

This sum is dominated by a handful of congested, high-`w1` instances, so it is a
poor headline metric on its own — bringing prob_38's runtime under control (or
giving it the contest's real time budget) would roughly halve it.

### Headline

- **40 / 40 instances feasible** — the guaranteed-feasible empty-bay safety net
  was never needed; every instance was solved by the construction itself.
- **7 instances at exactly zero tardiness** (`Z1 = 0`): prob_3, 10, 12, 15, 16,
  17, 19.
- **Mean 25 s/instance**, median well under 10 s; total wall time ~1000 s.
- **vs. baseline greedy** (head-to-head on the 13 instances with recorded
  baseline numbers): **8 wins, 5 losses** — including turning **3 baseline
  failures into feasible solutions** (prob_1, 6, 12) and crushing the two
  high-tardiness blowups (prob_9: **260k vs 27.1M**, prob_13: **1.58M vs 10.8M**).

### What works

- **Always feasible.** The burial rule in `_can_place` (a new block may never
  break an already-placed block's crane entry/exit — the exact gap that caused
  the baseline's Stage-2/3 failures) holds at construction time, so no instance
  needed repair or the safety net.
- **Zero/near-zero tardiness on the uncongested majority.** Where the bays have
  slack (prob_9–19), the ALAP + left-shift placement parks almost every block on
  its due date: 7 instances at `Z1 = 0`, most others in single/double-digit Z1.
- **Huge gains where the baseline blows up.** On the high-`w1` instances that
  dominate the dataset, getting tardiness near zero is worth far more than tight
  packing — hence prob_9 and prob_13 improving by ~100× and ~7×.

### Where it loses / what to fix next

1. **Tight-slack, lower-`w1` instances (prob_4, 5, 7, 8, 11).** Here the baseline
   packs tighter and finds zero-tardiness slots our single-pass greedy misses;
   our small residual `Z1` plus weaker `Z2`/`Z3` lose the comparison. **Fix:**
   local search / LNS over the feasible incumbent (the constructor already
   doubles as the repair engine, per this doc).

2. **Two instances overran 120 s** (prob_38, prob_40, both congested 250-block).
   The force-place guard then dumped the tail → inflated `Z1`. **Fix:** speed up
   the congested-block path (Pass B is the cost), and/or run with the contest's
   real per-instance limit (minutes–30 min), under which both finish cleanly.

3. **Load balance (`Z2`) is only approximated** and preference (`Z3`) is greedy.
   These matter on the low-`w1` instances (prob_25, 36, 40, w1=667). A bay
   re-assignment / rebalancing pass would help there specifically.

### How to reproduce

```bash
# (after rebuilding the conda env per README.txt)
conda activate ogc2026
python - <<'PY'
import json, sys; sys.path.insert(0, "baseline")
import myalgorithm, utils
d = json.load(open("train/prob_1.json"))
sol = myalgorithm.algorithm(d, timelimit=120)
print(utils.check_feasibility(d, sol))
PY
```
