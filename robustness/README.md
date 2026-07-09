# robustness/ — hidden-instance readiness checks

Contest scoring is per-instance rank points with **−1 for any crash / timeout /
infeasible**, the hidden timelimit varies per instance ("a few minutes to half
an hour", undisclosed), and hidden instances need not sit near our 40 training
instances. These tools check the failure modes that the performance campaign
(heuristics/heuristic_19.md) does not cover. None of them touch the submission
path.

All numbers produced on a dev laptop are **robustness signals only** — official
results.csv rows still come from the quiet Windows bench machine @600s serial.

Run everything under the `ogc2026` conda env (see `../ogc2026_env_local.yml`
for the trimmed Mac dev env):

```bash
conda run -n ogc2026 python bench_scaling.py myalgorithm --probs 1,27,31,38 --limits 60,120,300
conda run -n ogc2026 python stress_test.py  myalgorithm --probs 1,27,38 --timelimit 60
conda run -n ogc2026 python mem_profile.py  myalgorithm --prob 38 --timelimit 120
```

| tool | question it answers | fail condition |
|---|---|---|
| `bench_scaling.py` | Does the solver return a feasible solution and stay inside ANY timelimit the server might pass (60s–…)? Does quality degrade gracefully as T shrinks? | non-feasible result, or wall time > T |
| `stress_test.py` | Do perturbed instances (bay sizes ±, slack squeeze, release jitter, w1 collapse, ±10% blocks) near the solver's branch gates (overload 0.44/1.05, n≥250) still run clean? Prints the instance-computed branch flags per variant so gate flips are visible. | crash / hang / infeasible / overrun |
| `mem_profile.py` | Peak RSS of the whole 4-worker process tree vs the 16GB server cap (alert at 85%). Run once per giant instance BEFORE adding CP-SAT-heavy v19 components. | peak > 13.6 GB |

Each run executes the solver in a fresh subprocess with a hard watchdog, so a
hang shows up as `HANG`, never as a stuck bench. Exit code is non-zero iff
something failed — usable as a pre-submission gate:

```bash
python bench_scaling.py && python stress_test.py && echo SAFE TO SUBMIT
```
