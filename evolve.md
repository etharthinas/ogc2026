Goal: total loss over the training sets in train/ should be under the goal number

FOLDER-STRUCTURE: under heuristics/ , list in plain text what each heuristic's logic is.
under baseline/ , list the python files - incrementally from myalgorithm1.py etc.
in results.csv, write down in numbers what the losses were for each problem set and what the total was.

0. CONTEXT: read context.md and figure out what the problem is.

ITERATE:
1. PLAN: look at the previous algorithm in heuristic_n.md and its losses, and plan THREE different ways you could improve. Write that as heuristic_x.md (x is the version number) -> Your job, try to think radically outside of the box -> YOUR JOB
2. EXECUTE: incorporate those changes into a next myalgorithm_x.py -> Delegate to Opus
3. TEST: run the algorithm against the training sets and figure out the losses. -> Delegate to Opus
4. RECORD: record the numbers and your analysis of failure to results.csv and heuristic_x.md. -> Delegate to Opus
5. STORE: commit and push to github. if SOTA, overwrite myalgorithm.py with a self-contained version as well. -> Delegate to Opus

ITERATE until goal is met.

Make sure to test efficiently as possible. (Efficiency as in measured in wall-clock time for each iteration)