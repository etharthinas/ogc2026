Goal: total loss over the training sets in train/ should be under the goal number.

FOLDER-STRUCTURE: under heuristics/ , list in plain text what each heuristic's logic is.
under baseline/ , list the python files - incrementally from myalgorithm1.py etc.
in results.csv, write down in numbers what the losses were for each problem set and what the total was.

0. CONTEXT: read CONTEXT.md and figure out what the problem is.

ITERATE:
1. DIAGNOSE: find where the loss actually is before planning anything.
2. PLAN: look at the previous algorithm in heuristic_n.md and its losses, and plan THREE different
   ways you could improve. Write that as heuristic_x.md (x is the version number)
3. EXECUTE: incorporate those changes into a next myalgorithm_x.py
4. TEST: run the algorithm against the training sets and figure out the losses.
5. RECORD: record the numbers and your analysis of failure to results.csv and heuristic_x.md.
6. STORE: commit and push to github. if SOTA, overwrite myalgorithm.py with a self-contained
   version as well, and keep the previous entry point for rollback.

ITERATE until goal is met.

-------------------------------------------------------------------------------
PRINCIPLES
-------------------------------------------------------------------------------

DIAGNOSE BEFORE OPTIMISING
- Break the loss down by objective term first, then break the dominant term down by MECHANISM.
  One measured mechanism can eliminate a whole family of ideas in a single step.
- Work only where the money is. Cells differ in size by orders of magnitude.

AUDIT THE ENGINE, NOT ONLY THE SEARCH
- "This lever is dead" and "N is unreachable" are claims about the current implementation's basin,
  never about the problem itself. Re-test them whenever the implementation changes.
- Compare what the code BELIEVES against ground truth. A systematic gap is a bug, not a tuning
  opportunity -- and bugs pay far better than tuning.
- When an outside signal contradicts the internal story, trust the outside signal and hunt a defect.

THROUGHPUT IS PART OF THE ALGORITHM
- A strictly more accurate model can lose badly if it is slower: search that runs out of time never
  reaches its basin. Measure cost per operation alongside quality.
- Prefer applying expensive machinery only where it changes a decision, rather than everywhere.

GATE ON THE EXACT TRIGGER
- Fire expensive repair on the event that actually costs objective, not on a proxy for it. Proxies
  both over-fire and under-fire.

TUNE, AND EXPECT THE OPTIMUM TO MOVE
- Sweep every new threshold; never ship the first value that works. Effects are usually unimodal --
  too little does nothing, too much starves something else.
- The best value often depends on instance properties, so make it adaptive and verify per class.

DISTRUST RELAXED BOUNDS
- A bound that drops constraints will promise headroom that does not exist. Before building on one,
  test its cheapest possible realisation on a single cell.

MEASUREMENT DISCIPLINE
- Only paired, back-to-back A/B counts. Never compare a fresh run against a number banked in another
  session; keep the machine quiet and run no other work of your own during a bench.
- Run-to-run variance on the big cells can exceed the improvement you are chasing. Repeat any
  decision-sized measurement before believing it.
- Killed or starved runs leave plausible-looking invalid rows. Sanity-check elapsed time and shape
  before trusting a result.
- If the new arm ran under worse conditions than the reference, report the number as a floor.

KEEP CHANGES SAFE AND REVERSIBLE
- Put every new mechanism behind a default-off switch, with the old path unchanged when it is off.
  That keeps "is this change responsible?" a one-variable question.
- Verify any geometry or feasibility shortcut against the official checker primitives, not against
  your own reasoning. Never modify the checker; whatever it does is ground truth.
- Keep the submission entry point dependency-clean and verify it actually runs after promotion.
  Respect the evaluation environment's limits, which are smaller than the development machine's.

RECORD NEGATIVE RESULTS
- Write down what was measured, not what was believed. A documented dead end is worth as much as a
  gain: it is what stops the next session from paying for it twice.
