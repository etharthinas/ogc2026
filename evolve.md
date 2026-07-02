Goal: total loss over the training sets in train/ should be under the goal number

FOLDER-STRUCTURE: under heuristics/ , list in plain text what each heuristic's logic is.
under baseline/ , list the python files - incrementally from myalgorithm1.py etc.
in results.csv, write down in numbers what the losses were for each problem set and what the total was.

0. CONTEXT: read context.md and figure out what the problem is.

ITERATE:
1. PLAN: look at the previous algorithm in heuristic_n.md and its losses, and plan THREE different ways you could improve. Write that as heuristic_x.md (x is the version number)
2. EXECUTE: incorporate those changes into a next myalgorithm_x.py
3. TEST: run the algorithm against the training sets and figure out the losses.
4. RECORD: record the numbers and your analysis of failure to results.csv and heuristic_x.md.
5. STORE: if SOTA, overwrite myalgorithm.py with a self-contained version, and commit and push to github.

ITERATE until goal is met.