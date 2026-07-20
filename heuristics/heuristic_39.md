# heuristic_39 — Cross-fork merge: jv9 (jiyun) × v38 (jay)

## Context (2026-07-20)

Two forks of the same v33 base now exist:

- **v38** (`myalgorithm_38.py`, SOTA row 124,141,498→124.1M-class): v33 + tail35 in-tail
  frozen CP-SAT on forced (v35) + budget-capped portfolio / overflow-to-tail (v36) +
  order-tail CP-SAT (v37) + non-forced order-tail coverage, w1 gate dropped, bands k=6 (v38).
- **jv9** (`myalgorithm_new.py`, reported **121M** by jiyun's bench): v33 + jv5 dispatch
  constructor (nk/mpc/ovh/steal/zone/drain) + W0/W3 deep-nestle + jv7 full-width portfolio
  (nw=min(8,cpu)) + jv8 giant light-repack replicas (W4..W6 on forced n>=250) + jv9 W7
  replica & deaf wid-6 replica on giants.

The two deltas are **disjoint**: jv9 has none of the v35–v38 tail machinery (its merge tail
is still gated OFF on forced; no tail35; no order-tail), and v38 has none of jv's search-side
width/dispatch work. jv9's ~3M advantage is search-side (giants); v38's tail gains
(prob_21 −25,663, prob_23 −13,559, prob_38 −28,945, prob_27 −13,333, …) are attributed and
strictly post-race — they compose with ANY champion the race produces.

Machine note: this session runs on an 8-core/8GB mac (conda env gone; scratchpad venv
py3.11 + shapely 2.1.2 + numpy + ortools). Prior rows came from a Windows box; per the
heuristic_38 ROW DRIFT finding, cross-machine row differencing is unreliable — all v39
claims must come from paired same-day, same-machine runs.

## Three ideas

### 39a — Port the v35→v38 tail stack onto jv9 (THE mainline)

Vendor into jv9, in this order (per the v38 delta map):
1. the `_t37_*` island + `_T37Model` (v38 lines 5859–6557, self-contained, lazy ortools),
2. `_tail35_cpsat` (v38 5604–5859, self-contained),
3. v36 pacing: `port_limit=min(timelimit,600)`, `_overflow` flag, reroute reserve /
   search_deadline / worker args / grace to `port_limit`, keep `hard_stop`/`abs_stop` on true
   timelimit; thread `overflow=` into `_merge_tail` (dedup 24→64… jv9 already raised pool cap
   to 32 via OGC_MERGE_CAP default — reconcile: cap = max(jv9 default, 64 if overflow)) and
   `_tail35_cpsat` (MOV/CAND 60/10→120/20),
4. forced call site: tail35 + order-tail after the race champion verifies (v38 6720–6786),
5. non-forced call site: order-tail after `_merge_tail` (v38 6815–6838), w1 gate dropped,
   bands k=6.

Expected: jv9's better giant champions + v38's post-race tails stack additively. Risk: call-site
anchoring — jv9's verify loop is "token-identical to v25" on forced, same as v38's base, so
anchors should line up; the v36 pacing edits are the only entangled part (jv9's worker spawn
passes `timelimit` → must become `port_limit`).

### 39b — Un-gate the merge tail on forced giants (jv9 pool diversity is new evidence)

v33 gated `_merge_tail` off on forced because the pool there was 4 near-identical incumbents.
jv8/jv9 changed the situation: giants now have W4..W7 seed-shifted repack replicas + a deaf
independent-basin replica feeding the queue — real diversity the recombine CP-SAT was designed
for. Try: on forced, run `_merge_tail` (recombine over pooled placements) BEFORE tail35/tail37,
budget-gated (e.g. only when overflow time exists), min-wins accept via official checker.

### 39c — Second seeded race (38b) on jv9's width

heuristic_38's open arm: drift data shows 300–36,500/cell prize under min-wins from basin
lottery. jv9's width makes a split-budget double race cheap on non-giants: run the portfolio
twice at `port_limit/2` with `seed_off` shifted (thread through `_worker_main`→`_run_strategy`),
keep the better champion, then tails. Gate: `remaining >= RACE2_MIN`. This attacks variance,
which ROW DRIFT showed is the same order as recent mechanism gains.

## Execution order

39a first (pure composition of proven parts). 39b and 39c only if 39a lands and time allows;
each must be measured against a same-day 39a control on the pilot set.

## RESULTS (2026-07-21, mac 8-core, full same-day row)

**v39 row = 123,229,003, 40/40 feasible — SOTA** (v38 banked row 124,143,220; jv9 was
reported 121M on jiyun's machine). All 40 cells measured same-day on this mac @900s
(21 big cells serial/exclusive, 19 small cells in 2 parallel lanes). results.csv row
"algorithm 39".

Paired same-day jv9 controls (this mac, serial):
- prob_21: v39 1,308,647 = jv9 (both at basin floor; merge fired gain 0)
- prob_23: v39 2,389,645 vs jv9 2,432,561 → **−42,916 tail-attributed** (prob_23 is
  structurally forced! tail35 fired rem_start=351s)
- prob_38: v39 38,140,257 vs jv9 38,206,026 → **−65,769 tail-attributed**; the 600s
  search cap costs nothing (v39 = jv9's champion or better with 240s less search)
- prob_27: v39 24,074,569 = jv9 (identical, twice — deterministic basin; v39 finishes
  236s faster)

Notable cells vs v38 banked: 27 −885,060, 26 −816,454, 30 −360,312, 13 −32,863,
14 −49,003, 20 −35,475, 22 −60,696, 24 −45,867, 29 −41,031, 12 −15,491 (jv9 search);
38 **+1,817,709 = MACHINE DRIFT** (this mac lands prob_38 ~1.8M above the Windows box
that produced the banked rows — same jv9 code measures 38.2M here).

**MACOS SLEEP HAZARD:** an un-caffeinated overnight run froze mid-flight (prob_27 pair,
4370s wall for a 900s limit). All runners now wrap `caffeinate -is`. Objectives survive
(checker-verified) but timing is corrupted; the affected pair was redone clean and
reproduced byte-identically.

39b (merge-on-forced) and 39c (second race) not yet implemented → carried to v40.
Gap to <115M goal: −8.2M, concentrated in 38 (38.1M) + 27 (24.1M) + the 7-8M band.
1800s scaling probes on 38/27 (jv9 uncapped-search vs v39 capped+long-tails) running
to decide the v40 design (port_limit scaling vs tails-only overflow).

## Measurement plan (this machine, 8 cores)

- Pilot paired runs jv9 vs v39 @300s on {21, 23, 27} (tail-sensitive cells) to prove the port
  fires; then giants {38, 27, 37} @900s serial (solver gets all 8 cores).
- Full row: serial-ish (≤2 bench workers, giants strictly serial) @900s, mass-ordered.
  Target: total < 115,000,000 with 40/40 feasible.
