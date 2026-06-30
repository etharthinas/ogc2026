# OGC 2026 Project Context

This repository contains the starter materials for the Optimization Grand Challenge 2026 problem:
the "Grand Shipyard Puzzle: Pack the Block, Beat the Clock."

The task is a combined spatial packing, bay assignment, and scheduling problem inspired by shipyard
block production. The algorithm must decide where each irregular block goes, how it is oriented,
when it enters a bay, and when it exits.

## Repository Layout

- `problem_statement.pdf`
  - Official problem definition, submission rules, evaluation rules, and baseline description.
- `README.txt`
  - Top-level quick-start instructions.
  - Recommends creating the conda environment with:
    - `conda env create -f ogc2026_env.yml`
    - `conda activate ogc2026`
- `ogc2026_env.yml`
  - Conda environment definition.
  - Uses Python 3.12 and includes packages such as Shapely, PyQt6, OR-Tools, Gurobi, Xpress,
    PyTorch, TensorFlow, pandas, scipy, scikit-learn, and numba.
- `train/`
  - 40 training instances, named `prob_1.json` through `prob_40.json`.
- `baseline/`
  - Baseline algorithm template and utilities.
  - `myalgorithm.py` is the submission entry point.
  - `baseline_greedy.py` is the provided greedy/reference implementation.
  - `utils.py` contains geometry classes, feasibility checks, and scoring logic. It should not be
    modified for contest submissions.
- `alg_tester/`
  - PyQt-based GUI tester and visualizer.
  - Lets a user select an instance, select an algorithm folder, run the algorithm, view feasibility,
    objective value, and visualize bay/block layouts.

This directory is not currently a git repository.

## Problem Summary

For each block, the solver must decide:

1. Which bay to assign it to.
2. Which orientation to use.
3. Integer `(x, y)` position of the block reference point inside the bay.
4. `ENTRY` time.
5. `EXIT` time.

The submitted solution is a dictionary of operations:

```python
{
    "operations": {
        "0": [
            {
                "type": "ENTRY",
                "block_id": 4,
                "bay_id": 1,
                "x": 0,
                "y": 0,
                "orient_idx": 0,
            }
        ],
        "28": [
            {
                "type": "EXIT",
                "block_id": 25,
                "bay_id": 2,
            },
            {
                "type": "ENTRY",
                "block_id": 15,
                "bay_id": 0,
                "x": 106,
                "y": 0,
                "orient_idx": 0,
            },
        ],
    }
}
```

At a given time, all `EXIT` operations must be performed before `ENTRY` operations. Within each
type, operation order still matters because each operation changes the bay state.

## Instance Data

Each problem JSON contains:

- `name`
- `bays`
  - Each bay has `width` and `height`.
  - Bays are indexed from `0` to `m - 1`.
- `blocks`
  - Blocks are indexed from `0` to `n - 1`.
  - Each block has:
    - `release_time`
    - `due_date`
    - `processing_time`
    - `workload`
    - `bay_preferences`
    - `shape`
  - `shape` is a list of orientation options.
  - Each orientation has a list of polygonal `layers`.
  - The first vertex of the first layer is always `[0.0, 0.0]` and is the block reference point.
  - Other vertices may have fractional coordinates and may be negative relative to the reference
    point.
- `weights`
  - `w1`, `w2`, `w3`, used in the objective function.

## Feasibility Constraints

Every block must have exactly one `ENTRY` and one `EXIT`.

Temporal constraints:

- `ENTRY_i >= release_time_i`
- `EXIT_i - ENTRY_i >= processing_time_i`
- Blocks occupy the bay during `[ENTRY_i, EXIT_i)`.

Spatial constraints:

- The placed block must be fully contained in the selected bay.
- Blocks in the same bay at overlapping times must not collide at the same layer.
- Edge touching is allowed; positive interior overlap is not.

Crane constraints:

- The crane lowers or lifts blocks vertically.
- When placing or removing a block, every layer of the moving block must avoid every same-or-higher
  layer of blocks already present in that bay.
- This is stricter than normal same-layer collision checking.
- A placement can be spatially collision-free while still being impossible to enter or exit because
  a taller/upper layer blocks the vertical crane path.

## Objective Function

The objective is:

```text
w1 * Z1 + w2 * Z2 + w3 * Z3
```

Where:

- `Z1`: total tardiness
  - `sum(max(0, EXIT_i - due_date_i))`
- `Z2`: maximum normalized workload imbalance across bays
  - Larger bays receive smaller normalization weights because they can absorb more work/congestion.
- `Z3`: total bay preference penalty
  - For each block, penalty is `max_preference_for_block - assigned_bay_preference`.
  - Zero if every block is assigned to its most preferred bay.

The relative importance of tardiness, balance, and preference varies by instance through `w1`, `w2`,
and `w3`.

## Important Utility Code

`baseline/utils.py` provides the geometry and scoring primitives used by the official checker.

Important classes/functions:

- `Bay`
  - Rectangular bay dimensions and containment checks.
- `Block`
  - A block placed at `(x, y)` with an orientation.
  - Builds/caches world-coordinate layer polygons.
- `check_collisions(bay, blocks)`
  - Checks same-layer spatial collisions among co-present blocks.
- `check_entry(bay, blocks, new_block)`
  - Checks whether a block can be lowered into the bay without crane-path obstruction.
- `check_exit(bay, blocks, target_block)`
  - Checks whether a block can be lifted out without crane-path obstruction.
- `check_feasibility(prob_info, solution)`
  - Validates the complete solution in stages and computes objective components.

The checker validates:

1. Assignment and operation format.
2. Entry feasibility.
3. Exit feasibility.
4. Co-present spatial collision feasibility.
5. Sequential replay feasibility of operations at each time.

The official evaluator uses the same logic, so any algorithm should call `check_feasibility` before
returning if time permits.

## Current Baseline Entry Point

`baseline/myalgorithm.py` currently contains only a wrapper:

```python
def algorithm(prob_info, timelimit=60):
    import baseline_greedy
    return baseline_greedy.greedyalgorithm(prob_info, timelimit)
```

So the submitted algorithm is currently exactly the greedy baseline.

## Baseline Greedy Algorithm

The main implementation is in `baseline/baseline_greedy.py`.

High-level flow:

1. Validate that every block can fit in at least one bay/orientation at some integer position.
2. Sort blocks by earliest due date, tie-breaking by shortest processing time.
3. Place blocks one by one using a best-fit greedy search.
4. Build the `operations` solution.
5. Run feasibility repair on violating blocks.
6. Return the final operations dictionary.

### Phase 1: EDD Greedy Placement

Blocks are sorted by:

```python
(due_date, processing_time)
```

For each block, the baseline searches:

- bays, ordered by that block's bay preference from highest to lowest
- orientations
- candidate positions
- earliest feasible time slot at that bay/position/orientation

Candidate positions come from a bottom-left style heuristic:

- start at the lowest valid position induced by the block local bounding box
- add candidate x/y coordinates where the new block's bounding box touches the right/top edge of
  already placed blocks

This is AABB-driven, not an exhaustive geometry search.

For each candidate, the baseline checks:

- integer position exists
- block fits inside the bay
- crane entry feasibility at proposed entry time
- crane exit feasibility at proposed exit time
- some hidden Stage-4 spatial collisions for blocks whose intervals are strictly inside the new
  block interval

### Placement Scoring

Candidate placements are scored by:

```text
w1 * tardiness
+ w2 * approximate workload imbalance
+ w3 * preference penalty
+ tiny_weight * top_y
```

Where:

- tardiness is `max(0, exit_time - due_date)`
- workload imbalance approximates the official normalized imbalance objective
- preference penalty is `max_bay_preference - selected_bay_preference`
- `top_y` is a small tie-breaker that favors lower/tighter packing

### Time Slot Search

The baseline considers candidate entry times from:

- the block release time
- existing exit times in the selected bay

For each candidate entry time, it computes `exit_t = entry + processing_time`, then checks entry
and exit crane feasibility against blocks present at those moments.

### Phase 2: Repair

After the first greedy pass, the baseline calls `check_feasibility`.

If there are violations, it extracts block IDs mentioned in violation messages and repairs those
blocks.

Repair modes:

- `greedy`
  - Default.
  - Remove violating blocks.
  - Rebuild bay state from remaining assignments.
  - Re-place violating blocks using the same greedy search.
  - If a block repeatedly appears in repair passes, force it into an empty-bay window.
- `simple`
  - Keep the block's bay/position/orientation.
  - Push it later to the next empty-bay time window.
  - Faster but less flexible.

The force-placement fallback:

- chooses a fitting preferred bay/orientation
- places the block at a minimum valid reference-point coordinate
- schedules it in a completely empty bay window
- should be structurally safe for crane entry/exit, but usually hurts objective

## Baseline Weaknesses Observed

The baseline is useful but brittle.

Key issues:

- It is highly time-sensitive around a 60-second limit.
- It can return infeasible if repair is still unresolved near the time limit.
- The repair logic has a time guard, but it does not maintain and return a previously verified
  feasible incumbent.
- Candidate positions are limited and AABB-based, so it may miss good geometric placements.
- The greedy order is due-date-only and does not directly consider block area, layer count, crane
  conflict risk, or slack.
- It optimizes placement locally; early choices can block many later exits.
- Force placement guarantees progress but can increase tardiness and workload/preference penalties.
- Feasibility repair depends on parsing violation strings for block IDs, which is fragile.

## Environment Notes From This Session

The repository README says to use conda:

```bash
conda env create -f ogc2026_env.yml
conda activate ogc2026
```

The default shell did not have a working `conda` binary on `PATH`.

The user's `.zshrc` contains a conda init block pointing to:

```text
/Users/Jay/anaconda3/bin/conda
```

but that path was not present in the sandboxed environment.

To follow the README path without modifying the user's home setup, Miniforge was downloaded and
installed under:

```text
/private/tmp/miniforge3-ogc2026
```

The `ogc2026` conda environment was then created from `ogc2026_env.yml` under that temporary
Miniforge installation.

The conda-based commands used were equivalent to:

```bash
HOME=/private/tmp /private/tmp/miniforge3-ogc2026/bin/conda env create -f ogc2026_env.yml
HOME=/private/tmp /private/tmp/miniforge3-ogc2026/bin/conda run -n ogc2026 python ...
```

The temporary benchmark helper script created during this session is:

```text
/private/tmp/ogc_benchmark_greedy.py
```

It is outside the repository.

## Partial Baseline Performance Observed

A direct conda-run CLI smoke test on `train/prob_1.json`:

```bash
HOME=/private/tmp /private/tmp/miniforge3-ogc2026/bin/conda run -n ogc2026 \
  python baseline/baseline_greedy.py train/prob_1.json --timelimit 60 --repair greedy
```

Result:

- instance: `prob_1`
- blocks: 100
- bays: 2
- elapsed: `58.832s`
- feasible: `True`
- objective: `4,111,463.00`
- components:
  - `obj1 = 140.0`
  - `obj2 = 389.0`
  - `obj3 = 180.0`

A later quiet batch benchmark with `60s` per instance showed timing sensitivity. Partial results
before the benchmark was stopped:

| Instance | Blocks | Bays | Time | Status | Objective / Note |
|---|---:|---:|---:|---|---|
| `prob_1.json` | 100 | 2 | 60.479s | FAIL | Stage 5 obstruction. Direct CLI had passed earlier at 58.832s. |
| `prob_2.json` | 100 | 3 | 37.153s | PASS | 1,210,431.00 |
| `prob_3.json` | 100 | 3 | 38.201s | PASS | 339,403.00 |
| `prob_4.json` | 100 | 2 | 32.699s | PASS | 179,424.00 |
| `prob_5.json` | 150 | 3 | 19.821s | PASS | 133,539.00 |
| `prob_6.json` | 150 | 3 | 61.561s | FAIL | Stage 3 exit obstruction. |
| `prob_7.json` | 150 | 3 | 36.872s | PASS | 140,857.00 |
| `prob_8.json` | 150 | 2 | 26.910s | PASS | 11,252.00 |
| `prob_9.json` | 200 | 3 | 54.788s | PASS | 27,146,887.00 |
| `prob_10.json` | 200 | 4 | 52.386s | PASS | 200,567.00 |
| `prob_11.json` | 200 | 4 | 52.678s | PASS | 150,096.00 |
| `prob_12.json` | 200 | 4 | 59.417s | FAIL | Stage 2 entry obstruction. |
| `prob_13.json` | 250 | 4 | 57.518s | PASS | 10,763,884.00 |

The benchmark was interrupted during `prob_14`, then the background benchmark processes were
stopped.

The partial results should not be treated as final because:

- only the first 13 instances completed
- the baseline is sensitive near the time limit
- direct CLI and quiet wrapper produced different `prob_1` feasibility due to timing behavior

## Main Strategic Priority

The first major algorithmic priority should be:

```text
Always return a feasible solution.
```

The baseline does not reliably do this under tight time limits. In contest scoring, infeasible,
crashed, and time-limited solutions receive the same bad status. A mediocre feasible solution is
much more valuable than a nearly good infeasible one.

Recommended structure:

1. Build a guaranteed-feasible fallback solution early.
2. Store it as the incumbent.
3. Run greedy/improvement methods.
4. Whenever a candidate solution passes `check_feasibility`, update the incumbent if its objective
   improves.
5. Near the time limit, return the best feasible incumbent, not the latest attempted repair state.

## Guaranteed Feasible Fallback Ideas

### Sequential Empty-Bay Schedule

For each block:

- choose a bay/orientation where it fits
- place it at the minimum valid coordinate
- schedule it in an empty bay window
- never overlap blocks in the same bay

This should satisfy crane constraints because the bay is empty at entry and exit.

It may have high tardiness, but it gives a valid incumbent.

### Preference-Aware Sequential Fallback

For each block:

- choose the highest-preference bay where it fits
- schedule sequentially within that bay
- optionally choose among bays by earliest available finish time plus preference penalty

This is still simple but should reduce preference and tardiness penalties compared with a single
bay fallback.

### Workload-Balanced Sequential Fallback

Choose the bay using a score such as:

```text
alpha * projected_tardiness
+ beta * projected_normalized_load_imbalance
+ gamma * preference_penalty
```

This mimics the objective while keeping the bay empty-window guarantee.

## Strategy Suggestions

### 1. Add Incumbent Management

Before any sophisticated search:

- create a fallback feasible solution
- call `check_feasibility`
- store the objective
- during the main algorithm, periodically check candidate solutions
- return the best feasible candidate seen

This addresses the baseline's largest practical weakness.

Implementation target:

- modify `baseline/myalgorithm.py` or create helper modules beside it
- keep the required function signature:

```python
def algorithm(prob_info: dict, timelimit: float) -> dict:
    ...
```

### 2. Improve Block Ordering

Current order is only:

```text
earliest due date, shortest processing time
```

Try alternative construction orders:

- minimum slack:
  - `due_date - release_time - processing_time`
- earliest due date, then largest footprint area
- largest footprint area first within due-date buckets
- highest layer count first
- highest workload first when `w2` is large
- highest preference regret first:
  - difference between best and second-best bay preference
- highest conflict-risk first:
  - large area, many layers, many orientations that barely fit

Run several greedy variants within the time limit and keep the best feasible incumbent.

### 3. Improve Candidate Position Generation

The baseline candidate positions are limited AABB contact points. Add richer candidates:

- left/right edge contacts
- top/bottom edge contacts
- combinations from all active block bounding-box edges
- candidates near release-time active blocks only
- candidates from skyline/free-rectangle packing
- randomized jitter among integer positions near promising contact points
- candidate positions that reduce crane blocking, not only spatial packing

For each orientation, precompute:

- local bounding box
- width/height
- area by layer
- maximum layer count
- minimum valid integer coordinate range per bay

### 4. Crane-Aware Placement

Normal packing is not enough. A block can be spatially valid but impossible to lift out.

Add crane-aware penalties:

- avoid placing lower blocks under upper layers of blocks likely to exit earlier
- prefer placements where the block has vertical clearance at expected exit time
- penalize candidates that require many other blocks to move/exit first
- for blocks with early due dates, prefer positions/orientations with easier exit paths

Useful heuristic:

- if block A exits before block B and A's crane path is blocked by B, the pair/order is bad
- precompute pairwise obstruction relations for candidate relative placements where possible

### 5. Decouple Bay Assignment From Geometry

Current baseline mixes bay assignment, geometry, and timing in one local greedy decision.

Alternative:

1. Assign blocks to bays using a fast objective approximation.
2. Pack/schedule each bay independently.
3. Repair cross-objective issues by moving blocks between bays.

Bay assignment heuristic score:

```text
w1 * estimated_tardiness
+ w2 * estimated_load_imbalance
+ w3 * preference_penalty
+ congestion_penalty
```

Congestion can be approximated by:

- total footprint area / bay area
- total processing time density
- total workload density
- average layer count

### 6. Local Search After Greedy

Once a feasible solution exists, improve it with local moves:

- move one block to another bay
- change orientation
- shift position
- delay/advance entry time
- move a high-tardiness block earlier
- swap bay assignments of two blocks
- remove and reinsert a small set of blocks

Accept a move only if:

- it passes feasibility
- it improves objective

Use focused neighborhoods:

- blocks with largest tardiness
- blocks with largest preference penalty
- blocks in overloaded bays
- blocks involved in repair/force placement
- blocks causing feasibility violations during failed attempts

### 7. Large Neighborhood Search

Repeatedly destroy and repair part of the solution:

1. Start from feasible incumbent.
2. Remove a subset of blocks.
3. Reinsert them using a stronger greedy search.
4. Check feasibility.
5. Keep if improved.

Subset choices:

- all tardy blocks
- blocks in one bay
- blocks around a congested time window
- blocks with low bay preference assignment
- random 5-20% of blocks
- blocks involved in crane conflicts

This is often more useful than single-block local search when early greedy choices create structural
blocking.

### 8. Time Optimization With Fixed Geometry

If bay, orientation, and position are fixed, the remaining problem is scheduling entry/exit times
subject to release, processing, spatial coexistence, and crane constraints.

Potential approaches:

- greedy left-shift schedule
- interval graph conflict constraints
- CP-SAT / OR-Tools for small subsets
- optimize only a single bay at a time

This can reduce tardiness without changing geometry.

### 9. Geometry Optimization With Fixed Time Windows

If time windows are mostly fixed, improve packing:

- repack blocks active in congested windows
- use free-rectangle or no-fit-polygon style candidates
- prioritize blocks whose spatial placement causes crane obstruction

This is harder, but it can repair failures without pushing blocks far into the future.

### 10. Use OR-Tools / MIP for Subproblems

The full problem is probably too large for exact optimization, but solvers can help with restricted
subproblems:

- bay assignment ignoring geometry
- scheduling fixed placements
- choosing among a small menu of candidate placements
- repairing 10-30 problematic blocks
- balancing workloads after greedy

Candidate-placement MIP idea:

- precompute K feasible placement choices per block
- binary variable chooses one placement
- add incompatibility constraints between choices that overlap in space/time/crane relation
- optimize weighted objective approximation

This is only practical for subsets or heavily pruned candidate menus.

### 11. Multi-Start Greedy

Run many greedy variants within the time limit:

- different orderings
- different weights in placement scoring
- randomized tie-breaking
- different repair modes
- different candidate position limits

Keep the best feasible incumbent.

This is low-risk and easy to build on top of the baseline.

### 12. Tune Scoring By Instance Weights

The baseline uses the instance weights directly, but the heuristic score may need normalization.

For example:

- if `w1` is huge, prioritize schedule feasibility and due dates strongly
- if `w3` is huge, respect bay preferences unless it causes severe tardiness
- if `w2` is meaningful, track projected normalized load balance carefully

Raw objective components have different scales, so heuristic scoring can be dominated by one term
unless normalized.

### 13. Cache Expensive Geometry

Shapely checks are expensive.

Cache:

- `Block` objects for `(block_id, x, y, orient_idx)`
- local bounding boxes per `(block_id, orient_idx)`
- candidate positions per `(bay, block, orientation, active-set signature)` if practical
- polygon objects for block layers
- pairwise collision/obstruction checks for repeated candidate pairs

Avoid reconstructing the same geometry repeatedly inside repair loops.

### 14. Better Repair

Current repair reparses violation strings and repairs only mentioned blocks.

Improve repair by:

- returning structured violation data from a local/custom checker wrapper if possible
- repairing both blocker and blocked block, not only the block named first
- expanding repair neighborhood around violating block's bay/time interval
- using empty-window fallback only for last resort
- keeping previous feasible incumbent

For crane violations:

- if block A's exit is blocked by B, options include:
  - move A's exit earlier/later
  - move B's entry later
  - move A or B spatially
  - assign one to another bay

Repairing only A may not be enough.

## Suggested Implementation Roadmap

### Step 1: Feasible Incumbent Wrapper

Implement in `myalgorithm.py`:

- make guaranteed feasible fallback
- run baseline greedy if time allows
- check baseline result
- return better feasible result

This alone reduces risk.

### Step 2: Multi-Start Greedy

Create several orderings and scoring variants. For each:

- run construction
- run limited repair
- check feasibility
- update incumbent

Stop when elapsed time approaches `timelimit`.

### Step 3: Better Construction

Enhance candidate position generation and block ordering. Focus on:

- slack/order variants
- candidate positions beyond current bottom-left AABB contacts
- cache geometry

### Step 4: Local Search

Add improvement moves over feasible incumbent:

- reinsert high-tardiness blocks
- move preference-penalty blocks
- rebalance overloaded bays

### Step 5: Subproblem Optimization

Use OR-Tools/CP-SAT or MIP only for small subproblems:

- fixed geometry time optimization
- candidate placement selection for 10-30 blocks
- bay reassignment repair

## Practical Notes For Future Work

- Always keep `utils.py` unchanged for submission.
- `myalgorithm.py` must be at the root of the submitted zip.
- If additional helper modules are used, keep them beside `myalgorithm.py` and import relatively or
  by local module name.
- Avoid absolute paths in submission code.
- Hidden evaluation has no internet access.
- Evaluation server constraints from the PDF:
  - Ubuntu 24.04 LTS
  - AMD Ryzen Threadripper PRO 9955WX
  - at most 4 CPU cores
  - 16GB memory
  - time limits vary, expected from a few minutes to half an hour
- Do not rely on local-only packages outside the provided environment unless bundled.

## Commands Used / Useful Commands

Run a single baseline instance under the temporary conda environment from this session:

```bash
HOME=/private/tmp /private/tmp/miniforge3-ogc2026/bin/conda run -n ogc2026 \
  python baseline/baseline_greedy.py train/prob_1.json --timelimit 60 --repair greedy
```

Run the GUI tester if using an activated environment:

```bash
conda activate ogc2026
cd alg_tester
python alg_tester_app.py
```

Standalone feasibility usage:

```python
from utils import check_feasibility

result = check_feasibility(prob_info, solution)
print(result)
```

## Session Update (2026-06-18): Kickoff Prep

Prepared the kickoff meeting prep-note in Notion ("2026 OGC / 260622 Kickoff"). New
insights captured this session:

### Project / Operational Facts

- Submission deadline: 2026-07-28 14:00 (Asia/Seoul). ~5.5 weeks from kickoff.
- Team: 2-3 people, part-time. Meeting cadence: weekly.
- W1 (this week) single priority agreed: guaranteed-feasible incumbent wrapper + an
  automated 40-instance benchmark harness (score aggregation). Everything else compares
  against that harness.

### Instance Dataset Analysis (all 40 train instances)

- Block counts range 100-300; bay counts range 2-5.
- Blocks have up to 8 orientations; multi-layer shapes exist; vertices can be fractional
  and negative relative to the reference point.
- Weight distribution varies a lot per instance and should drive weight-adaptive scoring:
  - `w1` (tardiness): hundreds up to ~29,000 — usually dominant, so tardiness minimization
    is the leading term in most instances.
  - `w2` (load imbalance): small, 1-10.
  - `w3` (preference): 13-600.
  - Low-`w1` outliers where balance/preference matter relatively more: prob_25, prob_36,
    prob_40 (w1=667), and prob_32/34/37 (w1=3333).
- Slack is very tight: on prob_1, mean slack `due - release - processing` ≈ 1.4, min = 0.
  Tardiness avoidance is structurally hard. Workload is right-skewed (prob_1 mean ~90,
  max 666). prob_1 bays are small (51x20, 54x18).

### Solver Licensing Caveat (important)

- Env ships gurobipy and xpress, but the hidden eval server likely has NO commercial
  license (and no internet). Default to OR-Tools CP-SAT (free) for any subproblem solving;
  do NOT make the submission depend on Gurobi/Xpress. Confirm at meeting.

## Current Best Understanding

This is not just a packing problem and not just a scheduling problem. The hard part is the coupling:

- geometric footprint affects which blocks can coexist
- layer structure affects crane entry/exit feasibility
- schedule affects which blocks coexist
- bay assignment affects preference and workload balance
- bad early placements can force late exits and large tardiness

The baseline is a reasonable starting point because it already encodes the official geometry model
and performs crane-aware candidate checking. The first competitive improvement should not be a
large rewrite. It should be a robust wrapper and search framework around the baseline:

1. guaranteed feasible incumbent
2. multiple construction variants
3. better repair neighborhoods
4. feasible-only local improvement
5. geometry caching

Once feasibility is reliable, objective improvement can be pursued with more aggressive packing,
scheduling, and reassignment heuristics.
