Goal: total loss over the training sets in train/ should be under the goal number.

FOLDER-STRUCTURE: under heuristics/ , list in plain text what each heuristic's logic is.
under baseline/ , list the python files - incrementally from myalgorithm1.py etc.
in results.csv, write down in numbers what the losses were for each problem set and what the total was.

0. CONTEXT: read CONTEXT.md and figure out what the problem is.

ITERATE:
1. DIAGNOSE (before planning anything -- see WHERE IS THE MONEY below).
2. PLAN: look at the previous algorithm in heuristic_n.md and its losses, and plan THREE different
   ways you could improve. Write that as heuristic_x.md (x is the version number).
3. EXECUTE: incorporate those changes into a next myalgorithm_x.py, behind a default-off switch.
4. TEST: paired A/B against the current best on the cells that hold the money (see MEASUREMENT).
5. RECORD: record the numbers AND your analysis of failure to results.csv and heuristic_x.md.
   Negative results are the valuable ones -- write down what was measured, not what was believed.
6. STORE: commit and push to github. if SOTA, overwrite myalgorithm.py with a self-contained
   version as well, and keep the previous entry point as myalgorithm_<prev>.py for rollback.

ITERATE until goal is met.

===============================================================================
LESSONS PAID FOR IN MEASUREMENT TIME (2026-07-23, jv17: 122.73M -> 118.30M)
Read this section before proposing an improvement. Every rule below is here
because breaking it cost hours.
===============================================================================

WHERE IS THE MONEY -- diagnose before you optimise
- Decompose the loss FIRST: per instance, w1*Z1 vs w2*Z2 vs w3*Z3. One session found w1*Z1 = 83%,
  w3*Z3 = 17%, w2*Z2 = 0% -- half a day had been aimed at the 0% term before anyone checked.
- Then decompose the DOMINANT term by MECHANISM, not by instance. For tardiness the question is
  "waiting to get in" vs "slow once in": measured from the solution dumps, 100% was entry delay
  and 0% was lingering. That single number said the bottleneck was admission, i.e. packing, and
  killed every scheduling-side idea in one step.
- Sort cells by pool size and only work where the money is. Cell 38 alone is ~30% of total loss;
  cells 1-20 together are under 1%.

AUDIT THE ENGINE, NOT ONLY THE SEARCH
- "Lever X is dead / <N>M is foreclosed" is a statement about the CURRENT IMPLEMENTATION's basin,
  never about the problem. Seven lever families had been proven dead; the real bug was one line of
  geometry: the raster marked a unit cell occupied when a polygon merely TOUCHED it, so every
  fractional-coordinate block was inflated by up to a cell per edge. Bays that measured 48-70%
  full in true polygon area were reported "full", and blocks queued against phantom occupancy.
- Cheap check that found it: compare what the engine BELIEVES against ground truth. Compute the
  true peak co-resident polygon area per bay from a dumped solution and compare with the engine's
  own occupancy measure. A large systematic gap is a bug, not a tuning opportunity.
- When an external signal contradicts the internal story (e.g. "we are 130th" vs "this is optimal"),
  trust the external signal and go looking for a defect.

THROUGHPUT IS PART OF THE ALGORITHM
- A strictly more accurate model can lose badly. Rasterising everything at 1/4 resolution was
  correct and sound, but 6.5x slower per scan -- prob_38 collapsed from 36.8M to 198M because the
  search no longer had time to find its basin. The fix was not "make it faster" but "apply the
  expensive machinery only where it changes a decision": keep the cheap path verbatim, and consult
  the precise one only when a block is starving for anchors.
- Always measure cost/scan (or cost/iteration) alongside quality. If a change is >2x slower on the
  hot path, assume it loses on the big cells until proven otherwise.

GATE ON THE EXACT TRIGGER, NOT A PROXY
- Expensive rescue/repair should fire on the event that actually costs objective (an admission that
  FAILED = a unit of tardiness about to be paid), not on a proxy ("fewer than K candidate anchors").
  Proxies both over-fire (wasting the budget) and under-fire (missing the case you built it for).

TUNE, AND EXPECT THE OPTIMUM TO DEPEND ON INSTANCE SIZE
- Sweep every new width/threshold parameter; do not ship the first value that works. The rescue
  width sweep on one cell: 8/12/96 -> +210k, 32/24/192 -> +1.79M, 128/48/512 -> +2.58M,
  always-on -> +1.73M. Unimodal: too little does nothing, too much starves throughput.
- The optimum REVERSED with instance size (n=250 wanted wide, n=200 wanted narrow) -- so make such
  parameters adaptive to an instance property, and verify on one cell of each class.

BEWARE PHANTOM HEADROOM FROM RELAXED BOUNDS
- A relaxation that drops geometry will promise money that does not exist. A CP-SAT screen valued
  the preference pool at 13.5M; under real geometry ~95% of it was unreachable (single-block moves
  recovered 20-30k per cell, and opening the existing group-relocation gate recovered exactly zero).
- Before building on a bound, test the cheapest possible realisation of it on ONE cell.

MEASUREMENT DISCIPLINE (this is where results get faked accidentally)
- ONLY paired adjacent A/B counts: compare.py runs both arms back to back, so machine load,
  thermal state and background work hit both equally. NEVER compare a fresh run against a number
  banked in results.csv from another session.
- Per-cell run-to-run variance on the big cells is larger than most improvements. Same module, same
  budget: cell 38 measured +2.58M paired but -37k in the full-40; 26 measured +724k then -58k;
  27 measured -15k then +452k. A single measurement of a big cell means almost nothing -- repeat
  the decisive one 2-3 times before believing a promotion-sized number.
- Machine must be quiet during a bench, and NO other CPU work of your own. If the machine is busy,
  paired A/B is still usable; single-shot rows are not.
- A killed or starved run leaves a plausible-looking but invalid row. Signatures: elapsed >> the
  time limit, obj3 exactly 0, or a total in the billions (empty-bay fallback). Check elapsed time
  before trusting any row, and re-run the cell.
- Report a floor, not a hope: if the new arm ran under worse conditions than the reference, say so
  and treat the number as conservative.

KEEPING CHANGES SAFE
- Every new mechanism goes in behind a default-off env switch, with the old path byte-exact when
  the switch is off. That makes "is this change responsible?" a one-variable question, and makes an
  A/B arm a one-line copy of the module with a different default.
- Soundness of a geometry shortcut must be verified against the OFFICIAL utils primitives, not
  against your own reasoning: take the placements the new code accepts and re-check them with
  utils.check_entry / check_feasibility. (For the subcell rescue: 16 accepted anchors, 0 violations.)
- Never modify utils.py. Anything the checker does is ground truth: it rounds x,y to int, reads the
  operations dict in insertion order, and sorts EXITs before ENTRYs within a tick.
- Submission entry point must import only stdlib + numpy + shapely + ortools + utils. No Gurobi or
  Xpress (the eval server has no licence) and no internet. Eval server: Ubuntu, 4 CPU cores, 16GB --
  local is 8 cores, so spot-check worker scaling at 4 before submitting.

HARNESS GOTCHAS
- Use bench.py / compare.py / run_full40.ps1. They hard-exit via os._exit; a bare `python -c` driver
  that calls algorithm() hangs at exit with its output still buffered (orphaned portfolio workers).
- run_full40.ps1 gives per-instance process isolation; without it the tail of a long batch corrupts
  timing-sensitive giant cells.
- Probe scripts must reset the module caches per instance (_reset_caches + _MREL.clear); they are
  keyed by block id, not by instance, so a multi-instance probe process silently produces garbage
  after its first instance.
- Full-40 single-shot at 750s is ~8h. Budget it as an overnight job, and prefer paired A/B on the
  money cells for day-to-day decisions.
