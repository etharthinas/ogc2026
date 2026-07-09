# Research survey for the v19 campaign — what the literature says about our problem

> Compiled 2026-07-09 from a 5-track parallel web survey (shipyard spatial
> scheduling / 2D irregular nesting / metaheuristic search control / analogous
> space-time allocation problems / matheuristics & CP-SAT). Full track notes
> with all links live in the session scratchpad; every load-bearing claim here
> keeps its source. Read together with `heuristic_19.md` — each finding is
> mapped onto that plan's Improvements 1–10.

## 0. Headline conclusions

1. **Our problem is a named literature problem.** "Spatial scheduling problem"
   (SSP) / "block spatial scheduling" (BSS), studied since the DAS system at
   Daewoo's Koje yard (Lee, Lee & Choi 1996). Our v18 architecture —
   priority-rule dispatcher + placement heuristic + repair — is exactly the
   field's standard architecture. Published systems report **70–80% effective
   area utilization** vs our measured eta* of 0.28–0.48: the density headroom
   our instance analysis found is corroborated externally.
2. **The nesting literature's consensus explains our nine dead families.**
   Construction heuristics (any ordering × any placement rule) plateau far
   below SOTA because the ordering→quality mapping is chaotic
   ([sparrow, arXiv:2509.13329](https://arxiv.org/abs/2509.13329)). Every
   modern SOTA nesting method instead starts from a complete layout,
   **deliberately creates overlap, and repairs it with guided local search**
   (GLS) over a continuous collision-severity metric. We have never done this:
   all v1–v18 mechanisms preserve feasibility at every step. This is the
   single biggest untried idea in the file.
3. **Our LNS acceptance rule is the one clearly-wrong choice in a published
   comparison.** Santini, Ropke & Hvattum (J. Heuristics 2018) tested 9
   acceptance criteria inside LNS: hill-climbing-only (= our obj-gated rule)
   and random walk were "clearly inferior"; SA/TA/linear
   Record-to-Record-Travel formed the best group; LAHC mid-tier with few
   expensive iterations, strong with many cheap ones
   ([PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)).
   Improvement 5 (LAHC explorer) is therefore well-aimed; parameters below.
4. **No prior OGC write-ups exist to mine** (2024/2025 editions have no public
   winner reports; 2026 finalist code is disclosed only after the contest).
   Closest proxy: the CG:SHOP 2024 packing challenge, whose winners all used
   greedy construction → local search → **exact (ILP) refinement on
   subregions** ([arXiv:2403.16203](https://arxiv.org/pdf/2403.16203)) —
   the same shape as our portfolio + exact windows.

## 1. The density engine we are missing: overlap-tolerant GLS ("sparrow-style")

**What it is.** The 2007–2025 SOTA lineage for irregular packing (Egeblad 2007
→ [Umetani 2009 GLS](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-3995.2009.00707.x)
→ [rasterized coordinate descent, arXiv:2104.04525](https://ar5iv.labs.arxiv.org/html/2104.04525)
→ [sparrow 2025, arXiv:2509.13329](https://arxiv.org/abs/2509.13329) +
[open Rust code, MIT](https://github.com/JeroenGar/sparrow)): force an
improvement that creates overlap (shrink the container / insert a block into a
too-early slot), then minimize a **weighted overlap-severity function** with
per-pair GLS penalty weights that grow on persistently-colliding pairs. The
search traverses the infeasible corridor between two dense feasible layouts —
precisely what our feasible-only moves cannot do.

**Why it fits us unusually well.**
- Our raster masks are a first-class geometry kernel in this literature
  (Sato's raster penetration maps; Umetani's rasterized line searches) — and
  on the contest's integer grid the raster is *exact*, not an approximation.
- Sparrow's collision-severity proxy ("poles" = 8–16 largest inscribed
  circles per shape, from a one-time distance transform of our masks;
  severity = pairwise circle penetration, ~300 flops/pair, numpy-vectorizable)
  gives the cheap gradient signal greedy repair lacks.
- Time dimension: a collision pair = same-layer masks overlapping AND dwell
  intervals overlapping; crane entry/exit events add per-instant hazard pairs.
  Both fit the same severity sum.

**Concrete module (the "compress" move for 38/27/39/26).** On a (bay ×
time-window) snapshot: force block b's entry earlier (or shift a virtual bay
wall inward), creating overlap; run sparrow's separate() loop — sample ~50
candidate positions per colliding block (uniform + local), score by
Σ w_pair·severity, refine best few by ±1/±2/±4-cell coordinate descent, update
GLS weights, restore incumbent between attempts — then commit the repacked
window through the existing splice + official-verify path. Tens of ms per
separate() at |R|≤30. This is the strongest candidate yet for the "different
construction theory" the v18 verdict demanded for 38/27, and it can also serve
as Improvement 3's placement engine and Improvement 4's layout densifier.

**Cheap precursors (portfolio lottery tickets, ~day each):**
- **Jostle re-fill** ([Dowsland 1998](https://www.semanticscholar.org/paper/c252d981ee9f14ce1e85e2520e724100aec5f27d);
  [IJPE 2018 PDF](https://eprints.soton.ac.uk/414392/1/Accepted_article_IJPE.pdf)):
  alternate left-fill / right-fill passes over a congested bay-epoch, each pass
  ordered by the previous layout's coordinates; accept if the largest free
  rectangle grows. Reuses ~90% existing code.
- **Contact-perimeter / diagonal-fill placement scoring**
  ([Shang 2017](https://www.hindawi.com/journals/mpe/2017/1923646/);
  [Kwon & Lee 2015](https://www.sciencedirect.com/science/article/abs/pii/S0360835215002296)):
  score raster positions by boundary-contact cells; or dual-anchor fill
  (bottom-left + top-right) keeping free space contiguous in the middle —
  reported to beat plain bottom-left in our exact problem family.
- **DAS positioning strategies** ([DAS EJOR 1997 PDF](https://bmer.net/wp-content/uploads/2010/11/dasejor.pdf)):
  "maximal remnant space utilization" (overlap your bounding-box waste with
  neighbors' bounding-box waste) and "maximal free rectangle" scoring — 1996
  domain wisdom that our perimeter-contact ranking doesn't capture.
- **LP/CP compaction ("squeeze")** ([Gomes & Oliveira 2006](https://www.sciencedirect.com/science/article/abs/pii/S0377221704005879);
  [raster separation-and-compaction, ESWA 2023](https://www.sciencedirect.com/science/article/abs/pii/S0957417423002178)):
  small CP-SAT over integer (dx,dy) per co-resident block, trust region ≤4
  cells, one separating half-plane constraint per time-overlapping pair,
  objective = slide everything toward a wall. Coordinated multi-block slides
  that single-block moves can't make; re-verify crane events post-solve.

## 2. Improvement 5 (LAHC explorer) — evidence-based parameter sheet

- **Use "Improved LAHC"**: accept iff `f(cand) ≤ f(hist[i mod L])` **OR**
  `f(cand) ≤ f(current)`, with `≤` (not `<`) so w1-tardiness plateaus can
  drift ([Santini et al. description](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)).
- **L from the iteration budget, not instance features** (convergence time ∝
  L). Strongest direct datapoint: **GDRR**, a 2025 SOTA ruin-recreate
  guillotine-packing solver that uses LAHC with **L=1000 for 100–300 items**
  (our exact range), greedy recreate with **blink rate 0.05**
  ([arXiv:2508.19306](https://arxiv.org/html/2508.19306v1)). If an iteration
  costs 20–100 ms, scale down to L=200–500 keeping total_iters/L ≥ 50–100.
- **Restart on idle-acceptance streaks** ≈ 2% of elapsed iterations
  ([practical notes](https://github.com/Gunnstein/lahc)). Avoid deepcopy in
  the loop — the classic LAHC bottleneck (our assignment dicts pickle slowly).
- **Hedge**: implement **linear Record-to-Record Travel** behind a flag
  (accept iff `f(cand) < f(best) + T`, T linear → 0 over the slot;
  "consistently undominated" in the comparison study) and A/B it against LAHC
  in the explorer slot.
- **Ruin design — replace random removal with SISR-style strings**
  ([Christiaens & Vanden Berghe, Transp. Sci. 2020](https://pubsonline.informs.org/doi/10.1287/trsc.2019.0914)):
  random scatter-holes are re-filled idempotently by greedy repair (this is
  why our current ruin re-finds the same basin); removing one **contiguous
  spatio-temporal cluster** (same bay, (x,y)-adjacent, time-overlapping;
  avg ≈ 10 blocks, cap ≈ 15) concentrates slack so repair can genuinely
  restructure. Second operator: bay×time-strip removal. Repair keeps the
  existing greedy but adds **blinks** (skip best position w.p. 0.01–0.05).
- **Reactive ruin sizing**: on idle streaks escalate 1 string → 2 strings →
  bay-strip → whole-bay; reset on new best (ILS guidance).
- **Skip ALNS adaptive weights**: meta-analysis of 25 ALNS papers measured the
  adaptive layer at **+0.14% average** ([Turkeš et al., EJOR 2021](https://www.sciencedirect.com/science/article/abs/pii/S037722172030936X)).
  Operator design matters; roulette wheels don't.

## 3. Improvement 8 phase B — stacking-theory placement rules (from container/slab yards)

Our crane constraint is exactly yard-stacking retrieval blocking. The rules
that dominate reshuffle-minimization there transfer as placement tie-breaks
(pure scoring, zero new feasibility machinery):
- **Departure-time nesting** ([Dekker et al.](https://www.researchgate.net/publication/226468887_Advanced_methods_for_container_stacking)):
  place A's upper layers over B only if A exits before B → prefer
  exit-monotone stacks (upper exits first). We *know* exits exactly (we set
  them), which the stacking literature calls the best case.
- **ERI-style risk scoring** ([Stochastic CRP, Galle et al.](https://arxiv.org/pdf/1703.04769)):
  penalize (i) same-or-higher-layer overlap with a co-resident whose exit
  precedes ours, (ii) nesting slack min|exit_i − exit_j| < τ (retiming later
  breaks tight nests), choosing the "just above" candidate when forced.
- **Don't statically reserve crane lanes** — dynamic space sharing beats rigid
  reservation ([yard template, EJOR 2012](https://www.sciencedirect.com/science/article/abs/pii/S0377221712002044));
  penalize skyline fragmentation at times when known large blocks arrive
  instead.

## 4. CP-SAT window revival — why our exact windows saturated and what unsaturates them

- **Cell-cover instead of pairwise booleans** (dotted-board line:
  [Toledo 2013](https://www.sciencedirect.com/science/article/abs/pii/S0925527313001722);
  [clique-cover MIP 2017](https://www.sciencedirect.com/science/article/abs/pii/S0305054816302702)):
  coarsen the bay into 2×2/4×4 super-cells; per (super-cell, layer, time
  slice) add AtMostOne over covering placement literals. Constraint count
  drops from O(menu²·pairs) to O(cells·placements) → menus can grow from
  K=12 to 100+ positions. Keep exact pairwise checks as lazy conflict clauses.
- **Solver knobs** ([CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/advanced_modelling.html);
  [or-tools #3177](https://github.com/google/or-tools/discussions/3177)):
  `use_energetic_reasoning_in_no_overlap_2d`, `use_timetabling_in_no_overlap_2d`,
  `use_pairwise_reasoning_in_no_overlap_2d` — up to ~10× reported; benchmark
  on our ortools 9.15. One big NoOverlap2D with per-bay x-offsets beats
  per-bay models. Add redundant per-bay area cumulatives.
- **Always `AddHint` the incumbent** in every window solve; CP-SAT runs
  internal LNS off hints ([CP-SAT-LP, CP 2023](https://drops.dagstuhl.de/storage/00lipics/lipics-vol280-cp2023/LIPIcs.CP.2023.3/LIPIcs.CP.2023.3.pdf)).
- **Adaptive window sizing** ([Primer LNS chapter](https://d-krupke.github.io/cpsat-primer/lns.html)):
  shrink the destroyed set when a solve times out, grow when it solves —
  exponential factors. Our fixed D=14/K=12 saturation is the textbook symptom.
  Rotate a small pool of window types (time-band × bay-region /
  tardy-cluster / cross-bay swap) with stick-on-success switching.

## 5. Improvements 1–3 refinements from Benders / MPC literature

- **LB ledger as logic-based Benders (Improvement 1)**
  ([Hooker](https://johnhooker.tepper.cmu.edu/planning2.pdf)): the bucketed
  capacity model is the *master relaxation*; every failed exact-pack window is
  a **no-good cut** ("these k blocks cannot co-reside in bay b") — minimize
  the infeasible subset by greedy dropping, then feed it back to tighten the
  ledger where the area bound is too optimistic. Hooker: master-side
  subproblem relaxations are the single highest-leverage LBBD device.
  Calibrate the density coefficient at our measured 0.48, not 1.0.
- **DSA theory endorses calibrated flow gating (Improvement 2)**:
  OPT = Θ(LOAD) for dynamic storage allocation
  ([SICOMP](https://epubs.siam.org/doi/10.1137/S0097539703423941)) — the
  constant is what you calibrate empirically. This is exactly the
  "calibrated capacity, not fluid capacity" fix, now with theory behind it.
- **MPC constructor (Improvement 3), Ovacik–Uzsoy style**
  ([rolling-horizon heuristics](https://www.tandfonline.com/doi/abs/10.1080/00207549408956998)):
  solve overlapping windows exactly but **commit only a prefix** (~first 1/3
  of admissions) before rolling; adaptive window size (exponential
  grow/shrink on solve-within-limit). Terminal cost: θ·(admitted area) is the
  right shape, but θ should approximate the marginal future objective per
  admitted-area unit — **regress it from our own portfolio-run traces**
  (final tardiness vs area admitted by time t), and add a term valuing
  remaining slack of unadmitted urgent blocks, or the window model banks area
  while starving urgent blocks (end-of-horizon effect,
  [arXiv:2104.02863](https://arxiv.org/abs/2104.02863)).
- **Layout book (Improvement 4) = Monaci–Toth restricted set covering**
  ([IJOC 2006](https://pubsonline.informs.org/doi/10.1287/ijoc.1040.0089)):
  no pricing loop needed — harvest columns heuristically (from ALL portfolio/
  LNS runs + exact-pack density-max solves), then one small master picks a
  per-bay pattern sequence. Published validation in our own problem family:
  Zhang & Chen's **agglomeration** stage merges blocks with compatible time
  windows and complementary footprints into composite blocks before
  scheduling ([IJPR 2012](https://www.tandfonline.com/doi/abs/10.1080/00207543.2011.588623));
  GSPP/column models dominate exact berth allocation
  ([EJOR 2016](https://ideas.repec.org/a/eee/ejores/v250y2016i3p1001-1012.html)).

## 6. New candidate mechanism: Squeaky Wheel Optimization (SWO)

Construct → assign blame (per-block w1·tardiness + α·pref + β·space-it-held
while later blocks queued) → promote blamed blocks in the priority sequence →
reconstruct; accept sequences by LAHC. Documented wins on 2D strip packing and
oversubscribed interval problems
([Joslin & Clements JAIR 1999](https://arxiv.org/abs/1105.5454);
[SWO strip packing, C&OR](https://www.sciencedirect.com/science/article/abs/pii/S0305054810002200)).

**Dead-family adjacency warning**: family #1 (alpha-ATC triage variants) is
"order shuffles who is tardy, not total queue delay." SWO differs in being a
*feedback loop over the realized schedule* rather than a static rule variant —
but the burden of proof is on SWO. License it only as an explorer-slot
lottery ticket on {31, 33, 39} (NOT 38/27 where order levers died), with the
standard spot gate and a 2-day kill.

## 7. Structural randomness (fixes the "deterministic basin" pathology at the root)

Bet-and-run theory ([Fischetti & Monaci, OR 2014](http://www.dei.unipd.it/~fisch/papers/exploiting_erraticism_in_search.pdf)):
deterministic greedy search is a chaotic amplifier; you exploit it by running
k short *structurally diversified* runs then betting the budget on the best.
Our within-version determinism means seed changes do nothing unless the
algorithm has stochastic decision points. Cheap injection points: jittered ATC
weights, restricted candidate lists (top-k raster positions, pick uniformly),
blink repairs. Combined with min-wins banking this is strictly
regression-safe. GRASP path relinking between the 4 workers' elites
(relink the most *distant* pairs) is the principled way to combine basins
([Resende & Ribeiro](https://mauricio.resende.info/doc/sgrasppr.pdf)).

## 8. Explicitly deprioritized (so nobody burns time)

- **Learning-based placement / DRL**: no ESICUP-benchmark wins over GLS-class
  heuristics; wrong cost profile for CPU-only 4-core evaluation. Skip.
- **GA over orderings** (SVGnest-class): below our current portfolio. Skip.
- **ALNS adaptive weight layer**: +0.14% measured. Skip.
- **Static crane-lane reservation**: dominated by dynamic sharing + scoring.

## 9. Priority mapping onto the v19 ladder

| Rank | Idea | Feeds | Targets | Effort | Risk notes |
|---|---|---|---|---|---|
| 1 | Overlap-tolerant GLS compress (sparrow-style) | new engine for Impr. 3/4, or standalone explorer | 38, 27, 39, 26 | 3–5 d | genuinely new family; quarantine per §11 |
| 2 | SISR ruin + blinks + Improved-LAHC params (L=1000) + linear-RRT hedge | Impr. 5 | 31, 39, 26, 33 | 1–2 d | direct GDRR precedent at our scale |
| 3 | Cell-cover CP-SAT windows + solver knobs + AddHint + adaptive D/K | revives exact windows; Impr. 3/4 machinery | 38, 27, 39, 26 | 1–2 d | attacks a measured plateau with a published fix |
| 4 | ERI / departure-nesting placement scoring | Impr. 8B | 38, 27, 39, 31 | 1 d | gate on Impr. 8A counters first |
| 5 | Jostle + contact/diagonal-fill + DAS remnant-space scoring | constructor lottery tickets | broad 21–40 | 1 d each | cheap; explorer slots only |
| 6 | MPC commit-prefix + regressed θ + slack terminal term | Impr. 3 | 38, 27, 39 | refine | prevents known end-of-horizon failure |
| 7 | LBBD no-good cuts into the ledger | Impr. 1/2 | targeting | refine | makes the gate self-correcting |
| 8 | Monaci–Toth harvested-column master | Impr. 4 | 38, 27, 39, 26 | refine | columns from runs we already do |
| 9 | SWO blame loop | new explorer ticket | 31, 33, 39 | 1–2 d | dead-family-1 adjacent — kill fast |
| 10 | Bet-and-run + RCL/jitter + path relinking | portfolio infra | broad | 1–2 d | pacing-dangerous → quarantine |

Suggested wiring into the ladder: 19b gains ranks 2 (as planned, now with
parameters) and 4; 19c runs rank 1 as a third competitor next to Improvements
3 and 4 (min-wins at slot level decides), with rank 3 upgrading whichever
CP-SAT machinery survives; ranks 5/9/10 are standing lottery tickets wherever
a slot frees up after a kill.
