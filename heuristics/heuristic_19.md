# Heuristic v19 — cracking the saturated mass: new construction theories, calibrated flow plans, and acceptance-rule diversification (goal < 125,000,000)

> PLANNING DOCUMENT ONLY (no code yet). Written for an Opus implementer with no
> other context: every number, constraint, dead lever, and gate needed is
> restated here. Read this file top-to-bottom before touching code.

## 0. Where we stand (v18, the departure point)

- **Convention:** full-40 serial bench @600s/instance, 4-worker island model
  (`bench_row`, quiet machine, `.venv_ogc` python — see env rules in §12).
  The goal row is `algorithm 18 (4w 600s)` in results.csv, commit b356c58,
  `myalgorithm.py` = v18 = `baseline/myalgorithm_18.py`.
- **v18 total = 149,831,986 (40/40 feasible). Goal v19: < 125,000,000 at the
  same 600s convention.** That is −24.84M, by far the largest single-version
  ask of the campaign (v13 was −19M, everything since summed −5.7M).
- The −24.84M CANNOT come from polish. Nine mechanism families are measured
  dead (§1). It must come from the concentrated over-floor mass:

Per-instance v18 @600s values (probs 1–20 sum to only 1,592,168 — ignore them
except as byte-protect set):

| prob | v18 value | best known LB / floor | over-floor mass | v19 target band |
|---|---|---|---|---|
| 38 | 45,806,839 | fluid LB 24.2M (preemptive, ~40% loose) | ~21.6M | −6M … −12M |
| 27 | 29,185,135 | fluid LB 17.1M | ~12.1M | −3M … −6M |
| 39 | 12,361,461 | fluid LB 1.3M | ~11.1M | −4M … −8M |
| 31 | 11,268,243 | fluid LB ≈ 0 (joint Z2+Z3 floor 178,971) | ~11.1M | −4M … −8M |
| 26 | 9,653,490 | fluid LB 5.1M | ~4.6M | −1M … −3M |
| 33 | 9,566,490 | LB unknown (get via Improvement 1) | ? | −0.5M … −3M |
| 37 | 5,807,047 | LB unknown; w1=3333 (low) | ? | −0.3M … −2M |
| 30/32/28/23/40/34/35/21/22/24/25/29/36 | 26.6M combined | joint floor ~0.5M | mixed | −1M … −3M combined |

Mid-band sum ≈ −25M…−35M. The plan only closes if **at least three of the four
big rocks (38, 27, 39, 31) move by millions**. Everything in this file is
organized around that fact.

- **31 is the scandal and the cheapest big rock.** Fluid tardiness LB ≈ 0,
  joint floor 179k, yet it has sat at 11,268,243 UNCHANGED across
  v14→v17→v18 (300s AND 600s: deterministic-basin flat). Nobody has run a
  dedicated campaign on 31 since v12-era. It gets its own improvements (5, 1).
- **39 is second.** 12.36M vs 1.3M fluid LB; moved only −13.6k at 600s.
- **38/27 are the hard pair** (75M combined, ~34M over fluid LB) that survived
  nine families. They only move with a *different construction theory*
  (Improvements 2, 3, 4), not with more polish.

## 1. Dead levers — DO NOT REBUILD VARIANTS OF THESE (nine measured-dead families)

Each of these was implemented, unit-tested sound, and measured ~zero (or
negative) on the saturated set. Re-deriving a "variant" of one of these is the
main failure mode available to you. The list, with the reason it died:

1. **alpha-ATC triage variants** (ordering priority rules on 38/27) — order
   changes shuffle who is tardy, not total queue delay.
2. **CP-SAT retime, full + windowed** (fixed geometry, re-optimize times) —
   zero on ALL forced instances; the schedules are already left-tight.
3. **Fluid-target admission gating** (pace admissions to a fluid relaxation
   plan) — realization penalty 13–22M; fluid targets are ~40% unreachable.
   (Improvement 2 explains precisely how it differs from this corpse.)
4. **Joint window repack** (greedy multi-block rebuild) — reached its ceiling
   in v14; superseded by exact windows which also saturated.
5. **nw=4 specialist portfolio** (4 differently-tuned workers) — width without
   new mechanisms just re-finds the same basins.
6. **Z3 relocation endgame on forced instances** — preferred bays are
   space-saturated; there is nowhere to relocate to.
7. **Harvest/cycle schemes (×2 variants)** — "lottery noise" turned out to be
   code-version variance; within-version results are DETERMINISTIC, so
   re-rolling never pays (campaign law, v15/v16).
8. **Target-gated admission** — same family as 3, died the same way.
9. **Exact packing as incumbent improvement, ANY scope** (v17 windows D=14/K=12:
   sound, −27k/accept, but rare; v18 whole-bay: sound and ZERO yield in five
   configurations). Law learned: **exact neighborhoods pay only when small and
   dense enough to near-exhaust; scope expansion outruns solver power; and
   solves anchored at a polished incumbent are almost always
   feasible-at-hint-optimal.** (Improvements 3 and 4 re-aim this tool at
   UNANCHORED states — that is the difference, and the only licensed reuse.)

Also standing campaign laws:
- Within-version determinism: identical code+seed ⇒ byte-identical result.
  Any change to shared code paths changes rng pacing and can DISPLACE banked
  basins on untouched instances (the v14 lesson: −1.6M on targets, +0.6M
  collateral). Mitigation is structural: §11 (slot quarantine) is mandatory.
- Fluid "bounds" from preemptive relaxations are ~40% loose — never chase a
  fluid gap without first checking it with a non-preemptive model
  (Improvement 1 institutionalizes this).
- The attribution-probe → slot-clone playbook is the reliable way to restore
  displaced basins (v17 §Restoration). Keep it in the toolbox for assembly.

## 2. Strategy of this version (read before the ten improvements)

Three tiers, in dependency order:

- **Tier T (targeting, do first):** Improvement 1 (honest LB ledger) and
  Improvement 8 (exit-blocking instrumentation) are measure-only, zero-risk,
  and DECIDE how much of the −24.8M is real and where. If the honest LB sum
  over {38,27,39,31,26,33,37} says the reachable total is > 125M at 600s, we
  learn it in week one, not at bench time (see §13 for the escalation path).
- **Tier E (engine multipliers):** Improvements 6, 7, 9 make every search
  mechanism (old and new) faster/denser. They are pacing-dangerous, so they
  live behind the §11 quarantine.
- **Tier C (new construction theories — the actual payload):** Improvements
  2, 3, 4 for 38/27/39 (three DIFFERENT theories, run as competing explorer
  slots, min-wins keeps whichever lands), Improvement 5 for 31/39/26/33
  (acceptance-rule novelty — the first non-greedy acceptance of the campaign).
- Improvement 10 is the campaign protocol that sequences all of it into
  sub-versions 19a→19e with gates, so a single bad diff never costs the
  banked 149.83M.

The portfolio's min-wins/obj-gated accept + official `check_feasibility`
verify before banking stays MANDATORY and UNCHANGED for every new mechanism.
Nothing in this file relaxes soundness.

---

## THE TEN IMPROVEMENTS

### Improvement 1 — Honest capacity model: non-preemptive bucketed LB + per-instance target ledger

**Why.** Every remaining decision (which rock to push, when to stop, whether
<125M is even reachable) depends on bounds we do not have. The fluid LBs are
preemptive and ~40% loose; the joint floor row only bounds Z2+Z3. We need a
non-preemptive, capacity-honest LB per instance, and we need it FIRST.

**Mechanism.** Standalone script (NOT in the submission path), one CP-SAT
model per instance:
1. Time buckets of width `g = round(median processing_time / 2)` (clamp so
   bucket count ≤ ~600; coarser is fine for a bound).
2. One interval variable per block: `entry_b ≥ release_b`,
   `exit_b = entry_b + processing_b` (non-preemptive, exact durations,
   integer bucket granularity — round durations UP to preserve the bound).
3. Bay assignment literal `y[b,k]` (block b in bay k), exactly-one.
4. Capacity: for each bay k and bucket t,
   `sum over blocks active at t of area_b * y[b,k] ≤ cap_frac * Area_k`.
   Run TWO variants: `cap_frac = 1.0` (true relaxation → a VALID lower
   bound) and `cap_frac = d_k` = the best realized per-bay density ever
   observed in our own solutions (measure it from the v18 incumbents — see
   Improvement 2 step 1; → a REALISTIC target, not a bound).
   Use per-layer area profiles (a block's area per layer; capacity per layer)
   if cheap; else max-footprint area is still valid.
5. Objective `w1 * sum tardiness_b` (+ exact Z3 term via the y literals if it
   fits; Z2 may be dropped — dropping terms keeps the LB valid).
6. Budget: 300–600s per instance, minutes-scale is fine — this runs OFFLINE
   once, on the quiet machine, results checked into the ledger.

**Deliverable.** `heuristics/ledger_19.md`: per instance — fluid LB, bucketed
LB (cap=1.0), realistic target (cap=d_k), v18 value, verdict
(`CHASE` / `MAYBE` / `SATURATED`). Also the answer to: does
`sum(realistic targets) + 1.59M (probs 1-20)` clear 125M? If NO, invoke §13
immediately rather than burning weeks.

**Gate.** Model reproduces feasibility of the v18 solution values (each v18
incumbent, bucketed, must be feasible in the cap=1.0 model — if not, the
model is buggy, fix before trusting any bound).

**Kill criterion.** None — this is information, it cannot lose. 1–2 days max.

**Expected value.** Indirect but decisive: it converts "targets" from folklore
to numbers, and its bay-assignment/entry-order output seeds Improvement 2.

### Improvement 2 — Calibrated flow-plan construction for the over-subscribed giants (38, 27)

**Why.** On 38/27 tardiness is pure entry-queue delay during the release
burst (v12 diagnosis, never overturned). The dispatcher decides admissions
myopically. A globally-planned admission schedule can provably beat myopic
admission when the queue is over-subscribed — IF the plan is realizable.
The dead fluid-gating (family 3) failed exactly on realizability: preemptive
fluid targets were ~40% too aggressive, the realizer missed them, penalty
13–22M. This improvement is the same *shape* with the failure surgically
removed. The three differences are non-negotiable:

1. **Calibrated capacity, not fluid capacity.** First, MEASURE what our own
   packer actually achieves: replay the v18 incumbent for 38/27, compute
   per-bay per-bucket realized density `d_k(t)`; take
   `cap_k = 0.92 * max_t d_k(t)` (a density our raster engine has already
   demonstrated on THIS instance — not a relaxation's fantasy).
2. **Non-preemptive interval plan.** Solve the Improvement-1 model with
   `cap_frac = cap_k` and full durations (no preemption anywhere), 60–120s
   CP-SAT budget in-run (this is the SAME code as Improvement 1, wired
   in-run; ortools guarded with fallback = skip slot). Output: per block, a
   planned bay `k_b` and planned entry bucket `t_b`.
3. **Advisory realization with re-planning, not gated realization.** The
   realizer is the EXISTING v12 event dispatcher with two overrides: (a) the
   admission queue is ordered by planned entry bucket (ties: ATC as today);
   (b) bay choice tries `k_b` first, falls back to today's economics if no
   feasible position exists. Blocks that miss their planned bucket by more
   than `2g` trigger ONE re-plan (re-solve the flow model with placed blocks
   fixed at their realized values, remaining blocks free) — budget for at
   most 2 re-plans. The result is verified and obj-gated as usual: if the
   flow-built solution loses to the incumbent, min-wins discards it and we
   lost nothing but slot time.

**Wiring.** New explorer slot (§11) on instances classified over-subscribed:
`(sum area_b * processing_b) / (sum Area_k * horizon)` above a threshold
picked so exactly {38, 27} (and possibly 26) qualify. Runs the full
plan→realize→verify pipeline 2–4 times in its slot (different cap scalings
0.88/0.92/0.96), banks min.

**Units.** (a) plan feasible + realizer completes on prob_38 with ≥ 95% of
blocks within `2g` of plan; (b) measured realized density under the flow
build ≥ measured density of v18 incumbent (the point is to keep bays FULL —
if density drops, the plan is not binding and the theory is wrong for this
instance).

**Spot gate.** prob_38 OR prob_27 improves ≥ −1.0M @600s in the explorer
build. (We need millions here; −100k means the theory is not the unlock and
the slot should go to Improvement 3/4.)

**Kill criterion.** Both giants < −300k after the calibrated version with 2
re-plans works mechanically ⇒ record dead (tenth family), free the slot.

**Expected yield if it lands.** −3M … −10M across 38+27. This is the highest
variance item in the file.

### Improvement 3 — Rolling-horizon exact constructor (MPC) for 38/27/39

**Why.** Exact packing died as an *incumbent improver* (family 9) because a
polished incumbent is a deep interlock — the solver proves it optimal-at-hint.
But DURING construction there is no incumbent interlock: the partial state at
the burst front is exactly the "small and dense" regime where v17 measured
that exact solves DO pay (−27k/accept at window scale). So: use the proven
v17 machinery (D≈12–16 blocks, K≈12 candidate menus, two-tier relations —
mask prefilter + exact cached geometry, `_cpsat_retime`'s audited time
encodings, verbatim from `baseline/myalgorithm_17.py`) as the PLACEMENT
ENGINE of a constructor, hundreds of times per build, instead of 8 times on a
finished solution.

**Mechanism.** Event-driven construction as today, but at every decision
epoch (each time the dispatcher would admit from the queue):
1. Take the next `D = 12–16` queued blocks (by ATC or by Improvement-2 plan
   order if that slot is live).
2. For each, enumerate up to `K = 12` raster-feasible placements across
   allowed bays/orientations at candidate times in `[now, now + H]`
   (horizon `H ≈ 2 * pbar`), against the FIXED already-placed blocks.
3. CP-SAT: exactly-one-or-none per block (a block may stay queued),
   pairwise raster/crane compatibility (two-tier relations), integer entry
   times, objective `w1 * (tardiness within horizon) − θ * (admitted area)`
   — the second term is the MPC trick: reward pulling area INTO the bays now
   (θ small; sweep {0, w1·g/2, w1·g}). 3–8s per solve.
4. Commit the chosen placements, advance the event clock, repeat.
5. Full build budget: with ~40–80 epochs × 5s ≈ 200–400s — fits one 600s
   slot for one build. This mechanism gets ONE dedicated worker slot on
   {38, 27, 39} only (§11).

**Soundness.** Identical contract to v17: every CP-SAT-selected placement
re-validated with exact `_can_place` before commit; final solution through
official `check_feasibility`; obj-gated bank. Zero new trust surface.

**Units.** (a) constructor completes a full feasible build on prob_39;
(b) on a synthetic mini-instance (or prob_1 @60s in a sandbox run, not the
protect path), MPC build ≥ greedy build.

**Spot gate.** Any of {38, 27, 39} improves ≥ −800k @600s.

**Kill criterion.** All three < −200k with θ-sweep done ⇒ record dead, free
the slot. (This is the "fundamentally better construction theory" candidate
named in the v18 verdict — it deserves a real θ/D/K sweep before dying.)

**Expected yield if it lands.** −2M … −8M (39 is the most likely first
mover: 11M over a 1.3M fluid LB with only 200 blocks).

### Improvement 4 — Layout-book waves: pack-first, schedule-second (column generation lite)

**Why.** Third and most radical theory for the same rocks, attacking density
directly. Today geometry is chosen incrementally, so co-residency patterns
are accidents of arrival order. Invert it: FIRST compute a small library of
dense verified layouts (sets of blocks that can provably co-reside in a bay),
THEN schedule the library.

**Mechanism.**
1. **Column generation (the "layout book").** Cluster blocks by
   release/due window (waves of `W ≈ 15–30` blocks whose lifetimes can
   overlap). For each (wave, bay), run the v17 exact-pack model in
   *density-maximizer* mode: no incumbent hint, objective = maximize total
   selected area, subject to raster/crane pairwise compatibility (two-tier
   relations again) — i.e. a bin-packing use of the proven machinery, in the
   small/dense regime where it near-exhausts. 10–20s per solve. Keep the top
   2–3 layouts per (wave, bay). This is NOT family 9: nothing is anchored at
   an incumbent, and the model answers "what is the densest co-resident
   set", a question never asked before.
2. **Master schedule.** CP-SAT interval model over layout activations: each
   layout is an optional interval on its bay (no two layouts co-active on a
   bay), each block covered by ≥1 chosen layout containing it, block
   entry/exit derived from its layout's activation window, objective
   `w1 * tardiness + w3 * preference`. 60–120s. Coarse is fine — step 3
   repairs.
3. **Realization.** Emit operations wave-by-wave (entries of a wave at
   activation start, ordered by the layout's crane-feasible insertion order,
   which the exact model's relation set already implies; exits at coverage
   end). Then run the EXISTING polish stack (improve → cpsat → improve) on
   the realized solution. Verify, obj-gate, bank.

**Wiring.** Explorer slot (§11), instances {38, 27, 39, 26}; it shares slot
hardware with Improvement 3 (they alternate; whichever wins the first spot
round keeps the slot — min-wins at the slot-allocation level).

**Units.** (a) density-maximizer layout on one congested (bay, wave) of
prob_26 has area ≥ the incumbent's realized co-resident area for the same
window (if exact density-max cannot beat accidental density, kill early);
(b) end-to-end wave build feasible on prob_39.

**Spot gate.** Any of {38, 27, 39, 26} ≥ −800k @600s.

**Kill criterion.** Unit (a) failing on both 26 and 39 kills the whole idea
in a day — that is the cheap decisive experiment. Then slot reverts to
Improvement 3.

**Expected yield if it lands.** −2M … −6M; also produces reusable dense
layouts that Improvement 2's calibration can consume (`d_k` from exact
layouts instead of historical incumbents).

### Improvement 5 — First non-greedy acceptance: LAHC/SA ruin-and-recreate explorer for 31, 39, 26, 33

**Why.** Every one of the nine dead families was an obj-gated IMPROVER around
a deterministic basin. The portfolio has NEVER accepted an uphill move. 31 is
the poster child: fluid LB ≈ 0, stuck at 11,268,243 through three versions
and a 2× budget doubling — a textbook deep local optimum. The one family
never tried: trajectory methods that accept controlled worsening.

**Mechanism.** Dedicated explorer slot (§11) running Late-Acceptance Hill
Climbing (LAHC — one parameter, robust, no temperature schedule):
1. Start from the banked incumbent for the instance.
2. Move = ruin-and-recreate: remove a large set (20–40% of blocks; ruin
   modes: (a) random bay-slice, (b) time-window around the tardiest cluster,
   (c) worst-contribution blocks by `w1·tardiness + w3·pref`), re-insert with
   the strongest existing greedy (raster candidates + economics), optionally
   one v17 exact window shot on the rebuilt region (small/dense regime —
   licensed).
3. LAHC accept: keep candidate if `obj ≤ history[i % L]` (L ≈ 50), push
   current obj to history. Track best-seen separately.
4. Bank ONLY the best-seen after official verify — the explorer may wander
   uphill internally, but what leaves the slot is min-wins clean. The main
   portfolio's incumbent is never exposed to uphill moves.
5. Budget: the full slot for the whole run on {31, 39} (primary) and
   {26, 33} (secondary). Determinism: fixed seed; it is still a deterministic
   method — but its basin is a TRAJECTORY basin, not the greedy basin, which
   is the point.

**Units.** On prob_31: explorer executes ≥ 200 ruin-recreate iterations in a
600s slot (throughput check — if iterations are too slow, shrink ruin size
or wire Improvement 7 first) and best-seen ≤ incumbent (sanity).

**Spot gate.** prob_31 ≤ 10.4M (−868k) OR prob_39 ≤ 11.8M (−561k) @600s.
(Deliberately modest — ANY movement on 31 after three flat versions is
signal; if it moves at all, double the slot and sweep L ∈ {25, 50, 200} and
ruin fraction.)

**Kill criterion.** 31 AND 39 flat (< −100k) after the L/ruin sweep ⇒ the
basins are likely globally optimal-ish for this representation; downgrade 31's
ledger verdict and stop chasing its fluid mirage.

**Expected yield if it lands.** −1M … −6M (31 alone could be −4M+ if the
fluid LB is even half-honest).

### Improvement 6 — Build-time exact-geometry near-miss recovery (density unlock in the candidate generator)

**Why.** The v12 raster masks are CONSERVATIVE (unit-grid rounding): every
fractional-edge block loses up to a cell per side, and v17 measured the
consequence in-model ("conservative mask relations false-positive on every
nestled pair"). v17 fixed it INSIDE CP-SAT with two-tier relations; the main
dispatcher and every greedy re-inserter still see only the conservative
masks. On small bays with large blocks (38's and 27's regime, prob_1-style
51×20 bays) each recovered candidate is potential density → queue drain.

**Mechanism.**
1. In the candidate generator, after the mask scan produces its feasible
   set, collect NEAR-MISS positions: mask-infeasible where the overlap is
   only boundary cells (erosion difference of 1 cell). Cheap to detect from
   the same sliding-window machinery.
2. For up to `N ≈ 20` best-scored near-misses (by the existing economics
   score), run the exact cached-geometry check (v17's two-tier stage-2,
   shapely on cached polygons + entry/exit prism rules). Accept the ones
   that are exactly feasible into the candidate pool, flagged so `_can_place`
   final validation still runs at commit (it always does).
3. Cache verdicts by `(block, orient, bay, x, y, active-set signature)` —
   the v17 relation cache pattern.

**Wiring.** DANGEROUS FOR PACING (changes candidate counts everywhere ⇒
displaces every banked basin). Therefore: enabled ONLY inside the new
explorer slots (Improvements 2/3/4/5) and in a per-instance opt-in for
{38, 27} legacy paths IF the spot round shows it pays there. NEVER globally
in v19 (see §11).

**Units.** Zero soundness regressions: every near-miss-recovered placement
passes official check (run 1000-placement fuzz on 26/38 states). Measured
candidate-count uplift ≥ +10% on prob_38 congested windows (if uplift is
~0%, the conservative loss was not binding — kill).

**Spot gate.** Combined with whichever explorer it serves — no separate obj
gate, but log recovered-candidate usage: if <2% of committed placements are
near-miss recoveries, it is dead weight; remove.

**Expected yield.** Multiplier on Improvements 2/3/4; standalone maybe
−0.2M … −1M on the giants.

### Improvement 7 — Throughput multiplier: numba/vectorization of the hot loop, quarantined

**Why.** Candidate throughput is the one thing that unlocked v12 (4–10× more
candidates ⇒ −114M). Improvements 3/4/5 are all solver/iteration-bound; a
2–5× speedup in the raster scan + exact-check path multiplies all of them.
The env ships numba (contest env yml includes it — verify import under
`.venv_ogc` AND keep a pure-python fallback since the hidden server must
never crash on a missing/broken JIT).

**Mechanism.**
1. Profile first (cProfile on a 60s prob_38 build): expected hotspots are
   the sliding-window mask scan, mask AND/OR composition, and the placement
   scoring loop. Do not optimize unprofiled code.
2. numba `@njit` the top 2–3 kernels (they are already numpy-array-shaped);
   OR pure-numpy re-vectorization where the loop is python-level. Warm the
   JIT during the construction of the fallback solution (first seconds) so
   compile time never eats search time.
3. Guard: `try: import numba` — on failure, identical pure-python path.
   Determinism: JIT must not change float semantics in scoring comparisons;
   if any banked value shifts, pin the scoring path to pure python and JIT
   only boolean geometry kernels.

**Wiring.** Same quarantine as Improvement 6: explorer slots only in 19b;
global enablement is a SEPARATE sub-version (19e) with full protect + the
attribution/restoration playbook ready, because a global speedup shifts
every iteration count and WILL displace basins (v14 lesson). Global
enablement is only worth it if the speedup lets legacy slots finish
provably-truncated work (measure: do legacy slots currently hit their
per-phase budget ceilings? If they don't, global JIT buys nothing — skip).

**Units.** Kernel-level A/B: byte-identical outputs on 10k random mask
queries; ≥ 2× wall-clock on the profiled kernels on prob_38.

**Kill criterion.** < 1.5× end-to-end build speedup ⇒ not worth the risk
surface; keep it in explorer slots only or drop.

**Expected yield.** Multiplier (more MPC epochs, more LAHC iterations, more
layout columns per slot). No direct objective claim.

### Improvement 8 — Exit-blocking instrumentation, then exit-lane discipline (measure-first)

**Why.** Untested hypothesis from CONTEXT.md that has never been quantified
in this campaign: some giant tardiness may come not from entry-queue delay
but from EXIT delay — crane-path blocking forcing conservative co-residency
or late exits. If true, placement should reserve exit lanes; if false, we
close the question forever. Cost: half a day.

**Mechanism, phase A (measure, zero risk).** Counters in a probe build (NOT
the submission file) on {38, 27, 39, 31}: (a) # of placement candidates
rejected ONLY by exit-prism checks; (b) # of exits delayed past
`entry + processing` because the crane path was blocked at the earliest exit
event; (c) total tardiness attributable to (b) (exit_actual − exit_earliest
for tardy blocks). Report in ledger_19.md.

**Mechanism, phase B (only if (c) > ~3% of instance tardiness).** Exit-lane
discipline in the explorer constructors: score-penalize placements that put
a block's footprint inside the vertical prism of any earlier-due co-resident
(pairwise, cached); prefer "front" (low-y or lane-aligned) positions for
early-due blocks. Tunable penalty weight, swept {small, medium} in the slot.

**Units/gate.** Phase A numbers decide. Phase B ships only behind an
explorer-slot flag and must show ≥ −300k on its target instance to survive.

**Kill criterion.** (c) < 3% on all four probes ⇒ document "exit blocking
immaterial on giants" in the ledger and never revisit.

**Expected yield.** 0 (likely) or −0.5M … −2M (if the hypothesis is real on
27/38 where co-residency is extreme).

### Improvement 9 — Micro-time audit: same-tick handoff and off-event entry candidates

**Why.** Two low-level scheduling degrees of freedom may be silently unused
(cheap to audit, and in saturated bays each is direct queue-delay reduction):
1. **Same-tick handoff.** Rules: at time t, ALL EXITs precede ALL ENTRYs. So
   block B can enter at the exact tick block A exits, INTO A's footprint.
   If the dispatcher only tries entries at event times but tests entry
   feasibility against the pre-exit occupancy, it misses every handoff.
2. **Off-event entry times.** If candidate entry times are only
   {release, existing exits}, a position that becomes crane-feasible between
   events (e.g. after a neighbor's entry unblocks a prism at t+3) is never
   tried.

**Mechanism.** (a) AUDIT the v18 dispatcher code path: confirm/refute each of
the two, with a 20-line trace on prob_27 (count handoff placements actually
used; count feasible-but-never-tried off-event candidates in a sampled
window). (b) If (1) is unused: at each exit event, re-offer the freed
footprint to the queue head in the same tick (occupancy state ordered
exits-first — the official checker semantics). If (2) is real: add `t+δ`
candidates for δ ∈ {1, 2, 4, g/2} at top-scored blocked positions only
(bounded, to protect throughput).

**Wiring.** Explorer slots first (§11), same quarantine logic; legacy path
opt-in per instance only after a clean spot round on {27, 38}.

**Units.** Official-checker semantics test: construct a 3-block synthetic
where the handoff is the ONLY feasible schedule; verify `check_feasibility`
accepts our emitted op order (EXIT then ENTRY same tick).

**Spot gate.** prob_27 ≥ −300k or prob_38 ≥ −300k in the explorer build.

**Kill criterion.** Audit shows both already exploited ⇒ close, zero cost.

**Expected yield.** −0.3M … −1.5M on the saturated pair if the audit finds
either gap; the handoff especially targets exactly their binding constraint
(space-time reuse at full density).

### Improvement 10 — Campaign protocol: explorer/exploiter split, sub-version ladder, and kill-fast discipline

**Why.** Ten mechanisms cannot ship as one diff. v14 taught what a mixed diff
does to banked basins; v17 taught that restoration costs ~2h/instance of
attribution machine time. The protocol IS an improvement: it is the
difference between −25M compounding and −25M of churn.

**Mechanism.**
1. **Slot economics first.** From v18's structure, identify the phases that
   are provably dead weight on saturated instances (e.g. window-shot
   rotations on 38 that have never accepted; harvest cycles on instances
   where attribution shows W3-raw wins everything). Reclaim those slots as
   EXPLORER slots on a per-instance basis — the same trick v16/v18 used for
   reclaimed streams. Legacy winning paths keep their slots BYTE-EXACT
   (v17's W0-clone discipline): on every instance, at least one worker runs
   the exact v18 path so the banked value is always reproduced. **The bench
   can therefore never regress above +ε per instance — that invariant is
   what makes aggressive exploration affordable.**
2. **Sub-version ladder.**
   - **19a** = Improvements 1 + 8A + 9-audit (measure-only; no submission
     code touched; deliverable = ledger_19.md).
   - **19b** = explorer infrastructure + Improvement 5 (LAHC on 31/39) +
     Improvements 6/7 inside the slots. Spot: {31, 39, 26, 33}. Protect:
     {38, 27, 21, 23, 28, 30, 34, 35} + prob_1 @60s byte.
   - **19c** = Improvement 3 (MPC constructor) and 4 (layout book) competing
     in the giant slot. Spot: {38, 27, 39}. Protect: previous winners.
   - **19d** = Improvement 2 (flow plan), consuming 19a's calibration and
     19c's density tools. Spot: {38, 27, 26}.
   - **19e** = assembly: global enablement decisions (Improvement 7 global?
     6 on legacy paths?), row hygiene vs the per-instance best-known union
     across v13..v19 (attribution-probe playbook for anything displaced),
     full-40 @600s bench_row.
   Each sub-version: commit, record spot numbers in this file's Results
   section, THEN proceed. A sub-version that fails its gate is recorded
   (dead-family ledger grows) and its slot reverts — no partial keeps.
3. **Kill-fast discipline.** Every improvement above has an explicit kill
   criterion; honor them in ≤ 2 working days each. The ledger (19a) sets
   per-instance stop-lines: when an instance reaches its realistic target,
   STOP SPENDING THERE regardless of remaining fluid gap.
4. **Bench hygiene** (unchanged, restated): serial runs, quiet machine —
   CHECK MACHINE LOAD before every bench; foreign apps corrupt numbers.
   16GB ceiling — the CP-SAT models in 2/3/4 must cap variables (menu
   shrink, the v17 adaptive K trick) and be memory-profiled once on prob_38
   (300 blocks) before any long run.

**Expected value.** Protects 149.83M while the payload lands; converts the
ten ideas into ≤ 5 measurable diffs.

---

## 11. THE QUARANTINE RULE (mandatory, applies to Improvements 2,3,4,5,6,7,9)

Any code that changes iteration counts, rng consumption, candidate counts, or
float scoring on a SHARED path displaces banked basins on untouched instances
(campaign law; v14 cost +0.6M collateral this way). Therefore every new
mechanism in v19:
- runs in a DEDICATED explorer slot (its own worker phase / stream), with its
  own rng stream seeded independently (`seed = hash(instance, slot_name)`);
- never imports its behavior into a legacy path except behind a per-instance
  flag flipped only after a clean spot round + protect round;
- banks results ONLY through the existing verify + min-wins accept;
- on every instance at least one worker reproduces the v18 winning path
  byte-exactly (the W0-clone discipline from v17).
If a protect check ever misses, the FIRST suspect is pacing displacement:
run the attribution probe, restore via slot-clone, and only then look for
real bugs.

## 12. Budget & mechanics

- Baseline file: `baseline/myalgorithm_19.py` from v18 (commit b356c58).
  W0 byte-exact outside reclaimed slots. `myalgorithm.py` untouched until a
  full-40 row beats 149,831,986.
- Env: `.venv_ogc` python (no conda on this machine despite README);
  ortools guarded everywhere (hidden server has no commercial solvers —
  CP-SAT only, never gurobipy/xpress); numba guarded with pure fallback.
  Contest realities: 4 cores, 16GB, minutes-to-half-hour limits, no internet.
- Bench convention: spot rounds @600s serial on the named sets; protect
  rounds on {38,27,35,31,30,34,28,26,21,23} (superset of prior protects,
  because v19 touches giants directly) + prob_1 @60s byte-exact; full-40
  bench_row @600s only at 19e.
- Record everything in results.csv + this file's Results section, commit
  each sub-version (evolve.md protocol), push to dev/jay. Cloud agent note:
  pull before local work; cloud bench rows are NOT comparable to local.

## 13. Honesty clause — what if the ledger says <125M is unreachable?

If Improvement 1's realistic-target sum says the 600s frontier is above
125M, the options, in order of preference: (a) land the Tier-C construction
theories anyway and re-measure the frontier — the ledger's `d_k` calibration
itself moves if Improvement 4 finds denser layouts; (b) escalate the
convention to 1800s/instance ONLY together with mechanisms that are actually
time-responsive (v18 measured the giants byte-flat at 2× budget, so budget
alone is a proven zero — new mechanisms must first create time-responsiveness,
then budget can amplify them; 1800s is still contest-defensible per the
"half an hour" limit on much faster hardware); (c) renegotiate the goal with
the measured frontier as evidence. Do NOT silently bench-shop budgets.

## Results (filled after testing)

### 19a — ledger + instrumentation (DONE — see heuristics/ledger_19.md)
Tier-T capacity-honest measurement (the plan's "do first"). Method: reconstruct
the TRUE banked incumbent by running the real v18 4-worker `algorithm()` and
converting its operations back to an assignment (`baseline/run_v18_save.py`),
then measure realized bay density + admission delay + tardiness
(`baseline/measure_giant.py`). **Decisive result: the four big rocks
(38/27/39/31 = 96.6M, the plan's entire targetable mass) are DENSITY-SATURATED —
peak realized bay density ≥ 0.94 on every bay, > 1.0 where multi-layer stacking
is exploited.** No packing slack remains. This refutes the premise of
Improvements 2/3/4 (all assume untapped density); the fluid LBs the −24.84M
thesis rested on are ~40% loose preemptive mirages. Realistic floor ≈ incumbent.
Frontier verdict: **<125M is NOT reachable** — even conceding the entire
mid-band optimistically (−3M) leaves ~146.8M. This is the §13 case.

### 19b — acceptance-rule diversification (Improvement 5) — MEASURED DEAD
The one genuinely-untried family. Tested from the true banked incumbents
(`baseline/accept_test.py`, `baseline/lahc_run.py`):
- greedy floor: 31 → 11,030,700 (−25k); **39 → FLAT (+0)** (giant not
  round-starved once converged).
- SA (`sa=True`, the wired-but-never-used uphill path): 31 → 11,030,700,
  IDENTICAL to greedy — no better basin reachable.
- LAHC ruin-recreate, multiple L/ruin/seed configs incl. seeded history:
  43–56 uphill accepts (it wanders), best-seen NEVER below incumbent on 31 or 39.
- Throughput wall: ~0.2–0.7 iters/s; profiling pins 92% in `_Raster.scan_scoped`;
  numba NOT importable in `.venv_ogc` → Improvement 7 (the multiplier the plan
  counted on) unavailable. Iteration-heavy metaheuristics structurally infeasible.
Kill criterion ("31 AND 39 flat") MET → the campaign's **tenth measured-dead
family**.

### 19c/19d — MPC constructor / layout book / calibrated flow plan — NOT PURSUED
19a's saturation measurement is exactly Improvement 4's own cheap kill test
("if exact density-max cannot beat accidental density, kill early"): accidental
density is already ≥0.94–1.13, so exact density-max cannot beat it. Implementing
the intricate rolling-horizon CP-SAT machinery to reconfirm a measured-negative
result is poor engineering judgment. Recorded as premise-refuted, not attempted.

### 19e — assembly + full-40 @600s
myalgorithm_19.py == v18 (no mechanism improved on it). `myalgorithm.py` stays
v18 (code unchanged). §13 decision surfaced to the user → user chose "renegotiate
to a reachable target".

**Renegotiated-target harvest (clean 600s re-bench, 9 variable non-giant insts):**
Only prob_31 moved reliably: banked 11,268,243 → clean 10,981,881 (−286,362),
CONFIRMED by two independent clean runs (300s=11,055,999; 600s=10,981,881, both
< banked, and more budget gave the lower value) ⇒ the banked cell was a
loaded-machine artifact, not a lucky draw. prob_32 REGRESSED +54,186 on one
clean run (inconclusive noise). prob_26/33/37/30/23/28/40 reproduced banked
BYTE-EXACTLY (deterministic/saturated). So within-version run variance is real
but BIDIRECTIONAL and small (confirms dead family #7: re-rolling is not a lever;
taking per-instance mins would be bench-shopping). Recorded row `algorithm 19`
= actual clean measurements (31/32 re-measured, rest banked) = **149,599,810**
(−232,176 vs v18, all of it the two-sided noise on 31/32; NOT an algorithmic
gain). Honest frontier ≈ 149.55–149.83M within noise. **<125M remains
structurally unreachable** (19a). No code change; the campaign's lever arsenal
is exhausted.
