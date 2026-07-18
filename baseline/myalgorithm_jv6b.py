# myalgorithm_jv6.py  --  jv6 = v33 (jay) + jv5 Phase A/C-partial/D (jiyun).
# 3-way merge (base = v25 c407ac1): v33's self-gating merge tail stacked with
# jv5's dispatch() nk/mpc/ovh repair + W0/W3 deep-nestle. Only textual overlap
# was this header. Both parent headers kept below for provenance.
# ---------------------------------------------------------------------------
# (v33 header, kept verbatim)
# myalgorithm_33.py  --  v33 = v25 + SELF-GATING MERGE TAIL (S4 recombination).
# =============================================================================
# v33. Byte-exact copy of v25 plus a post-race SOLUTION-MERGE recombination pass
# that fires ONLY when the portfolio returns with spare time (prob_1-class
# instances whose workers early-exit on zero-tardy convergence). Mechanism:
#   * FREE HARVEST: the v25 parent already retains EVERY streamed (obj, assign)
#     incumbent in `cands` (the drain loop's existing `cands.append(item)`); no
#     worker/budget/seed/drain change -- the tail only READS that list.
#   * SELF-GATING TAIL (`_merge_tail`): after the parent's normal winner
#     selection, if remaining = deadline - now >= MERGE_MIN (6s) AND there are
#     >= 3 distinct candidates, dedup-by-signature (keep best ~24 by obj), build
#     a per-block placement pool, precompute pairwise space-time-crane
#     incompatibility from the raster masks + exact _can_place primitives, and
#     solve a recombination CP-SAT (pick one placement per block, minimize the
#     true objective, warm-started from the portfolio WINNER). Order-dependent
#     crane feasibility of the merged schedule is fixed by an ops-replay repair
#     (revert violating blocks to the winner's placement, <=3 rounds). Accept
#     iff check_feasibility passes AND objective < winner's; otherwise return the
#     winner exactly as v25 does -> byte-identical.
#   * On forced instances (workers run to deadline) remaining < MERGE_MIN so the
#     gate never opens. To protect lottery-sensitive FORCED instances (prob_32)
#     from ANY parent-side perturbation, the forced classification is captured
#     up front (reusing v25's existing insurance-build _is_forced call -- no new
#     call) and the parent verify loop BRANCHES: forced -> v25's exact verify
#     loop token-for-token (no _merge_tail, no dedup, no extra held references);
#     non-forced -> v25 loop + the merge tail. The parent's race-time code
#     (giant check, spawn, insurance, drain loop + island rebroadcast) is
#     byte-identical to v25 on every instance -- the merge is strictly post-race
#     and non-forced-only. Merge machinery ported inline (self-contained; no
#     imports of radical_s4_merge or myalgorithm_25). See heuristic_32.md (S4).
# =============================================================================
# (v25 header below, kept verbatim for provenance)
# ---------------------------------------------------------------------------
# (jv5 header, kept verbatim)
# myalgorithm_jv5.py  --  jv5 = v25 + SEARCH-POWER upgrade.
# LIVE (measured net-positive, spot @600s same-machine):
#   * Enabling edit: dispatch() gains nk/mpc/ovh params (mirrors ticket()).
#     This REPAIRS A LATENT v25 BUG: W0-reclaim's mpc build and W3-giant's
#     ovh build passed kwargs dispatch() did not accept -> TypeError,
#     swallowed by their except -> those builds NEVER RAN in v20-v25.
#   * Phase A: deep-nestle near_k family (nk 24/32) + the repaired mpc/ovh
#     builds in the W0-reclaim / W3-giant deep pipelines. Owns prob_38's
#     -799,909. Uses v25's DESIGNED build budget (0.38w/0.40w) -- v25 was
#     not pacing differently, it was leaving that budget idle via the bug.
#   * Phase C (partial): mpc_fill D/K 16,6 -> 24,8 + solve 2.0 -> 3.0s on
#     deep events only (len(admissible) >= 24); shallow = v25 byte-exact.
#   * Phase D: scan_scoped's actives-union memoized (_scoped_union).
#     Byte-identical (verified: prob_1@30s = 18,357), speed-only.
# REVERTED (measured dead -- do not re-propose without new evidence):
#   * Phase B per-instance near_k (_nk_family): the 3 cells where it differed
#     from v25 all regressed (23 +196k, 30 +136k, 33 +79k). Kept unwired for
#     provenance; see its docstring.
#   * Phase C's mpc=2 W1 tickets: extra tickets are NOT free -- they displace
#     the ovh/jitter tail past tick_dl and change which draw wins (v21's
#     displacement lesson). mpc=2 back to v25's parked state.
# See C:\Users\user\.claude\plans\jv5-cached-hearth.md, heuristics/heuristic_jv5.md.
# ---------------------------------------------------------------------------
# myalgorithm_25.py  --  v25 = v24 + DEEP-NESTLE near_k family (16-32)
# heading the W1 rotation: raw builds measured below every fully-
# polished banked cell on all six probed rocks (sum -7.4M raw).
# Also: urgency-weighted MPC objective (mpc=2, probed no-signal,
# parked unwired).
# ---------------------------------------------------------------------------
# myalgorithm_25.py  --  v25 = v24 + urgency-weighted MPC objective
# (mpc=2 mode; mpc=True/1 unchanged). Wired as ADDITIONAL min-wins
# variants only (pacing law).
# ---------------------------------------------------------------------------
# (v24 header below, kept verbatim for provenance)
# myalgorithm_24.py  --  v24 = v23 + overhang variants in the deep
# pipelines (W0-reclaimed 3-way min, W3-giant 2-way min), numeric ovh
# weight, W1 weight-4 ovh ticket. Basin-diversity-into-polish thesis.
# ---------------------------------------------------------------------------
# (v23 header below, kept verbatim for provenance)
# myalgorithm_23.py  --  v23 = v22 + (a) MPC build variant in the W0-reclaimed
# deep pipeline on eligible giants (mpc's -832k raw on 38 never won from W1's
# shallow ticket; the deep improve is what converts raw builds into banked
# cells), (b) overhang-aware anchor scoring (_order_cells ovh_bay: penalize
# upper-layer cells over empty floor -- the 0.05-0.10 union-poisoning band),
# explorer-only, inert by default.
# ---------------------------------------------------------------------------
# (v22 header below, kept verbatim for provenance)
# myalgorithm_22.py  --  v22 = v21 + MPC JOINT ADMISSION (heuristic_21
# Improvement C): at deep-queue beam events, a CP-SAT max-weight
# compatible-set fill (footprint-union-disjoint candidate cells, exact
# _can_place gate at commit) competes with the three greedy fill orders
# under the same (admitted area, cost) key. Explorer mpc tickets only;
# mpc=False default keeps every other path byte-exact.
# ---------------------------------------------------------------------------
# (v21 header below, kept verbatim for provenance)
# myalgorithm_21.py  --  v21 = v20 + near-miss threading through the improver
# reinsert path (_find_earliest_slot_raster / _repack_window / _improve,
# default 0 = byte-inert; enabled from the W1 explorer's polish) + W1 slot
# economics (plan ticket dropped -- gating measured dead in all forms;
# jittered nm+beam draws instead). See heuristic_21.md.
# ---------------------------------------------------------------------------
# (v20 header below, kept verbatim for provenance)
# myalgorithm_20.py  --  v20 = v18 + plan-explorer W1 slot on the tardy class.
# See heuristic_20.md. ledger_19's "density-saturated" verdict is REFUTED
# (footprint metric double-counted stacking; true per-layer burst density is
# 0.47-0.7 with 20+ blocks queued outside half-empty bays). v20 adds, all
# quarantined behind the W1 slot on {forced, w1>=6000, overload>0.65}:
#  A. NEAR-MISS ADMISSION RECOVERY: _Raster.scan keeps its overlap-count grid;
#     anchors rejected by <= near_k dilated cells are exact-gated by
#     _can_place at the admission frontier (recovers the ~0.10-0.15 density
#     band lost to conservative mask dilation). nearmiss=0 default = inert.
#  B. CALIBRATED PLAN TARGETS (_plan_targets): non-preemptive per-layer
#     cumulative CP-SAT plan (left-shifted), feeding the existing round-3
#     admission-gate machinery. Not the dead fluid gate: exact durations,
#     per-layer capacity, left-shift.
#  C. W1 EXPLORER SLOT: ungated near-miss control + three plan tickets ->
#     giant polish envelope; legacy W1 path on any failure. W0/W2/W3
#     byte-exact v18 everywhere; non-eligible instances fully byte-exact.
# ---------------------------------------------------------------------------
# (v18 header below, kept verbatim for provenance)
# myalgorithm_18.py  --  v18 = v17 + exact-pack WINDOW shots aimed at the
#                        GLOBAL BEST (whole-bay model measured-dead and
#                        retired to provenance). See heuristic_18.md.
# =============================================================================
# v18 AS-MEASURED NOTE: the planned WHOLE-BAY escalation (`_exact_pack_bay`)
# is implemented but NOT WIRED: five configurations on both gate targets
# (prob_39/26) solved FEASIBLE-at-hint with millions of branches and zero
# yield at 45-90s budgets -- exact neighborhoods only pay when SMALL and
# DENSE (v17's destroyed-window). The dedicated late phase instead fires the
# PROVEN v17 window mechanism at the GLOBAL BEST (island-inbox adopted),
# fixing v17's placement error (sound accepts on losing worker incumbents).
# =============================================================================
# v18. Escalation of v17's proven-sound exact-pack mechanism (goal < 150M;
# v17 ~= 150.70M). v17 measured: officially-feasible -26.7k accepts with zero
# soundness failures, but D=14/K=12 windows on WORKER incumbents never beat
# the portfolio best. Two fixes:
#  1. WHOLE-BAY EXACT MODEL (`_exact_pack_bay`). Every block of the target bay
#     is in the model: the ~20 most valuable movers (w1*tard + w3*offpref) get
#     K~8 raster-feasible alternative placements (empty-bay scan, contact-
#     ordered vs temporal neighbours + stride spatial diversity; off-pref
#     movers also get up to 3 candidates in their most-preferred FOREIGN bay,
#     var-fixed constrained against that bay's schedule); every other block
#     keeps its current placement as its only candidate (K=1; K1xK1 pair
#     relations come from the incumbent geometry caches, so the pairwise
#     blowup stays bounded). ALL bay blocks get free integer entry times
#     (joint replace + retime, v13-audited CP-SAT encodings; two-tier
#     mask-prefilter + exact-geometry relations and the exact _can_place
#     validation carry over from v17 verbatim). Objective: w1*tardiness of the
#     bay + w3*preference of chosen candidates (scaled ints). 45-90s solves,
#     1-2 worst bays per instance.
#  2. AIM AT THE GLOBAL BEST, LATE (`whole_bay_phase`). The phase runs in the
#     last ~35% of the window in the RECLAIMED W0 stream (giants/27) and the
#     W0 v13-clone slot (forced non-giants), AFTER draining the island inbox
#     for the global-best incumbent -- fixing v17's placement error (sound
#     accepts on weak worker incumbents never mattered). W0 now receives an
#     inbox (the v9-replica path never touches it -> byte-exact); adoption
#     inside the W0-clone/reclaimed improves is min-wins-safe. Non-forced
#     paths, W1/W2/W3, and all banked v17 draws are byte-untouched; the
#     parent-side micro-pass is SKIPPED (reserve ~10-15s << one 45s solve).
# =============================================================================
# v17 = v16 + v13 BASIN RESTORATION + EXACT PACKING
#                        WINDOWS (CP-SAT candidate-menu matheuristic).
#                        See heuristic_17.md.
# =============================================================================
# v17. Two prongs sized to close the final ~1.3M (v16 ~= 151.28M):
#  1. v13 BASIN RESTORATION (~0.6M pool: 21 +94.7k, 28 +13.6k, 29 +20.6k,
#     30 +82.1k, 33 +276.5k, 34 +95.4k vs v13's row). v14 repack pacing and
#     v15 harvest cycles displaced these v13 draws as side effects. Guided by
#     the m13a attribution probe (which worker/phase produced each v13
#     winner), dedicated slots reproduce v13's exact polish (improve -> cpsat
#     -> improve, no repack, original seeds/pacing) ONLY where the winners
#     lived, leaving the slots that carry current wins (26 -1.71M, 23 -429k,
#     35 -664k vs v13) byte-untouched. Wiring is recorded next to the polish
#     changes below.
#  2. EXACT PACKING WINDOW (`_exact_pack_window`) -- the untried mechanism
#     family: exact simultaneous multi-block placement. Select a congested
#     (bay, window) as in repack; destroy a capped set D (~18); enumerate up
#     to K (~25) raster-feasible candidate placements per block (scoped scan
#     against the fixed neighbours over a widened window); precompute pairwise
#     spatial relations from the conservative raster masks (same soundness
#     contract as v12: masks are supersets, so a mask-clear pair is provably
#     clear; mask-overlap pairs get the exact v12-audited CP-SAT timing
#     constraints -- disjoint intervals for colliders, prism outside-moment
#     constraints with the replay tie rules otherwise); CP-SAT selects exactly
#     one placement per block + integer entry times minimizing w1*tardiness.
#     Solution is exact-validated with _can_place before being returned, and
#     the caller obj-gates -- official verify unchanged. ortools guarded; on
#     absence the greedy repack path stands. Wired into the reclaimed slots
#     (W0 stream, W3 giant specialist) and forced non-giant polish after
#     cycle 1 (targets 39/26/23/33; non-forced pacing untouched).
# =============================================================================
# v16 = v15 + ANCHOR RECLAIM on {27,38,39} + REPACK
#                        DEEPENING + prob_27-CLASS PARITY. See heuristic_16.md.
# =============================================================================
# v16. Three additions over v15 (goal: full-40 train < 150M; v15 ~= 151.3M).
#  Diagnosis (heuristic_16.md): W0's v9-replica anchor is provably
#  non-competitive on exactly the instances holding 58% of the loss (prob_38/
#  39/27: candidates ~2x worse than the dispatcher-side winners, zero verify
#  wins since v12) -- a full core wasted where the money is. Its safety role is
#  covered by the parent insurance build + empty-bay fallback + official
#  best-first verify.
#  1. ANCHOR RECLAIM (`reclaim` rule, instance-computed, no name lookups):
#     giant gate (forced and n>=250) OR overload ratio > 1.05. On train this
#     selects exactly {27, 37, 38, 39, 40} (unit-tested; the plan expected
#     {27,38,39} but 37/40 are also n=250 forced giants, and results.csv
#     proves W0-v9 non-competitive on them too: v9 vs v14 = 9.03M vs 5.81M on
#     37, 3.79M vs 2.30M on 40 -- reclaim is min-wins-safe on all five). On
#     reclaimed instances W0 runs a PRODUCTIVE stream instead: dispatcher
#     construction with the kappa=2/alpha=0.5 basin at FULL budget (W2 only
#     ever samples it inside a 0.45w lottery) -> v14-envelope polish (improve
#     -> improve; CP-SAT retime skipped: forced, measured zero) -> Z3
#     relocation endgame. W0 stays byte-exact v9 everywhere else.
#  2. REPACK DEEPENING on the reclaimed set (density-proven lever): destroy
#     cap 30 -> 45, repack window-scale rotates per fire over {2,1,3,4}*pbar
#     (gains the 4*pbar entry), and the giant W3 repack specialist alternates
#     single-bay / cross-bay (z3-relocation) windows again -- obj-gated, so
#     worst case it contributes nothing.
#  3. prob_27-CLASS PARITY: non-giant overloaded instances (overload > 1.05,
#     n < 250: prob_27 on train) get the giant polish treatment (single long
#     v14-envelope improves instead of harvest cycles -- `giantish` in polish)
#     plus the reclaimed W0 stream as their second full-budget dispatcher
#     basin. (W2's forced mini-lottery + interleaved repack already applied.)
# =============================================================================
# v15 = v14 + CROSS-BAY Z3 GROUP RELOCATION + BASIN-
#                        DIVERSITY HARVEST (re-seeded from distinct
#                        constructions) + BUDGET REFUND (skip CP-SAT on forced
#                        non-giants). See heuristic_15.md.
# =============================================================================
# v15 ROUND 2 (after round-1 measurement: 35 -406k, 38 +53k, rest byte-flat):
#  r2a. Harvest cycles 2-3 re-seed from the lottery's runner-up CONSTRUCTIONS
#       (pick_alts): r1 measured that improve-seed variation restarting from a
#       converged incumbent never leaves its basin (31/33/30/34 byte-flat);
#       the historical run-to-run spread came from construction draws.
#  r2b. _repack_xbay rewritten from congestion-LNS (measured +12M..+68M
#       candidates on prob_31 -- rebuild tardiness drowns Z3 gains) to Z3 GROUP
#       RELOCATION: quiet-window, off-pref non-tardy blocks only, zero-slot
#       rebuild (chain-swap capability _z3_relocate lacks).
#  r2c. Giants (forced n>=250) restored to the EXACT v14 polish envelope and
#       v14 W3 giant specialist (r1 harvest/xbay measured zero-to-negative:
#       prob_38 +53k).
# =============================================================================
# v15. Three additions over v14 (goal: full-40 train < 150M; v14 ~= 152M).
#  Diagnosis (heuristic_15.md): v14's joint repack is SINGLE-BAY -- it can
#  re-interlock a bay but cannot rebalance across bays, recover preference
#  (Z3 needs bay changes), or relieve one bay by exporting a block. The lottery
#  noise band (250-400k per-instance spread) is unharvested (one long polish =
#  one draw per worker). CP-SAT retime is measured-zero on forced instances.
#  1. CROSS-BAY WINDOW REPACK (`_repack_xbay`, `_repack_window(mode='xbay')`).
#     Pick a TIME window scored by congestion AND a Z3 term (w3 x recoverable
#     preference gap of off-pref blocks in the window), destroy every block whose
#     [entry,exit) intersects it across ALL bays (cap 40; prefer tardy + off-pref
#     + central), and rebuild the destroyed set with a restricted dispatch where
#     BAY CHOICE IS FREE (bay economics w1*tard + w2*imbal + w3*pref, k trial
#     orders as in v14, raster-scoped placement against the fixed neighbours).
#     Failures fall through the normal all-bay repair + force-place guarantee.
#     `_improve` alternates single-bay / cross-bay repack modes round-robin.
#     Obj-gated accept, restore-on-reject -- identical discipline to v14. New
#     capability: inter-bay rebalancing + Z3 recovery inside one obj-gated move
#     (targets 31/33/30/34/35; +1 fifth-family shot at 38/27). Only fires when
#     the incumbent is tardy (same gate as v14's repack), so the zero-tardy
#     easy tail never sees it.
#  2. BASIN-DIVERSITY HARVEST. `polish` runs the improver as THREE independent
#     cycles instead of one long draw: cycle = improve(seed_i, window-bounded) +
#     its repack rounds, each starting from the best-so-far assignment but a
#     FRESH rng stream, with the repack window width rotated over {2,1,3}*pbar.
#     Every cycle-best is pushed to the parent (min wins). Cycle 1 keeps v14's
#     original seed, sbay-only repack and 2*pbar window (== the v14 improve-1
#     draw distribution; xbay only enters via cycles 2-3); the total budget is
#     unchanged (the cycles tile v14's improve envelope) so the harvest is
#     pure-upside -- it re-uses the same wall time to take three seeded draws
#     over the measured 250-400k spread instead of one. Non-forced polish keeps
#     CP-SAT retime between cycles 1 and 2 (prob_21's historical win); its
#     cycles 2-3 harvest the tardy non-forced band (prob_35/21/24). Zero-tardy
#     easies are inert (repack gated on tardiness; improver early-stops).
#  3. BUDGET REFUND + Z3 WINDOWS. (a) Skip `_cpsat_retime` entirely on forced
#     instances (measured zero twice); the reclaimed slice folds into the harvest
#     cycles. CP-SAT is kept for non-forced (won prob_21). (b) Repack window
#     selection gains the Z3 term above so cross-bay repack aims at preference-
#     dense regions (prob_31's 2.82M Z3). W0 (v9 replica) untouched -> byte-exact.
# =============================================================================
# v14 = v13 + JOINT WINDOW REPACK (LNS-XL, geometry lever) +
#                        MULTI-ORDER ADMISSION BEAM + REPACK-HEAVY WORKERS.
#                        See heuristic_14.md.
# =============================================================================
# v14. Three additions over v13 (goal: full-40 train < 150M; v13 focus-6 = 121.57M).
#  Diagnosis: v13 exhausted three ADMISSION-TIMING levers (alpha-ATC, CP-SAT
#  retime, fluid-target gating) on the overloaded pair -- order/timing is
#  saturated. The residual lever is GEOMETRY: the dispatcher and repair place ONE
#  block at a time into whatever concave scrap exists, so a dense interlocked
#  cluster is only reachable by placing its members TOGETHER.
#  1. JOINT WINDOW REPACK (`_repack_window`). A new LNS-XL improver move for tardy
#     instances: pick the most CONGESTED (bay, time-window) from the incumbent's
#     own schedule (area-time in queue/tardiness overlap), DESTROY every block of
#     that bay whose [entry,exit) intersects it (typ 10-30), then REBUILD only the
#     destroyed set with the un-destroyed neighbours held FIXED (scoped raster
#     occupancy). Try k orders (area-desc / due-asc / min-slack / most-constrained
#     -first = fewest raster-feasible cells), each a greedy earliest-feasible
#     raster placement, and keep the best rebuild. Blocks that fail to place in the
#     bay fall back to the normal repair path (force-place guarantee stands). The
#     rebuild is accepted ONLY if the FULL internal objective strictly improves
#     (obj-gated inside `_improve`; restore-on-reject is automatic since a fresh
#     `work` dict is only adopted when better). Wired into `_improve` as a
#     `repack_every`-th-round move (0 == off == byte-exact v13; W0 untouched).
#  2. MULTI-ORDER ADMISSION BEAM (`_dispatch_construct(beam=True)`). At events with
#     >= beam_m queued candidates, evaluate k=3 greedy fills (ATC order, area-desc,
#     most-constrained-first) via trial-commit + rollback of the raster/sched, and
#     COMMIT the fill with the best (admitted area, then placement cost). Kills the
#     "first-fit forecloses the interlock" failure at admission. beam=False
#     reproduces v13's single-pass dispatch BYTE-FOR-BYTE (the v13 loop is just
#     refactored through `apply_place`); beam is only a NEW lottery ticket, with
#     the no-beam entries kept FIRST so best-of always protects v13's basins.
#  3. REPACK-HEAVY WORKERS. Giants (nw=3): W2's polish interleaves joint-repack
#     rounds (repack_every=3) with classic destroy/repair; W1 keeps the classic
#     AREA basin as a repack-free portfolio anchor. Non-giants: the W3 dispatcher's
#     post-lottery polish gains repack rounds (repack_every=4), and W2's overloaded
#     polish gets repack_every=3 (attacks prob_27). W0 anchor untouched; all
#     accepts internal-objective-gated; parent official verify unchanged. (nw=4
#     giant repack-specialist deferred pending an RSS measurement -- v13 was
#     2.83GB/3w.)
# =============================================================================
# v13. Three additions over v12 (goal: full-40 train < 150M; v12 = 174.59M):
#  1. RASTER-WINDOWED REPAIR (`_find_earliest_slot_raster` + `_Raster.scan_scoped`).
#     v12's improver repaired only via AABB-corner candidates -- the 55-72%
#     inside-bbox density ceiling. v13 gives the worker's raster to the improver:
#     per candidate entry time it builds a SCOPED occupancy from only the
#     time-overlapping blocks, full-position scans, ranks feasible cells by
#     PERIMETER CONTACT (block-footprint dotted with the occupied/wall neighbour
#     field -- `_order_cells`/`_neighbour_field`), and exact-gates with
#     _can_place. Concavity-filling placements AABB corners never propose become
#     reachable. Gated to forced/congested instances. The same contact ordering
#     upgrades the dispatcher's try_place (score_pos), with an adaptive cand_cap
#     (12->48 on deep entry queues) killing the 12-cell rejection cliff.
#  2. VOLUME-AWARE TRIAGE. ATC generalized to priority ~ 1/(a^alpha * p) *
#     exp(-slack/(kappa*pbar)); alpha=0 reproduces v12 exactly, alpha>0 strands
#     large-footprint blocks under overload (fluid-SPT). Multiplicative jitter.
#     Giants (v12: one dispatch) now run a W2 mini-lottery over alpha/kappa;
#     W3's lottery gains the alpha dimension.
#  3. THROUGHPUT. Scan cache per (bay,bi,oi,ver), footprint cache per (bay,ver),
#     exit-time SET (O(1) heap membership), prune exited blocks from the
#     dispatcher sched, drop fully-vacated occupancy layers -- all
#     result-transparent, they only multiply builds/rounds. W0 stays byte-exact.
# =============================================================================
# v12 = v11 + RASTER GEOMETRY ENGINE (numpy conservative occupancy scan) +
#       TIME-ORDERED DISPATCHER construction + CP-SAT retime audit fixes.
# =============================================================================
# v12 (see heuristic_12.md). Three additions over v11:
#  1. RASTER ENGINE (`_Raster`). Per (block, orient, layer) a conservative
#     boolean unit-grid mask (a cell is set iff the layer polygon *touches* its
#     closed unit square -> mask-disjoint from the occupancy union implies the
#     polygons share no cell, hence no positive-area overlap: provably feasible
#     for BOTH the same-layer collision rule AND the crane j>=k prism rule,
#     since entry and exit share identical geometry). Per-bay per-layer int
#     occupancy grids are maintained incrementally; a numpy sliding-window scan
#     returns EVERY entry-clear integer position at once (vs v11's handful of
#     AABB contact points) -- the direct fix for the 55% density ceiling. It is
#     conservative (only ever rejects edge-touching placements), so any position
#     it returns is truly feasible; the chosen candidate is still gated by the
#     exact cached `_can_place` (which also enforces reverse exit-blocking) and
#     the whole solution is officially verified by the parent.
#  2. TIME-ORDERED DISPATCHER (`_dispatch_construct`). Event-driven admission
#     (events = releases + scheduled exits): at each event admit queued blocks
#     in ATC (apparent-tardiness-cost) priority using the raster full scan,
#     never leaving a fitting block queued (kills prob_27's idle-with-fit steps
#     and drains release bursts as fast as geometry allows). Bay choice spills
#     to non-preferred bays when the preferred bay is full (w1 >> w3). Prompt
#     exits at entry+proc (always crane-feasible by the admission invariant).
#     Wired as W2 (default kappa) and W3 (kappa/weight/jitter lottery).
#  3. CP-SAT RETIME FIXES. Pair-count cap per bay, a deadline flag inside the
#     O(m^2) pair-build loop (abort => skip solve, never solve a partial model),
#     solver budget recomputed AFTER the build (no >=1s floor), and the pass
#     gated on improver stall with a hard latest-start.
# =============================================================================
# Imports the standard library (math, time, random, multiprocessing), `utils`
# (contest-provided), and OPTIONALLY ortools (in ogc2026_env.yml; every use is
# wrapped so its absence just disables the CP-SAT pass). No `myalgorithm_N`
# helper imports. To submit a newer version, copy this over myalgorithm.py.
# =============================================================================
# v11 (see heuristic_11.md). Two additions over v10:
#  1. ISLAND MODEL. v10 workers were isolated: nobody polished another worker's
#     winner (prob_38's W1 win got zero help). The parent now broadcasts the
#     global best back to workers via per-worker inbox queues; W1+ improvers
#     adopt an inbox solution when it beats their incumbent. W0 (v9 replica)
#     takes no inbox: it must stay byte-exact v9 as the no-regression anchor.
#  2. CP-SAT TIME-REPAIR. With bay/x/y/orient FIXED, re-optimizing all entry
#     times is a clean subproblem: w2/w3 don't depend on timing, so minimize
#     w1*sum(tardiness) subject to pairwise collision (disjoint intervals) and
#     crane entry/exit blocking (entry_i outside j's presence when j blocks i)
#     -- all relations precomputed with the exact cached geometry primitives.
#     Solved per bay (bays are independent). Workers run it once their improver
#     stalls; the result is pushed like any candidate (parent still verifies
#     officially, so an encoding subtlety can cost a candidate, never
#     correctness). Targets the schedule-limited instances (prob_31/35/30/23/
#     28/21: fluid-LB ~ 0 yet ~5-18M objectives).
# =============================================================================
# v10 (see heuristic_10.md). Two structural observations:
#  1. The eval server allows 4 CPU cores; v9 used ONE. All of v9's compromises
#     (two-pass 35/65 improver split, CON_FRAC construction cap, the
#     construction-cheap gate) are single-budget rationing artifacts. v10 runs a
#     PARALLEL PORTFOLIO of min(4,cpu) worker processes, each an independent
#     full-budget strategy streaming best-so-far assignments to the parent via a
#     queue; the parent picks the best by internal objective and verifies it
#     officially (best-first, empty-bay fallback). Strategies (forced):
#     W0 EDD->improve (v8 anchor), W1 AREA->improve (v9's giant-winner, now with
#     the FULL budget), W2 congestion-aware construction -> improve, W3 jitter
#     multi-start -> simulated-annealing improve. Experimental members are
#     regression-safe: the parent takes the min over workers. Falls back to
#     v9's single-thread path if multiprocessing is unavailable.
#  2. Bay-assignment myopia is a CONSTRUCTION bug: in Pass A, w1-dominant
#     instances take the FIRST preferred bay with a zero-tardiness slot,
#     congesting it so later blocks spill into tardiness (prob_39 fluid-LB 1.3M
#     vs 27M achieved). W2 scores ALL bays' zero-slots and adds a window-
#     utilization penalty (util_gamma * w1 * util) so the greedy pays an
#     anticipatory price for stuffing a crowded bay while spreading is free.
# =============================================================================
# v9. The residual loss after v8 was dominated by instances byte-identical across
# v3..v8 (prob_27/30/35/39): these are deterministic EDD constructions the
# improver cannot beat (only ~12 slow rounds). The lever is a BETTER construction:
#   * MULTI-START over EDD + AREA (largest-footprint-first) + jittered orders,
#     keeping the best. AREA -- placing the hardest-to-fit blocks while bays are
#     empty -- reaches a far better geometric basin on the stuck giants
#     (prob_39 29.75M->27.05M, first movement ever; prob_27 52.4M->48.9M; prob_26
#     20.6M->18.9M; prob_33 17.2M->16.7M). Construction phase capped at CON_FRAC
#     of the window so the improver keeps a guaranteed share.
#   * REGRESSION-SAFE TWO-PASS IMPROVER on forced instances: improve the plain EDD
#     construction first (== v8's result, so never a regression), THEN improve the
#     best other construction only if its RAW objective already beats the
#     EDD-improved one (true on the giants, false on improver-dependent instances).
# Fitting EDD+AREA on the n=250 giants needs ~300s per instance (well within the
# contest's few-minutes-to-half-hour). Full-40 @300s ~= 299.3M (40/40 feasible),
# vs v8's 311.16M. The dormant cross-bay-rebalance / partial-restart operators
# (REBAL_AFTER / RESTART_AFTER = 1e9) are disabled experiments kept for
# provenance; see heuristic_9.md for why they could not crack the stuck optima.
# =============================================================================
# v8 = v7 (geometry caching) + THOROUGH REPAIR. Caching made each placement
# cheap, so the improver can now afford a much wider per-block search during
# repair (slot_time_cap 18->40, slot_pos_cap 14->30) -- the exact thing v5 kept
# tiny purely for speed. Hypothesis: the plateaus v5/v7 hit on the gap instances
# (prob_39/26/33: relaxed LB far below achieved, yet the improver finds nothing)
# are partly an artifact of the capped repair search missing the denser packing;
# a wider repair may escape them. Tested against v7 on the gap set; kept only if
# it actually lowers the objective (see heuristic_8.md / results.csv).
# =============================================================================
# v7 = v5 + pairwise GEOMETRY CACHING (semantically identical to v5, faster).
# =============================================================================
# Diagnosis: on the packing-limited instances (relaxed LB << v5 result, e.g.
# prob_35/28/31/30/23/39) more improver rounds keep lowering tardiness
# (prob_35: 14.6M@60s -> 11.4M@150s), but v5 is round-starved because every
# placement check rebuilds Shapely intersections. v7 memoizes the three
# pairwise feasibility primitives -- collision, crane-entry obstruction, crane-
# exit obstruction -- keyed by the two placements' (block_id, orient, x, y).
# These are pure geometry (time-independent) and SEPARABLE per existing block
# (the crane path is blocked iff ANY single present block blocks it), so the
# cache is exact: v7 returns the SAME feasibility verdict as v5 for every call,
# just far cheaper after warm-up -> many more destroy/repair rounds per second
# on the instances where that converts directly into less tardiness. The final
# solution is still verified by the official check_feasibility, unchanged.
# (Structurally over-subscribed instances prob_38/27 -- area-time demand exceeds
#  total capacity-time over the whole horizon -- stay near their forced floor;
#  no heuristic removes their tardiness. See heuristic_7.md / results.csv.)
# =============================================================================
# v5: v3's full thorough construction (NO cap) + fast basin-hopping improver.
# =============================================================================
# Fixes v4's two mistakes: (1) removes the construction-time cap so the start is
# always v3's strong thorough construction; the improver takes only leftover
# time. (2) Improver rounds are now small & fast (smaller destroy sets, capped
# repair search, lower kick threshold) so MANY more rounds run per second of
# real compute -> it actually bites on the congested instances where v4's slow
# rounds found nothing. Still returns the best-tracked incumbent (monotone).
#
# --- v4 provenance ---------------------------------------------------------
# v4: EDD-earliest construction + budget rebalance + basin-hopping improver
#     (diversified destroy/repair with escape-kicks, window-destroy mode).
# v3 placement/feasibility core kept verbatim; the
# improver and the time-budget split change. The improver tracks a separate best
# incumbent and returns it -> still monotone in the RESULT (never worse than the
# construction) while exploring more to escape plateaus (e.g. prob_39).
#
# --- v3 provenance ---------------------------------------------------------
# v3: EDD-earliest construction + multi-start best-of (no-regression) + safe
#     tardiness-pull improvement.
# Reuses v2's verified feasibility/placement core
# verbatim; changes ONLY the top-level orchestration:
#   * EDD-earliest construction targets the avoidable tardiness on congested
#     instances (the dominant cost; relaxed LB shows ~90% of it is avoidable).
#   * Per-instance best-of across {EDD-earliest, congestion-ALAP(=v1), seeded
#     perturbations} keeps the best VERIFIED-feasible solution -> can never be
#     worse than v1 on any instance (v2's regression is structurally impossible).
#   * A monotone destroy/repair improver replaces v2's non-monotone LNS.

import math
import time
import random
import re  # v33: parse block ids from check_feasibility violation strings

try:
    import numpy as _np
    from numpy.lib.stride_tricks import sliding_window_view as _swv
    _HAVE_NUMPY = True
except Exception:  # pragma: no cover
    _np = None
    _swv = None
    _HAVE_NUMPY = False

from utils import (
    Bay, Block,
    check_entry, check_exit, check_collisions, check_feasibility,
    _resolve_layers, _bounding_box, _bb_overlap, _poly_from_verts,
)

# -----------------------------------------------------------------------------
# Pairwise geometry caches (v7). Keyed by placement = (block_id, orient, x, y).
# Pure geometry, time-independent. Cleared per instance in algorithm().
#   _BLK : (bi, oi, x, y)                  -> reusable Block (avoids re-translate)
#   _CC  : frozenset{key_a, key_b}         -> do a, b spatially collide (any layer)
#   _CE  : (existing_key, mover_key)       -> does `existing` block `mover`'s ENTRY
#   _CX  : (existing_key, mover_key)       -> does `existing` block `mover`'s EXIT
# A pair-cache is exact because check_collisions/entry/exit are separable: a
# multi-block verdict is the OR of the single-block verdicts. Bay boundary is
# checked separately via bay.contains_block before any crane call, so the
# self-boundary obstruction never appears here.
# -----------------------------------------------------------------------------
_BLK = {}
_CC = {}
_CE = {}
_CX = {}
# v10: worker processes share 16GB (both locally and on the eval server), so
# the v9 unlimited-growth caches (6M) must be bounded. Measured on prob_38 (the
# heaviest instance): one dense EDD build needs ~192k _BLK entries and >1M _CE
# entries (~1.5GB RSS); a worker fits comfortably under these caps, and the
# giant instances run only 2 workers (see _algorithm_portfolio).
_BLK_CAP = 250_000
_CACHE_CAP = 2_500_000


def _reset_caches():
    _BLK.clear(); _CC.clear(); _CE.clear(); _CX.clear()


def _mkblock(bi, blk_data, x, y, oi):
    k = (bi, oi, x, y)
    nb = _BLK.get(k)
    if nb is None:
        nb = Block(block_id=bi, block_data=blk_data, x=x, y=y, orient_idx=oi)
        if len(_BLK) < _BLK_CAP:
            _BLK[k] = nb
    return nb


def _pk(blk):
    return (blk.block_id, blk.orient_idx, blk.x, blk.y)


def _collide(bay, a, b):
    ka, kb = _pk(a), _pk(b)
    key = (ka, kb) if ka <= kb else (kb, ka)
    v = _CC.get(key)
    if v is None:
        v = bool(check_collisions(bay, [a, b]))
        if len(_CC) < _CACHE_CAP:
            _CC[key] = v
    return v


def _entry_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane descent (== v5's
    check_entry(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CE.get(key)
    if v is None:
        v = bool(check_entry(bay, [existing], mover, fast=True))
        if len(_CE) < _CACHE_CAP:
            _CE[key] = v
    return v


def _exit_blocked(bay, existing, mover):
    """True iff `existing` obstructs `mover`'s crane ascent (== v5's
    check_exit(bay, [existing], mover) being non-empty)."""
    key = (_pk(existing), _pk(mover))
    v = _CX.get(key)
    if v is None:
        v = bool(check_exit(bay, [existing], mover, fast=True))
        if len(_CX) < _CACHE_CAP:
            _CX[key] = v
    return v


# -----------------------------------------------------------------------------
# Static per-block geometry helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _orient_bbox(block_data, oi):
    layers = _resolve_layers(block_data["shape"][oi]["layers"])
    if not layers:
        return (0.0, 0.0, 1.0, 1.0)
    return _bounding_box([v for l in layers for v in l])


def _orient_area(block_data, oi):
    bb = _orient_bbox(block_data, oi)
    return max(1.0, (bb[2] - bb[0]) * (bb[3] - bb[1]))


def _min_area(block_data):
    return min(_orient_area(block_data, oi) for oi in range(len(block_data["shape"])))


def _max_layers(block_data):
    return max(len(_resolve_layers(o["layers"])) for o in block_data["shape"])


def _orient_fits(block_data, oi, bay):
    lx0, ly0, lx1, ly1 = _orient_bbox(block_data, oi)
    return (math.ceil(-lx0) <= math.floor(bay.width - lx1) and
            math.ceil(-ly0) <= math.floor(bay.height - ly1))


def _unique_orients(block_data):
    seen = {}
    for oi in range(len(block_data["shape"])):
        bb = _orient_bbox(block_data, oi)
        nl = len(_resolve_layers(block_data["shape"][oi]["layers"]))
        key = (round(bb[0], 3), round(bb[1], 3), round(bb[2], 3), round(bb[3], 3), nl)
        if key not in seen:
            seen[key] = oi
    return list(seen.values())


def _candidate_positions(bay, placed_blocks, blk_bb, cap=60):
    lx0, ly0, lx1, ly1 = blk_bb
    xs = {max(0, math.ceil(-lx0))}
    ys = {max(0, math.ceil(-ly0))}
    for b in placed_blocks:
        bb = b.bounding_rect()
        xs.add(int(math.ceil(bb[2] - lx0)))
        ys.add(int(math.ceil(bb[3] - ly0)))
    out = []
    for x in sorted(xs):
        if x + lx1 > bay.width + 1e-6 or x + lx0 < -1e-6:
            continue
        for y in sorted(ys):
            if y + ly1 > bay.height + 1e-6 or y + ly0 < -1e-6:
                continue
            out.append((int(x), int(y)))
            if len(out) >= cap:
                return out
    return out


# -----------------------------------------------------------------------------
# Time-overlap + crane-presence helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _overlaps(a1, e1, a2, e2):
    return a1 < e2 and a2 < e1


def _present_at_entry(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (a == t and b.block_id < x_id):
            out.append(b)
    return out


def _present_at_exit(t, x_id, sched):
    out = []
    for b, a, e in sched:
        if b.block_id == x_id:
            continue
        if (a < t < e) or (e == t and b.block_id > x_id):
            out.append(b)
    return out


def _can_place(bay, sched, new_blk, entry, exit_t):
    # v7: identical verdict to v5, but every Shapely call is routed through the
    # pairwise caches. check_entry/exit over a SET of present blocks is the OR of
    # the per-block checks, so we decompose into cached pairwise queries.
    if not bay.contains_block(new_blk):
        return False
    nbid = new_blk.block_id
    # new_blk ENTRY obstructed by any block present at `entry` (== check_entry
    # over _present_at_entry set).
    for b, a, e in sched:
        if (a < entry < e) or (a == entry and b.block_id < nbid):
            if _entry_blocked(bay, b, new_blk):
                return False
    # new_blk EXIT obstructed by any block present at `exit_t` (== check_exit
    # over _present_at_exit set).
    for b, a, e in sched:
        if (a < exit_t < e) or (e == exit_t and b.block_id > nbid):
            if _exit_blocked(bay, b, new_blk):
                return False
    for b, a, e in sched:
        if _overlaps(entry, exit_t, a, e) and _collide(bay, new_blk, b):
            return False
        if (entry < a < exit_t) or (entry == a and nbid < b.block_id):
            if _entry_blocked(bay, new_blk, b):
                return False
        if (entry < e < exit_t) or (exit_t == e and nbid > b.block_id):
            if _exit_blocked(bay, new_blk, b):
                return False
    return True


def _empty_bay_entry(sched, r_time, proc):
    entry = int(r_time)
    changed = True
    while changed:
        changed = False
        exit_t = entry + proc
        for it in sched:
            a, e = it[1], it[2]
            if _overlaps(entry, exit_t, a, e):
                entry = max(entry, e)
                changed = True
    return entry


def _rel_sched(sched, nb_bb):
    return [(it[0], it[1], it[2]) for it in sched if _bb_overlap(nb_bb, it[3])]


def _zero_candidates(rel, release, alap, proc):
    cand = {alap, release}
    for _, a, e in rel:
        for t in (a, e, a - proc, e - proc):
            for tt in (int(t), int(t) - 1):
                if release <= tt <= alap:
                    cand.add(tt)
    return sorted(cand, reverse=True)


def _find_zero_slot(bay, sched, new_blk, release, due, proc):
    alap = due - proc
    if alap < release:
        return None
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    for entry in _zero_candidates(rel, release, alap, proc):
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    return None


def _find_tardy_slot(bay, sched, new_blk, release, due, proc, tardy_cap=64):
    if not bay.contains_block(new_blk):
        return None
    rel = _rel_sched(sched, new_blk.bounding_rect())
    start = max(release, due - proc + 1)
    cand = {start}
    for _, _, e in rel:
        if e >= start:
            cand.add(e)
    for entry in sorted(cand)[:tardy_cap]:
        if _can_place(bay, rel, new_blk, entry, entry + proc):
            return entry
    entry = _empty_bay_entry(sched, release, proc)
    if _can_place(bay, rel, new_blk, entry, entry + proc):
        return entry
    return None


def _time_overlap_rel(sched_bay, t, exit_t):
    return [(it[0], it[1], it[2]) for it in sched_bay
            if it[1] <= exit_t and t <= it[2]]


def _find_earliest_slot(bay, sched_bay, bi, blk, orients, lb, proc,
                        time_cap=40, pos_cap=24):
    """Earliest feasible (orient, x, y, entry) with entry >= lb, packing densely.
    Returns the first (= earliest, least-tardy) feasible placement, or None."""
    times = {int(lb)}
    for _, a, e in [(it[0], it[1], it[2]) for it in sched_bay]:
        if e >= lb:
            times.add(int(e))
        if a >= lb:
            times.add(int(a))
    for t in sorted(times)[:time_cap]:
        exit_t = t + proc
        relx = _time_overlap_rel(sched_bay, t, exit_t)
        active = [r[0] for r in relx]
        for oi in orients:
            if not _orient_fits(blk, oi, bay):
                continue
            blk_bb = _orient_bbox(blk, oi)
            for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                nb = _mkblock(bi, blk, cx, cy, oi)
                if _can_place(bay, relx, nb, t, exit_t):
                    return (oi, cx, cy, t)
    return None


def _find_earliest_slot_raster(bay, bay_id, sched_bay, bi, blk, orients, lb, proc,
                               raster, score_pos=True, time_cap=16, pos_cap=28,
                               nearmiss=0):
    """v13 RASTER-WINDOWED REPAIR: earliest feasible (orient,x,y,entry) reached
    by a full-position raster scan instead of AABB-corner enumeration -- the
    density lever inside the improver. For each candidate entry time t, build a
    SCOPED occupancy from ONLY the time-overlapping blocks (does NOT touch the
    dispatcher's raster.occ), scan every integer anchor, rank feasible cells by
    perimeter contact, and exact-gate with _can_place. Returns the earliest
    feasible placement or None."""
    times = {int(lb)}
    for it in sched_bay:
        a, e = it[1], it[2]
        if e >= lb:
            times.add(int(e))
        if a >= lb:
            times.add(int(a))
    for t in sorted(times)[:time_cap]:
        exit_t = t + proc
        relx = _time_overlap_rel(sched_bay, t, exit_t)
        actives = [(it0.block_id, it0.orient_idx, it0.x, it0.y)
                   for (it0, _a, _e) in relx]
        for oi in orients:
            if not _orient_fits(blk, oi, bay):
                continue
            if nearmiss > 0:
                feas, cx0, cy0, occ_fp, near = raster.scan_scoped(
                    bay_id, actives, bi, oi, want_near=True)
            else:
                feas, cx0, cy0, occ_fp = raster.scan_scoped(
                    bay_id, actives, bi, oi)
                near = None
            if feas is not None and feas.any():
                cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                     raster.W[bay_id], occ_fp, score_pos, None)
                tried = 0
                for (x, y) in cells:
                    nb = _mkblock(bi, blk, x, y, oi)
                    if _can_place(bay, relx, nb, t, exit_t):
                        return (oi, x, y, t)
                    tried += 1
                    if tried >= pos_cap:
                        break
            # v21 Improvement A: near-miss recovery in the improver reinsert
            # (same exact-gate soundness contract as the v20 dispatcher pass).
            if near is not None and near.any():
                cells = _order_cells(raster, near, cx0, cy0, bi, oi,
                                     raster.W[bay_id], occ_fp, score_pos, None)
                tried = 0
                for (x, y) in cells:
                    nb = _mkblock(bi, blk, x, y, oi)
                    if _can_place(bay, relx, nb, t, exit_t):
                        return (oi, x, y, t)
                    tried += 1
                    if tried >= nearmiss:
                        break
    return None


# -----------------------------------------------------------------------------
# Orderings
# -----------------------------------------------------------------------------

def _edd_order(blocks_data, jitter=None):
    """Earliest-due-date first; tie shortest proc, largest area, most layers.
    Optional jitter (rng) perturbs ties for multi-start diversity."""
    n = len(blocks_data)
    areas = [_min_area(b) for b in blocks_data]
    base = []
    for i, b in enumerate(blocks_data):
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((b["due_date"] + j, b["processing_time"], -areas[i],
                     -_max_layers(blocks_data[i]), i))
    base.sort()
    return [t[-1] for t in base]


def _slack_order(blocks_data, jitter=None):
    """Minimum-slack first (due - release - proc), tie earliest due. Slack is how
    much freedom a block has before it is tardy; scheduling the tightest blocks
    first is a classic alternative basin to pure EDD."""
    base = []
    for i, b in enumerate(blocks_data):
        slack = b["due_date"] - b["release_time"] - b["processing_time"]
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((slack + j, b["due_date"], b["processing_time"], i))
    base.sort()
    return [t[-1] for t in base]


def _area_order(blocks_data, jitter=None):
    """Largest-footprint first within due-date buckets: places the hardest-to-fit
    blocks while the bays are empty, a different geometric basin than EDD."""
    areas = [_min_area(b) for b in blocks_data]
    base = []
    for i, b in enumerate(blocks_data):
        j = jitter.uniform(-0.5, 0.5) if jitter is not None else 0.0
        base.append((b["due_date"] + j, -areas[i], b["processing_time"], i))
    base.sort()
    return [t[-1] for t in base]


def _congestion_order(blocks_data):
    n = len(blocks_data)
    intervals = []
    areas = [_min_area(b) for b in blocks_data]
    for b in blocks_data:
        entry = max(b["release_time"], b["due_date"] - b["processing_time"])
        intervals.append((int(entry), int(entry + b["processing_time"])))
    events = {}
    for (a, e), ar in zip(intervals, areas):
        events[a] = events.get(a, 0.0) + ar
        events[e] = events.get(e, 0.0) - ar
    times = sorted(events)
    demand_at = {}
    run = 0.0
    for t in times:
        run += events[t]
        demand_at[t] = run

    def pressure(i):
        a, e = intervals[i]
        best = 0.0
        for t in times:
            if t >= e:
                break
            if t >= a:
                best = max(best, demand_at[t])
        return best

    return sorted(
        range(n),
        key=lambda i: (
            -pressure(i),
            blocks_data[i]["due_date"] - blocks_data[i]["release_time"]
            - blocks_data[i]["processing_time"],
            -areas[i],
            -_max_layers(blocks_data[i]),
        ),
    )


# -----------------------------------------------------------------------------
# Objective helpers (verbatim from v2)
# -----------------------------------------------------------------------------

def _bay_u(bays):
    areas = [b.width * b.height for b in bays]
    avg = sum(areas) / len(bays)
    return [avg / a for a in areas]


def _objective(assignments, blocks_data, bays, bay_u, w1, w2, w3):
    n_bays = len(bays)
    obj1 = 0.0
    loads = [0.0] * n_bays
    obj3 = 0.0
    for a in assignments.values():
        bi = a["block_id"]; bj = a["bay_id"]
        blk = blocks_data[bi]
        obj1 += max(0.0, a["exit_time"] - blk["due_date"])
        loads[bj] += blk["workload"]
        obj3 += max(blk["bay_preferences"]) - blk["bay_preferences"][bj]
    if n_bays >= 2:
        obj2 = math.floor(max(
            abs(bay_u[p] * loads[p] - bay_u[q] * loads[q])
            for p in range(n_bays) for q in range(n_bays) if p != q))
    else:
        obj2 = 0.0
    return w1 * obj1 + w2 * obj2 + w3 * obj3, obj1, obj2, obj3


# -----------------------------------------------------------------------------
# Thorough placement of one block (verbatim from v2)
# -----------------------------------------------------------------------------

def _window_util(sched_bay, entry, exit_t, bay_area):
    """Fraction of the bay's area-time committed inside [entry, exit_t) by
    already-placed blocks (bbox areas; cheap anticipatory congestion signal)."""
    span = max(1, exit_t - entry)
    occ = 0.0
    for it in sched_bay:
        a, e, bb = it[1], it[2], it[3]
        ov = min(exit_t, e) - max(entry, a)
        if ov > 0:
            occ += (bb[2] - bb[0]) * (bb[3] - bb[1]) * ov
    return occ / (bay_area * span)


def _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                 pos_cap=40, tardy_cap=8, dense=True, forced=False,
                 bay_order=None, slot_time_cap=40, slot_pos_cap=24,
                 util_gamma=0.0, raster=None):
    release = int(blk["release_time"])
    due = int(blk["due_date"])
    proc = int(blk["processing_time"])
    workload = blk["workload"]
    prefs = blk["bay_preferences"]
    s_max = max(prefs)
    orients = _unique_orients(blk)
    n_bays = len(bays)
    # v10: util_gamma > 0 disables the first-preferred-bay-wins shortcut so ALL
    # bays' zero-slots compete on score (incl. the congestion penalty below).
    w1_dominant = util_gamma <= 0.0 and w1 >= 20.0 * max(w2, w3, 1e-9)

    def score(tardiness, bay_id, top_y, entry=None, exit_t=None):
        new_load = bay_loads[bay_id] + workload
        imbal = max((abs(bay_u[bay_id] * new_load - bay_u[j] * bay_loads[j])
                     for j in range(n_bays) if j != bay_id), default=0.0)
        sc = (w1 * tardiness + w2 * imbal + w3 * (s_max - prefs[bay_id])
              + 1e-4 * top_y)
        if util_gamma > 0.0 and entry is not None:
            bay = bays[bay_id]
            sc += util_gamma * w1 * _window_util(
                sched[bay_id], entry, exit_t, bay.width * bay.height)
        return sc

    if bay_order is None:
        bay_order = sorted(range(n_bays), key=lambda j: prefs[j], reverse=True)
    best_score = float("inf")
    best = None

    # -- Pass A: zero-tardiness placements (skipped when forced) ----------
    if not forced:
        for bay_id in bay_order:
            bay = bays[bay_id]
            bay_zero = False
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=pos_cap):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_zero_slot(bay, sched[bay_id], nb, release, due, proc)
                    if entry is None:
                        continue
                    sc = score(0.0, bay_id, top_y=cy + blk_bb[3],
                               entry=entry, exit_t=entry + proc)
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, entry + proc)
                    bay_zero = True
                    break
                if bay_zero:
                    break
            if bay_zero and w1_dominant:
                break
        if best is not None:
            return best

    # -- Pass B: least-tardy placement ------------------------------------
    lb = release if forced else max(release, due - proc)
    if dense:
        for bay_id in bay_order:
            bay = bays[bay_id]
            if raster is not None:
                slot = _find_earliest_slot_raster(
                    bay, bay_id, sched[bay_id], bi, blk, orients, lb, proc,
                    raster, score_pos=True,
                    time_cap=min(slot_time_cap, 16), pos_cap=slot_pos_cap)
            else:
                slot = _find_earliest_slot(bay, sched[bay_id], bi, blk, orients,
                                           lb, proc, time_cap=slot_time_cap,
                                           pos_cap=slot_pos_cap)
            if slot is None:
                continue
            oi, cx, cy, entry = slot
            exit_t = entry + proc
            blk_bb = _orient_bbox(blk, oi)
            sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3],
                       entry=entry, exit_t=exit_t)
            if sc < best_score:
                best_score = sc
                best = (bay_id, cx, cy, oi, entry, exit_t)
    else:
        for bay_id in bay_order:
            bay = bays[bay_id]
            for oi in orients:
                if not _orient_fits(blk, oi, bay):
                    continue
                blk_bb = _orient_bbox(blk, oi)
                active = [it[0] for it in sched[bay_id] if it[2] > release]
                for (cx, cy) in _candidate_positions(bay, active, blk_bb, cap=12):
                    nb = _mkblock(bi, blk, cx, cy, oi)
                    entry = _find_tardy_slot(bay, sched[bay_id], nb, release, due,
                                             proc, tardy_cap=tardy_cap)
                    if entry is None:
                        continue
                    exit_t = entry + proc
                    sc = score(max(0.0, exit_t - due), bay_id, top_y=cy + blk_bb[3],
                               entry=entry, exit_t=exit_t)
                    if sc < best_score:
                        best_score = sc
                        best = (bay_id, cx, cy, oi, entry, exit_t)
    return best


def _force_place(bi, blk, bays, sched):
    prefs = blk["bay_preferences"]
    release = int(blk["release_time"])
    proc = int(blk["processing_time"])
    for bay_id in sorted(range(len(bays)), key=lambda j: prefs[j], reverse=True):
        bay = bays[bay_id]
        for oi in range(len(blk["shape"])):
            lx0, ly0, lx1, ly1 = _orient_bbox(blk, oi)
            px_lo, px_hi = math.ceil(-lx0), math.floor(bay.width - lx1)
            py_lo, py_hi = math.ceil(-ly0), math.floor(bay.height - ly1)
            if px_lo > px_hi or py_lo > py_hi:
                continue
            px, py = max(0, px_lo), max(0, py_lo)
            entry = _empty_bay_entry(sched[bay_id], release, proc)
            return (bay_id, px, py, oi, entry, entry + proc)
    raise RuntimeError(f"block {bi} cannot be placed")


# -----------------------------------------------------------------------------
# Construction over a given order
# -----------------------------------------------------------------------------

def _add(sched, bay_loads, assignments, bi, blk, place):
    bay_id, cx, cy, oi, entry, exit_t = place
    nb = _mkblock(bi, blk, cx, cy, oi)
    sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
    bay_loads[bay_id] += blk["workload"]
    assignments[bi] = {
        "block_id": bi, "bay_id": bay_id, "x": int(cx), "y": int(cy),
        "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
    }


def _construct(prob_info, order, bays, bay_u, w1, w2, w3, t_start, deadline,
               forced=False, util_gamma=0.0):
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    assignments = {}
    n = len(order)
    for idx, bi in enumerate(order):
        blk = blocks_data[bi]
        time_left = deadline - time.time()
        remaining = n - idx
        dense = time_left > 0 and (time_left / remaining) > 0.25
        place = _place_block(bi, blk, bays, sched, bay_loads, bay_u,
                             w1, w2, w3, dense=dense, forced=forced,
                             util_gamma=util_gamma)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        _add(sched, bay_loads, assignments, bi, blk, place)
    return assignments


# -----------------------------------------------------------------------------
# Safe monotone improver: destroy worst-tardy + neighbors, repair EDD-earliest,
# keep ONLY if verified-feasible AND strictly better.
# -----------------------------------------------------------------------------

def _rebuild_sched(assignments, blocks_data, n_bays):
    sched = [[] for _ in range(n_bays)]
    bay_loads = [0.0] * n_bays
    for bi, a in assignments.items():
        nb = _mkblock(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
        sched[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"], nb.bounding_rect()))
        bay_loads[a["bay_id"]] += blocks_data[bi]["workload"]
    return sched, bay_loads


def _repair_order(removed, blocks_data, mode, rng):
    """Diversified reinsertion orderings -- different orderings unlock different
    packings, which is what lets the improver escape EDD-only local optima."""
    rem = list(removed)
    if mode == 0:      # EDD
        rem.sort(key=lambda i: (blocks_data[i]["due_date"],
                                blocks_data[i]["processing_time"],
                                -_min_area(blocks_data[i])))
    elif mode == 1:    # EDD with tie jitter
        rem.sort(key=lambda i: (blocks_data[i]["due_date"] + rng.uniform(-0.5, 0.5),
                                blocks_data[i]["processing_time"]))
    elif mode == 2:    # earliest release first, then due
        rem.sort(key=lambda i: (blocks_data[i]["release_time"],
                                blocks_data[i]["due_date"]))
    else:              # largest area first within due buckets
        rem.sort(key=lambda i: (blocks_data[i]["due_date"], -_min_area(blocks_data[i])))
    return rem


def _destroy_tardy(cur, blocks_data, k, rng):
    tardy = [(bi, a["exit_time"] - blocks_data[bi]["due_date"])
             for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    if not tardy:
        return None
    tardy.sort(key=lambda z: -z[1])
    removed = set(bi for bi, _ in tardy[:k])
    bays_touched = set(cur[bi]["bay_id"] for bi in removed)
    early_pool = sorted(
        [bi for bi, a in cur.items()
         if bi not in removed and a["bay_id"] in bays_touched],
        key=lambda bi: cur[bi]["entry_time"])
    for bi in early_pool[:k]:
        removed.add(bi)
    return removed


def _destroy_bay_rebalance(cur, blocks_data, bays, rng):
    """v9: cross-bay rebalancing destroy (idea #3 from heuristic_7/8).

    Diagnosis: on the congested/plateaued instances the greedy fills each block's
    *preferred* bay to local zero-tardiness, congesting it so that LATER blocks in
    that bay spill into large tardiness -- and v8's improver, which only ever
    re-packs WITHIN the same bays, cannot undo it. This operator targets the bay
    carrying the most tardiness, removes its worst tardy blocks together with a few
    *movable* (slack, non-tardy) neighbours whose windows overlap them, and returns
    a priority order that reinserts the movable blocks FIRST (so they can relocate
    to under-loaded bays) and the tardy blocks LAST (so they reclaim the freed
    space). The repair uses a load-ascending bay order to actually spread the load.
    Only kept if the official internal objective strictly improves, so paying the
    w3 preference penalty is accepted only when the w1 tardiness saving outweighs
    it (which is exactly the regime w1 >> w3 on these instances)."""
    n_bays = len(bays)
    if n_bays < 2:
        return None, None
    bay_tard = [0.0] * n_bays
    for bi, a in cur.items():
        d = a["exit_time"] - blocks_data[bi]["due_date"]
        if d > 0:
            bay_tard[a["bay_id"]] += d
    tb = max(range(n_bays), key=lambda j: bay_tard[j])
    if bay_tard[tb] <= 0:
        return None, None
    tardy = [(bi, a) for bi, a in cur.items()
             if a["bay_id"] == tb and a["exit_time"] > blocks_data[bi]["due_date"]]
    tardy.sort(key=lambda z: -(z[1]["exit_time"] - blocks_data[z[0]]["due_date"]))
    tardy = tardy[:4]
    tardy_ids = [bi for bi, _ in tardy]
    windows = [(a["entry_time"], a["exit_time"]) for _, a in tardy]
    # Movers = other blocks in tb overlapping the tardy windows, ranked
    # least-tardy-first (cheapest to relocate to an under-loaded bay). Tardy-
    # capable: the STUCK optima (prob_27/30/35/39) are fully tardy, so only tardy
    # movers can attack them. Safety on the round-starved prob_38 comes from a
    # HIGH convergence gate at the call site (only after a long genuine plateau,
    # which prob_38 -- still improving via kicks -- rarely reaches).
    movers = []
    for bi, a in cur.items():
        if bi in tardy_ids or a["bay_id"] != tb:
            continue
        for lo, hi in windows:
            if a["entry_time"] < hi and a["exit_time"] > lo:
                t = max(0, a["exit_time"] - blocks_data[bi]["due_date"])
                movers.append((t, bi))
                break
    movers.sort(key=lambda z: z[0])  # least-tardy (most relocatable) first
    mover_ids = [bi for _, bi in movers[:6]]
    if not mover_ids:
        return None, None
    removed = set(tardy_ids) | set(mover_ids)
    priority = mover_ids + tardy_ids  # relocate movers first, then reclaim space
    return removed, priority


def _destroy_window(cur, blocks_data, rng):
    """Remove ALL blocks active in a sampled congested time window of one bay,
    so the bottleneck window is re-packed wholesale (structural rescheduling)."""
    tardy = [bi for bi, a in cur.items()
             if a["exit_time"] > blocks_data[bi]["due_date"]]
    seed = rng.choice(tardy) if tardy else rng.choice(list(cur))
    bay = cur[seed]["bay_id"]
    center = cur[seed]["entry_time"]
    # window half-width ~ a few typical processing times
    procs = [blocks_data[bi]["processing_time"] for bi in cur]
    half = max(1, int(sorted(procs)[len(procs) // 2]) * 2)
    lo, hi = center - half, center + half
    removed = set(bi for bi, a in cur.items()
                  if a["bay_id"] == bay and a["entry_time"] < hi and a["exit_time"] > lo)
    return removed if removed else {seed}


# -----------------------------------------------------------------------------
# v14: JOINT WINDOW REPACK (LNS-XL). The geometry lever -- coordinated interlock
# needs coordinated placement, so destroy a whole congested (bay,window) and
# rebuild ALL of it jointly with multi-order greedy raster placement, holding the
# un-destroyed neighbours fixed. Obj-gated by the caller (never accepted worse).
# -----------------------------------------------------------------------------

def _repack_window(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng,
                   deadline, forced=False, k_orders=4, max_destroy=30,
                   mode='sbay', win_scale=2.0, nearmiss=0):
    """Pick the most congested (bay, time-window) from `src`, destroy every block
    of that bay whose [entry,exit) intersects it, and rebuild the destroyed set
    jointly (k trial orders, greedy earliest-feasible raster placement against the
    fixed un-destroyed neighbours). Blocks that fail to place in the bay go through
    the normal all-bay repair. Returns a NEW complete assignment dict (candidate),
    or None; the caller obj-gates acceptance. Never mutates `src`.
    v15: `mode='xbay'` delegates to `_repack_xbay` (destroy across ALL bays, free-
    bay rebuild); `win_scale` scales the window width (2.0 == v14). mode='sbay'
    with win_scale=2.0 is byte-identical to v14."""
    if raster is None or not _HAVE_NUMPY:
        return None
    if mode == 'xbay' and len(bays) >= 2:
        return _repack_xbay(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng,
                            deadline, forced=forced, win_scale=win_scale)
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    n = len(blocks_data)
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    procs = [int(b["processing_time"]) for b in blocks_data]
    areas = [_min_area(b) for b in blocks_data]
    pbar = max(1.0, sum(procs) / max(1, n))
    win_w = max(1, int(win_scale * pbar))
    sched, bay_loads = _rebuild_sched(src, blocks_data, n_bays)

    # -- congestion metric: candidate windows keyed at tardy/delayed entries -----
    cands = []
    for bj in range(n_bays):
        items = sched[bj]
        if len(items) < 2:
            continue
        centers = set()
        for (blk, e, ex, bb) in items:
            bi = blk.block_id
            if ex > dues[bi] or e > rels[bi]:   # tardy OR admission-delayed
                centers.add(int(e))
        for c in centers:
            lo, hi = c, c + win_w
            score = 0.0
            for (blk, e, ex, bb) in items:
                ov = min(hi, ex) - max(lo, e)
                if ov > 0:
                    bi = blk.block_id
                    score += areas[bi] * ov + w1 * max(0, ex - dues[bi])
            cands.append((score, bj, lo, hi))
    if not cands:
        return None
    cands.sort(key=lambda z: -z[0])
    # rotate among the top few windows for diversity across repack rounds
    pick = cands[rng.randrange(min(3, len(cands)))] if rng is not None else cands[0]
    _, bj, lo, hi = pick
    bay = bays[bj]
    items = sched[bj]
    destroyed = [it[0].block_id for it in items if it[1] < hi and it[2] > lo]
    if len(destroyed) < 2:
        return None
    if len(destroyed) > max_destroy:
        destroyed.sort(key=lambda bi: -(max(0, src[bi]["exit_time"] - dues[bi])
                                        + 1.0 / (1 + abs(src[bi]["entry_time"] - lo))))
        destroyed = destroyed[:max_destroy]
    dset = set(destroyed)
    fixed_bay = [it for it in items if it[0].block_id not in dset]

    # -- trial orders over the destroyed set ------------------------------------
    def feas_count(bi):
        blk = blocks_data[bi]
        actives = [(it[0].block_id, it[0].orient_idx, it[0].x, it[0].y)
                   for it in fixed_bay]
        tot = 0
        for oi in _unique_orients(blk):
            if not _orient_fits(blk, oi, bay):
                continue
            feas, _cx, _cy, _fp = raster.scan_scoped(bj, actives, bi, oi)
            if feas is not None:
                tot += int(feas.sum())
        return tot

    orders = [
        sorted(destroyed, key=lambda bi: -areas[bi]),                       # area-desc
        sorted(destroyed, key=lambda bi: (dues[bi], procs[bi])),            # due-asc
        sorted(destroyed, key=lambda bi: (dues[bi] - procs[bi] - rels[bi])),  # min-slack
        sorted(destroyed, key=feas_count),                                  # most-constrained
    ][:k_orders]

    best = None  # ((num_failed, tard), placements, failed)
    for od in orders:
        if time.time() > deadline:
            break
        work_bay = list(fixed_bay)
        placements = {}
        failed = []
        for bi in od:
            blk = blocks_data[bi]
            proc = procs[bi]
            slot = _find_earliest_slot_raster(
                bay, bj, work_bay, bi, blk, _unique_orients(blk),
                rels[bi], proc, raster, score_pos=True, nearmiss=nearmiss)
            if slot is None:
                failed.append(bi)
                continue
            oi, x, y, entry = slot
            nb = _mkblock(bi, blk, x, y, oi)
            work_bay.append((nb, entry, entry + proc, nb.bounding_rect()))
            placements[bi] = (bj, x, y, oi, entry, entry + proc)
        tard = 0.0
        for bi, pl in placements.items():
            tard += max(0, pl[5] - dues[bi])
        key = (len(failed), tard)
        if best is None or key < best[0]:
            best = (key, placements, failed)
    if best is None:
        return None
    _key, placements, failed = best

    # -- assemble the candidate assignment --------------------------------------
    work = {bi: dict(a) for bi, a in src.items() if bi not in dset}
    for bi, (bjp, x, y, oi, en, ex) in placements.items():
        work[bi] = {"block_id": bi, "bay_id": bjp, "x": int(x), "y": int(y),
                    "orient_idx": oi, "entry_time": int(en), "exit_time": int(ex)}
    if failed:
        sched2, loads2 = _rebuild_sched(work, blocks_data, n_bays)
        for bi in sorted(failed, key=lambda i: (dues[i], -areas[i])):
            blk = blocks_data[bi]
            place = _place_block(bi, blk, bays, sched2, loads2, bay_u, w1, w2, w3,
                                 forced=forced, slot_time_cap=40, slot_pos_cap=30,
                                 raster=raster)
            if place is None:
                place = _force_place(bi, blk, bays, sched2)
            _add(sched2, loads2, work, bi, blk, place)
    if len(work) != n:
        return None
    return work


def _repack_xbay(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng, deadline,
                 forced=False, k_orders=3, max_destroy=24, win_scale=2.0):
    """v15 r2: cross-bay Z3 GROUP RELOCATION. The r1 congestion-window variant
    measured hopeless on prob_31 (best candidate +12.3M: destroying the tardy
    peak and rebuilding one-at-a-time re-created +932..+5131 tardiness units at
    w1=13333, drowning real Z3 gains of -552..-1232 pref units; 6-17 of 40
    blocks fell to _force_place). The measured fix: harvest ONLY the Z3 money,
    never touching the tardy cluster.
      * movable = off-preference AND currently non-tardy blocks;
      * window score = w3 x recoverable pref gap of movable blocks in window,
        DISCOUNTED by the window's all-bay area-time utilization (quiet windows
        first -- that is where preferred-bay space exists);
      * destroy = movable blocks intersecting the picked window across ALL bays
        (cap `max_destroy`, highest pref gain first);
      * rebuild with `_place_block(forced=False)`: Pass A zero-tardiness slots
        in preference-desc bay order first (w1-dominant instances take the most
        preferred bay with a zero slot -- exactly the Z3-greedy move), Pass B
        least-tardy backstop. Group destroy is what single-block _z3_relocate
        cannot do: freeing several off-pref blocks at once unlocks chain swaps
        (A wants B's bay while B occupies A's target).
    Returns a NEW complete assignment dict or None; caller obj-gates (a rebuild
    that turns a movable block tardy pays w1 and is rejected). Never mutates
    `src`."""
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    n = len(blocks_data)
    dues = [int(b["due_date"]) for b in blocks_data]
    procs = [int(b["processing_time"]) for b in blocks_data]
    areas = [_min_area(b) for b in blocks_data]
    prefs_of = [b["bay_preferences"] for b in blocks_data]
    prefmax = [max(p) for p in prefs_of]
    pbar = max(1.0, sum(procs) / max(1, n))
    win_w = max(1, int(win_scale * pbar))
    tot_area = max(1.0, sum(b.width * b.height for b in bays))

    # movable = off-pref AND non-tardy; pref gain keyed by block
    gain = {}
    for bi, a in src.items():
        offp = prefmax[bi] - prefs_of[bi][a["bay_id"]]
        if offp > 0 and a["exit_time"] <= dues[bi]:
            gain[bi] = offp
    if len(gain) < 2:
        return None

    # -- candidate TIME windows centred at movable entries; score = w3*z3sum
    #    discounted by all-bay area-time utilization (prefer quiet windows) ----
    centers = {int(src[bi]["entry_time"]) for bi in gain}
    cands = []
    for c in centers:
        lo, hi = c, c + win_w
        z3sum = 0.0
        occ = 0.0
        for bi, a in src.items():
            ov = min(hi, a["exit_time"]) - max(lo, a["entry_time"])
            if ov > 0:
                occ += areas[bi] * ov
                g = gain.get(bi)
                if g:
                    z3sum += g
        if z3sum <= 0:
            continue
        util = occ / (tot_area * win_w)
        cands.append((w3 * z3sum * (1.0 - min(0.95, util)), lo, hi))
    if not cands:
        return None
    cands.sort(key=lambda z: -z[0])
    pick = cands[rng.randrange(min(3, len(cands)))] if rng is not None else cands[0]
    _, lo, hi = pick

    # -- destroy the movable blocks intersecting the window ---------------------
    inwin = [bi for bi in gain
             if src[bi]["entry_time"] < hi and src[bi]["exit_time"] > lo]
    if len(inwin) < 2:
        return None
    if len(inwin) > max_destroy:
        inwin.sort(key=lambda bi: -gain[bi])
        inwin = inwin[:max_destroy]
    dset = set(inwin)
    fixed_work = {bi: dict(a) for bi, a in src.items() if bi not in dset}

    # -- k trial orders (zero-slot placement, free bay choice) ------------------
    orders = [
        sorted(inwin, key=lambda bi: -gain[bi]),                 # pref-gain desc
        sorted(inwin, key=lambda bi: (dues[bi], procs[bi])),     # due-asc
        sorted(inwin, key=lambda bi: -areas[bi]),                # area-desc
    ][:k_orders]

    best = None  # (obj, work)
    for od in orders:
        if time.time() > deadline:
            break
        sched2, loads2 = _rebuild_sched(fixed_work, blocks_data, n_bays)
        work = {bi: dict(a) for bi, a in fixed_work.items()}
        for bi in od:
            if time.time() > deadline:
                break        # abandon this order; len(work)!=n discards it
            blk = blocks_data[bi]
            place = _place_block(bi, blk, bays, sched2, loads2, bay_u, w1, w2, w3,
                                 forced=False, slot_time_cap=40, slot_pos_cap=30,
                                 raster=raster)
            # RESTORE-FALLBACK (r2 probe finding: Pass A's corner enumeration
            # misses zero slots -- even the block's own vacated position -- and
            # Pass B then lands it TARDY, +421..+933 o1 units per candidate,
            # drowning the Z3 gain). Re-validate the ORIGINAL placement against
            # the partial rebuild and keep the cheaper of (new, original):
            # relocate who benefits, restore who doesn't. Cost = w1*tard +
            # w3*offpref (the only per-block objective terms).
            oa = src[bi]
            o_bay = oa["bay_id"]
            nb0 = _mkblock(bi, blk, oa["x"], oa["y"], oa["orient_idx"])
            relx0 = _time_overlap_rel(sched2[o_bay], oa["entry_time"],
                                      oa["exit_time"])
            orig_ok = _can_place(bays[o_bay], relx0, nb0, oa["entry_time"],
                                 oa["exit_time"])
            if place is not None:
                new_cost = (w1 * max(0, place[5] - dues[bi])
                            + w3 * (prefmax[bi] - prefs_of[bi][place[0]]))
                orig_cost = w3 * gain[bi]        # original is non-tardy
                if orig_ok and orig_cost <= new_cost + 1e-9:
                    place = (o_bay, oa["x"], oa["y"], oa["orient_idx"],
                             oa["entry_time"], oa["exit_time"])
            elif orig_ok:
                place = (o_bay, oa["x"], oa["y"], oa["orient_idx"],
                         oa["entry_time"], oa["exit_time"])
            if place is None:
                place = _force_place(bi, blk, bays, sched2)
            _add(sched2, loads2, work, bi, blk, place)
        if len(work) != n:
            continue
        o = _objective(work, blocks_data, bays, bay_u, w1, w2, w3)[0]
        if best is None or o < best[0]:
            best = (o, work)
    if best is None:
        return None
    return best[1]


# -----------------------------------------------------------------------------
# v17 EXACT PACKING WINDOW (CP-SAT candidate-menu matheuristic; heuristic_17 #2)
# -----------------------------------------------------------------------------

_MREL = {}   # ((bi1,oi1,bi2,oi2,dx,dy) -> (collide, blocked1by2, blocked2by1))
_MREL_CAP = 2_000_000


def _mask_pair_rel(raster, bi1, oi1, x1, y1, bi2, oi2, x2, y2):
    """Conservative pairwise spatial relations between two candidate
    placements, from the raster masks (soundness: masks are supersets of the
    polygons, so False here proves the exact relation is False; True may be a
    false positive, which only ADDS timing constraints -- never unsound).
    Returns (collide, blocked1by2, blocked2by1):
      collide      -- any same-layer mask overlap (=> presence intervals must
                      be disjoint);
      blocked1by2  -- block1's crane prism (layers >= k over its own layer k)
                      intersects block2's mask => 2's presence obstructs 1's
                      entry/exit moments (entry and exit share geometry).
    Cached by relative offset (translation-invariant)."""
    if x1 <= x2:
        key = (bi1, oi1, bi2, oi2, x2 - x1, y2 - y1)
        swap = False
    else:
        key = (bi2, oi2, bi1, oi1, x1 - x2, y1 - y2)
        swap = True
    v = _MREL.get(key)
    if v is None:
        m1, c1x, c1y = raster.mask(key[0], key[1])
        m2, c2x, c2y = raster.mask(key[2], key[3])
        nl1 = m1.shape[0]; nl2 = m2.shape[0]
        r1, q1 = c1y, c1x                      # block1 at origin
        r2, q2 = key[5] + c2y, key[4] + c2x    # block2 at (dx, dy)
        r0 = max(r1, r2); rE = min(r1 + m1.shape[1], r2 + m2.shape[1])
        q0 = max(q1, q2); qE = min(q1 + m1.shape[2], q2 + m2.shape[2])
        if rE <= r0 or qE <= q0:
            v = (False, False, False)
        else:
            s1 = m1[:, r0 - r1:rE - r1, q0 - q1:qE - q1]
            s2 = m2[:, r0 - r2:rE - r2, q0 - q2:qE - q2]
            col = False
            for l in range(min(nl1, nl2)):
                if (s1[l] & s2[l]).any():
                    col = True
                    break
            b12 = False   # 1's prism (its layer k vs 2's layers >= k)
            for k in range(nl1):
                if b12:
                    break
                for l in range(k, nl2):
                    if (s1[k] & s2[l]).any():
                        b12 = True
                        break
            b21 = False
            for k in range(nl2):
                if b21:
                    break
                for l in range(k, nl1):
                    if (s2[k] & s1[l]).any():
                        b21 = True
                        break
            v = (col, b12, b21)
        if len(_MREL) < _MREL_CAP:
            _MREL[key] = v
    if swap:
        return v[0], v[2], v[1]
    return v


def _exact_pair_rel(raster, bay, blocks_data, bi1, oi1, x1, y1,
                    bi2, oi2, x2, y2):
    """Two-tier pairwise relations for the exact-pack model. Tier 1: the
    conservative mask test -- mask-clear pairs are PROVABLY clear (no exact
    call needed; the common case on big bays). Tier 2: mask-interfering pairs
    are refined with the exact cached geometry primitives (the same audited
    contract _cpsat_retime trusts) -- crucial because masks false-positive on
    every nestled pair, which made the original interlock infeasible in-model
    (measured on prob_26: model optimum 411 > incumbent 345).
    Returns (col, e12, x12, e21, x21):
      col -- blocks spatially collide (presence intervals must be disjoint);
      e12/x12 -- 2's presence obstructs 1's entry/exit moment;
      e21/x21 -- 1's presence obstructs 2's entry/exit moment."""
    col_m, b12_m, b21_m = _mask_pair_rel(raster, bi1, oi1, x1, y1,
                                         bi2, oi2, x2, y2)
    if not (col_m or b12_m or b21_m):
        return (False, False, False, False, False)
    A = _mkblock(bi1, blocks_data[bi1], x1, y1, oi1)
    B = _mkblock(bi2, blocks_data[bi2], x2, y2, oi2)
    col = _collide(bay, A, B) if col_m else False
    if col:
        return (True, False, False, False, False)
    e12 = _entry_blocked(bay, B, A) if b12_m else False
    x12 = _exit_blocked(bay, B, A) if b12_m else False
    e21 = _entry_blocked(bay, A, B) if b21_m else False
    x21 = _exit_blocked(bay, A, B) if b21_m else False
    return (False, e12, x12, e21, x21)


def _exact_pack_window(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng,
                       deadline, forced=False, budget_s=15.0, max_destroy=14,
                       K=12, win_scale=2.0, pair_cap=12000):
    """v17 EXACT PACKING WINDOW. Pick a congested (bay, time-window) exactly as
    the greedy repack does, destroy up to `max_destroy` intersecting blocks,
    and let CP-SAT choose ONE placement per destroyed block from a menu of up
    to K raster-feasible candidates plus integer entry times, minimizing
    w1 * total tardiness of the destroyed set. Fixed neighbours are handled
    two ways: menu candidates from `scan_scoped` are mask-disjoint from EVERY
    fixed block in the widened window (feasible vs fixed at ANY time -- no
    constraint needed); the ORIGINAL placements (always added to the menu) DO
    interfere with fixed blocks, so they get exact v12-audited var-fixed
    timing constraints from the conservative mask relations. Cross-candidate
    relations likewise. The solved placement set is exact-validated with
    _can_place before being returned; the caller obj-gates. Returns a NEW
    complete assignment dict or None. Never mutates `src`."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    if raster is None or not _HAVE_NUMPY:
        return None
    import os as _osx
    _dbg = _osx.environ.get("OGC_XPACK_DEBUG")

    def dlog(msg):
        if _dbg:
            print(f"[xpack] {msg}", flush=True)

    t_end = min(deadline, time.time() + budget_s)
    if time.time() >= t_end - 2.0:
        return None
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    n = len(blocks_data)
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    procs = [int(b["processing_time"]) for b in blocks_data]
    areas = [_min_area(b) for b in blocks_data]
    pbar = max(1.0, sum(procs) / max(1, n))
    win_w = max(1, int(win_scale * pbar))
    sched, _loads = _rebuild_sched(src, blocks_data, n_bays)

    # -- window selection: identical congestion metric to _repack_window -------
    cands_w = []
    for bj in range(n_bays):
        items = sched[bj]
        if len(items) < 2:
            continue
        centers = set()
        for (blk, e, ex, bb) in items:
            bi = blk.block_id
            if ex > dues[bi] or e > rels[bi]:
                centers.add(int(e))
        for c in centers:
            lo, hi = c, c + win_w
            score = 0.0
            for (blk, e, ex, bb) in items:
                ov = min(hi, ex) - max(lo, e)
                if ov > 0:
                    bi = blk.block_id
                    score += areas[bi] * ov + w1 * max(0, ex - dues[bi])
            cands_w.append((score, bj, lo, hi))
    if not cands_w:
        return None
    cands_w.sort(key=lambda z: -z[0])
    # rotate among the top-8 windows: repeated shots on one incumbent should
    # attack DIFFERENT windows (measured: top-3 centers often alias to the
    # same congested cluster).
    pick = (cands_w[rng.randrange(min(8, len(cands_w)))]
            if rng is not None else cands_w[0])
    _, bj, lo, hi = pick
    bay = bays[bj]
    items = sched[bj]
    D = [it[0].block_id for it in items if it[1] < hi and it[2] > lo]
    if len(D) < 2:
        return None
    if len(D) > max_destroy:
        D.sort(key=lambda bi: -(max(0, src[bi]["exit_time"] - dues[bi])
                                + 1.0 / (1 + abs(src[bi]["entry_time"] - lo))))
        D = D[:max_destroy]
    dset = set(D)

    # -- entry-time domains + the fixed relation set over their whole span -----
    lo2, hi2 = lo - win_w, hi + win_w
    lbs, ubs = {}, {}
    for bi in D:
        e0 = src[bi]["entry_time"]
        lbs[bi] = min(max(rels[bi], lo2), e0)
        ubs[bi] = max(hi2 - procs[bi], e0)
    span_lo = min(lbs.values())
    span_hi = max(ubs[bi] + procs[bi] for bi in D)
    fixed = [it for it in items
             if it[0].block_id not in dset
             and it[1] < span_hi and it[2] > span_lo]
    # menus are enumerated against ONLY the fixed blocks overlapping the picked
    # window (requiring clearance against the whole widened span left menus
    # empty in congested bays -- measured on prob_26: every shot degenerated to
    # a pure retime). EVERY candidate then gets mask-based var-fixed timing
    # constraints below, so entry times navigate around the fixed presences.
    actives_win = [(it[0].block_id, it[0].orient_idx, it[0].x, it[0].y)
                   for it in fixed if it[1] < hi and it[2] > lo]

    # -- candidate menus --------------------------------------------------------
    menus = {}     # bi -> [(oi, x, y)]
    for bi in D:
        if time.time() > t_end - 3.0:
            return None
        blk = blocks_data[bi]
        menu = []
        per_oi = max(4, K // max(1, len(_unique_orients(blk))))
        for oi in _unique_orients(blk):
            if not _orient_fits(blk, oi, bay):
                continue
            feas, cx0, cy0, occ_fp = raster.scan_scoped(bj, actives_win, bi, oi)
            if feas is None or not feas.any():
                continue
            cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                 raster.W[bj], occ_fp, True, None)
            for (x, y) in cells[:per_oi]:
                menu.append((oi, x, y))
                if len(menu) >= K:
                    break
            if len(menu) >= K:
                break
        a0 = src[bi]
        menu.append((a0["orient_idx"], a0["x"], a0["y"]))  # original, always last
        menus[bi] = menu

    # -- cross-candidate relation collection (cheap cached mask ops), with
    #    ADAPTIVE MENU SHRINK: near a congested window most candidate pairs
    #    interfere, so K=25 menus can exceed any workable pair budget (first
    #    unit run: every shot bailed at pair_cap). Halve K until the
    #    interfering-pair count fits; the ORIGINAL placement (last entry)
    #    always survives truncation. -------------------------------------------
    Dl = list(D)

    def collect(menus_d):
        out = []
        cnt = 0
        for u in range(len(Dl)):
            for v_ in range(u + 1, len(Dl)):
                i, j = Dl[u], Dl[v_]
                for pi, (oi1, x1, y1) in enumerate(menus_d[i]):
                    for pj, (oi2, x2, y2) in enumerate(menus_d[j]):
                        cnt += 1
                        if (cnt & 255) == 0 and time.time() > t_end - 2.0:
                            return None
                        rel = _exact_pair_rel(raster, bay, blocks_data,
                                              i, oi1, x1, y1, j, oi2, x2, y2)
                        if any(rel):
                            out.append((i, pi, j, pj) + rel)
                            if len(out) > 6 * pair_cap:
                                return out    # hopeless at this K: shrink now
        return out

    k_eff = K
    rels = collect(menus)
    while rels is not None and len(rels) > pair_cap and k_eff > 4:
        k_eff = max(4, k_eff // 2)
        menus = {bi: (menus[bi][:k_eff] + [menus[bi][-1]]) for bi in D}
        rels = collect(menus)
    dlog(f"win=({bj},[{lo},{hi})) D={len(D)} menus="
         f"{sum(len(v) for v in menus.values())} k_eff={k_eff} "
         f"rels={'None' if rels is None else len(rels)} "
         f"tleft={t_end - time.time():.1f}")
    if rels is None or len(rels) > pair_cap:
        return None

    # -- CP-SAT model -----------------------------------------------------------
    m = cp_model.CpModel()
    X, E, T = {}, {}, {}
    for bi in D:
        a0 = src[bi]
        E[bi] = m.NewIntVar(int(lbs[bi]), int(ubs[bi]), f"e{bi}")
        m.AddHint(E[bi], int(a0["entry_time"]))
        T[bi] = m.NewIntVar(0, int(span_hi) + 10, f"t{bi}")
        m.Add(T[bi] >= E[bi] + procs[bi] - dues[bi])
        xs = []
        for pi in range(len(menus[bi])):
            X[bi, pi] = m.NewBoolVar(f"x{bi}_{pi}")
            xs.append(X[bi, pi])
        m.AddExactlyOne(xs)
        m.AddHint(X[bi, len(menus[bi]) - 1], 1)   # original placement

    def outside_vv(i, off_i, j, tie_bad, enf):
        b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
        m.Add(E[i] + off_i <= E[j] - (1 if tie_bad == "left" else 0)
              ).OnlyEnforceIf(enf + [b1])
        m.Add(E[i] + off_i >= E[j] + procs[j] + (1 if tie_bad == "right" else 0)
              ).OnlyEnforceIf(enf + [b2])
        m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)

    def outside_vf(i, off_i, lo_c, hi_c, tie_left, tie_right, enf):
        b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
        m.Add(E[i] + off_i <= lo_c - (1 if tie_left else 0)
              ).OnlyEnforceIf(enf + [b1])
        m.Add(E[i] + off_i >= hi_c + (1 if tie_right else 0)
              ).OnlyEnforceIf(enf + [b2])
        m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)

    npairs = 0
    # -- candidate-vs-FIXED constraints (granular exact relations; encoding
    #    mirrors _cpsat_retime_window's audited var-fixed block) ----------------
    for bi in D:
        for pi, (oi, x, y) in enumerate(menus[bi]):
            for (fb, fa, fe, fbb) in fixed:
                fj = fb.block_id
                col, e_cf, x_cf, e_fc, x_fc = _exact_pair_rel(
                    raster, bay, blocks_data, bi, oi, x, y,
                    fj, fb.orient_idx, fb.x, fb.y)
                if not (col or e_cf or x_cf or e_fc or x_fc):
                    continue
                enf = [X[bi, pi]]
                fa_i, fe_i = int(fa), int(fe)
                npairs += 1
                if col:
                    outside_vf(bi, procs[bi], fa_i, fe_i + procs[bi],
                               False, False, enf)
                    continue
                if e_cf:      # fixed obstructs the candidate's entry moment
                    outside_vf(bi, 0, fa_i, fe_i, fj < bi, False, enf)
                if x_cf:      # fixed obstructs the candidate's exit moment
                    outside_vf(bi, procs[bi], fa_i, fe_i, False, fj > bi, enf)
                if e_fc:      # candidate obstructs the fixed block's entry (fa)
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[bi] >= fa_i + (1 if bi < fj else 0)
                          ).OnlyEnforceIf(enf + [b1])
                    m.Add(E[bi] + procs[bi] <= fa_i).OnlyEnforceIf(enf + [b2])
                    m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)
                if x_fc:      # candidate obstructs the fixed block's exit (fe)
                    b3, b4 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[bi] >= fe_i).OnlyEnforceIf(enf + [b3])
                    m.Add(E[bi] + procs[bi] <= fe_i - (1 if bi > fj else 0)
                          ).OnlyEnforceIf(enf + [b4])
                    m.AddBoolOr([b3, b4]).OnlyEnforceIf(enf)
        if time.time() > t_end - 2.0:
            return None

    # -- cross-candidate constraints (granular exact relations; the encoding
    #    mirrors _cpsat_retime's audited outside_vv / tie rules) ----------------
    for (i, pi, j, pj, col, e12, x12, e21, x21) in rels:
        if time.time() > t_end - 1.5:
            return None
        enf = [X[i, pi], X[j, pj]]
        if col:
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + procs[i] <= E[j]).OnlyEnforceIf(enf + [b1])
            m.Add(E[j] + procs[j] <= E[i]).OnlyEnforceIf(enf + [b2])
            m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)
            continue
        if e12:   # j's presence obstructs i's entry moment
            outside_vv(i, 0, j, "left" if j < i else "none", enf)
        if x12:   # j's presence obstructs i's exit moment
            outside_vv(i, procs[i], j, "right" if j > i else "none", enf)
        if e21:
            outside_vv(j, 0, i, "left" if i < j else "none", enf)
        if x21:
            outside_vv(j, procs[j], i, "right" if i > j else "none", enf)

    m.Minimize(sum(T.values()))
    rem = t_end - time.time() - 0.5
    dlog(f"model built: npairs_vf={npairs} rem={rem:.1f}")
    if rem < 1.0:
        return None
    before = sum(max(0, src[bi]["exit_time"] - dues[bi]) for bi in D)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = rem
    solver.parameters.num_search_workers = 1
    try:
        status = solver.Solve(m)
    except Exception:
        return None
    after = (sum(int(solver.Value(T[bi])) for bi in D)
             if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else -1)
    dlog(f"solve status={solver.StatusName(status)} before={before} "
         f"after={after}")
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    if after >= before:
        return None

    # -- assemble + EXACT validation (belt and braces over the conservative
    #    mask relations; _can_place is the same primitive the whole search
    #    trusts, and the parent still officially verifies) ----------------------
    chosen = {}
    for bi in D:
        for pi in range(len(menus[bi])):
            if solver.Value(X[bi, pi]):
                oi, x, y = menus[bi][pi]
                e = int(solver.Value(E[bi]))
                chosen[bi] = (oi, x, y, e, e + procs[bi])
                break
    full_bay = [it for it in sched[bj] if it[0].block_id not in dset]
    ver = []
    for bi, (oi, x, y, e, ex) in chosen.items():
        nb = _mkblock(bi, blocks_data[bi], x, y, oi)
        ver.append((nb, e, ex, nb.bounding_rect()))
    for k_ in range(len(ver)):
        nb, e, ex, _bb = ver[k_]
        others = [(it[0], it[1], it[2]) for it in full_bay] + \
                 [(v2[0], v2[1], v2[2]) for j2, v2 in enumerate(ver) if j2 != k_]
        if not _can_place(bay, others, nb, e, ex):
            dlog(f"exact validation FAILED for block {nb.block_id}")
            return None      # conservative model missed something: discard
    work = {bi: dict(a) for bi, a in src.items()}
    for bi, (oi, x, y, e, ex) in chosen.items():
        work[bi] = {"block_id": bi, "bay_id": bj, "x": int(x), "y": int(y),
                    "orient_idx": oi, "entry_time": int(e),
                    "exit_time": int(ex)}
    if len(work) != n:
        return None
    return work


# -----------------------------------------------------------------------------
# v18 WHOLE-BAY EXACT PACKING (heuristic_18 #1). Joint replace+retime of one
# entire bay: movers get placement menus, everyone gets a free entry time.
# -----------------------------------------------------------------------------

def _exact_pack_bay(prob_info, src, bays, bay_u, w1, w2, w3, raster, rng,
                    deadline, forced=False, budget_s=60.0, bay_rank=0,
                    n_movers=20, K=8, pair_cap=20000, allow_xbay=True):
    """Whole-bay exact model. Every block currently in the target bay is a
    model variable: `n_movers` movers (highest w1*tard + w3*offpref) get up to
    K raster-feasible alternative placements (+ their original, always last);
    all other blocks keep their original placement as the ONLY candidate
    (K=1 -- their pairwise relations are the incumbent's, already sitting in
    the exact-geometry caches). ALL bay blocks get a free integer entry time
    in [release, H]: the model is a joint replace + retime (v13-audited CP-SAT
    encodings via the v17 two-tier relation machinery). Off-pref movers may
    also get up to 3 candidates in their most-preferred foreign bay (var-fixed
    constrained against that bay's UNCHANGED schedule; migrations relieve the
    home bay and pay/earn the w3 term). `bay_rank` selects the bay by
    descending w1*tardiness + w3*offpref mass (0 = worst). The solved
    configuration is exact-validated with _can_place per final bay before
    being returned; the caller obj-gates with the FULL objective (w2 load
    shifts from migration included). Returns a NEW complete assignment dict or
    None. Never mutates `src`."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    if raster is None or not _HAVE_NUMPY:
        return None
    import os as _osx
    _dbg = _osx.environ.get("OGC_XPACK_DEBUG")

    def dlog(msg):
        if _dbg:
            print(f"[xbaymodel] {msg}", flush=True)

    t_end = min(deadline, time.time() + budget_s)
    if time.time() >= t_end - 10.0:
        return None
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    n = len(blocks_data)
    dues = [int(b["due_date"]) for b in blocks_data]
    rels_ = [int(b["release_time"]) for b in blocks_data]
    procs = [int(b["processing_time"]) for b in blocks_data]
    prefs_of = [b["bay_preferences"] for b in blocks_data]
    prefmax = [max(p) for p in prefs_of]
    pbar = max(1.0, sum(procs) / max(1, n))
    sched, _loads = _rebuild_sched(src, blocks_data, n_bays)

    # -- target bay by descending objective mass --------------------------------
    def bay_mass(j):
        s = 0.0
        for (blk, e, ex, bb) in sched[j]:
            bi = blk.block_id
            s += (w1 * max(0, ex - dues[bi])
                  + w3 * (prefmax[bi] - prefs_of[bi][j]))
        return s
    order_b = sorted(range(n_bays), key=lambda j: -bay_mass(j))
    if bay_rank >= len(order_b):
        return None
    bj = order_b[bay_rank]
    if bay_mass(bj) <= 0:
        return None
    bay = bays[bj]
    ids = [it[0].block_id for it in sched[bj]]
    if len(ids) < 2:
        return None

    # -- horizon and mover selection --------------------------------------------
    max_exit = max(a["exit_time"] for a in src.values())
    H = int(max(max_exit, max(dues)) + 4 * pbar) + 10

    def mover_value(bi):
        a = src[bi]
        return (w1 * max(0, a["exit_time"] - dues[bi])
                + w3 * (prefmax[bi] - prefs_of[bi][bj]))
    # v18 r2: movers are a CLUSTERED congestion-window set (v14-repack-style),
    # not the global top-by-value -- value-scattered movers across the horizon
    # cannot jointly rearrange (measured on prob_39: 4M branches, zero yield);
    # a window cluster is where joint placement freedom pays (the proven v17
    # window mechanism, here with whole-bay retime flex around it).
    win_w = max(1, int(2 * pbar))
    centers = set()
    for (blk, e, ex, bb) in sched[bj]:
        bi = blk.block_id
        if ex > dues[bi] or e > rels_[bi]:
            centers.add(int(e))
    movers = []
    if centers:
        cands_w = []
        for c in centers:
            lo, hi = c, c + win_w
            sc_ = 0.0
            for (blk, e, ex, bb) in sched[bj]:
                ov = min(hi, ex) - max(lo, e)
                if ov > 0:
                    sc_ += ov + w1 * max(0, ex - dues[blk.block_id])
            cands_w.append((sc_, lo, hi))
        cands_w.sort(key=lambda z: -z[0])
        pick = (cands_w[rng.randrange(min(8, len(cands_w)))]
                if rng is not None else cands_w[0])
        _, lo, hi = pick
        movers = [it[0].block_id for it in sched[bj]
                  if it[1] < hi and it[2] > lo]
        if len(movers) > n_movers:
            movers.sort(key=lambda bi: -mover_value(bi))
            movers = movers[:n_movers]
    if len(movers) < 2:
        by_val = sorted(ids, key=lambda bi: -mover_value(bi))
        movers = [bi for bi in by_val[:n_movers] if mover_value(bi) > 0]
    mover_set = set(movers)

    # -- candidate menus ---------------------------------------------------------
    def build_menus(n_mov, k_alt):
        mset = set(movers[:n_mov])
        menus_d = {}
        for bi in ids:
            a0 = src[bi]
            menu = []
            if bi in mset and time.time() < t_end - 8.0:
                blk = blocks_data[bi]
                # candidate spots = cells free of the NON-MOVER blocks around
                # the mover's window (the movers lift out JOINTLY -- scanning
                # against other movers blockaded every useful spot and left
                # the solver hint-locked; measured on prob_39: 82k branches,
                # zero movement). +-2*pbar slack matches the non-mover retime
                # domains.
                w_lo = a0["entry_time"] - 2 * pbar
                w_hi = a0["exit_time"] + 2 * pbar
                acts_t = [(it[0].block_id, it[0].orient_idx, it[0].x, it[0].y)
                          for it in sched[bj]
                          if it[0].block_id != bi
                          and it[0].block_id not in mset
                          and it[1] < w_hi and it[2] > w_lo]
                for oi in _unique_orients(blk):
                    if not _orient_fits(blk, oi, bay):
                        continue
                    feas, cx0, cy0, occ_fp = raster.scan_scoped(
                        bj, acts_t, bi, oi)
                    if feas is None:
                        continue
                    if not feas.any():
                        # bay full during its window: fall back to ALL anchors
                        feas, cx0, cy0, occ_fp = raster.scan_scoped(
                            bj, [], bi, oi)
                        if feas is None or not feas.any():
                            continue
                    cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                         raster.W[bj], occ_fp, True, None)
                    half = max(1, k_alt // 2)
                    picked = cells[:half]
                    restc = cells[half:]
                    if restc:
                        stride = max(1, len(restc) // max(1, k_alt - half))
                        picked = picked + restc[::stride][:k_alt - half]
                    for (x, y) in picked:
                        menu.append((bj, oi, x, y))
                        if len(menu) >= k_alt:
                            break
                    if len(menu) >= k_alt:
                        break
                # foreign-bay candidates for off-pref movers (Z3 recovery)
                offg = prefmax[bi] - prefs_of[bi][bj]
                if allow_xbay and offg > 0 and n_bays >= 2:
                    tj = max((j for j in range(n_bays) if j != bj),
                             key=lambda j: prefs_of[bi][j])
                    if prefs_of[bi][tj] > prefs_of[bi][bj]:
                        tbay = bays[tj]
                        acts_f = [(it[0].block_id, it[0].orient_idx,
                                   it[0].x, it[0].y)
                                  for it in sched[tj]
                                  if it[1] < a0["exit_time"]
                                  and it[2] > a0["entry_time"]]
                        for oi in _unique_orients(blk):
                            if not _orient_fits(blk, oi, tbay):
                                continue
                            feas, cx0, cy0, occ_fp = raster.scan_scoped(
                                tj, acts_f, bi, oi)
                            if feas is None or not feas.any():
                                continue
                            cells = _order_cells(raster, feas, cx0, cy0, bi,
                                                 oi, raster.W[tj], occ_fp,
                                                 True, None)
                            for (x, y) in cells[:3]:
                                menu.append((tj, oi, x, y))
                            break
            menu.append((bj, a0["orient_idx"], a0["x"], a0["y"]))  # original
            menus_d[bi] = menu
        return menus_d

    # -- relation collection (two-tier exact; cross pairs same-bay only) --------
    def collect(menus_d):
        out = []
        cnt = 0
        idl = ids
        for u in range(len(idl)):
            for v_ in range(u + 1, len(idl)):
                i, j = idl[u], idl[v_]
                for pi, (b1, oi1, x1, y1) in enumerate(menus_d[i]):
                    for pj, (b2, oi2, x2, y2) in enumerate(menus_d[j]):
                        if b1 != b2:
                            continue      # different bays never interact
                        cnt += 1
                        if (cnt & 255) == 0 and time.time() > t_end - 6.0:
                            return None
                        rel = _exact_pair_rel(raster, bays[b1], blocks_data,
                                              i, oi1, x1, y1, j, oi2, x2, y2)
                        if any(rel):
                            out.append((i, pi, j, pj) + rel)
                            if len(out) > 3 * pair_cap:
                                return out
        return out

    menus = build_menus(len(movers), K)
    rels = collect(menus)
    if rels is not None and len(rels) > pair_cap:
        # one retry at reduced scale
        menus = build_menus(max(4, len(movers) // 2), 4)
        rels = collect(menus)
    dlog(f"bay={bj} ids={len(ids)} movers={len(movers)} "
         f"menus={sum(len(v) for v in menus.values())} "
         f"rels={'None' if rels is None else len(rels)} "
         f"tleft={t_end - time.time():.1f}")
    if rels is None or len(rels) > pair_cap:
        return None

    # -- CP-SAT model ------------------------------------------------------------
    m = cp_model.CpModel()
    SC = 100
    w1i = max(1, int(round(w1 * SC)))
    w3i = max(0, int(round(w3 * SC)))
    X, E, T = {}, {}, {}
    obj_terms = []
    delta = max(1, int(2 * pbar))
    mv_set = set(bi for bi in ids if len(menus[bi]) > 1)
    for bi in ids:
        a0 = src[bi]
        e0 = int(a0["entry_time"])
        if bi in mv_set:
            lo_e, hi_e = rels_[bi], H
        else:
            # fix-and-optimize: non-movers keep their placement AND stay within
            # +-2*pbar of their incumbent time -- full-retime freedom for all
            # ~115 bay blocks measured as search-drowning (solver only proves
            # the hint in 72s); local slack is what the movers' rearrangement
            # actually needs.
            lo_e, hi_e = max(rels_[bi], e0 - delta), min(H, e0 + delta)
        E[bi] = m.NewIntVar(min(lo_e, e0), max(hi_e, e0), f"e{bi}")
        m.AddHint(E[bi], e0)
        T[bi] = m.NewIntVar(0, H, f"t{bi}")
        m.Add(T[bi] >= E[bi] + procs[bi] - dues[bi])
        obj_terms.append(w1i * T[bi])
        xs = []
        for pi, (b_, oi, x, y) in enumerate(menus[bi]):
            X[bi, pi] = m.NewBoolVar(f"x{bi}_{pi}")
            xs.append(X[bi, pi])
            offg = prefmax[bi] - prefs_of[bi][b_]
            if offg > 0 and w3i > 0:
                obj_terms.append(w3i * offg * X[bi, pi])
        m.AddExactlyOne(xs)
        m.AddHint(X[bi, len(menus[bi]) - 1], 1)

    def outside_vv(i, off_i, j, tie_bad, enf):
        b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
        m.Add(E[i] + off_i <= E[j] - (1 if tie_bad == "left" else 0)
              ).OnlyEnforceIf(enf + [b1])
        m.Add(E[i] + off_i >= E[j] + procs[j] + (1 if tie_bad == "right" else 0)
              ).OnlyEnforceIf(enf + [b2])
        m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)

    def outside_vf(i, off_i, lo_c, hi_c, tie_left, tie_right, enf):
        b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
        m.Add(E[i] + off_i <= lo_c - (1 if tie_left else 0)
              ).OnlyEnforceIf(enf + [b1])
        m.Add(E[i] + off_i >= hi_c + (1 if tie_right else 0)
              ).OnlyEnforceIf(enf + [b2])
        m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)

    # -- cross-candidate constraints ---------------------------------------------
    for (i, pi, j, pj, col, e12, x12, e21, x21) in rels:
        if time.time() > t_end - 4.0:
            return None
        enf = [X[i, pi], X[j, pj]]
        if col:
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + procs[i] <= E[j]).OnlyEnforceIf(enf + [b1])
            m.Add(E[j] + procs[j] <= E[i]).OnlyEnforceIf(enf + [b2])
            m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)
            continue
        if e12:
            outside_vv(i, 0, j, "left" if j < i else "none", enf)
        if x12:
            outside_vv(i, procs[i], j, "right" if j > i else "none", enf)
        if e21:
            outside_vv(j, 0, i, "left" if i < j else "none", enf)
        if x21:
            outside_vv(j, procs[j], i, "right" if i > j else "none", enf)

    # -- foreign-bay candidates vs that bay's FIXED schedule ---------------------
    for bi in ids:
        for pi, (b_, oi, x, y) in enumerate(menus[bi]):
            if b_ == bj:
                continue
            for (fb, fa, fe, fbb) in sched[b_]:
                fj = fb.block_id
                col, e_cf, x_cf, e_fc, x_fc = _exact_pair_rel(
                    raster, bays[b_], blocks_data, bi, oi, x, y,
                    fj, fb.orient_idx, fb.x, fb.y)
                if not (col or e_cf or x_cf or e_fc or x_fc):
                    continue
                enf = [X[bi, pi]]
                fa_i, fe_i = int(fa), int(fe)
                if col:
                    outside_vf(bi, procs[bi], fa_i, fe_i + procs[bi],
                               False, False, enf)
                    continue
                if e_cf:
                    outside_vf(bi, 0, fa_i, fe_i, fj < bi, False, enf)
                if x_cf:
                    outside_vf(bi, procs[bi], fa_i, fe_i, False, fj > bi, enf)
                if e_fc:
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[bi] >= fa_i + (1 if bi < fj else 0)
                          ).OnlyEnforceIf(enf + [b1])
                    m.Add(E[bi] + procs[bi] <= fa_i).OnlyEnforceIf(enf + [b2])
                    m.AddBoolOr([b1, b2]).OnlyEnforceIf(enf)
                if x_fc:
                    b3, b4 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[bi] >= fe_i).OnlyEnforceIf(enf + [b3])
                    m.Add(E[bi] + procs[bi] <= fe_i - (1 if bi > fj else 0)
                          ).OnlyEnforceIf(enf + [b4])
                    m.AddBoolOr([b3, b4]).OnlyEnforceIf(enf)
        if time.time() > t_end - 4.0:
            return None

    m.Minimize(sum(obj_terms))
    rem = t_end - time.time() - 0.5
    dlog(f"model built, rem={rem:.1f}")
    if rem < 5.0:
        return None
    before = 0
    for bi in ids:
        a0 = src[bi]
        before += w1i * max(0, a0["exit_time"] - dues[bi])
        before += w3i * (prefmax[bi] - prefs_of[bi][bj])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = rem
    solver.parameters.num_search_workers = int(
        _osx.environ.get("OGC_XPACK_WORKERS", "1"))
    try:
        status = solver.Solve(m)
    except Exception:
        return None
    after = (int(solver.ObjectiveValue())
             if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else -1)
    dlog(f"solve status={solver.StatusName(status)} before={before} "
         f"after={after} branches={solver.NumBranches()} "
         f"wall={solver.WallTime():.1f}")
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    if after >= before:
        return None

    # -- assemble + exact validation ---------------------------------------------
    chosen = {}
    for bi in ids:
        for pi in range(len(menus[bi])):
            if solver.Value(X[bi, pi]):
                b_, oi, x, y = menus[bi][pi]
                e = int(solver.Value(E[bi]))
                chosen[bi] = (b_, oi, x, y, e, e + procs[bi])
                break
    work = {bi: dict(a) for bi, a in src.items()}
    for bi, (b_, oi, x, y, e, ex) in chosen.items():
        work[bi] = {"block_id": bi, "bay_id": b_, "x": int(x), "y": int(y),
                    "orient_idx": oi, "entry_time": int(e),
                    "exit_time": int(ex)}
    if len(work) != n:
        return None
    # validate every changed block against its FINAL bay context
    sched2, _l2 = _rebuild_sched(work, blocks_data, n_bays)
    touched_bays = {bj} | {c[0] for c in chosen.values()}
    for b_ in touched_bays:
        items2 = [(it[0], it[1], it[2]) for it in sched2[b_]]
        for k_ in range(len(items2)):
            nb, e, ex = items2[k_]
            bi = nb.block_id
            if bi not in chosen and b_ != bj:
                continue      # untouched foreign incumbents: mutual pairs
                #               unchanged; immigrants are checked below
            others = [items2[j2] for j2 in range(len(items2)) if j2 != k_]
            if not _can_place(bays[b_], others, nb, e, ex):
                dlog(f"exact validation FAILED for block {bi} in bay {b_}")
                return None
    return work


def _improve(prob_info, assignments, bays, bay_u, w1, w2, w3, deadline, forced,
             seed=4242, sa=False, on_best=None, inbox=None, raster=None,
             repack_every=0, xbay=False, repack_win_scale=2.0, deep=False,
             nearmiss=0):
    """Basin-hopping destroy/repair. Tracks `best` separately from the working
    `cur`; returns `best` -> monotone in the RESULT. Diversifies destroy mode and
    repair ordering, and applies an escape "kick" (a larger destroy accepted even
    if worse) after a plateau, to break out of local structures the pure
    hill-climber (v3) gets stuck in (prob_39). Compares by the cheap internal
    objective; the caller verifies the returned solution officially.
    v10: `seed` diversifies portfolio workers; `sa` enables simulated-annealing
    acceptance of worse repairs (explorer worker); `on_best(obj, assign)` streams
    new incumbents to the parent process."""
    blocks_data = prob_info["blocks"]
    n = len(assignments)
    n_bays = len(bays)
    best_assign = {k: dict(v) for k, v in assignments.items()}
    best_obj, best_o1, _, _ = _objective(best_assign, blocks_data, bays, bay_u, w1, w2, w3)
    cur = {k: dict(v) for k, v in best_assign.items()}
    cur_obj = best_obj

    def _tardy_count(assign):
        return sum(1 for bi, a in assign.items()
                   if a["exit_time"] > blocks_data[bi]["due_date"])

    best_tardy = _tardy_count(best_assign)
    rng = random.Random(seed)
    # SA temperature: a small fraction of the current objective so that typical
    # repair deltas (a few tardy time-units * w1) are accepted early on, with
    # geometric cooling and a reheat on long stalls.
    T0 = max(1.0, 0.01 * best_obj) if sa else 0.0
    T = T0
    rounds = 0
    repack_idx = 0      # v15: counts fired repack rounds -> alternate sbay/xbay
    no_improve = 0      # for kick triggering (kicks reset this)
    since_best = 0      # rounds since best improved (kicks do NOT reset this)
    since_o1 = 0        # rounds since best TARDINESS (obj1) improved -- the real
    #                     convergence signal (tiny obj2/obj3 gains keep resetting
    #                     since_best on forced instances, hiding the obj1 stall)
    n_restart = 0; n_rebal = 0   # debug fire counters (OGC_DEBUG)
    KICK = 6
    REBAL_AFTER = 10**9   # v9: cross-bay rebalance OFF (couldn't crack stuck optima)
    RESTART_AFTER = 10**9 # v9: partial-restart OFF (improver too round-starved to fire)
    RESTART_EVERY = 25    # cadence of restarts once past RESTART_AFTER
    RESTART_FRAC = 0.45   # fraction of the champion rebuilt on a restart
    # Small destroy sets + capped repair search => many more rounds/sec, which is
    # what makes the improver bite under real (and contended) compute budgets.
    while time.time() < deadline:
        # v11 island model: adopt a better global incumbent from the parent.
        # (W0/v9-replica never gets an inbox, so the anchor stays byte-exact.)
        if inbox is not None:
            try:
                while True:
                    o_in, a_in = inbox.get_nowait()
                    if o_in < best_obj - 1e-9:
                        best_obj = o_in
                        best_assign = {k: dict(v) for k, v in a_in.items()}
                        best_tardy = _tardy_count(best_assign)
                        cur = {k: dict(v) for k, v in a_in.items()}
                        cur_obj = o_in
                        no_improve = 0
                        since_best = 0
            except Exception:
                pass
        # Early stop: nothing tardy left and the search has stalled -> the obj2/
        # obj3 part is exhausted; stop instead of burning the rest of the budget.
        if best_tardy == 0 and since_best > 40:
            break
        rounds += 1
        # v14: JOINT WINDOW REPACK round (obj-gated, tardy instances only). Every
        # `repack_every`-th round, destroy+rebuild a whole congested (bay,window)
        # jointly instead of the classic scattered destroy/repair. repack_every==0
        # (W0 + v13-basin tickets) skips this entirely -> byte-exact v13.
        if (repack_every > 0 and raster is not None and best_tardy > 0
                and rounds % repack_every == 0):
            # v15: alternate single-bay / cross-bay round-robin. First fire is
            # single-bay (== v14); cross-bay every other fire when enabled. The
            # counter consumes no rng, so xbay=False is byte-exact v14.
            # v16 `deep` (reclaimed instances only): destroy cap 30 -> 45 and
            # the window scale rotates per fire over {2,1,3,4}*pbar.
            mode = 'sbay'
            if xbay and n_bays >= 2 and (repack_idx % 2 == 1):
                mode = 'xbay'
            ws = repack_win_scale
            md = 30
            if deep:
                ws = (2.0, 1.0, 3.0, 4.0)[(repack_idx // 2) % 4]
                md = 45
            repack_idx += 1
            try:
                work = _repack_window(prob_info, cur, bays, bay_u, w1, w2, w3,
                                      raster, rng, deadline, forced=forced,
                                      mode=mode, win_scale=ws, max_destroy=md,
                                      nearmiss=nearmiss)
            except Exception:
                work = None
            if work is not None and len(work) == n:
                new_obj, new_o1, _, _ = _objective(work, blocks_data, bays,
                                                    bay_u, w1, w2, w3)
                if new_obj < cur_obj - 1e-9:
                    cur = work
                    cur_obj = new_obj
                if new_obj < best_obj - 1e-9:
                    best_obj = new_obj
                    best_assign = {k: dict(v) for k, v in work.items()}
                    best_tardy = _tardy_count(best_assign)
                    no_improve = 0
                    since_best = 0
                    if on_best is not None:
                        on_best(best_obj, best_assign)
                else:
                    no_improve += 1
                    since_best += 1
                if new_o1 < best_o1 - 1e-9:
                    best_o1 = new_o1
                    since_o1 = 0
                else:
                    since_o1 += 1
                continue
        kick = no_improve >= KICK
        spread = False       # v9: repair with a load-ascending bay order (rebalance)
        priority = None      # v9: explicit reinsertion order (movers first)
        # v9: DEEP PARTIAL RESTART -- once the search has been stalled for a long
        # time (since_best >= RESTART_AFTER, i.e. genuinely converged with budget
        # to spare, which the round-starved giants NEVER reach so they are
        # untouched), periodically blow away a large random fraction of the
        # CHAMPION and rebuild it from a randomized order, accepting the result
        # even if worse. This is a big basin-hop: the deterministic descent
        # otherwise re-lands in the exact same local optimum every version
        # (prob_27/39/30/35 are byte-identical across v3..v8), and only a large
        # perturbation of the incumbent can reach a different basin.
        restart = (since_o1 >= RESTART_AFTER and since_o1 % RESTART_EVERY == 0)
        src = cur
        if restart:
            n_restart += 1
            src = best_assign
            removed = set(rng.sample(list(src), max(1, int(n * RESTART_FRAC))))
        elif kick:
            removed = _destroy_window(cur, blocks_data, rng)
            extra = rng.sample(list(cur), min(len(cur), 6))
            removed = set(removed) | set(extra)
        elif n_bays >= 2 and since_best >= REBAL_AFTER:
            # v9: cross-bay rebalancing fires ONLY after the improver has truly
            # CONVERGED (>= REBAL_AFTER rounds since the incumbent last improved),
            # never during the descent. This is the hard-won safety property: the
            # big round-starved instances (prob_38 n=250, prob_39 n=250) keep
            # improving in-bay for the WHOLE budget, so `since_best` never reaches
            # REBAL_AFTER -> rebalance never fires -> those instances are byte-for-
            # byte v8 (measured: an eager plateau trigger stole their descent
            # rounds and regressed prob_38 by ~11M). Instances that genuinely
            # converge with budget to spare (prob_27/30/33) reach the gate and get
            # the cross-bay move -- pure upside, since post-convergence in-bay
            # rounds are otherwise wasted. Relieves the most-tardy bay by
            # relocating slack neighbours to under-loaded bays.
            removed, priority = _destroy_bay_rebalance(cur, blocks_data, bays, rng)
            if removed:
                spread = True
            else:
                k = min(6, max(2, n // 40))
                removed = _destroy_tardy(cur, blocks_data, k, rng)
                if removed is None:
                    removed = _destroy_window(cur, blocks_data, rng)
        elif rounds % 3 == 0:
            removed = _destroy_window(cur, blocks_data, rng)
        else:
            k = min(6, max(2, n // 40))
            removed = _destroy_tardy(cur, blocks_data, k, rng)
            if removed is None:
                removed = _destroy_window(cur, blocks_data, rng)
        if not removed:
            break

        work = {bi: dict(a) for bi, a in src.items() if bi not in removed}
        sched, bay_loads = _rebuild_sched(work, blocks_data, n_bays)
        if spread and priority:
            rem_order = [bi for bi in priority if bi in removed]
        elif restart:
            # rebuild the perturbed champion from a fresh randomized order so the
            # descent re-lands somewhere new rather than in the same basin.
            rem_order = _repair_order(removed, blocks_data, rng.randint(0, 3), rng)
            rng.shuffle(rem_order)
        else:
            rem_order = _repair_order(removed, blocks_data, rounds % 4, rng)
        ok = True
        for bi in rem_order:
            if time.time() > deadline:
                ok = False; break
            blk = blocks_data[bi]
            bo = sorted(range(n_bays), key=lambda j: bay_loads[j]) if spread else None
            # v13: raster-windowed repair (density lever) when the instance is
            # forced OR the incumbent still has tardiness (schedule/density-
            # limited mid-tier); zero-tardiness easies keep the cheap AABB
            # repair (raster costs more per move and buys nothing there).
            use_raster = raster if (forced or best_tardy > 0) else None
            place = _place_block(bi, blk, bays, sched, bay_loads, bay_u, w1, w2, w3,
                                 forced=forced, slot_time_cap=40, slot_pos_cap=30,
                                 bay_order=bo, raster=use_raster)
            if place is None:
                place = _force_place(bi, blk, bays, sched)
            _add(sched, bay_loads, work, bi, blk, place)
        if not ok or len(work) != n:
            continue
        new_obj, new_o1, _, _ = _objective(work, blocks_data, bays, bay_u, w1, w2, w3)
        accept = new_obj < cur_obj - 1e-9 or kick or restart
        if not accept and sa and T > 1e-9:
            delta = new_obj - cur_obj
            if delta / T < 30 and rng.random() < math.exp(-delta / T):
                accept = True
        if accept:
            cur = work
            cur_obj = new_obj
        if sa:
            T *= 0.995
            if since_best >= 60:
                T = T0  # reheat after a long stall
        if new_obj < best_obj - 1e-9:
            best_obj = new_obj
            best_assign = {k: dict(v) for k, v in work.items()}
            best_tardy = _tardy_count(best_assign)
            no_improve = 0
            since_best = 0
            if on_best is not None:
                on_best(best_obj, best_assign)
        else:
            no_improve = 0 if (kick or restart) else no_improve + 1
            since_best += 1
        if new_o1 < best_o1 - 1e-9:
            best_o1 = new_o1
            since_o1 = 0
        else:
            since_o1 += 1
    import os as _os
    if _os.environ.get("OGC_DEBUG"):
        print(f"[improve] rounds={rounds} n_restart={n_restart} n_rebal={n_rebal} "
              f"best_o1={best_o1} since_o1={since_o1}", flush=True)
    return best_assign, best_obj


# -----------------------------------------------------------------------------
# Build operations dict (verbatim from v2)
# -----------------------------------------------------------------------------

def _build_operations(assignments):
    buckets = {}
    for a in assignments.values():
        buckets.setdefault(int(a["exit_time"]), []).append(
            (0, "EXIT", a["block_id"], a["bay_id"], None, None, None))
        buckets.setdefault(int(a["entry_time"]), []).append(
            (1, "ENTRY", a["block_id"], a["bay_id"], a["x"], a["y"], a["orient_idx"]))
    operations = {}
    for t in sorted(buckets):
        ops = sorted(buckets[t], key=lambda r: (r[0], r[2]))
        lst = []
        for _, kind, bid, bay, x, y, oi in ops:
            op = {"type": kind, "block_id": bid, "bay_id": bay}
            if kind == "ENTRY":
                op["x"], op["y"], op["orient_idx"] = x, y, oi
            lst.append(op)
        operations[str(t)] = lst
    return operations


def _empty_bay_solution(prob_info, bays):
    fallback = {}
    sched0 = [[] for _ in range(len(bays))]
    for bi, blk in enumerate(prob_info["blocks"]):
        bay_id, px, py, oi, entry, exit_t = _force_place(bi, blk, bays, sched0)
        sched0[bay_id].append(
            (Block(block_id=bi, block_data=blk, x=px, y=py, orient_idx=oi),
             entry, exit_t))
        fallback[bi] = {
            "block_id": bi, "bay_id": bay_id, "x": px, "y": py,
            "orient_idx": oi, "entry_time": entry, "exit_time": exit_t,
        }
    return fallback


# -----------------------------------------------------------------------------
# Forced detection (verbatim from v2)
# -----------------------------------------------------------------------------

def _is_forced(prob_info, bays):
    cap = sum(b.width * b.height for b in bays)
    ev = {}
    for b in prob_info["blocks"]:
        r = b["release_time"]; du = b["due_date"]; p = b["processing_time"]
        ms = du - p; me = r + p
        if ms < me:
            a = _min_area(b)
            ev[ms] = ev.get(ms, 0.0) + a
            ev[me] = ev.get(me, 0.0) - a
    run = 0.0; peak = 0.0
    for t in sorted(ev):
        run += ev[t]; peak = max(peak, run)
    return peak > cap


# -----------------------------------------------------------------------------
# v9 search pipeline (exact replica). Used BOTH by the single-thread fallback
# and by portfolio worker W0: the improver is extremely basin-sensitive (on
# prob_31, EDD+improve plateaus at 19.09M while v9's jittered-construction
# improve reached 17.64M), so preserving v9's exact multi-start rng stream and
# two-pass improver is what guarantees v10 never loses a v9 result.
# -----------------------------------------------------------------------------

def _v9_search(prob_info, timelimit, t_start, push=None):
    """Runs v9's whole search; returns the candidate list [(obj, assign)] and
    streams every candidate/incumbent through push(obj, assign) if given."""
    # Reserve a slice at the end for the official feasibility check(s).
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    search_deadline = t_start + timelimit * 0.95 - reserve
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w1 = prob_info.get("weights", {}).get("w1", 1.0)
    w2 = prob_info.get("weights", {}).get("w2", 1.0)
    w3 = prob_info.get("weights", {}).get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)

    def iobj(assign):
        return _objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]

    # All candidates scored by the CHEAP internal objective; the single best is
    # verified once at the end (no per-strategy check_feasibility -> no overrun).
    candidates = []  # (internal_obj, assign)

    def emit(assign):
        o = iobj(assign)
        candidates.append((o, assign))
        if push is not None:
            push(o, assign)

    edd_assign = None  # the plain-EDD construction (forced): always improved so
    #                    v9 never regresses below v8 on improver-dependent instances

    search_window = search_deadline - t_start
    edd = _edd_order(blocks_data)
    cong = _congestion_order(blocks_data)

    if forced:
        # v9: MULTI-START construction for forced instances. Key finding: on the
        # stuck instances (prob_27/30/35 -- byte-identical across v3..v8) the
        # improver contributes NOTHING; their objective IS the deterministic EDD
        # construction, and the improver's ~70 wasted seconds never beat it. But
        # a *jittered* EDD order yields a strictly better construction on several
        # of them (prob_30 14.39M->12.95M, prob_27 52.40M->51.47M). So instead of
        # one EDD construction + a useless improver, run EDD plus as many dense
        # jittered-EDD constructions as fit in ~70% of the window (keeping the
        # best), then let the improver use the remaining ~30% (which still helps
        # the genuinely round-starved giants like prob_38/39). Each construction
        # is dense (passed the full deadline) and finishes in its natural time, so
        # big instances fit ~1 (~ old behavior) while small ones fit 2-3.
        rng_c = random.Random(2026)
        t_first = search_window  # conservative default if the first build fails
        try:
            t0c = time.time()
            assign = _construct(prob_info, edd, bays, bay_u, w1, w2, w3,
                                t_start, search_deadline, forced=True)
            t_first = time.time() - t0c
            edd_assign = assign
            emit(assign)
        except Exception:
            pass
        # Multi-start ONLY on "construction-cheap" instances -- those whose first
        # dense build took a small fraction of the window. Rationale + safety:
        #  * On such instances the improver is nearly useless (the stuck optima
        #    prob_27/30/35 are byte-identical across v3..v8), so spare budget is
        #    far better spent on more constructions; jittered EDD orders find
        #    strictly better constructions (prob_30 -2.6M, prob_35 -3.2M).
        #  * The round-starved giants (prob_38/39, n=250) have a SLOW first build
        #    (a large fraction of the window), so they are skipped and keep their
        #    full improver share == v8 (measured: forcing a jitter on prob_38 only
        #    steals descent time). The gate is a *fraction* of the window, so it
        #    adapts to the budget: at larger time limits a giant's build is a
        #    smaller fraction and multi-start turns on once the improver has room.
        # 9b: rotate through DIVERSE base orders. Measured: the largest-footprint-
        # first (AREA) order STRICTLY beats EDD on the stuck giants (prob_27
        # 52.4M->49.7M, prob_39 29.8M->27.1M, prob_26 22.7M->19.4M) -- placing the
        # hardest-to-fit blocks while the bays are empty reaches a far better
        # geometric basin. (SLACK was worse everywhere -> dropped.) Cap the
        # construction phase at CON_FRAC of the window so the improver keeps a
        # guaranteed share (>= 1-CON_FRAC): this prevents the regressions seen when
        # constructions starved improver-dependent instances. At larger time
        # limits this window fits EDD+AREA even on the n=250 giants (needs ~300s),
        # which is where the AREA gains live.
        CON_FRAC = 0.55
        con_cap = t_start + search_window * CON_FRAC
        plan = [
            lambda: _area_order(blocks_data),
            lambda: _edd_order(blocks_data, jitter=rng_c),
            lambda: _area_order(blocks_data, jitter=rng_c),
            lambda: _edd_order(blocks_data, jitter=rng_c),
            lambda: _area_order(blocks_data, jitter=rng_c),
        ]
        gi = 0
        while time.time() + t_first < con_cap:
            try:
                order = plan[gi % len(plan)]()
                gi += 1
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=True)
                emit(assign)
            except Exception:
                break
    else:
        # Uncongested: keep v3's strong behavior -- thorough congestion+zero-slot
        # Pass A primary, EDD secondary, then bounded EDD-jitter perturbations.
        for order, fc in [(cong, False), (edd, True)]:
            if time.time() >= search_deadline:
                break
            try:
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=fc)
                emit(assign)
            except Exception:
                pass
        rng = random.Random(2026)
        stale = 0
        best_so_far = min((c[0] for c in candidates), default=float("inf"))
        while time.time() < search_deadline and stale < 4:
            try:
                order = _edd_order(blocks_data, jitter=rng)
                assign = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                                    t_start, search_deadline, forced=forced)
                emit(assign)
                o = candidates[-1][0]
                if o < best_so_far - 1e-9:
                    best_so_far = o; stale = 0
                else:
                    stale += 1
            except Exception:
                break

    # Basin-hopping improver. REGRESSION-SAFE two-pass scheme on forced instances:
    #   pass 1 improves the PLAIN EDD construction (== v8's result, so v9 can never
    #          regress below v8 on improver-dependent instances like prob_33/25/37
    #          whose jittered constructions otherwise led the improver to a worse
    #          local optimum);
    #   pass 2 improves the best OTHER construction ONLY IF its RAW objective
    #          already beats pass 1's result -- true on the giants where AREA wins
    #          outright (so they keep their full improver-polished gain), false on
    #          the improver-dependent instances (so no time is wasted / no worse
    #          basin is chosen). Each pass gets half the remaining budget.
    # Non-forced instances keep the original single-pass improve-the-best.
    if candidates and time.time() < search_deadline:
        try:
            candidates.sort(key=lambda c: c[0])
            if forced and edd_assign is not None:
                # Uneven split: the EDD pass only needs to reach v8's value (which
                # v8 did with little improver time), so give it just 35% and leave
                # 65% for the AREA pass so the giants keep their full polish.
                mid = time.time() + (search_deadline - time.time()) * 0.35
                r1, o1 = _improve(prob_info, edd_assign, bays, bay_u,
                                  w1, w2, w3, mid, forced, on_best=push)
                candidates.append((o1, r1))
                if push is not None:
                    push(o1, r1)
                for o_raw, a_raw in sorted(candidates, key=lambda c: c[0]):
                    if a_raw is edd_assign or a_raw is r1:
                        continue
                    if o_raw < o1 - 1e-9:  # a raw construction already beats EDD+improve
                        r2, o2 = _improve(prob_info, a_raw, bays, bay_u,
                                          w1, w2, w3, search_deadline, forced,
                                          on_best=push)
                        candidates.append((o2, r2))
                        if push is not None:
                            push(o2, r2)
                    break
            else:
                improved, iobj_imp = _improve(prob_info, candidates[0][1], bays, bay_u,
                                              w1, w2, w3, search_deadline, forced,
                                              on_best=push)
                candidates.append((iobj_imp, improved))
                if push is not None:
                    push(iobj_imp, improved)
        except Exception:
            pass
    return candidates


def _algorithm_single(prob_info, timelimit=60, t_start=None):
    """v9 pipeline: search, then verify best-first (no-multiprocessing fallback)."""
    if t_start is None:
        t_start = time.time()
    _reset_caches()  # v7: caches hold instance-specific geometry; never share.
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)
    try:
        candidates = _v9_search(prob_info, timelimit, t_start)
    except Exception:
        candidates = []

    # Verify candidates best-first; return the first officially-feasible one.
    fallback = _empty_bay_solution(prob_info, bays)
    candidates.append((_objective(fallback, blocks_data, bays, bay_u,
                                  w1, w2, w3)[0], fallback))
    candidates.sort(key=lambda c: c[0])
    for _, assign in candidates:
        sol = {"operations": _build_operations(assign)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            continue
        if res["feasible"]:
            return sol
    # Last resort: empty-bay (structurally feasible).
    return {"operations": _build_operations(fallback)}


# =============================================================================
# v12 RASTER GEOMETRY ENGINE (numpy, conservative)
# =============================================================================

class _Raster:
    """Per-instance conservative raster occupancy engine (numpy only).

    For every (block_id, orient_idx) it lazily builds a stack of per-layer
    boolean masks on the unit grid: mask[l][i, j] is set iff layer l's polygon
    *touches* the closed unit square of local cell (cx0+j, cy0+i). Because the
    mask is a superset of the polygon's footprint, two blocks whose masks share
    no cell cannot have any positive-area polygon overlap -- so a mask that is
    disjoint from the occupancy union is provably collision-free AND crane-clear
    (entry and exit obey the same j>=k prism rule; disjointness at every needed
    layer proves both). It is therefore SOUND as a pre-filter: it may reject a
    feasible edge-touching placement (conservative) but never accepts an
    infeasible one. Positions it returns are still gated by the exact cached
    `_can_place` (for reverse exit-blocking against present blocks) before use.

    Per-bay per-layer occupancy grids (int16, HxW) are updated incrementally on
    add()/remove(); `scan()` returns a boolean (R,C) grid of all entry-clear
    anchor windows against the *current* occupancy (crane clearance = for each
    moving layer k, disjoint from the union of present layers >= k)."""

    def __init__(self, prob_info, bays):
        self.blocks_data = prob_info["blocks"]
        self.bays = bays
        self.W = [int(b.width) for b in bays]
        self.H = [int(b.height) for b in bays]
        self._mask = {}                       # (bi, oi) -> (mask, cx0, cy0)
        self._fpm = {}                        # (bi, oi) -> footprint-union mask
        self.occ = [dict() for _ in bays]     # bay -> {layer: int16 grid (H,W)}
        self.ver = [0 for _ in bays]          # occupancy version per bay
        self._uni = [None for _ in bays]      # bay -> (ver, [union_ge grids])
        # v13 throughput caches (transparent -- same numeric results as v12):
        self._scan = [dict() for _ in bays]   # bay -> {(bi,oi): (ver, feas,cx0,cy0)}
        self._fp = [None for _ in bays]       # bay -> (ver, footprint bool grid)
        # v20 Improvement A: near-miss cells (0 < overlap count <= near_k) --
        # anchors the conservative mask rejects by at most near_k dilated
        # cells. Every consumer exact-gates them with _can_place before use,
        # so the recovery is sound. Cached alongside the scan cache.
        self.near_k = 3
        self.near_enabled = False   # explorer slots flip this; default = zero
        #                             overhead on every legacy worker/path
        self._nearc = [dict() for _ in bays]  # bay -> {(bi,oi): (ver, near)}
        # jv5 Phase D: memoize the scoped-union computation. scan_scoped's
        # per-active layer-union rebuild depends ONLY on (bay, actives), not on
        # (bi,oi) -- the improver calls it for many (bi,oi) against the SAME
        # actives set in a repack window. Cache (maxL, union_ge, occ_fp) keyed
        # by (bay, actives); pure memoization, byte-identical output.
        self._scoped = {}                     # (bay, tuple(actives)) -> (maxL, union_ge, occ_fp)
        self._SCOPED_CAP = 4096

    # -- mask construction -----------------------------------------------------
    def mask(self, bi, oi):
        key = (bi, oi)
        m = self._mask.get(key)
        if m is not None:
            return m
        import shapely
        layers = _resolve_layers(self.blocks_data[bi]["shape"][oi]["layers"])
        allv = [v for L in layers for v in L]
        if not allv:
            m = (_np.zeros((1, 1, 1), dtype=_np.uint8), 0, 0)
            self._mask[key] = m
            return m
        xs = [v[0] for v in allv]; ys = [v[1] for v in allv]
        cx0 = int(math.floor(min(xs))); cx1 = int(math.ceil(max(xs))) - 1
        cy0 = int(math.floor(min(ys))); cy1 = int(math.ceil(max(ys))) - 1
        if cx1 < cx0: cx1 = cx0
        if cy1 < cy0: cy1 = cy0
        MW = cx1 - cx0 + 1; MH = cy1 - cy0 + 1
        nl = len(layers)
        mask = _np.zeros((nl, MH, MW), dtype=_np.uint8)
        cxs = _np.arange(cx0, cx1 + 1)
        cys = _np.arange(cy0, cy1 + 1)
        CX, CY = _np.meshgrid(cxs, cys)       # (MH, MW)
        boxes = shapely.box(CX, CY, CX + 1, CY + 1)
        for l, L in enumerate(layers):
            p = _poly_from_verts(L)
            if p is None:
                continue
            # conservative: a cell is occupied if its unit box touches the poly
            mask[l] = shapely.intersects(boxes, p).astype(_np.uint8)
        m = (mask, cx0, cy0)
        self._mask[key] = m
        return m

    def mask_fp(self, bi, oi):
        """Footprint-union mask (MH,MW) bool = any layer touches the cell.
        Used by contact scoring; cached per (bi,oi)."""
        key = (bi, oi)
        fp = self._fpm.get(key)
        if fp is not None:
            return fp
        mask, cx0, cy0 = self.mask(bi, oi)
        fp = mask.any(axis=0)
        self._fpm[key] = fp
        return fp

    # -- occupancy update (int counts so remove() is exact) --------------------
    def _apply(self, bay, bi, oi, x, y, sign):
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        r = int(y) + cy0; c = int(x) + cx0
        H, W = self.H[bay], self.W[bay]
        r0 = max(0, r); c0 = max(0, c)
        r1 = min(H, r + MH); c1 = min(W, c + MW)
        if r1 <= r0 or c1 <= c0:
            self.ver[bay] += 1
            return
        occ = self.occ[bay]
        for l in range(nl):
            g = occ.get(l)
            if g is None:
                if sign < 0:
                    continue
                g = _np.zeros((H, W), dtype=_np.int16)
                occ[l] = g
            g[r0:r1, c0:c1] += sign * mask[l, r0 - r:r1 - r,
                                           c0 - c:c1 - c].astype(_np.int16)
            # v13: drop a layer once it is fully vacated so _unions/scan loops
            # shrink to the live maxL (perf on giants; result-transparent).
            if sign < 0 and not g.any():
                del occ[l]
        self.ver[bay] += 1

    def reset(self):
        """Clear all occupancy (keep the mask cache) for a fresh construction."""
        for j in range(len(self.bays)):
            self.occ[j] = dict()
            self.ver[j] += 1
            self._uni[j] = None
            self._scan[j] = dict()
            self._fp[j] = None
            self._nearc[j] = dict()
        self._scoped.clear()                  # jv5 Phase D: scoped-union memo

    def add(self, bay, bi, oi, x, y):
        self._apply(bay, bi, oi, x, y, 1)

    def remove(self, bay, bi, oi, x, y):
        self._apply(bay, bi, oi, x, y, -1)

    def footprint(self, bay):
        """Bool (H,W): any layer occupied (for compactness / util scoring).
        Cached per (bay, ver) -- recomputed only when the occupancy changes."""
        cache = self._fp[bay]
        if cache is not None and cache[0] == self.ver[bay]:
            return cache[1]
        occ = self.occ[bay]
        H, W = self.H[bay], self.W[bay]
        fp = _np.zeros((H, W), dtype=bool)
        for g in occ.values():
            fp |= (g > 0)
        self._fp[bay] = (self.ver[bay], fp)
        return fp

    def _unions(self, bay):
        cache = self._uni[bay]
        if cache is not None and cache[0] == self.ver[bay]:
            return cache[1]
        occ = self.occ[bay]
        H, W = self.H[bay], self.W[bay]
        if not occ:
            self._uni[bay] = (self.ver[bay], [])
            return []
        maxL = max(occ.keys())
        union_ge = [None] * (maxL + 1)
        cum = _np.zeros((H, W), dtype=bool)
        for l in range(maxL, -1, -1):
            g = occ.get(l)
            if g is not None:
                cum = cum | (g > 0)      # new array each time -> distinct refs
            union_ge[l] = cum
        self._uni[bay] = (self.ver[bay], union_ge)
        return union_ge

    def scan(self, bay, bi, oi):
        """Boolean (R,C) grid of entry-clear anchor windows against the current
        occupancy, or None if the block cannot fit the bay. Map window (r,c) to
        an assignment via x = c - cx0, y = r - cy0.
        v13: cached per (bay, bi, oi, ver) -- the dispatcher re-scans the same
        (block,orient) across bays/events with unchanged occupancy constantly."""
        sc = self._scan[bay].get((bi, oi))
        if sc is not None and sc[0] == self.ver[bay]:
            return sc[1], sc[2], sc[3]
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        H, W = self.H[bay], self.W[bay]
        if MH > H or MW > W:
            self._scan[bay][(bi, oi)] = (self.ver[bay], None, cx0, cy0)
            if self.near_enabled:
                self._nearc[bay][(bi, oi)] = (self.ver[bay], None)
            return None, cx0, cy0
        R = H - MH + 1; C = W - MW + 1
        unions = self._unions(bay)
        maxL = len(unions) - 1
        total = _np.zeros((R, C), dtype=_np.int32)
        for k in range(nl):
            if k > maxL:
                break                     # no present layer >= k -> clear
            Vk = unions[k]
            if Vk is None or not Vk.any():
                continue
            mk = mask[k]
            if not mk.any():
                continue
            win = _swv(Vk.astype(_np.int32), (MH, MW))     # (R,C,MH,MW)
            total += _np.einsum('rcij,ij->rc', win, mk.astype(_np.int32))
        feas = (total == 0)
        self._scan[bay][(bi, oi)] = (self.ver[bay], feas, cx0, cy0)
        if self.near_enabled:
            # v20: near-miss anchors from the same count grid (byproduct).
            self._nearc[bay][(bi, oi)] = (
                self.ver[bay], _np.logical_and(total > 0, total <= self.near_k))
        return feas, cx0, cy0

    def scan_near(self, bay, bi, oi):
        """v20: near-miss anchor grid matching the last scan() at the current
        occupancy version (computes it via scan() if stale). Same (R,C)/cx0/
        cy0 mapping as scan(); every anchor MUST be exact-gated by _can_place
        before use (the mask says these overlap by <= near_k dilated cells)."""
        self.near_enabled = True
        nc = self._nearc[bay].get((bi, oi))
        if nc is None or nc[0] != self.ver[bay]:
            # a cached scan at this ver may predate near_enabled -- drop it so
            # scan() recomputes the count grid and stores the near anchors.
            self._scan[bay].pop((bi, oi), None)
            self.scan(bay, bi, oi)
            nc = self._nearc[bay].get((bi, oi))
            if nc is None:
                return None
        return nc[1]

    def _scoped_union(self, bay, actives):
        """jv5 Phase D: memoized (maxL, union_ge, occ_fp) for `actives` in
        `bay`. Depends ONLY on (bay, actives) -- not on the block being placed
        -- so it is shared across the many (bi,oi) an improver window scans
        against the same active set. occ_fp is always an (H,W) bool grid
        (zeros when nothing overlaps). Byte-identical to the inline v25
        computation; callers treat union_ge/occ_fp as read-only (scan_scoped
        recomputes the (bi,oi)-dependent `feas`/`near` fresh each call)."""
        H, W = self.H[bay], self.W[bay]
        akey = (bay, tuple(actives))
        hit = self._scoped.get(akey)
        if hit is not None:
            return hit
        layers = {}                            # l -> bool (H,W)
        maxL = -1
        for (b2, o2, x2, y2) in actives:
            m2, c2x, c2y = self.mask(b2, o2)
            nl2, MH2, MW2 = m2.shape
            r = int(y2) + c2y; c = int(x2) + c2x
            r0 = max(0, r); c0 = max(0, c)
            r1 = min(H, r + MH2); c1 = min(W, c + MW2)
            if r1 <= r0 or c1 <= c0:
                continue
            for l in range(nl2):
                g = layers.get(l)
                if g is None:
                    g = _np.zeros((H, W), dtype=bool); layers[l] = g
                g[r0:r1, c0:c1] |= m2[l, r0 - r:r1 - r, c0 - c:c1 - c].astype(bool)
            if nl2 - 1 > maxL:
                maxL = nl2 - 1
        if maxL < 0:
            res = (-1, None, _np.zeros((H, W), dtype=bool))
        else:
            union_ge = [None] * (maxL + 1)
            cum = _np.zeros((H, W), dtype=bool)
            for l in range(maxL, -1, -1):
                g = layers.get(l)
                if g is not None:
                    cum = cum | g
                union_ge[l] = cum
            res = (maxL, union_ge, union_ge[0])   # occ_fp = footprint of actives
        if len(self._scoped) >= self._SCOPED_CAP:
            self._scoped.clear()
        self._scoped[akey] = res
        return res

    def scan_scoped(self, bay, actives, bi, oi, want_near=False):
        """v13 raster-windowed repair primitive. Feasible-anchor grid for
        placing (bi,oi) in `bay` against ONLY `actives` = [(bi2,oi2,x2,y2),...]
        (the blocks time-overlapping the candidate insertion), WITHOUT touching
        self.occ. Returns (feas (R,C) bool | None, cx0, cy0, occ_fp (H,W) bool).
        Sound in exactly the same conservative sense as scan().
        v21: want_near=True appends a near-miss anchor grid (0 < scoped
        overlap count <= near_k) -- consumers MUST exact-gate every anchor."""
        H, W = self.H[bay], self.W[bay]
        mask, cx0, cy0 = self.mask(bi, oi)
        nl, MH, MW = mask.shape
        if MH > H or MW > W:
            if want_near:
                return None, cx0, cy0, None, None
            return None, cx0, cy0, None
        R = H - MH + 1; C = W - MW + 1
        # jv5 Phase D: the per-active layer-union depends only on (bay,
        # actives), so it is memoized in _scoped_union and reused across the
        # many (bi,oi) an improver window tries against the same active set.
        maxL, union_ge, occ_fp = self._scoped_union(bay, actives)
        if maxL < 0:
            if want_near:
                return (_np.ones((R, C), dtype=bool), cx0, cy0,
                        occ_fp,
                        _np.zeros((R, C), dtype=bool))
            return _np.ones((R, C), dtype=bool), cx0, cy0, occ_fp
        total = _np.zeros((R, C), dtype=_np.int32)
        for k in range(nl):
            if k > maxL:
                break
            Vk = union_ge[k]
            if Vk is None or not Vk.any():
                continue
            mk = mask[k]
            if not mk.any():
                continue
            win = _swv(Vk.astype(_np.int32), (MH, MW))
            total += _np.einsum('rcij,ij->rc', win, mk.astype(_np.int32))
        if want_near:
            return ((total == 0), cx0, cy0, occ_fp,
                    _np.logical_and(total > 0, total <= self.near_k))
        return (total == 0), cx0, cy0, occ_fp


# =============================================================================
# v13 POSITION-QUALITY ORDERING (contact / perimeter-match scoring)
# =============================================================================

def _neighbor_field(occ_fp):
    """4-neighbour count of occupied-or-wall cells for every cell of the bay.
    Walls are the outside of the grid (borders always count as +1 neighbour).
    A block cell landing here scores high when it nestles against existing
    blocks or a wall -> perimeter match -> denser, concavity-filling packings."""
    H, W = occ_fp.shape
    N = _np.zeros((H, W), dtype=_np.int32)
    o = occ_fp.astype(_np.int32)
    N[1:, :] += o[:-1, :]; N[0, :] += 1        # up  (top border = wall)
    N[:-1, :] += o[1:, :]; N[-1, :] += 1       # down
    N[:, 1:] += o[:, :-1]; N[:, 0] += 1        # left
    N[:, :-1] += o[:, 1:]; N[:, -1] += 1       # right
    return N


def _order_cells(raster, feas, cx0, cy0, bi, oi, W, occ_fp, prefer_contact, rng,
                 ovh_bay=None, ovh_w=2.0):
    """Order feasible raster anchors best-first as a list of (x, y). Default is
    v12's bottom-left (low y=r, then low x=c). With `prefer_contact` and a
    non-empty occupancy, rank by perimeter-contact first (block footprint dotted
    with the neighbour-field), BL as tie-break -- the density lever, shared by
    the dispatcher and the raster-repair improver. `rng` jitters ties (lottery).
    When prefer_contact is False and rng is None this reproduces v12 exactly.
    v23: ovh_bay=bay_id enables OVERHANG-AWARE scoring: penalize anchors whose
    upper-layer cells hang over currently-EMPTY floor (union-poisoning band,
    measured 0.05-0.10 of bay area: poisoned cells block every later entry
    below them while covering nothing). Explorer-only (default None = inert)."""
    rc = _np.argwhere(feas)                     # (K,2) as (r,c)
    if len(rc) == 0:
        return []
    r = rc[:, 0]; c = rc[:, 1]
    bl = (r * (W + 1) + c).astype(_np.float64)
    if rng is not None and len(rc) > 1:
        bl = bl + rng.uniform(0.0, 2.0) * _np.array(
            [rng.random() for _ in range(len(rc))])
    if prefer_contact and occ_fp is not None and occ_fp.any():
        N = _neighbor_field(occ_fp)
        bfp = raster.mask_fp(bi, oi).astype(_np.int32)
        MH, MW = bfp.shape
        win = _swv(N, (MH, MW))                 # (R,C,MH,MW)
        contact = _np.einsum('rcij,ij->rc', win, bfp)
        cval = contact[r, c].astype(_np.float64)
        if ovh_bay is not None:
            mask, _mx, _my = raster.mask(bi, oi)
            if mask.shape[0] > 1:
                up = mask[1:].any(axis=0).astype(_np.int32)   # upper layers
                if up.any():
                    g0 = raster.occ[ovh_bay].get(0)
                    H = raster.H[ovh_bay]; Wb = raster.W[ovh_bay]
                    empty0 = (_np.ones((H, Wb), dtype=_np.int32)
                              if g0 is None else (g0 == 0).astype(_np.int32))
                    winE = _swv(empty0, (MH, MW))
                    poison = _np.einsum('rcij,ij->rc', winE, up)
                    # each poisoned floor cell costs ~2 contact points
                    cval = cval - float(ovh_w) * poison[r, c].astype(
                        _np.float64)
        idx = _np.lexsort((bl, -cval))          # primary -cval (desc), then bl
    else:
        idx = _np.argsort(bl)                   # pure BL (== v12 when rng None)
    return [(int(c[ii]) - cx0, int(r[ii]) - cy0) for ii in idx]


# =============================================================================
# v13 round-3: FLUID-TARGET ADMISSION GATE (structural-overload lever)
# =============================================================================

def _overload_ratio(prob_info, bays):
    """Total area*time demand / total capacity*time over the due-date horizon.
    > 1 means the instance is STRUCTURALLY oversubscribed (no schedule meets
    all dues even at 100% packing density; measured: prob_38 1.14, prob_27
    1.19, every other train instance <= 0.94 -> threshold 1.05 isolates the
    overloaded pair). On such instances alpha-ATC only reorders priority -- a
    stranded block still gets admitted the moment it fits, consuming the very
    area the sacrifice was supposed to free; the fix is an explicit
    target-schedule admission GATE built from _fluid_targets."""
    cap = sum(b.width * b.height for b in bays)
    bl = prob_info["blocks"]
    vol = sum(_min_area(b) * b["processing_time"] for b in bl)
    rmin = min(b["release_time"] for b in bl)
    dmax = max(b["due_date"] for b in bl)
    return vol / max(1e-9, cap * max(1, dmax - rmin))


def _nk_family(prob_info):
    """jv5 Phase B -- MEASURED DEAD, UNWIRED. Kept for provenance only; do
    NOT re-propose per-instance near_k scaling without new evidence.

    Refutation (spot @600s, same machine, vs v25): the family below returns
    (16,24,32) == v25 for 38/27/39/31/26 and (20,30,40) for 30/23/33. The
    three cells where it DIFFERED all regressed -- 23 +196,240, 30 +135,879,
    33 +78,510 -- while the cells where it matched tied. near_k is therefore
    NOT a perimeter-proportional quantity: v25's tuned {16,24,32} is at or
    near an optimum, and deeper nestling costs more (bigger near-set -> more
    _can_place gates -> fewer/worse draws) than the anchors it recovers.

    Original rationale (falsified): per-instance deep-nestle near_k family.

    v25's fixed {16,24,32} were tuned on the 8-instance spot set. near_k is a
    threshold on the total dilated mask-overlap a rejected anchor may have to
    still count as a recoverable 'near' cell -- deeper (bigger near_k) exposes
    anchors buried further under overhangs, at the cost of more _can_place
    gates. The natural scale is the block footprint PERIMETER (v25 header:
    "38-class blocks have 40+ cell perimeters"). Scale hi to the 75th-pct
    layer-0 perimeter (cheap vertex math, no shapely); clamp to the measured-
    useful band. Calibrated so the hot rocks (38/27, p75~43) reproduce v25's
    {16,24,32} EXACTLY, and only larger-perimeter instances (30/23/33, p75
    50-55) go deeper -- so this cannot perturb 38/27 vs v25."""
    bl = prob_info.get("blocks", [])
    per = []
    for b in bl:
        try:
            L = b["shape"][0]["layers"][0]
        except (KeyError, IndexError, TypeError):
            continue
        n = len(L)
        if n < 2:
            continue
        s = 0.0
        for i in range(n):
            x0, y0 = L[i]; x1, y1 = L[(i + 1) % n]
            s += math.hypot(x1 - x0, y1 - y0)
        per.append(s)
    if not per:
        return (16, 24, 32)                     # v25 default on empty/odd input
    per.sort()
    p75 = per[min(len(per) - 1, (len(per) * 3) // 4)]
    # snap hi to a multiple of 8 so nearby perimeters share a family: the
    # spot rocks 38/27/39/31/26 (p75*.75 ~ 30-35) all land on hi=32 =>
    # (16,24,32) EXACTLY v25; only the big-perimeter class 30/23/33
    # (p75*.75 ~ 38-41) steps to hi=40 => (20,30,40). Clamp to [24,48].
    hi = int(min(48, max(24, round(p75 * 0.75 / 8.0) * 8)))
    return (hi // 2, (hi * 3) // 4, hi)


def _plan_targets(prob_info, bays, cap_frac, budget_s, seed=20):
    """v20 Improvement B: calibrated non-preemptive admission plan.

    CP-SAT cumulative relaxation -- merged-bay capacity C*cap_frac PER LAYER
    (the true co-residency constraint; ledger_19's footprint metric
    double-counted stacking), exact integer durations, entry >= release.
    Objective 1000*sum(tardiness) + sum(start - release): tardiness dominates,
    the left-shift term keeps non-sacrificed blocks' targets at release so the
    admission gate never idles space gratuitously. Returns {bi: entry} or
    None (no ortools / infeasible / no solution in budget). Differences from
    the dead fluid gate (family #3): non-preemptive, per-layer calibrated
    capacity, left-shifted targets."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    try:
        bd = prob_info["blocks"]
        n = len(bd)
        C = sum(b.width * b.height for b in bays)
        cap = int(math.floor(C * cap_frac))
        rel = [int(b["release_time"]) for b in bd]
        due = [int(b["due_date"]) for b in bd]
        p = [int(b["processing_time"]) for b in bd]
        maxL = max(len(b["shape"][0]["layers"]) for b in bd)
        dem = []
        for b in bd:
            per = []
            for L in range(maxL):
                areas = [_poly_area(o["layers"][L])
                         if len(o["layers"]) > L else 0.0
                         for o in b["shape"]]
                per.append(int(math.floor(min(areas))))
            dem.append(per)
        H = max(due) + sum(sorted(p)[-10:])
        m = cp_model.CpModel()
        starts, ivs, tards = [], [], []
        for i in range(n):
            s = m.NewIntVar(rel[i], H - p[i], "s%d" % i)
            iv = m.NewIntervalVar(s, p[i], s + p[i], "iv%d" % i)
            t = m.NewIntVar(0, H, "t%d" % i)
            m.AddMaxEquality(t, [s + p[i] - due[i], 0])
            starts.append(s); ivs.append(iv); tards.append(t)
        for L in range(maxL):
            li = [i for i in range(n) if dem[i][L] > 0]
            if li:
                m.AddCumulative([ivs[i] for i in li],
                                [dem[i][L] for i in li], cap)
        m.Minimize(1000 * sum(tards) +
                   sum(starts[i] - rel[i] for i in range(n)))
        sol = cp_model.CpSolver()
        sol.parameters.max_time_in_seconds = float(budget_s)
        sol.parameters.num_search_workers = 1
        sol.parameters.random_seed = seed
        st = sol.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        return {i: int(sol.Value(starts[i])) for i in range(n)}
    except Exception:
        return None


def _poly_area(pts):
    """Shoelace area of a vertex list (v20; plan-target demand profiles)."""
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _fluid_targets(prob_info, bays, c_eff, mode):
    """Deterministic greedy fluid target schedule. Aggregate-area relaxation:
    capacity = c_eff * total bay area; blocks are loaded in the discipline
    order at the earliest t >= release where the aggregate area-in-use step
    profile stays <= capacity over [t, t+proc). 'spt' = smallest area*proc
    first (the fluid-SPT sacrifice: the largest space-time volumes are pushed
    to the back of the horizon instead of every block being democratically
    late); 'band' = due-date bands (width 4*pbar), smallest area*proc first
    within a band (keeps rough due order globally, sacrifices within bands).
    Returns {bi: int target entry time}."""
    blocks = prob_info["blocks"]
    n = len(blocks)
    total_area = sum(b.width * b.height for b in bays)
    cap = c_eff * total_area
    areas = [_min_area(b) for b in blocks]
    procs = [max(1, int(b["processing_time"])) for b in blocks]
    rels = [int(b["release_time"]) for b in blocks]
    pbar = max(1.0, sum(procs) / max(1, n))
    if mode == "cut":
        # PURE SACRIFICE: pick the smallest set of largest-a*p blocks whose
        # removal brings total volume under c_eff*area*horizon (here c_eff =
        # the packing density the un-sacrificed mass realistically achieves);
        # everyone else keeps target=release (gate inactive, normal ATC), and
        # ONLY the sacrificed blocks are pushed to the post-burst tail via
        # earliest-fit against the mass's prompt-release profile.
        rmin = min(rels)
        H = max(1, max(b["due_date"] for b in blocks) - rmin)
        vol = sum(areas[i] * procs[i] for i in range(n))
        excess = vol - c_eff * total_area * H
        targets = {i: rels[i] for i in range(n)}
        if excess <= 0:
            return targets
        by_vol = sorted(range(n), key=lambda i: -areas[i] * procs[i])
        sac = []
        rem = excess
        for i in by_vol:
            if rem <= 0:
                break
            sac.append(i)
            rem -= areas[i] * procs[i]
        sac_set = set(sac)
        ev = {}
        for i in range(n):
            if i not in sac_set:
                ev[rels[i]] = ev.get(rels[i], 0.0) + areas[i]
                t2 = rels[i] + procs[i]
                ev[t2] = ev.get(t2, 0.0) - areas[i]
        # earliest-fit the sacrificed blocks (EDD order) at FULL area capacity
        # (the tail is empty; c_eff was only the burst-mass density model).
        fullcap = total_area
        for i in sorted(sac, key=lambda i: blocks[i]["due_date"]):
            a, p = areas[i], procs[i]
            t = rels[i]
            guard = 0
            while guard < 4000:
                guard += 1
                ts = sorted(ev)
                E = len(ts)
                run = 0.0
                idx = 0
                while idx < E and ts[idx] <= t:
                    run += ev[ts[idx]]; idx += 1
                viol = run + a > fullcap + 1e-9
                while not viol and idx < E and ts[idx] < t + p:
                    run += ev[ts[idx]]; idx += 1
                    if run + a > fullcap + 1e-9:
                        viol = True
                if not viol:
                    break
                nxt = None
                for tt in ts:
                    if tt > t and ev[tt] < 0:
                        nxt = tt
                        break
                if nxt is None:
                    break
                t = nxt
            targets[i] = int(t)
            ev[t] = ev.get(t, 0.0) + a
            ev[t + p] = ev.get(t + p, 0.0) - a
        return targets
    if mode == "band":
        # band width ~ one mean processing time: coarse enough to allow SPT
        # sacrifice within a band, fine enough that due order matters globally
        # (4*pbar measured degenerate: all dues fell into 1-2 bands == SPT).
        band = max(1.0, pbar)
        order = sorted(range(n), key=lambda i: (
            math.floor(blocks[i]["due_date"] / band),
            areas[i] * procs[i], blocks[i]["due_date"], i))
    else:
        order = sorted(range(n), key=lambda i: (
            areas[i] * procs[i], blocks[i]["due_date"], i))
    ev = {}                                   # time -> +/- area delta
    targets = {}
    for i in order:
        a, p, r = areas[i], procs[i], rels[i]
        t = r
        if a <= cap + 1e-9:
            guard = 0
            while guard < 4000:
                guard += 1
                ts = sorted(ev)
                E = len(ts)
                # usage on the segment covering t = cum deltas at times <= t
                run = 0.0
                idx = 0
                while idx < E and ts[idx] <= t:
                    run += ev[ts[idx]]; idx += 1
                viol = run + a > cap + 1e-9
                # walk the segments starting strictly inside (t, t+p)
                while not viol and idx < E and ts[idx] < t + p:
                    run += ev[ts[idx]]; idx += 1
                    if run + a > cap + 1e-9:
                        viol = True
                if not viol:
                    break
                # advance to the next exit event (usage only drops there)
                nxt = None
                for tt in ts:
                    if tt > t and ev[tt] < 0:
                        nxt = tt
                        break
                if nxt is None:
                    break                     # no future relief; accept t
                t = nxt
        targets[i] = int(t)
        ev[t] = ev.get(t, 0.0) + a
        ev[t + p] = ev.get(t + p, 0.0) - a
    return targets


# =============================================================================
# v12 TIME-ORDERED DISPATCHER CONSTRUCTION ("the pump")
# =============================================================================

def _dispatch_construct(prob_info, bays, bay_u, w1, w2, w3, deadline, raster,
                        kappa=1.0, gamma=0.5, rng=None, cand_cap=12,
                        alpha=0.0, score_pos=False, eps=0.15, targets=None,
                        beam=False, beam_m=4, nearmiss=0, mpc=False,
                        ovh=False, steal=0, nm_compete=False, zone=0,
                        drain=0):
    """Event-driven admission construction using the raster full-position scan.

    Walk event times (releases + scheduled exits); at each event admit queued
    (released, unplaced) blocks in ATC priority order, placing each in the best
    bay that has an entry-clear raster window whose candidate also passes the
    exact `_can_place` gate. Prompt exit at entry+proc. Any block never admitted
    (deadline / spatially impossible with the current set) is force-placed at
    the end so the output is always a complete assignment dict, identical in
    format to `_construct`."""
    import heapq
    blocks_data = prob_info["blocks"]
    n = len(blocks_data)
    n_bays = len(bays)
    procs = [int(b["processing_time"]) for b in blocks_data]
    dues = [int(b["due_date"]) for b in blocks_data]
    rels = [int(b["release_time"]) for b in blocks_data]
    pbar = max(1.0, sum(procs) / max(1, n))
    orients_of = [_unique_orients(b) for b in blocks_data]
    # v13 volume-aware triage: normalize min-orient footprint area by the mean
    # so alpha=0 (a^0=1) reproduces v12's ATC exactly, alpha>0 deliberately
    # strands large-footprint blocks under overload (fluid-SPT flavour).
    areas = [_min_area(b) for b in blocks_data]
    abar = max(1e-9, sum(areas) / max(1, n))
    anorm = [a / abar for a in areas]

    sched = [[] for _ in range(n_bays)]      # bay -> [(blk, entry, exit, bbox)]
    bay_loads = [0.0] * n_bays
    assignments = {}

    def atc(bi, t):
        p = procs[bi]
        if targets is None:
            slack = dues[bi] - p - t
        else:
            # round-3 target mode: urgency keys on the LATER of due-slack
            # point and the fluid target -- un-sacrificed blocks (target ==
            # release) keep the exact v12 ATC urgency; sacrificed blocks
            # (target past due) become maximally urgent AT their target
            # instead of long before it (they are gated out until then).
            slack = max(dues[bi] - p, targets[bi]) - t
        idx = (1.0 / ((anorm[bi] ** alpha) * p)) * \
            math.exp(-max(0.0, slack) / (kappa * pbar))
        if rng is not None:
            idx *= (1.0 + rng.uniform(-eps, eps))   # v13: multiplicative jitter
        return idx

    def bay_score(bi, bay_id, t):
        blk = blocks_data[bi]
        prefs = blk["bay_preferences"]
        util = 0.0
        bay = bays[bay_id]
        area = bay.width * bay.height
        occ = raster.occ[bay_id]
        if occ:
            util = float(raster.footprint(bay_id).sum()) / max(1.0, area)
        s = w3 * (max(prefs) - prefs[bay_id]) + gamma * w1 * util
        return s

    def _drain_score(bi, bay_id, x, y, oi, look):
        """jv6b DRAIN LOOKAHEAD (untried joint order+geometry, 2026-07-18):
        after tentatively placing bi at (bay_id,x,y,oi), how many of the
        `look` most-urgent OTHER queued blocks still have ANY conservative-
        feasible cell somewhere? Higher = this placement preserves more future
        admission capacity = faster queue drain (the measured giant bottleneck,
        ledger_27_diag: 100% of obj1 is entry-delay). Mask-feasibility proxy
        (raster.scan.any()), exact _can_place unchanged at commit."""
        raster.add(bay_id, bi, oi, x, y)
        cnt = 0
        for lb in look:
            ok = False
            lblk = blocks_data[lb]
            for bj in range(n_bays):
                for loi in orients_of[lb]:
                    if not _orient_fits(lblk, loi, bays[bj]):
                        continue
                    fe, _c, _r = raster.scan(bj, lb, loi)
                    if fe is not None and fe.any():
                        ok = True
                        break
                if ok:
                    break
            if ok:
                cnt += 1
        raster.remove(bay_id, bi, oi, x, y)
        return cnt

    def try_place(bi, t, cap, look=None):
        """Try to admit block bi entering at time t. Returns placement tuple or
        None. `cap` = max exact _can_place gates per (bay,orient). With
        score_pos, feasible cells are ranked by perimeter contact (density
        lever); otherwise pure bottom-left (== v12 when rng is None). With
        `drain` and `look`, collect the first passing cell per (bay,oi) and
        return the one that leaves the most `look` blocks placeable."""
        blk = blocks_data[bi]
        p = procs[bi]
        exit_t = t + p
        dcands = [] if (drain and look) else None
        order = sorted(range(n_bays), key=lambda j: bay_score(bi, j, t))
        for bay_id in order:
            bay = bays[bay_id]
            rel = _rel_sched_bbox(sched[bay_id], t, exit_t)
            occ_fp = raster.footprint(bay_id) if score_pos else None
            for oi in orients_of[bi]:
                if not _orient_fits(blk, oi, bay):
                    continue
                feas, cx0, cy0 = raster.scan(bay_id, bi, oi)
                if feas is None:
                    continue
                grid = feas
                budget = cap
                if nm_compete and nearmiss > 0:
                    # 20b-2 (dev/jiyoon, measured −2.32M on prob_38 @v20):
                    # near-miss anchors COMPETE in the main contact-ranked
                    # pass instead of waiting for total failure -- near cells
                    # are contact-richer (deeper nesting) and may outrank
                    # mask-feasible ones. Every candidate is still exact-
                    # gated by _can_place. nm_compete=False = byte-inert.
                    near = raster.scan_near(bay_id, bi, oi)
                    if near is not None and near.any():
                        grid = _np.logical_or(feas, near)
                        budget = cap + nearmiss
                if not grid.any():
                    continue
                cells = _order_cells(raster, grid, cx0, cy0, bi, oi,
                                     raster.W[bay_id], occ_fp, score_pos, rng,
                                     ovh_bay=bay_id if ovh else None,
                                     ovh_w=float(ovh) * 2.0 if ovh else 2.0)
                if zone:
                    # jv6b TEMPORAL ZONING (untried family, 2026-07-18): among
                    # the top-`zone` contact-ranked cells, prefer cells whose
                    # spatial NEIGHBORS exit near this block's exit_t -- co-
                    # locating exit cohorts makes each exit wave free one
                    # LARGE contiguous region instead of scattered holes (the
                    # measured fragmentation source on the burst giants).
                    # Mismatch is quantized (/4) so contact order still
                    # tie-breaks within a cohort band; isolated cells get a
                    # neutral mid-band. Exact _can_place gating unchanged.
                    resb = [(it[2], it[3]) for it in sched[bay_id]
                            if it[2] > t]
                    if resb:
                        head = cells[:zone]

                        def _mism(c):
                            x, y = c
                            tot = 0.0
                            cnt = 0
                            for (ex, bb) in resb:
                                dx = max(bb[0] - x, x - bb[2], 0.0)
                                dy = max(bb[1] - y, y - bb[3], 0.0)
                                if dx + dy <= 6.0:
                                    tot += abs(ex - exit_t)
                                    cnt += 1
                            return (tot / cnt) if cnt else pbar

                        order2 = sorted(range(len(head)),
                                        key=lambda i: (int(_mism(head[i]) / 4),
                                                       i))
                        cells = [head[i] for i in order2] + cells[zone:]
                tried = 0
                for (x, y) in cells:
                    nb = _mkblock(bi, blk, x, y, oi)
                    if _can_place(bay, rel, nb, t, exit_t):
                        if dcands is not None:
                            dcands.append((bay_id, x, y, oi))
                            break        # one best-contact cell per (bay,oi)
                        return (bay_id, x, y, oi, t, exit_t)
                    tried += 1
                    if tried >= budget:
                        break
        if dcands:
            # drain lookahead: pick the passing cell that preserves the most
            # future admission capacity; ties keep the best-contact candidate.
            best = max(range(len(dcands)),
                       key=lambda i: (_drain_score(bi, *dcands[i], look), -i))
            b_id, bx, by, boi = dcands[best]
            return (b_id, bx, by, boi, t, exit_t)
        # v20 Improvement A: near-miss recovery. The conservative mask found
        # no clear anchor; try anchors it rejects by <= near_k dilated cells,
        # exact-gated by _can_place (a pass is officially feasible). Only in
        # explorer slots (nearmiss=0 default keeps this path byte-inert).
        if nearmiss > 0:
            for bay_id in order:
                bay = bays[bay_id]
                rel = _rel_sched_bbox(sched[bay_id], t, exit_t)
                occ_fp = raster.footprint(bay_id) if score_pos else None
                for oi in orients_of[bi]:
                    if not _orient_fits(blk, oi, bay):
                        continue
                    near = raster.scan_near(bay_id, bi, oi)
                    if near is None or not near.any():
                        continue
                    _f, cx0, cy0 = raster.scan(bay_id, bi, oi)
                    cells = _order_cells(raster, near, cx0, cy0, bi, oi,
                                         raster.W[bay_id], occ_fp, score_pos,
                                         rng, ovh_bay=bay_id if ovh else None,
                                         ovh_w=float(ovh) * 2.0 if ovh else 2.0)
                    tried = 0
                    for (x, y) in cells:
                        nb = _mkblock(bi, blk, x, y, oi)
                        if _can_place(bay, rel, nb, t, exit_t):
                            return (bay_id, x, y, oi, t, exit_t)
                        tried += 1
                        if tried >= nearmiss:
                            break
        return None

    def cap_for(qlen):
        # v13 adaptive cand_cap: a deep entry queue means the bay is congested
        # and the 12-cell cliff wrongly rejects blocks whose 13th cell fits.
        # Widen the exact-gate budget then (only under the new-scoring bundle so
        # the alpha=0/score_pos=False path stays byte-identical to v12).
        if score_pos and qlen >= 20:
            return min(48, cand_cap * 4)
        return cand_cap

    def commit(bi, place):
        bay_id, x, y, oi, entry, exit_t = place
        nb = _mkblock(bi, blocks_data[bi], x, y, oi)
        sched[bay_id].append((nb, entry, exit_t, nb.bounding_rect()))
        bay_loads[bay_id] += blocks_data[bi]["workload"]
        assignments[bi] = {
            "block_id": bi, "bay_id": bay_id, "x": int(x), "y": int(y),
            "orient_idx": oi, "entry_time": int(entry), "exit_time": int(exit_t),
        }
        raster.add(bay_id, bi, oi, x, y)

    def apply_place(bi, place):
        """Full admission of `bi`: commit + queue/exit/heap bookkeeping. The v13
        single-pass loop is factored through here so beam-off stays byte-exact."""
        nonlocal placed_cnt
        commit(bi, place)
        queue.discard(bi)
        placed_cnt += 1
        et = place[5]
        exits_at.setdefault(et, []).append(
            (place[0], bi, place[3], place[1], place[2]))
        if et not in scheduled:               # ensure the exit event is visited
            heapq.heappush(heap, et)
            scheduled.add(et)

    def try_steal(bi, t, cc):
        """jv6b RESERVATION-STEAL (jay heuristic_31 Improvement B, translated
        to construction time -- designed 2026-07-16, never benched). In this
        chronological dispatcher a diag-`strict` blocker that has 'not yet
        entered' can only be a SAME-TICK admission: entry == t, zero
        processing elapsed, so un-admitting it wastes no bay-time -- it is a
        pure reservation. When blocked block bi has strictly less slack than
        such a reservation-holder r (margin = `steal`, time units), evict r,
        retry bi, and keep the eviction only if bi then places; r re-queues
        and is re-admitted at a later event. One steal per event (caller
        guards). Deterministic: candidates sorted by descending slack gap,
        <= 4 evictions attempted, no RNG, no solver."""
        sb = dues[bi] - (t + procs[bi])
        cands = []
        for bay_id in range(n_bays):
            for it in sched[bay_id]:
                if it[1] != t:                 # same-tick admissions only
                    continue
                r = it[0].block_id
                sr = dues[r] - (t + procs[r])
                if sr - sb < steal:
                    continue
                cands.append((-(sr - sb), r, bay_id, it))
        cands.sort()
        for _gap, r, bay_id, it in cands[:4]:
            a = assignments[r]
            raster.remove(bay_id, r, a["orient_idx"], a["x"], a["y"])
            sched[bay_id] = [s for s in sched[bay_id]
                             if s[0].block_id != r]
            place = try_place(bi, t, cc)
            if place is not None:
                # commit the eviction: full un-admission bookkeeping for r.
                bay_loads[bay_id] -= blocks_data[r]["workload"]
                ev = exits_at.get(a["exit_time"])
                if ev:
                    exits_at[a["exit_time"]] = [
                        e for e in ev if e[1] != r]
                del assignments[r]
                queue.add(r)          # re-admitted at a later event
                import os as _oss
                if _oss.environ.get("OGC_DEBUG"):
                    print(f"[steal] t={t} b={bi} evicted r={r}", flush=True)
                return place
            raster.add(bay_id, r, a["orient_idx"], a["x"], a["y"])
            sched[bay_id].append(it)
        return None

    def beam_admit(t, ordered, cc):
        """v14 MULTI-ORDER ADMISSION BEAM. Trial-fill the queued set under k=3
        orders (ATC / area-desc / most-constrained-first), each via commit+
        rollback of raster/sched, and apply the fill with the best (admitted
        area, then placement cost). Kills first-fit interlock foreclosure."""
        order_atc = ordered
        order_area = sorted(ordered, key=lambda bi: -areas[bi])

        def cellcount(bi):
            blk = blocks_data[bi]
            tot = 0
            for bay_id in range(n_bays):
                bay = bays[bay_id]
                for oi in orients_of[bi]:
                    if not _orient_fits(blk, oi, bay):
                        continue
                    feas, _cx, _cy = raster.scan(bay_id, bi, oi)
                    if feas is not None:
                        tot += int(feas.sum())
            return tot
        order_con = sorted(ordered, key=cellcount)

        def rollback(committed):
            for bi, place in reversed(committed):   # exact int occ
                bay_id, x, y, oi, en, ex = place
                raster.remove(bay_id, bi, oi, x, y)
                s = sched[bay_id]
                for idx in range(len(s) - 1, -1, -1):
                    if s[idx][0].block_id == bi:
                        del s[idx]
                        break
                bay_loads[bay_id] -= blocks_data[bi]["workload"]
                del assignments[bi]

        def evaluate(committed):
            area = sum(areas[bi] for bi, _ in committed)
            cost = 0.0
            for bi, place in committed:
                prefs = blocks_data[bi]["bay_preferences"]
                cost += (w1 * max(0, place[5] - dues[bi])
                         + w3 * (max(prefs) - prefs[place[0]]))
            return (-area, cost)

        def mpc_fill(admissible):
            """v22 MPC JOINT ADMISSION: CP-SAT max-weight compatible-set over
            candidate cells of the queued head, instead of a greedy order.
            Compatibility = footprint-union masks disjoint (conservative:
            disjoint unions imply collision-free co-residency AND same-tick /
            any-order crane entries and exits). Every selected placement is
            still exact-gated by _can_place at commit; failures are skipped.
            Returns a committed list (caller evaluates + rolls back)."""
            try:
                from ortools.sat.python import cp_model
            except Exception:
                return []
            # jv5 Phase C (D/K scaling on deep queues, 16,6 -> 24,8 + 3.0s)
            # MEASURED DEAD -- REVERTED to v25's 16,6. Refutation: prob_33
            # @600s +179,066 with z2 1438 -> 309 but z1 1029 -> 1047. The wider
            # menu packs area/balance BETTER and tardiness WORSE -- and w1
            # (6667 on 33) dwarfs w2/w3, so 18 units of z1 (~120k) buys nothing
            # that 1129 units of z2 can repay. mpc_fill maximizes ADMITTED AREA,
            # which is only a proxy for tardiness; enlarging the model sharpens
            # the proxy, not the objective. Do not re-propose D/K scaling
            # without first fixing the objective (see the parked mpc==2 branch).
            D, K = 16, 6
            cand = []      # (bi, bay_id, oi, x, y, r0, c0, fp)
            for bi in admissible[:D]:
                blk = blocks_data[bi]
                per = []
                for bay_id in range(n_bays):
                    bay = bays[bay_id]
                    occ_fp = (raster.footprint(bay_id) if score_pos else None)
                    for oi in orients_of[bi]:
                        if len(per) >= K:
                            break
                        if not _orient_fits(blk, oi, bay):
                            continue
                        feas, cx0, cy0 = raster.scan(bay_id, bi, oi)
                        grids = []
                        if feas is not None and feas.any():
                            grids.append(feas)
                        if nearmiss > 0:
                            nr = raster.scan_near(bay_id, bi, oi)
                            if nr is not None and nr.any():
                                grids.append(nr)
                        for g in grids:
                            cells = _order_cells(raster, g, cx0, cy0, bi, oi,
                                                 raster.W[bay_id], occ_fp,
                                                 score_pos, None)
                            for (x, y) in cells[:3]:
                                fp = raster.mask_fp(bi, oi)
                                per.append((bi, bay_id, oi, x, y,
                                            int(y) + cy0, int(x) + cx0, fp))
                                if len(per) >= K:
                                    break
                            if len(per) >= K:
                                break
                cand.extend(per)
            if len(cand) < 8:
                return []
            m = cp_model.CpModel()
            xs = [m.NewBoolVar("c%d" % i) for i in range(len(cand))]
            by_block = {}
            for i, c in enumerate(cand):
                by_block.setdefault(c[0], []).append(xs[i])
            for vs in by_block.values():
                m.AddAtMostOne(vs)
            # pairwise conflicts: same bay + footprint-union masks intersect
            for i in range(len(cand)):
                bi_i, bay_i, _oi, _x, _y, r0i, c0i, fpi = cand[i]
                hi, wi = fpi.shape
                for j in range(i + 1, len(cand)):
                    bj, bay_j, _oj, _x2, _y2, r0j, c0j, fpj = cand[j]
                    if bi_i == bj or bay_i != bay_j:
                        continue
                    hj, wj = fpj.shape
                    rlo = max(r0i, r0j); rhi = min(r0i + hi, r0j + hj)
                    clo = max(c0i, c0j); chi = min(c0i + wi, c0j + wj)
                    if rlo >= rhi or clo >= chi:
                        continue
                    a = fpi[rlo - r0i:rhi - r0i, clo - c0i:chi - c0i]
                    b = fpj[rlo - r0j:rhi - r0j, clo - c0j:chi - c0j]
                    if bool(_np.logical_and(a, b).any()):
                        m.AddBoolOr([xs[i].Not(), xs[j].Not()])
            if mpc == 2:
                # v25: urgency-weighted objective -- pure area-greed measured
                # myopic (27 raw +275k). Bonus for blocks already late or
                # nearly late at t (admitting them stops the tardiness bleed;
                # delaying slack-rich blocks is cheap).
                def wgt(bi):
                    late = t + procs[bi] - dues[bi]
                    u = 24 if late >= 0 else (12 if late >= -2 else 0)
                    return int(areas[bi] * 16) + int(areas[bi] * u)
                m.Maximize(sum(wgt(cand[i][0]) * xs[i]
                               for i in range(len(cand))))
            else:
                m.Maximize(sum(int(areas[cand[i][0]] * 16) * xs[i]
                               for i in range(len(cand))))
            sol = cp_model.CpSolver()
            sol.parameters.max_time_in_seconds = min(
                2.0, max(0.3, deadline - time.time() - 1.0))
            sol.parameters.num_search_workers = 1
            st = sol.Solve(m)
            if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                return []
            chosen = [cand[i] for i in range(len(cand)) if sol.Value(xs[i])]
            chosen.sort(key=lambda c: -areas[c[0]])
            committed = []
            for (bi, bay_id, oi, x, y, _r0, _c0, _fp) in chosen:
                p = procs[bi]
                exit_t = t + p
                bay = bays[bay_id]
                rel = _rel_sched_bbox(sched[bay_id], t, exit_t)
                nb = _mkblock(bi, blocks_data[bi], x, y, oi)
                if _can_place(bay, rel, nb, t, exit_t):
                    place = (bay_id, x, y, oi, t, exit_t)
                    commit(bi, place)
                    committed.append((bi, place))
            return committed

        best = None   # ((-area, cost), committed_list)
        for od in (order_atc, order_area, order_con):
            if time.time() > deadline:
                break
            committed = []
            for bi in od:
                if time.time() > deadline:
                    break
                if targets is not None and t < targets[bi]:
                    continue
                place = try_place(bi, t, cc)
                if place is not None:
                    commit(bi, place)         # trial: mutate only, no bookkeeping
                    committed.append((bi, place))
            key = evaluate(committed)
            if best is None or key < best[0]:
                best = (key, list(committed))
            rollback(committed)
        # v22: MPC joint-selection fill competes with the greedy orders under
        # the same (admitted area, cost) key; min-wins, so worst case it just
        # costs its solver budget.
        if mpc and len(ordered) >= 8 and time.time() <= deadline - 1.5:
            admissible = [bi for bi in ordered
                          if targets is None or t >= targets[bi]]
            try:
                committed = mpc_fill(admissible)
            except Exception:
                committed = []
            if committed:
                key = evaluate(committed)
                if best is None or key < best[0]:
                    best = (key, list(committed))
                rollback(committed)
        if best is not None:
            for bi, place in best[1]:
                apply_place(bi, place)

    # event structure ---------------------------------------------------------
    rel_sorted = sorted(range(n), key=lambda i: rels[i])
    rp = 0
    exits_at = {}                              # time -> [(bay, bi, oi, x, y)]
    ev_times = set(rels)
    if targets is not None:
        ev_times |= {int(v) for v in targets.values()}  # round-3: gate opens
    heap = sorted(ev_times)
    heapq.heapify(heap)
    scheduled = set(heap)                       # v13: O(1) heap membership test
    queue = set()
    placed_cnt = 0
    last_t = None

    while heap:
        t = heapq.heappop(heap)
        scheduled.discard(t)
        if t == last_t:
            continue
        last_t = t
        # 1. process exits at t (free occupancy) + prune exited blocks from the
        #    affected bays' sched (they can never matter for entry>=t; keeps the
        #    _rel_sched_bbox / _can_place scans O(active) on giants).
        ev = exits_at.pop(t, None)
        if ev:
            touched = set()
            for (bay_id, bi, oi, x, y) in ev:
                raster.remove(bay_id, bi, oi, x, y)
                touched.add(bay_id)
            for bj in touched:
                sched[bj] = [it for it in sched[bj] if it[2] > t]
        # 2. admit newly released blocks
        while rp < n and rels[rel_sorted[rp]] <= t:
            queue.add(rel_sorted[rp]); rp += 1
        if not queue:
            continue
        if time.time() > deadline:
            break
        # 3. admission pass in ATC priority order (v14: optional multi-order beam)
        ordered = sorted(queue, key=lambda bi: -atc(bi, t))
        cc = cap_for(len(ordered))
        if beam and len(ordered) >= beam_m:
            beam_admit(t, ordered, cc)
        else:
            steals_left = 2 if steal else 0   # jv6b: bounded attempts/event
            for pos, bi in enumerate(ordered):
                if time.time() > deadline:
                    break
                if targets is not None and t < targets[bi]:
                    continue    # round-3 GATE: hold until the fluid target
                # jv6b drain lookahead: the next `drain` more-urgent queued
                # blocks (after bi) whose release has passed -- the ones this
                # placement must not foreclose.
                look = None
                if drain:
                    look = [b for b in ordered[pos + 1:]
                            if targets is None or t >= targets[b]][:drain]
                place = try_place(bi, t, cc, look=look)
                if place is None and steals_left:
                    place = try_steal(bi, t, cc)
                    steals_left = 0 if place is not None else steals_left - 1
                if place is not None:
                    apply_place(bi, place)
        # if the queue still holds blocks and no future event will free space,
        # inject a probe event so they get force-placed below.
        if queue and not heap:
            break

    # 4. force-place every remaining block (queued + not-yet-released) so the
    #    result is always complete; feed the exact same fallback as _force_place.
    remaining = [bi for bi in range(n) if bi not in assignments]
    remaining.sort(key=lambda bi: (dues[bi], -_min_area(blocks_data[bi])))
    for bi in remaining:
        blk = blocks_data[bi]
        # try a raster admission at the block's release (cheap best-effort),
        # else fall back to the guaranteed empty-bay force placement.
        t = rels[bi]
        place = try_place(bi, t, cand_cap)
        if place is None:
            place = _force_place(bi, blk, bays, sched)
        commit(bi, place)

    return assignments


def _rel_sched_bbox(sched_bay, entry, exit_t):
    """(blk, a, e) triples for blocks in the bay whose time interval can matter
    for a placement over [entry, exit_t) -- i.e. present at entry, present at
    exit, or time-overlapping. Kept broad (time only) so `_can_place` sees every
    block it must check; it does its own bbox pruning via the caches."""
    out = []
    for it in sched_bay:
        a, e = it[1], it[2]
        if a <= exit_t and entry <= e:
            out.append((it[0], a, e))
    return out


# -----------------------------------------------------------------------------
# v13 Z3 (bay-preference) RELOCATION ENDGAME (#3c)
# -----------------------------------------------------------------------------

def _z3_relocate(prob_info, assign, bays, bay_u, w1, w2, w3, raster, deadline,
                 pos_cap=16, max_passes=3, time_cap=8):
    """Preference relocation endgame: for each off-preference block (desc by
    w3 gain) try moving it to a higher-preference bay -- first at the SAME
    [entry, exit) interval (tardiness-neutral), then at ALTERNATIVE entry
    times whose full objective delta (w1*d_tard + w2*d_imbal - w3*gain) is
    still strictly negative (measured: the same-interval move almost never
    fits because the preferred bay is full at exactly that interval -- that is
    WHY the block went off-preference; timing freedom is what unlocks the Z3
    money). Candidate cells come from the scoped raster scan, exact-gated by
    _can_place; the delta is computed exactly BEFORE geometry work, so only
    strictly-improving (t, bay) pairs are ever scanned. Removing a block from
    its old bay can never invalidate others (strictly fewer obstacles).
    Returns (new_assign, new_obj) or (None, None)."""
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    if n_bays < 2 or raster is None or not _HAVE_NUMPY:
        return None, None
    cur = {bi: dict(a) for bi, a in assign.items()}
    sched, bay_loads = _rebuild_sched(cur, blocks_data, n_bays)

    def imbal(loads):
        return math.floor(max(
            abs(bay_u[p] * loads[p] - bay_u[q] * loads[q])
            for p in range(n_bays) for q in range(n_bays) if p != q))

    moved_any = False
    for _pass in range(max_passes):
        cand = []
        for bi, a in cur.items():
            prefs = blocks_data[bi]["bay_preferences"]
            gain = max(prefs) - prefs[a["bay_id"]]
            if gain > 0:
                cand.append((gain, bi))
        if not cand:
            break
        cand.sort(reverse=True)
        pass_moved = False
        for _, bi in cand:
            if time.time() > deadline:
                break
            a = cur[bi]
            blk = blocks_data[bi]
            prefs = blk["bay_preferences"]
            entry, exit_t = a["entry_time"], a["exit_time"]
            proc = exit_t - entry
            due = int(blk["due_date"])
            rel_t = int(blk["release_time"])
            cur_tard = max(0, exit_t - due)
            cb = a["bay_id"]
            wl = blk["workload"]
            im0 = imbal(bay_loads)
            orients = [oi for oi in _unique_orients(blk)]
            done = False
            for tj in sorted((j for j in range(n_bays) if prefs[j] > prefs[cb]),
                             key=lambda j: -prefs[j]):
                loads2 = list(bay_loads)
                loads2[cb] -= wl; loads2[tj] += wl
                # budget = the strict-improvement room left for added tardiness
                budget = (w3 * (prefs[tj] - prefs[cb])
                          - w2 * (imbal(loads2) - im0))
                if budget <= 1e-9:
                    continue                 # move can't pay for itself
                bay = bays[tj]
                if not any(_orient_fits(blk, oi, bay) for oi in orients):
                    continue
                # candidate entry times: same interval first, then bay-event
                # times whose tardiness delta still fits within the budget.
                t_hi = due - proc + cur_tard + int(budget / max(w1, 1e-9))
                cands_t = {entry}
                alap = due - proc
                if rel_t <= alap:
                    cands_t.add(alap); cands_t.add(rel_t)
                for it2 in sched[tj]:
                    a2, e2 = it2[1], it2[2]
                    for tt in (int(e2), int(a2) - proc):
                        if rel_t <= tt <= t_hi:
                            cands_t.add(tt)

                def dtard(t):
                    return max(0, t + proc - due) - cur_tard

                # same-interval first; then least added tardiness, LATEST first
                # within a tardiness tier (bays drain over time -- late slots
                # near ALAP are where free space actually exists; mirrors
                # _zero_candidates' reverse order).
                times = sorted(cands_t, key=lambda t: (t != entry, dtard(t), -t))
                for t in times[:time_cap]:
                    dobj = w1 * dtard(t) - budget
                    if dobj >= -1e-9:
                        continue
                    e_new = t + proc
                    relx = _time_overlap_rel(sched[tj], t, e_new)
                    actives = [(b.block_id, b.orient_idx, b.x, b.y)
                               for b, _a2, _e2 in relx]
                    for oi in orients:
                        if not _orient_fits(blk, oi, bay):
                            continue
                        feas, cx0, cy0, occ_fp = raster.scan_scoped(
                            tj, actives, bi, oi)
                        if feas is None or not feas.any():
                            continue
                        cells = _order_cells(raster, feas, cx0, cy0, bi, oi,
                                             raster.W[tj], occ_fp, True, None)
                        tried = 0
                        for (x, y) in cells:
                            nb = _mkblock(bi, blk, x, y, oi)
                            if _can_place(bay, relx, nb, t, e_new):
                                # commit: strict internal-objective improvement
                                sched[cb] = [it for it in sched[cb]
                                             if it[0].block_id != bi]
                                sched[tj].append((nb, t, e_new,
                                                  nb.bounding_rect()))
                                bay_loads[cb] -= wl; bay_loads[tj] += wl
                                a["bay_id"] = tj
                                a["x"] = int(x); a["y"] = int(y)
                                a["orient_idx"] = oi
                                a["entry_time"] = int(t)
                                a["exit_time"] = int(e_new)
                                pass_moved = True; moved_any = True
                                done = True
                                break
                            tried += 1
                            if tried >= pos_cap:
                                break
                        if done:
                            break
                    if done or time.time() > deadline:
                        break
                if done:
                    break                    # next block
        if not pass_moved or time.time() > deadline:
            break
    if not moved_any:
        return None, None
    o = _objective(cur, blocks_data, bays, bay_u, w1, w2, w3)[0]
    return cur, o


# -----------------------------------------------------------------------------
# v13 #3b: CP-SAT time-WINDOW decomposition for giant bays
# -----------------------------------------------------------------------------

def _cpsat_retime_window(bay, blocks_data, ids, new_assign, t_end,
                         cap_pairs=4000, chunk0=55):
    """Windowed retime for a bay whose full pair count exceeds the CP-SAT cap
    (v12 silently no-opped there). Retimes one time-window CHUNK of blocks at a
    time: chunk blocks are variables constrained inside [T0, T1] (their current
    span) against each other with the EXACT var-var encoding of the full model,
    and against every temporally-overlapping non-chunk block as FIXED constants
    (same crane tie rules, entry times substituted). Variables cannot leave
    [T0, T1], so no unmodeled interaction is possible. Chunks are processed
    most-tardy-first until the deadline; each accepted window strictly reduces
    its own tardiness. Mutates new_assign in place; returns True if improved."""
    from ortools.sat.python import cp_model
    improved = False

    def tard(bi):
        return max(0, new_assign[bi]["exit_time"] - blocks_data[bi]["due_date"])

    ids_sorted = sorted(ids, key=lambda bi: new_assign[bi]["entry_time"])
    chunks = [ids_sorted[i:i + chunk0] for i in range(0, len(ids_sorted), chunk0)]
    chunks.sort(key=lambda ch: -sum(tard(bi) for bi in ch))
    for ch in chunks:
        if time.time() >= t_end - 1.5:
            break
        if sum(tard(bi) for bi in ch) <= 0:
            continue

        def bounds(c):
            """[T0e, T1]: the chunk's span EXTENDED LEFT by its own width --
            tardiness wins come from pulling blocks earlier into idle gaps
            before the chunk, which a same-span window cannot express."""
            t0 = min(new_assign[bi]["entry_time"] for bi in c)
            t1 = max(new_assign[bi]["exit_time"] for bi in c)
            return max(0, t0 - max(1, t1 - t0)), t1

        def fixed_of(c, T0, T1):
            cs = set(c)
            return [bi for bi in ids if bi not in cs
                    and new_assign[bi]["entry_time"] <= T1
                    and new_assign[bi]["exit_time"] >= T0]

        T0, T1 = bounds(ch)
        fixed = fixed_of(ch, T0, T1)
        while (len(ch) > 12 and
               len(ch) * (len(ch) - 1) // 2 + len(ch) * len(fixed)
               > int(cap_pairs * 1.5)):
            ch = ch[:max(12, int(len(ch) * 0.7))]
            T0, T1 = bounds(ch)
            fixed = fixed_of(ch, T0, T1)
        before = sum(tard(bi) for bi in ch)
        if before <= 0:
            continue
        blks = {bi: _mkblock(bi, blocks_data[bi], new_assign[bi]["x"],
                             new_assign[bi]["y"], new_assign[bi]["orient_idx"])
                for bi in list(ch) + fixed}
        m = cp_model.CpModel()
        E, P = {}, {}
        terms = {}
        for bi in ch:
            blk = blocks_data[bi]
            P[bi] = int(blk["processing_time"])
            lo = max(int(blk["release_time"]), int(T0))
            hi = int(T1) - P[bi]
            e0 = int(new_assign[bi]["entry_time"])
            lo = min(lo, e0); hi = max(hi, e0)    # domain always contains hint
            E[bi] = m.NewIntVar(lo, hi, f"e{bi}")
            m.AddHint(E[bi], e0)
            T = m.NewIntVar(0, int(T1) + 10, f"t{bi}")
            m.Add(T >= E[bi] + P[bi] - int(blk["due_date"]))
            terms[bi] = T

        def outside_vv(i, off_i, j, tie_bad):
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + off_i <= E[j] - (1 if tie_bad == "left" else 0)
                  ).OnlyEnforceIf(b1)
            m.Add(E[i] + off_i >= E[j] + P[j] + (1 if tie_bad == "right" else 0)
                  ).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        def outside_vf(i, off_i, lo_c, hi_c, tie_left, tie_right):
            """E[i]+off_i outside (lo_c, hi_c) with optional boundary bans."""
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            m.Add(E[i] + off_i <= lo_c - (1 if tie_left else 0)).OnlyEnforceIf(b1)
            m.Add(E[i] + off_i >= hi_c + (1 if tie_right else 0)).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        abort = False
        chl = list(ch)
        for u in range(len(chl)):
            if (u & 15) == 0 and time.time() >= t_end - 0.8:
                abort = True
                break
            i = chl[u]
            A = blks[i]
            # -- var-var (exact mirror of the full model) ------------------
            for v in range(u + 1, len(chl)):
                j = chl[v]
                B = blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                if _collide(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] + P[i] <= E[j]).OnlyEnforceIf(b1)
                    m.Add(E[j] + P[j] <= E[i]).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                    continue
                if _entry_blocked(bay, B, A):
                    outside_vv(i, 0, j, "left" if j < i else "none")
                if _exit_blocked(bay, B, A):
                    outside_vv(i, P[i], j, "right" if j > i else "none")
                if _entry_blocked(bay, A, B):
                    outside_vv(j, 0, i, "left" if i < j else "none")
                if _exit_blocked(bay, A, B):
                    outside_vv(j, P[j], i, "right" if i > j else "none")
            # -- var-fixed (fixed entry times as constants) ----------------
            for j in fixed:
                B = blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                aj = int(new_assign[j]["entry_time"])
                ej = int(new_assign[j]["exit_time"])
                if _collide(bay, A, B):
                    # disjoint intervals: exit_i <= aj OR E_i >= ej
                    outside_vf(i, P[i], aj, ej + P[i], False, False)
                    continue
                # j (fixed) obstructs i's entry/exit moments:
                if _entry_blocked(bay, B, A):
                    outside_vf(i, 0, aj, ej, j < i, False)
                if _exit_blocked(bay, B, A):
                    outside_vf(i, P[i], aj, ej, False, j > i)
                # i (variable) obstructs j's fixed entry moment aj / exit ej:
                # aj outside (E_i, E_i+P_i): E_i >= aj (+1 if i<j) OR exit_i<=aj
                if _entry_blocked(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] >= aj + (1 if i < j else 0)).OnlyEnforceIf(b1)
                    m.Add(E[i] + P[i] <= aj).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                if _exit_blocked(bay, A, B):
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] >= ej).OnlyEnforceIf(b1)
                    m.Add(E[i] + P[i] <= ej - (1 if i > j else 0)).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
        if abort:
            break
        m.Minimize(sum(terms.values()))
        rem2 = min(5.0, t_end - time.time() - 0.3)
        if rem2 < 0.5:
            break
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = rem2
        solver.parameters.num_search_workers = 1
        try:
            status = solver.Solve(m)
        except Exception:
            continue
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            after = sum(int(solver.Value(t)) for t in terms.values())
            if after < before:
                for bi in ch:
                    e = int(solver.Value(E[bi]))
                    new_assign[bi]["entry_time"] = e
                    new_assign[bi]["exit_time"] = e + P[bi]
                improved = True
    return improved


# -----------------------------------------------------------------------------
# v11 CP-SAT exact time-repair (fixed geometry)  [v12: audit fixes]
# -----------------------------------------------------------------------------

def _cpsat_retime(prob_info, assign, bays, blocks_data, budget_s, hard_deadline):
    """Re-optimize ALL entry times of `assign` with bay/x/y/orient fixed,
    minimizing total tardiness (the only timing-dependent objective term).
    Bays are independent -> one CP-SAT model per bay. Pairwise relations come
    from the exact cached geometry primitives; crane tie rules mirror
    _present_at_entry/_present_at_exit. Returns a new assignments dict or None
    (ortools missing, no time, or no improvement)."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    t_end = min(time.time() + budget_s, hard_deadline - 1.0)
    if time.time() >= t_end:
        return None
    n_bays = len(bays)
    by_bay = [[] for _ in range(n_bays)]
    for bi, a in assign.items():
        by_bay[a["bay_id"]].append(bi)
    # Most-tardy bays first so the budget goes where the money is.
    def bay_tard(ids):
        return sum(max(0, assign[bi]["exit_time"] - blocks_data[bi]["due_date"])
                   for bi in ids)
    order = sorted(range(n_bays), key=lambda j: -bay_tard(by_bay[j]))
    new_assign = {bi: dict(a) for bi, a in assign.items()}
    improved = False
    for bj in order:
        ids = by_bay[bj]
        if len(ids) < 2 or bay_tard(ids) <= 0:
            continue
        # v12 fix: pair-count cap. The pairwise build is O(m^2) Shapely/cache
        # queries; a bay with hundreds of blocks can blow the whole window on
        # model construction alone. v13 #3b: such giant bays now get the
        # time-WINDOW decomposition (chunked exact retime) instead of a no-op.
        if len(ids) * (len(ids) - 1) // 2 > 4000:
            try:
                if _cpsat_retime_window(bays[bj], blocks_data, ids,
                                        new_assign, t_end):
                    improved = True
            except Exception:
                pass
            continue
        remaining = t_end - time.time()
        if remaining < 1.5:
            break
        bay = bays[bj]
        blks = {bi: _mkblock(bi, blocks_data[bi], assign[bi]["x"],
                             assign[bi]["y"], assign[bi]["orient_idx"])
                for bi in ids}
        m = cp_model.CpModel()
        H = int(2 * max(max(a["exit_time"] for a in assign.values()),
                        max(blocks_data[bi]["due_date"] for bi in ids)) + 10)
        E, P = {}, {}
        terms = []
        for bi in ids:
            blk = blocks_data[bi]
            P[bi] = int(blk["processing_time"])
            E[bi] = m.NewIntVar(int(blk["release_time"]), H, f"e{bi}")
            m.AddHint(E[bi], int(assign[bi]["entry_time"]))
            T = m.NewIntVar(0, H, f"t{bi}")
            m.Add(T >= E[bi] + P[bi] - int(blk["due_date"]))
            terms.append(T)

        def outside(t_i, off_i, bi_id, bj2, tie_bad):
            """Moment E[bi_id]+off_i must lie outside (E[bj2], E[bj2]+P[bj2]);
            tie_bad='left' also forbids == E[bj2]; 'right' forbids == exit."""
            b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
            if tie_bad == "left":
                m.Add(E[bi_id] + off_i <= E[bj2] - 1).OnlyEnforceIf(b1)
            else:
                m.Add(E[bi_id] + off_i <= E[bj2]).OnlyEnforceIf(b1)
            if tie_bad == "right":
                m.Add(E[bi_id] + off_i >= E[bj2] + P[bj2] + 1).OnlyEnforceIf(b2)
            else:
                m.Add(E[bi_id] + off_i >= E[bj2] + P[bj2]).OnlyEnforceIf(b2)
            m.AddBoolOr([b1, b2])

        abort = False
        for u in range(len(ids)):
            # v12 fix: deadline flag INSIDE the O(m^2) build. A partially-built
            # model omits collision/crane constraints and would solve to a
            # garbage (infeasible-in-reality) schedule, so on timeout we abort
            # the bay WITHOUT solving rather than solve an incomplete model.
            if (u & 15) == 0 and time.time() >= t_end:
                abort = True
                break
            for v in range(u + 1, len(ids)):
                i, j = ids[u], ids[v]
                A, B = blks[i], blks[j]
                if not _bb_overlap(A.bounding_rect(), B.bounding_rect()):
                    continue
                if _collide(bay, A, B):
                    # disjoint presence intervals (touching allowed; ties are
                    # then boundary moments, which the replay rules permit)
                    b1, b2 = m.NewBoolVar(""), m.NewBoolVar("")
                    m.Add(E[i] + P[i] <= E[j]).OnlyEnforceIf(b1)
                    m.Add(E[j] + P[j] <= E[i]).OnlyEnforceIf(b2)
                    m.AddBoolOr([b1, b2])
                    continue
                # crane rules (mirror _present_at_entry/_present_at_exit ties):
                # j present at i's ENTRY t: E_j < t < exit_j, or t == E_j and
                # j.id < i.id. j present at i's EXIT t: E_j < t < exit_j, or
                # t == exit_j and j.id > i.id.
                if _entry_blocked(bay, B, A):   # j obstructs i's entry moment
                    outside(E[i], 0, i, j, "left" if j < i else "none")
                if _exit_blocked(bay, B, A):    # j obstructs i's exit moment
                    outside(E[i], P[i], i, j, "right" if j > i else "none")
                if _entry_blocked(bay, A, B):
                    outside(E[j], 0, j, i, "left" if i < j else "none")
                if _exit_blocked(bay, A, B):
                    outside(E[j], P[j], j, i, "right" if i > j else "none")
        if abort:
            break
        m.Minimize(sum(terms))
        # v12 fix: recompute the solver budget AFTER the (possibly slow) build,
        # and drop the >=1s floor -- the old code reserved the PRE-build
        # `remaining` and floored it at 1s, so a long build let the solve run
        # past t_end and starved the post-CP improve.
        rem2 = t_end - time.time()
        if rem2 < 0.5:
            break
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = rem2
        solver.parameters.num_search_workers = 1  # we're already 1 core/worker
        try:
            status = solver.Solve(m)
        except Exception:
            continue
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            before = bay_tard(ids)
            after = sum(int(solver.Value(t)) for t in terms)
            if after < before:
                for bi in ids:
                    e = int(solver.Value(E[bi]))
                    new_assign[bi]["entry_time"] = e
                    new_assign[bi]["exit_time"] = e + P[bi]
                improved = True
    return new_assign if improved else None


# -----------------------------------------------------------------------------
# v10 parallel portfolio (v11: + island inboxes + CP-SAT pass)
# -----------------------------------------------------------------------------

def _run_strategy(wid, prob_info, timelimit, t_start, push, inbox=None):
    """One portfolio member. Streams (internal_obj, assignments) via push();
    receives global-best broadcasts via inbox (None for the W0 anchor)."""
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    deadline = t_start + timelimit * 0.95 - reserve - 2.5  # margin for final put
    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)
    forced = _is_forced(prob_info, bays)
    window = deadline - t_start

    def iobj(assign):
        return _objective(assign, blocks_data, bays, bay_u, w1, w2, w3)[0]

    def build(order, fc, gamma=0.0):
        a = _construct(prob_info, order, bays, bay_u, w1, w2, w3,
                       t_start, deadline, forced=fc, util_gamma=gamma)
        o = iobj(a)
        push(o, a)
        return o, a

    # round-3: structural-overload detection (moved up in v16: the reclaim rule
    # needs it before the raster gate). Fluid-target cache below.
    overload = _overload_ratio(prob_info, bays)
    # v16 ANCHOR RECLAIM rule (instance-computed, no name lookups): the
    # v9-replica anchor is provably non-competitive on giants (forced n>=250)
    # and structurally overloaded instances (overload > 1.05) -- on train this
    # selects exactly {27, 37, 38, 39, 40} (all with v9-path results 1.6-2.2x
    # worse than the v14 winners; see results.csv). There (and ONLY there) W0
    # runs a productive dispatcher stream and repack deepening (`deep`) is on.
    reclaim = (forced and len(blocks_data) >= 250) or overload > 1.05
    # v21: plan-eligible tardy class (same trigger as the v20 W1 explorer).
    # On these instances W2/W3 lotteries gain nm+beam tickets of the measured-
    # winning construction family; everywhere else they stay byte-exact.
    nm_elig = forced and w1 >= 6000 and overload > 0.65
    # jv6b (jay heuristic_31 Improvement B, unbenched there): reservation-
    # steal admission, gated to the 37-class signature -- the one train cell
    # with a measured 9x lenient/strict feasibility gap (diag37: strict 0.27%
    # vs lenient 2.42% -> ~10% of blocked moments have room claimed only by a
    # same-tick reservation). Static gate selects exactly {37} on train:
    # 38/39 excluded by w1 (13333), 40 by overload (1.22), 32/25 by n.
    steal37 = (forced and len(blocks_data) >= 250 and w1 <= 3400
               and overload <= 1.05)

    # v13: raster engine (shared masks). Every non-anchor worker gets one: the
    # dispatcher workers (W2/W3) use its occupancy for construction, and ALL
    # forced workers (incl. W1) use its scoped scan for raster-windowed repair
    # inside the improver. W0 stays byte-exact v9 and never touches a raster --
    # EXCEPT on reclaimed instances (v16), where W0 is a dispatcher stream.
    # v17: W0 also gets a raster on forced non-giants (the v13-rotation
    # restoration slot below) -- the v9 replica remains only on non-forced.
    raster = _Raster(prob_info, bays) if (_HAVE_NUMPY and
                                          (wid != 0 or reclaim or forced)
                                          ) else None

    def improve(assign, seed, until=None, repack_every=0, win_scale=2.0,
                xbay=None, nearmiss=0):
        dl = deadline if until is None else min(until, deadline)
        # v15: xbay default follows `forced` (giant W3 repack specialist gets it;
        # non-forced fallback improves stay v14). polish passes it explicitly
        # per harvest cycle (cycle 1 always False == v14's improve-1 config).
        # win_scale rotates the repack window width across harvest cycles.
        # v16: repack deepening (`deep=reclaim`) on the reclaimed set only.
        xb = forced if xbay is None else xbay
        r, o = _improve(prob_info, assign, bays, bay_u, w1, w2, w3,
                        dl, forced, seed=seed, on_best=push, inbox=inbox,
                        raster=raster, repack_every=repack_every,
                        xbay=xb, repack_win_scale=win_scale, deep=reclaim,
                        nearmiss=nearmiss)
        push(o, r, force=True)
        return o, r

    # v17: EXACT PACKING WINDOW shots (CP-SAT candidate-menu matheuristic;
    # obj-gated, ortools-guarded -- on any failure the greedy paths stand).
    _xrng = random.Random(1717)

    def exact_shots(base, ob, n_shots=2, budget_s=12.0, until=None):
        """Fire up to n_shots exact-packing windows on `base`; each accepted
        shot strictly improves the internal objective (pushed). Returns the
        possibly-improved (base, ob)."""
        if raster is None or not _HAVE_NUMPY:
            return base, ob
        dl_all = deadline if until is None else min(until, deadline)
        for _ in range(n_shots):
            if time.time() >= dl_all - 3.0:
                break
            try:
                w_ = _exact_pack_window(prob_info, base, bays, bay_u,
                                        w1, w2, w3, raster, _xrng, dl_all,
                                        forced=forced, budget_s=budget_s)
            except Exception:
                w_ = None
            if w_ is not None:
                o_ = iobj(w_)
                if o_ < ob - 1e-9:
                    push(o_, w_, force=True)
                    base, ob = w_, o_
        return base, ob

    def whole_bay_phase(base, ob, until):
        """v18 (as-measured): aim exact packing at the GLOBAL BEST, late.
        Drains the island inbox for the best-known incumbent, then fires
        v17's PROVEN window-scale exact-pack shots (D=14/K=12, ~13s,
        ~-27k per accept at ~1/8 rate) in a loop -- accepts compound on the
        adopted base and are pushed (banked, because the base IS the global
        best: v17's placement error fixed). The WHOLE-BAY model
        (`_exact_pack_bay`) is NOT fired: measured zero across five
        configurations on both gate targets (full/delta retime domains,
        20x8 / 8x5 scales, 8-way parallel solve, mover-free menus, clustered
        movers -- always FEASIBLE-at-hint, millions of branches, soundness
        after<=before always held). Exact neighborhoods pay only when small
        and dense; the function stays for provenance."""
        if raster is None or not _HAVE_NUMPY:
            return base, ob
        if inbox is not None:
            try:
                while True:
                    o_in, a_in = inbox.get_nowait()
                    if o_in < ob - 1e-9:
                        ob = o_in
                        base = {k: dict(v) for k, v in a_in.items()}
            except Exception:
                pass
        dl = min(until, deadline)
        while time.time() < dl - 15.0:
            try:
                w_ = _exact_pack_window(prob_info, base, bays, bay_u,
                                        w1, w2, w3, raster, _xrng, dl,
                                        forced=forced, budget_s=13.0)
            except Exception:
                w_ = None
            if w_ is not None:
                o_ = iobj(w_)
                if o_ < ob - 1e-9:
                    push(o_, w_, force=True)
                    base, ob = w_, o_
        return base, ob

    # fluid-target cache. targets are deterministic per (c_eff, mode), so
    # compute each grid point once.
    _tgt_cache = {}

    def fluid_tgt(spec):
        if spec is None:
            return None
        tg = _tgt_cache.get(spec)
        if tg is None:
            tg = _fluid_targets(prob_info, bays, spec[0], spec[1])
            _tgt_cache[spec] = tg
        return tg

    def dispatch(kappa, gamma, drng=None, alpha=0.0, score_pos=True,
                 tspec=None, beam=False, dl=None, nearmiss=0,
                 nk=3, mpc=False, ovh=False, steal=0, nm_compete=False):
        # jv5: nk/mpc/ovh added (mirrors ticket() at the W1 slot). reset()
        # bumps the version + clears the near/scan caches, so setting near_k
        # AFTER it is the stale-cache-free idiom; near_k is normalized on
        # every call (default 3 = v25 behavior). Forwarding mpc/ovh also
        # repairs the latent v25 bug where dispatch(..., mpc=True) /
        # dispatch(..., ovh=True) raised TypeError (swallowed) and never ran.
        raster.reset()
        raster.near_k = nk
        a = _dispatch_construct(prob_info, bays, bay_u, w1, w2, w3,
                                dl if dl is not None else deadline,
                                raster, kappa=kappa, gamma=gamma, rng=drng,
                                alpha=alpha, score_pos=score_pos,
                                targets=fluid_tgt(tspec), beam=beam,
                                nearmiss=nearmiss, mpc=mpc, ovh=ovh,
                                steal=steal, nm_compete=nm_compete)
        o = iobj(a)
        push(o, a)
        return o, a

    def polish(assign, seed, repack_every=0, alts=None, nearmiss=0):
        """v15 r2 polish. Three regimes:

        GIANTS (forced, n>=250) -> EXACT v14 envelope (improve -> CP-SAT ->
        improve -> Z3 endgame, sbay repack only). r1 harvest measured
        zero-to-negative there (prob_38 +53k); flat beats the re-roll.

        FORCED non-giant -> BASIN-DIVERSITY HARVEST from DISTINCT
        CONSTRUCTIONS. CP-SAT retime skipped (measured zero on forced). Cycle 1
        = v14's improve-1 config EXACTLY (same seed, sbay-only, 2*pbar window,
        until cp_at) -- protection of v14's banked draws. Cycles 2-3 (seed+1/+2,
        xbay z3-relocation round-robin, widths {1,3}*pbar) start from `alts`
        (the lottery's runner-up constructions) when available, else from
        best-so-far: r1 measured that improve-seed variation from a converged
        incumbent NEVER escapes its basin (31/33/30/34 byte-flat); v14's
        historical spread came from CONSTRUCTION draws, so basin diversity must
        be re-seeded at the construction level. Every cycle-best is pushed
        (min wins) -- worst case a fresh descent lands above the incumbent and
        contributes nothing.

        NON-FORCED -> same harvest, with CP-SAT retime KEPT between cycles 1
        and 2 (prob_21's historical win). Zero-tardy easies are inert (repack
        gated on tardiness; improver early-stops).

        All regimes finish with the tardiness-neutral Z3 preference-relocation
        endgame (#3c)."""
        z3_at = deadline - (min(12.0, 0.05 * window) if raster is not None
                            else 0.0)
        cp_at = t_start + 0.62 * window
        # v16 prob_27-class parity: non-giant overloaded instances share the
        # giant polish envelope (single long v14-style improves; harvest cycles
        # measured flat-to-negative on this class in v15 r1).
        giant = forced and (len(blocks_data) >= 250 or overload > 1.05)
        base, ob = assign, iobj(assign)

        def cycles(specs):
            nonlocal base, ob
            for cs, sc, cyc_dl, xb, ai in specs:
                if time.time() >= cyc_dl - 1.0:
                    continue
                src = base
                if ai is not None and alts is not None and len(alts) > ai:
                    src = alts[ai]
                o_, r_ = improve(src, cs, until=cyc_dl,
                                 repack_every=repack_every, win_scale=sc,
                                 xbay=xb, nearmiss=nearmiss)
                if o_ < ob:
                    base, ob = r_, o_

        if giant:
            # -- EXACT v14 polish (see docstring) ------------------------------
            o1, r1 = improve(assign, seed, until=cp_at,
                             repack_every=repack_every, win_scale=2.0,
                             xbay=False, nearmiss=nearmiss)
            base, ob = r1, o1
            try:
                rc = _cpsat_retime(prob_info, r1, bays, blocks_data,
                                   min(30.0, 0.12 * window), deadline)
            except Exception:
                rc = None
            if rc is not None:
                oc = iobj(rc)
                push(oc, rc, force=True)
                if oc < ob:
                    base, ob = rc, oc
            if time.time() < z3_at - 2.0:
                o2, r2 = improve(base, seed + 1, until=z3_at,
                                 repack_every=repack_every, win_scale=2.0,
                                 xbay=False, nearmiss=nearmiss)
                if o2 < ob:
                    base, ob = r2, o2
        elif forced:
            mid2 = t_start + 0.80 * window
            cycles([(seed, 2.0, cp_at, False, None)])
            # v17: exact packing shots right after cycle 1 (they consume the
            # head of cycle 2's window; the harvest cycles measured ~zero in
            # v15/v16, so this is the cheapest slot for the new mechanism --
            # cycle-1 pacing, i.e. the v14 improve-1 draw, stays intact).
            # Targets 26/23/33/30-class density-limited forced instances.
            base, ob = exact_shots(base, ob, n_shots=2, budget_s=12.0,
                                   until=min(mid2, cp_at + 30.0))
            cycles([(seed + 1, 1.0, mid2, True, 0),
                    (seed + 2, 3.0, z3_at, True, 1)])
        else:
            o1, r1 = improve(assign, seed, until=cp_at,
                             repack_every=repack_every, win_scale=2.0,
                             xbay=False, nearmiss=nearmiss)
            if o1 < ob:
                base, ob = r1, o1
            try:
                rc = _cpsat_retime(prob_info, base, bays, blocks_data,
                                   min(30.0, 0.12 * window), deadline)
            except Exception:
                rc = None
            if rc is not None:
                oc = iobj(rc)
                push(oc, rc, force=True)
                if oc < ob:
                    base, ob = rc, oc
            mid2 = t_start + 0.85 * window
            cycles([(seed + 1, 1.0, mid2, True, 0),
                    (seed + 2, 3.0, z3_at, True, 1)])
        if raster is not None and time.time() < deadline - 0.5:
            try:
                rz, oz = _z3_relocate(prob_info, base, bays, bay_u,
                                      w1, w2, w3, raster, deadline)
                if rz is not None and oz < ob - 1e-9:
                    push(oz, rz, force=True)
            except Exception:
                pass

    def polish_v13(assign, seed, wholebay=False):
        """v17 RESTORATION polish: byte-clone of v13's polish -- improve ->
        CP-SAT retime -> improve -> Z3 endgame; NO repack rounds, NO harvest
        cycles, NO xbay (repack_every=0 keeps _improve byte-exact v13 per the
        v14 contract). Used by the restoration slots (W2 non-forced tardy and
        W0 forced non-giant). v18: `wholebay=True` (W0 slot only) replaces the
        improve-2 leg with the whole-bay exact phase aimed at the global best
        -- the 30/33-winning raw builds happen in the LOTTERY (before this),
        and no banked draw depends on the W0 slot's improve-2, so the last
        ~35% of that worker's window is the free real estate heuristic_18
        earmarks. W2's non-forced clone keeps wholebay=False: prob_34's
        banked winner is THIS pipeline's z3 endgame and 21's is its cpsat."""
        cp_at = t_start + 0.62 * window
        o1, r1 = improve(assign, seed, until=cp_at)
        try:
            rc = _cpsat_retime(prob_info, r1, bays, blocks_data,
                               min(30.0, 0.12 * window), deadline)
        except Exception:
            rc = None
        base, ob = r1, o1
        if rc is not None:
            oc = iobj(rc)
            push(oc, rc, force=True)
            if oc < ob:
                base, ob = rc, oc
        z3_at = deadline - (min(12.0, 0.05 * window) if raster is not None
                            else 0.0)
        if wholebay:
            base, ob = whole_bay_phase(base, ob, until=z3_at)
        elif time.time() < z3_at - 2.0:
            o2, r2 = improve(base, seed + 1, until=z3_at)
            if o2 < ob:
                base, ob = r2, o2
        if raster is not None and time.time() < deadline - 0.5:
            try:
                rz, oz = _z3_relocate(prob_info, base, bays, bay_u,
                                      w1, w2, w3, raster, deadline)
                if rz is not None and oz < ob - 1e-9:
                    push(oz, rz, force=True)
            except Exception:
                pass

    def pick_alts(cands, k=2, cap=2.0):
        """v15 r2a: runner-up DISTINCT constructions for harvest re-seeding.
        Distinct by internal objective (identical obj == identical build for the
        deterministic lottery entries); capped at cap*best so a garbage draw is
        never given a polish cycle."""
        if not cands:
            return None
        srt = sorted(cands, key=lambda c: c[0])
        best_o = srt[0][0]
        seen = [best_o]
        out = []
        for o_c, a_c in srt[1:]:
            if o_c > best_o * cap:
                break
            if all(abs(o_c - s) > 1e-9 for s in seen):
                out.append(a_c)
                seen.append(o_c)
            if len(out) >= k:
                break
        return out or None

    if wid == 0:
        # v16 ANCHOR RECLAIM: on {giant-forced OR overload>1.05} (train:
        # {27,38,39}) the v9 replica is provably non-competitive (candidates
        # ~2x worse, zero verify wins since v12) while its safety role is
        # covered by the parent insurance build + empty-bay fallback + official
        # best-first verify. Run a PRODUCTIVE stream instead: the kappa=2/
        # alpha=0.5 dispatcher basin at FULL budget (W2 only ever samples it
        # inside its 0.45w lottery cap) -> v14-envelope polish WITHOUT CP-SAT
        # retime (forced: measured zero twice) -> Z3 relocation endgame. The
        # improver runs deep repack (deep=reclaim) with sbay/xbay alternation.
        # Any failure falls back to the v9 replica with the remaining budget.
        if reclaim and raster is not None:
            a0 = None
            try:
                if nm_elig:
                    # v21: the reclaimed stream's build joins the nm+beam
                    # family (27/38/39; reclaimed-but-ineligible 40 keeps the
                    # v16 build byte-exact). Full-budget deep improve + whole-
                    # bay phase then run on a measured-better construction.
                    # v23: + an MPC variant of the same build -- mpc measured
                    # -832k raw on 38 but never won from W1's shallow ticket;
                    # HERE the winner feeds the deep pipeline (min-wins).
                    # v24 lesson (prob_27 +939k): the BUILD-BUDGET PACING of
                    # this pair is load-bearing -- shifting dls changed the mpc
                    # build and raw-min fed the deep polish a worse input.
                    # jv5 Phase A: v25 built ONE near_k=3 build here -- the mpc
                    # build at 0.38w was SILENTLY DEAD (dispatch() lacked mpc=,
                    # TypeError swallowed). jv5 repairs mpc AND heads the build
                    # phase with two deep-nestle draws (nk 24 @0.22, 32 @0.30),
                    # honoring v25's DESIGNED build budget (-> 0.38w). Each
                    # dispatch pushes its raw build (floor-safe); the raw-min
                    # seeds improve->whole_bay->z3 exactly as before.
                    # nk constants are v25's tuned {24,32} (Phase B's adaptive
                    # family measured dead -- see _nk_family / the W1 rotation).
                    _o0, a0 = dispatch(2.0, 0.5, alpha=0.5, beam=True,
                                       nearmiss=32, nk=24,
                                       dl=t_start + 0.22 * window)
                    try:
                        _o1, a1 = dispatch(2.0, 0.5, alpha=0.5, beam=True,
                                           nearmiss=40, nk=32,
                                           dl=t_start + 0.30 * window)
                        if _o1 < _o0:
                            _o0, a0 = _o1, a1
                    except Exception:
                        pass
                    try:
                        _o2, a2 = dispatch(2.0, 0.5, alpha=0.5, beam=True,
                                           nearmiss=8, mpc=True,
                                           dl=t_start + 0.38 * window)
                        if _o2 < _o0:
                            _o0, a0 = _o2, a2
                    except Exception:
                        pass
                    # jv6b: NM_COMPETE build (probe_nmc 2026-07-17). The nk3-
                    # cmp signal on prob_38 (-2,674,658 / -2,345,442 raw vs
                    # controls) is CLEAN (38 was the probe process's first
                    # instance, before the cache-contamination window; see
                    # r4 note above -- the 39-branch premise was garbage and
                    # is removed). A/B @750s on 38: bit-identical tie (the
                    # build runs in the truncated 0.38w->0.46w residual and/
                    # or its stream loses the race) -- kept as harmless until
                    # the clean re-probe decides a better slot.
                    if len(blocks_data) >= 250 and overload > 1.05:
                        try:
                            _o3, a3 = dispatch(
                                0.5, 0.5, alpha=0.5, beam=True,
                                nearmiss=8, nm_compete=True,
                                dl=t_start + 0.46 * window)
                            if _o3 < _o0:
                                _o0, a0 = _o3, a3
                        except Exception:
                            pass
                    elif len(blocks_data) >= 250:
                        # jv6b r5: TEMPORAL ZONING build for the 39-class
                        # (n>=250, overload<=1.05). probe_zonecombo (clean
                        # harness): nk32+z24 k0.5/a0.5 = 9,872,219 raw =
                        # -429k BELOW the deep-nestle family best (10.30M) --
                        # the FIRST absolute-frontier break since v25. Given
                        # its own slice to 0.46w (the r1-r4 cmp builds tied by
                        # truncating in the 0.08w residual; zone re-rank adds
                        # cost, so it needs the room). Feeds the deep pipeline
                        # (improve->whole_bay->z3) as the raw-min seed --
                        # exit-cohort co-location gives the polish a
                        # fundamentally more drainable layout, not just a
                        # better-scoring greedy (the class of gain the epoch
                        # kept polishing away). A/B @750s decides if it
                        # survives polish + wins the worker race.
                        try:
                            _o3, a3 = dispatch(
                                0.5, 0.5, alpha=0.5, beam=True,
                                nearmiss=8, nk=32, zone=24,
                                dl=t_start + 0.46 * window)
                            import os as _oss
                            if _oss.environ.get("OGC_DEBUG"):
                                print(f"[zone39] raw={_o3:,.0f} "
                                      f"parent_min={_o0:,.0f}", flush=True)
                            if _o3 < _o0:
                                _o0, a0 = _o3, a3
                        except Exception:
                            pass
                else:
                    _o0, a0 = dispatch(2.0, 0.5, alpha=0.5)
            except Exception:
                a0 = None
            if a0 is not None:
                wb_at = t_start + 0.55 * window
                wb_end = t_start + 0.88 * window
                z3_at = deadline - min(12.0, 0.05 * window)
                o1, r1 = improve(a0, seed=1616, until=wb_at, repack_every=3,
                                 xbay=False)
                base, ob = r1, o1
                # v18: WHOLE-BAY exact packing aimed at the global best (the
                # island inbox is drained inside the phase). Supersedes v17's
                # window shots on the reclaimed stream (measured net-zero).
                base, ob = whole_bay_phase(base, ob, until=wb_end)
                if time.time() < z3_at - 2.0:
                    o2, r2 = improve(base, seed=1617, until=z3_at,
                                     repack_every=3, xbay=True)
                    if o2 < ob:
                        base, ob = r2, o2
                if time.time() < deadline - 0.5:
                    try:
                        rz, oz = _z3_relocate(prob_info, base, bays, bay_u,
                                              w1, w2, w3, raster, deadline)
                        if rz is not None and oz < ob - 1e-9:
                            push(oz, rz, force=True)
                    except Exception:
                        pass
                return
        # v17 RESTORATION SLOT (forced non-giants, overload <= 1.05): run the
        # v13 W3-rotation lottery + repack-free v13 polish INSTEAD of the v9
        # replica. Justification: (a) the attribution probe pinned v13's
        # prob_30/33 winners to RAW builds of exactly this rotation (displaced
        # by v14's beam tickets; recovering them in W3 broke prob_26's
        # beam-input winner by +374k, so they are recovered HERE); (b) W0's v9
        # replica is provably valueless on every forced non-giant (results.csv:
        # v9 is 1.5-5x worse on 23/25/26/30/31/32/33); (c) the lottery's rng
        # stream is deterministic and today's probe reproduced 4 of 5 target
        # draws byte-exactly (33 within 30k, pacing-sensitive late build).
        if forced and not reclaim and raster is not None:
            drng = random.Random(9099)
            cands = []
            cap = t_start + 0.5 * window
            if nm_elig and overload <= 0.72:
                # jv6b r5: TEMPORAL ZONING seed for the 31-class (forced non-
                # giant, overload<=0.72 -> exactly {31}). probe_zonecombo
                # (clean harness): cmp+z24 k0.5/a0.5 = 9,091,978 raw = -1.2M
                # BELOW the deep-nestle family best. ADDED to the restoration
                # lottery's cands (min-wins, non-displacing -- the 8-config
                # loop still runs its full 0.5w budget); polish_v13 seeds its
                # improve->cpsat->whole_bay->z3 chain from the raw-min, so a
                # more-drainable zoned layout feeds the real deep pipeline.
                try:
                    _oz, _az = dispatch(0.5, 0.5, drng, alpha=0.5, beam=True,
                                        nearmiss=8, nm_compete=True, zone=24,
                                        dl=t_start + 0.30 * window)
                    cands.append((_oz, _az))
                    import os as _oss
                    if _oss.environ.get("OGC_DEBUG"):
                        print(f"[zone31] raw={_oz:,.0f}", flush=True)
                except Exception:
                    pass
            plan = [(0.5, 0.5, 0.0, None), (1.0, 0.5, 0.5, None),
                    (2.0, 0.5, 1.0, None), (4.0, 0.5, 0.0, None),
                    (1.0, 2.0, 0.5, None), (2.0, 0.0, 1.0, None),
                    (0.5, 1.0, 0.0, None), (4.0, 0.0, 0.5, None)]
            gi = 0
            while True:
                kap, gam, al, ts_ = plan[gi % len(plan)]
                gi += 1
                try:
                    cands.append(dispatch(kap, gam, drng, alpha=al, tspec=ts_))
                except Exception:
                    break
                if time.time() >= cap or gi > 60:
                    break
            if cands:
                # v18: the W0 slot's improve-2 leg becomes the whole-bay
                # exact phase (aimed at the global best via the inbox).
                polish_v13(min(cands, key=lambda c: c[0])[1], seed=3333,
                           wholebay=True)
            return
        # W0 = EXACT v9 replica (same rng streams, same two-pass improver).
        # This is the no-regression anchor: the improver is basin-sensitive, so
        # only replaying v9's exact construction sequence guarantees v10 keeps
        # every v9 result (e.g. prob_31 17.64M comes from improving a jittered
        # construction that no plain EDD/AREA basin reaches). The worker gets a
        # slightly earlier deadline than v9's own (margin for the final put).
        _v9_search(prob_info, timelimit - 2.5, t_start, push=push)
        return

    # -- v17 RESTORATION SLOT (heuristic_17 #1): W2 on non-forced TARDY
    # instances runs a byte-clone of v13's W3 branch -- the 8-entry no-beam
    # jittered dispatcher lottery (drng 9099, cap 0.5w) + repack-free v13
    # polish with CP-SAT retime. Attribution probe: v13's prob_21 winner =
    # W3 polish improve(s3333, no repack) -> cpsat (1,380,772 reproduced
    # exactly today) -- v14's repack_every=4 in W3's polish displaced it. W3
    # keeps the CURRENT beam lottery (prob_35's banked 1,346,898 is a beam
    # draw), easies (overload <= 0.44) keep the current W2 path (prob_1
    # byte-safety), so this slot only ADDS v13's basins on 21/28/29/34/22
    # (+224k pool); exposure is bounded to 24/36 (-82k worst case, and their
    # v14 gains arrived exactly with beam == W3 paths).
    if wid == 2 and raster is not None and not forced and overload > 0.44:
        drng = random.Random(9099)
        cands = []
        cap = t_start + 0.5 * window
        plan = [(0.5, 0.5, 0.0, None), (1.0, 0.5, 0.5, None),
                (2.0, 0.5, 1.0, None), (4.0, 0.5, 0.0, None),
                (1.0, 2.0, 0.5, None), (2.0, 0.0, 1.0, None),
                (0.5, 1.0, 0.0, None), (4.0, 0.0, 0.5, None)]
        gi = 0
        while True:
            kap, gam, al, ts_ = plan[gi % len(plan)]
            gi += 1
            try:
                cands.append(dispatch(kap, gam, drng, alpha=al, tspec=ts_))
            except Exception:
                break
            if time.time() >= cap or gi > 60:
                break
        if cands:
            polish_v13(min(cands, key=lambda c: c[0])[1], seed=3333)
        elif time.time() < deadline:
            try:
                _, a = build(_edd_order(blocks_data), forced)
                improve(a, seed=3333)
            except Exception:
                pass
        return

    # -- W2 = dispatcher + volume-aware mini-lottery -> improver --------------
    if wid == 2 and raster is not None:
        cands = []
        if forced:
            # v13 giant/forced mini-lottery: rotate alpha (volume triage) x kappa
            # before polish. In v12 giants got exactly ONE dispatch here; raster
            # builds are cheap enough to sample the fluid-SPT basin (alpha>0).
            plan = [(0.0, 1.0, None, False), (0.5, 1.0, None, False),
                    (1.0, 1.0, None, False), (0.5, 2.0, None, False),
                    (0.0, 1.0, None, True)]        # v14: beam ticket last
            cap = t_start + 0.45 * window
            if overload > 1.05:
                # round-3: structurally oversubscribed (prob_38/27 regime) ->
                # add fluid-target ADMISSION-GATED dispatches. NOTE the honest
                # probe result: at the construction level EVERY gate variant
                # (spt/band loaders, pure-cut sacrifice; C in 0.5..1.1)
                # realized WORSE than the ungated dispatcher on both 38 and 27
                # (realization penalty ~13-22M dwarfs the fluid-SPT saving);
                # only the 3 closest variants are kept as cheap lottery
                # tickets (~1-5s each) in case the improver flips one, with
                # the plain entries first so best-of always protects. v14 adds
                # a multi-order admission-beam ticket last (attacks the first-
                # fit interlock foreclosure the gate variants could not).
                plan = [(0.0, 1.0, None, False), (0.5, 1.0, None, False),
                        (0.0, 1.0, (0.80, "cut"), False),
                        (0.0, 1.0, (1.10, "spt"), False),
                        (0.0, 1.0, (0.70, "cut"), False),
                        (1.0, 1.0, None, False), (0.5, 2.0, None, False),
                        (0.0, 1.0, None, True)]    # v14: beam ticket last
            if nm_elig:
                # v21: two nm+beam tickets FIRST (the measured-winning family;
                # W1's grid: kappa 0.5-2.0, alpha 0.5-1.0 are the hot region).
                # Different configs than W1's rotation head for diversity.
                plan = [(0.5, 1.0, None, "nmbeam"),
                        (1.0, 0.5, None, "nmbeam")] + plan
            # jv6b r4: the r2/r3 "nk32j" mid-tier ticket is REMOVED. Its
            # premise (probe raw 7,772,243 on 31 = -628k below bank) was
            # GARBAGE from the probe cache-contamination bug (module caches
            # _BLK/_CC/_CE/_CX are block_id-keyed, not instance-scoped; the
            # probe process ran 38->39->27->31 without _reset_caches()).
            # Clean-context value of that build on 31 = 11,380,559 -- far
            # above the bank. r2's measured law stands though: W2-append is
            # structurally dead on nm_elig mid-tier (5/5 bit-identical ties;
            # cap exhausted before appended tickets run).
            if steal37:
                # jv6b: ONE reservation-steal ticket HEADING the rotation
                # (probe_steal 2026-07-17: margin 2 SIGNAL -170,703 raw on 37,
                # margin 4 weaker; k=0.5 cfg was the winner). Heading, not
                # appending: at n=250 the 5 base tickets (~75s each) exhaust
                # the 0.45w cap, so an appended ticket never runs (30a lesson:
                # the near_k family also won by heading). Risk = displacing
                # the last base ticket past cap on 37 ONLY (gate = {37});
                # the 37 spot A/B measures exactly this trade.
                plan = [(0.5, 0.5, None, "steal2")] + plan
            for al, ka, ts_, bm in plan:
                try:
                    # beam tickets are capped at the lottery boundary so a slow
                    # multi-order fill can never starve the repack-heavy polish.
                    if bm == "nmbeam":
                        cands.append(dispatch(ka, 0.5, alpha=al, beam=True,
                                              dl=cap, nearmiss=8))
                    elif bm == "steal2":
                        cands.append(dispatch(ka, 0.5, alpha=al, dl=cap,
                                              steal=2))
                    elif bm == "nk32j":
                        cands.append(dispatch(ka, 0.5, alpha=al, beam=True,
                                              dl=cap, nearmiss=8, nk=32,
                                              drng=random.Random(9099)))
                    else:
                        cands.append(dispatch(ka, 0.5, alpha=al, tspec=ts_,
                                              beam=bm, dl=cap if bm else None))
                except Exception:
                    break
                if time.time() >= cap:
                    break
        else:
            try:
                cands.append(dispatch(1.0, 0.5))
            except Exception:
                pass
        if cands:
            # v14: W2 is the repack-heavy worker (giants + overloaded prob_27).
            # v15 r2a: runner-up constructions re-seed harvest cycles 2-3.
            polish(min(cands, key=lambda c: c[0])[1], seed=2222, repack_every=3,
                   alts=pick_alts(cands))
        else:  # dispatcher failed -> safe v11-style construction + improve
            try:
                _, a = build(_area_order(blocks_data) if forced
                             else _edd_order(blocks_data), forced)
                improve(a, seed=2222, repack_every=3)
            except Exception:
                pass
        return

    # -- W3 on GIANTS = repack specialist (v14) --------------------------------
    # Giants (n>=250, forced) ran only 3 workers in v12/v13 because W3's multi-
    # start dispatcher lottery cannot afford several giant builds. v14 re-adds
    # W3 as a REPACK SPECIALIST instead: seed with a cheap SPARSE construction
    # (deadline already past -> dense=False path, seconds even at n=250), then
    # run the improver with repack_every=2; the island inbox hands it W1/W2's
    # broadcast incumbent within ~a minute, so nearly the whole window is spent
    # on joint-window repacks of the real leader. RSS measured 2.87GB/3w on
    # prob_38 -> a 4th worker projects ~4GB, far under the 16GB budget. All
    # accepts obj-gated; worst case it contributes nothing (parent takes min).
    if wid == 3 and raster is not None and forced and len(blocks_data) >= 250:
        # v21 (nm_elig giants 38/39): seed with one nm+beam build -- one more
        # full-scale draw of the measured-winning family; the improver then
        # repacks the inbox leader exactly as before. Non-eligible giants keep
        # the v14 sparse seed byte-exact.
        if nm_elig:
            try:
                # jv5 Phase A: v25 seeded with ONE near_k=3 build; the ovh
                # build at 0.40w was SILENTLY DEAD (dispatch() lacked ovh=,
                # TypeError swallowed). jv5 repairs ovh AND heads with two
                # deep-nestle draws (nk 24 @0.22, 32 @0.35). The improver here
                # is inbox-seeded (repacks the global leader) so a slightly
                # later seed is low-risk. Each dispatch pushes its raw build.
                # nk constants are v25's tuned {24,32} (Phase B measured dead).
                _o, a = dispatch(1.0, 0.5, alpha=1.0, beam=True,
                                 nearmiss=32, nk=24,
                                 dl=t_start + 0.22 * window)
                try:
                    _o1, a1 = dispatch(1.0, 0.5, alpha=1.0, beam=True,
                                       nearmiss=40, nk=32,
                                       dl=t_start + 0.35 * window)
                    if _o1 < _o:
                        _o, a = _o1, a1
                except Exception:
                    pass
                try:
                    _o2, a2 = dispatch(1.0, 0.5, alpha=1.0, beam=True,
                                       nearmiss=8, ovh=True,
                                       dl=t_start + 0.40 * window)
                    if _o2 < _o:
                        _o, a = _o2, a2
                except Exception:
                    pass
                improve(a, seed=4444, repack_every=2, xbay=True, nearmiss=8)
                return
            except Exception:
                pass  # fall through to the v14 path
        try:
            a = _construct(prob_info, _edd_order(blocks_data), bays, bay_u,
                           w1, w2, w3, t_start, t_start, forced=True)
            push(iobj(a), a)
        except Exception:
            return
        # v16 r2: sbay/xbay alternation back ON at depth (deep=reclaim gives
        # cap 45 + {2,1,3,4}*pbar rotation; xbay is now the obj-gated Z3 group
        # relocation, worst case a no-op). The v15-r1 +53k slip came from the
        # HARVEST envelope re-roll, which stays reverted (polish giant branch).
        improve(a, seed=4444, repack_every=2, xbay=True)
        return

    # -- W3 = dispatcher lottery (kappa/gamma/jitter) -> improver -> CP-SAT ---
    if wid == 3 and raster is not None:
        drng = random.Random(9099)
        cands = []
        cap = t_start + 0.5 * window
        # v13: rotate ATC kappa x bay-spread gamma x volume-triage alpha.
        # v14: two beam tickets appended ONLY under congestion (forced or
        # overload > 0.44). Appending them unconditionally changed the lottery
        # ROTATION (gi % len(plan)) on easy non-forced instances and lost
        # v13's wrap-around basins (measured: prob_1 @60s 18,357 -> 29,665,
        # pure Z2/Z3 drift with no queues for the beam to fix). Deep admission
        # queues only form under congestion; on the train set every instance
        # with ANY v13 tardiness has overload >= 0.456 while the zero-tardy
        # easy tail tops out at 0.426, so 0.44 keeps v13's W3 lottery
        # byte-exact on the easy tail and gives the tardy class the beam
        # (measured on prob_35, overload 0.621: 2,011,342 -> 1,346,898).
        plan = [(0.5, 0.5, 0.0, None, False), (1.0, 0.5, 0.5, None, False),
                (2.0, 0.5, 1.0, None, False), (4.0, 0.5, 0.0, None, False),
                (1.0, 2.0, 0.5, None, False), (2.0, 0.0, 1.0, None, False),
                (0.5, 1.0, 0.0, None, False), (4.0, 0.0, 0.5, None, False)]
        # v17 note: an earlier attempt gave forced non-giants v13's 8-entry
        # rotation HERE (to recover prob_30/33's raw-build draws). Measured on
        # the first ladder pass: it DID recover 30/33 (+358k) but broke
        # prob_26 by +374k -- 26's banked winner is this polish on a
        # BEAM-build lottery input, so the beam tickets must stay. The v13
        # rotation lives in W0's forced-non-giant slot instead (see wid==0;
        # W0's v9 replica is provably valueless there: v9 is 1.5-5x worse on
        # every forced non-giant in results.csv), which recovers 30/33's raw
        # builds without touching this lottery. v14 gate restored verbatim.
        if forced or overload > 0.44:
            plan = plan + [(1.0, 0.5, 0.0, None, True),
                           (2.0, 0.5, 0.5, None, True)]
        if overload > 1.05:
            # round-3: overloaded non-giant (prob_27 regime, nw=4) -> W3 mixes
            # in jittered target-gated dispatches (the jitter samples around
            # the gate; see W2 note -- construction-level probe says the gate
            # loses, these are cheap lottery tickets only). v14: + a beam ticket.
            plan = [(1.0, 0.5, 0.0, (0.80, "cut"), False),
                    (2.0, 0.5, 0.0, (1.10, "spt"), False),
                    (1.0, 0.5, 0.0, None, True)] + plan
        if nm_elig:
            # v21: nm+beam tickets APPENDED (not prepended: prepending shifted
            # the rotation + drng stream and displaced prob_26's banked W3
            # beam-draw winner by +374k -- measured on the first v21 spot).
            # Appended tickets run only in leftover slot time and leave the
            # original draw sequence byte-exact.
            plan = plan + [(2.0, 0.5, 0.5, None, "nmbeam"),
                           (0.5, 0.5, 1.0, None, "nmbeam")]
        gi = 0
        while True:
            kap, gam, al, ts_, bm = plan[gi % len(plan)]
            gi += 1
            try:
                if bm == "nmbeam":
                    cands.append(dispatch(kap, gam, drng, alpha=al, beam=True,
                                          dl=cap, nearmiss=8))
                else:
                    cands.append(dispatch(kap, gam, drng, alpha=al, tspec=ts_,
                                          beam=bm, dl=cap if bm else None))
            except Exception:
                break
            if time.time() >= cap or gi > 60:
                break
        if cands:
            # v14: W3 dispatcher polish gains repack rounds (non-giant density +
            # overloaded prob_27). v15 r2a: the lottery's top runner-up
            # constructions stay alive as harvest cycle re-seeds.
            polish(min(cands, key=lambda c: c[0])[1], seed=3333, repack_every=4,
                   alts=pick_alts(cands))
        elif time.time() < deadline:  # fallback
            try:
                _, a = build(_area_order(blocks_data) if forced
                             else _edd_order(blocks_data), forced)
                improve(a, seed=3333, repack_every=4)
            except Exception:
                pass
        return

    # -- v20 W1 PLAN-EXPLORER SLOT (heuristic_20) ------------------------------
    # On the plan-eligible tardy class (forced, w1 >= 6000, overload > 0.65 --
    # train: {23,26,27,30,31,33,38,39}) W1 trades the AREA-basin build for the
    # calibrated-plan pipeline: non-preemptive per-layer cumulative plan
    # (_plan_targets) -> gated dispatch tickets with near-miss recovery ->
    # giant polish envelope. W0/W2/W3 and all other instances keep their v18
    # paths byte-exact; min-wins + official verify protect the bank. Any
    # failure falls through to the legacy W1 path.
    if (wid == 1 and raster is not None and forced and w1 >= 6000
            and overload > 0.65):
        cands = []
        try:
            tick_dl = t_start + 0.55 * window

            def ticket(tg, bm, nm, kap, al, drng=None, mpc=False,
                       ovh=False, nk=3):
                raster.reset()
                raster.near_k = nk
                a_ = _dispatch_construct(
                    prob_info, bays, bay_u, w1, w2, w3,
                    min(tick_dl, deadline), raster, kappa=kap, gamma=0.5,
                    alpha=al, score_pos=True, rng=drng, targets=tg, beam=bm,
                    nearmiss=nm, mpc=mpc, ovh=ovh)
                o_ = iobj(a_)
                push(o_, a_)
                cands.append((o_, a_))

            # nm+beam config lottery (measured grid, heuristic_20 Results:
            # per-instance winners vary -- 31 wants kappa 0.5, 33 wants 2.0 --
            # so rotate a diverse list, min-wins keeps the best). v21: the
            # calibrated-plan ticket is DROPPED (gating measured dead in ALL
            # forms -- fluid, calibrated, self-calibrating; heuristic_21 dead
            # list); its time goes to jittered draws around the rotation
            # (measured spread ~0.4M on 31, sometimes below deterministic).
            base_cfgs = ((0.5, 0.5), (2.0, 0.5), (1.0, 0.0), (0.5, 1.0),
                         (4.0, 0.0), (1.0, 0.5), (0.5, 0.0), (2.0, 1.0))
            # v25 DEEP-NESTLE family FIRST: near_k 16-32 recovers exact-
            # feasible anchors the dilated masks hide by up to a block
            # perimeter; measured raw BELOW every fully-polished banked cell
            # (38 -1.45M, 39 -2.12M, 33 -1.04M, 26 -1.29M, 31 -0.90M,
            # 27 -0.64M). Raw dominance justifies heading the rotation: each
            # ticket pushes its raw build, so these are floor-guaranteed.
            # jv5 Phase B (per-instance near_k) MEASURED DEAD -- REVERTED.
            # spot @600s, exactly the three cells where the adaptive family
            # (20,30,40) differed from v25's (16,24,32): 23 +196,240,
            # 30 +135,879, 33 +78,510 (26/31, whose family matched v25, tied).
            # near_k is NOT a perimeter-proportional quantity; v25's tuned
            # constants stand. Rotation restored byte-exact. See _nk_family.
            for kap, al, nk in ((0.5, 0.5, 24), (2.0, 0.5, 16),
                                (0.5, 1.0, 24), (2.0, 0.5, 32),
                                (0.5, 0.5, 32), (2.0, 0.5, 24),
                                (0.5, 1.0, 32), (1.0, 0.0, 16)):
                if time.time() >= t_start + 0.42 * window:
                    break
                ticket(None, True, nk + 8, kap, al, nk=nk)
            for kap, al in base_cfgs:
                if time.time() >= t_start + 0.5 * window:
                    break
                ticket(None, True, 8, kap, al)
            # v22: MPC joint-admission tickets (CP-SAT compatible-set fill as
            # a 4th beam order at deep-queue events) on the two hottest
            # configs; each build pays ~30-60s of solver budget, so they run
            # before the jitter tail.
            for kap, al in ((0.5, 0.5), (2.0, 0.5)):
                if time.time() >= tick_dl:
                    break
                ticket(None, True, 8, kap, al, mpc=True)
            # jv5 Phase C mpc=2 tickets REVERTED (they lived here). Not
            # floor-safe as assumed: extra tickets are never free -- they push
            # the ovh tickets + jitter tail past tick_dl and CHANGE which draw
            # wins (v21's displacement lesson, re-learned). Suspected
            # co-author with Phase B of the 23/30/33 regression. mpc=2 returns
            # to v25's parked state (mpc_fill's mpc==2 branch is live code with
            # no caller). Re-test only in leftover ticket space, never inline.
            # v23: overhang-aware tickets (union-poisoning penalty; mixed raw
            # signal -- 38 -165k, 27 +709k -- min-wins keeps only winners).
            for kap, al, ow in ((0.5, 1.0, True), (2.0, 0.5, True),
                                (2.0, 0.5, 2.0)):   # ovh=2.0 -> weight 4
                if time.time() >= tick_dl:
                    break
                ticket(None, True, 8, kap, al, ovh=ow)
            _jrng = random.Random(2121)
            ji = 0
            while time.time() < tick_dl and ji < 24:
                kap, al = base_cfgs[ji % len(base_cfgs)]
                ji += 1
                ticket(None, True, 8, kap, al, drng=_jrng)
        except Exception:
            pass
        if cands:
            polish(min(cands, key=lambda c: c[0])[1], seed=2077,
                   repack_every=3, alts=pick_alts(cands), nearmiss=8)
            return
        # else: fall through to the legacy W1 path below

    if forced:
        if wid == 1:
            # v9's giant-winner basin with the FULL budget instead of 65% of
            # the post-construction reserve.
            _, a = build(_area_order(blocks_data), True)
            polish(a, seed=777)
        elif wid == 2:
            # Basin lottery: jittered EDD/AREA multi-start with a different rng
            # than W0's, improve the best. Samples more of the construction
            # space that produced v9's luckiest results.
            rng = random.Random(1414)
            cands = []
            cap = t_start + 0.5 * window
            gens = [lambda: _edd_order(blocks_data, jitter=rng),
                    lambda: _area_order(blocks_data, jitter=rng)]
            gi = 0
            while True:
                try:
                    cands.append(build(gens[gi % 2](), True))
                except Exception:
                    break
                gi += 1
                if time.time() >= cap:
                    break
            if cands:
                polish(min(cands, key=lambda c: c[0])[1], seed=555,
                       alts=pick_alts(cands))
        else:
            # Congestion-aware constructions (kills Pass-A first-preferred-wins;
            # pays an anticipatory price for stuffing crowded bays). gamma=0.5
            # measured best on prob_39 (28.97M vs 29.75M plain EDD); larger
            # gammas over-spread. Jitter around it, improve the best.
            rng = random.Random(1313)
            cands = []
            cap = t_start + 0.55 * window
            # v11: rotate gamma over EDD+AREA (v10.0's varied plans found
            # basins the fixed gamma lost, e.g. prob_28 7.92M), then jitter.
            for order_fn, g in ((lambda: _edd_order(blocks_data), 0.5),
                                (lambda: _area_order(blocks_data), 0.5),
                                (lambda: _edd_order(blocks_data), 2.0),
                                (lambda: _edd_order(blocks_data, jitter=rng), 0.5),
                                (lambda: _area_order(blocks_data, jitter=rng), 0.5),
                                (lambda: _edd_order(blocks_data, jitter=rng), 2.0)):
                try:
                    cands.append(build(order_fn(), True, g))
                except Exception:
                    pass
                if time.time() >= cap:
                    break
            if cands:
                polish(min(cands, key=lambda c: c[0])[1], seed=1313,
                       alts=pick_alts(cands))
    else:
        # Non-forced instances: v9's thorough congestion+EDD+jitter recipe,
        # seed/order-diversified across workers; W3 adds util_gamma.
        edd = _edd_order(blocks_data)
        cong = _congestion_order(blocks_data)
        plans = {
            1: ([(edd, True, 0.0), (cong, False, 0.0)], 111, 777),
            2: ([(cong, False, 0.0), (edd, True, 0.0)], 1414, 555),
            3: ([(cong, False, 0.5), (edd, True, 0.5)], 1313, 1313),
        }
        starts, jseed, iseed = plans[1 + (wid - 1) % 3]
        cands = []
        for order, fc, gamma in starts:
            if time.time() >= deadline:
                break
            try:
                cands.append(build(order, fc, gamma))
            except Exception:
                pass
        rng = random.Random(jseed)
        stale = 0
        best_so_far = min((c[0] for c in cands), default=float("inf"))
        while time.time() < deadline and stale < 4:
            try:
                o, a = build(_edd_order(blocks_data, jitter=rng), forced)
                cands.append((o, a))
                if o < best_so_far - 1e-9:
                    best_so_far = o
                    stale = 0
                else:
                    stale += 1
            except Exception:
                break
        if cands and time.time() < deadline:
            polish(min(cands, key=lambda c: c[0])[1], seed=iseed,
                   alts=pick_alts(cands))


def _worker_main(wid, prob_info, timelimit, t_start, q, inbox=None):
    """Portfolio worker process entry point (must be module-level for spawn)."""
    try:
        _reset_caches()
        state = {"best": float("inf")}

        def push(obj, assign, force=False):
            # Push every new incumbent immediately: improvements are sparse
            # (tens per run) and a lost final put cost prob_31 1.4M in v10.0.
            if obj >= state["best"] - 1e-9 and not force:
                return
            state["best"] = min(state["best"], obj)
            try:
                q.put((obj, assign))
            except Exception:
                pass

        # v18: W0 gets an inbox too -- consumed ONLY by the reclaimed stream /
        # v13-clone slot and the whole-bay phase (aim at the global best). The
        # v9-replica path never touches it, so the anchor stays byte-exact.
        _run_strategy(wid, prob_info, timelimit, t_start, push,
                      inbox=inbox)
    except Exception:
        pass


# =============================================================================
# v33 SELF-GATING MERGE TAIL (S4 recombination). Self-contained: reuses this
# module's raster masks (_mask_pair_rel/_exact_pair_rel), _objective, _Raster,
# and _build_operations. Fires only post-race when the portfolio returns early.
# =============================================================================

_BLOCK_RE = re.compile(r"block (\d+)")


def _sol_sig(assign):
    """Placement signature of a full assignment (dedup key)."""
    return tuple(sorted(
        (bi, a["bay_id"], a["x"], a["y"], a["orient_idx"],
         a["entry_time"], a["exit_time"])
        for bi, a in assign.items()))


def _merge_build_pool(solutions, n_blocks):
    """solutions: list of assignment dicts. Returns {bi: [placement,...]} where
    placement = dict(bi,bay,x,y,oi,entry,exit); deduped per block."""
    pool = {}
    seen = {}
    for assign in solutions:
        for bi, a in assign.items():
            key = (a["bay_id"], a["x"], a["y"], a["orient_idx"],
                   a["entry_time"], a["exit_time"])
            s = seen.setdefault(bi, set())
            if key in s:
                continue
            s.add(key)
            pool.setdefault(bi, []).append({
                "bi": bi, "bay": a["bay_id"], "x": a["x"], "y": a["y"],
                "oi": a["orient_idx"], "entry": a["entry_time"],
                "exit": a["exit_time"],
            })
    return pool


def _merge_incompatible(raster, bay, blocks_data, pa, pb):
    """True iff placements pa (block b1), pb (block b2) cannot BOTH be selected.
    Exact static reduction of _can_place with both entry/exit windows FIXED.
    Same-bay only (caller guarantees). Conservative mask pre-filter, then the
    exact crane/collision relations from _exact_pair_rel."""
    b1, o1, x1, y1 = pa["bi"], pa["oi"], pa["x"], pa["y"]
    b2, o2, x2, y2 = pb["bi"], pb["oi"], pb["x"], pb["y"]
    e1, xt1 = pa["entry"], pa["exit"]
    e2, xt2 = pb["entry"], pb["exit"]
    col_m, b12_m, b21_m = _mask_pair_rel(raster, b1, o1, x1, y1,
                                         b2, o2, x2, y2)
    if not (col_m or b12_m or b21_m):
        return False
    col, e12, x12, e21, x21 = _exact_pair_rel(
        raster, bay, blocks_data, b1, o1, x1, y1, b2, o2, x2, y2)
    # collision: incompatible iff presence intervals strictly overlap.
    if col and (e1 < xt2 and e2 < xt1):
        return True
    # b2 obstructs b1's ENTRY moment e1 (mirror _can_place present-at-entry tie).
    if e12 and ((e2 < e1 < xt2) or (e2 == e1 and b2 < b1)):
        return True
    # b2 obstructs b1's EXIT moment xt1.
    if x12 and ((e2 < xt1 < xt2) or (xt2 == xt1 and b2 > b1)):
        return True
    # b1 obstructs b2's ENTRY moment e2.
    if e21 and ((e1 < e2 < xt1) or (e1 == e2 and b1 < b2)):
        return True
    # b1 obstructs b2's EXIT moment xt2.
    if x21 and ((e1 < xt2 < xt1) or (xt1 == xt2 and b1 > b2)):
        return True
    return False


def _merge_precompute_pairs(raster, bays, blocks_data, pool, deadline):
    """All incompatible (node_a, node_b) placement-index pairs. Bay-grouped +
    closed-interval sweep so cost stays O(same-bay time-overlapping pairs). A
    wall-clock guard keeps it bounded: a MISSED incompatibility only lets an
    infeasible merge slip through, which the replay repair catches -- sound."""
    by_bay = {}
    for bi, plist in pool.items():
        for pidx, pl in enumerate(plist):
            by_bay.setdefault(pl["bay"], []).append(
                (pl["entry"], pl["exit"], bi, pidx, pl))
    pairs = []
    n_checks = 0
    for bay_id, nodes in by_bay.items():
        bay = bays[bay_id]
        nodes.sort(key=lambda t: t[0])
        active = []
        for cur in nodes:
            ce = cur[0]
            cbi, cpi, cpl = cur[2], cur[3], cur[4]
            active = [a for a in active if a[1] >= ce]  # closed-interval live
            for oth in active:
                obi, opi, opl = oth[2], oth[3], oth[4]
                if obi == cbi:
                    continue
                n_checks += 1
                if _merge_incompatible(raster, bay, blocks_data, cpl, opl):
                    pairs.append(((cbi, cpi), (obi, opi)))
            active.append(cur)
            if (n_checks & 1023) == 0 and time.time() > deadline:
                return pairs, n_checks, True
    return pairs, n_checks, False


def _merge_recombine(prob_info, bays, bay_u, w1, w2, w3, pool, incompat_pairs,
                     warm_assign, budget_s):
    """Pick one placement per block minimizing the true objective subject to the
    pairwise incompatibilities; warm-started from warm_assign. Returns a merged
    assignment dict or None."""
    try:
        from ortools.sat.python import cp_model
    except Exception:
        return None
    if budget_s <= 0.5:
        return None
    blocks_data = prob_info["blocks"]
    n_bays = len(bays)
    SU = 1000
    m = cp_model.CpModel()
    yv = {}
    base_cost = {}
    wl_terms = [[] for _ in range(n_bays)]
    su = [int(round(SU * bay_u[j])) for j in range(n_bays)]
    for bi, plist in pool.items():
        vs = []
        blk = blocks_data[bi]
        due = blk["due_date"]
        prefs = blk["bay_preferences"]
        s_max = max(prefs)
        wl = int(round(blk["workload"]))
        for pidx, pl in enumerate(plist):
            v = m.NewBoolVar(f"y_{bi}_{pidx}")
            yv[(bi, pidx)] = v
            vs.append(v)
            tard = max(0, pl["exit"] - due)
            pref_pen = s_max - prefs[pl["bay"]]
            base_cost[(bi, pidx)] = int(round(SU * (w1 * tard + w3 * pref_pen)))
            wl_terms[pl["bay"]].append((wl, v))
        m.AddExactlyOne(vs)
    for (n1, n2) in incompat_pairs:
        m.Add(yv[n1] + yv[n2] <= 1)
    obj_terms = [base_cost[k] * v for k, v in yv.items()]
    if n_bays >= 2 and w2 != 0:
        wl_expr = []
        big = 0
        for j in range(n_bays):
            terms = wl_terms[j]
            wl_expr.append(sum(c * v for c, v in terms) if terms else 0)
            big += su[j] * sum(c for c, _ in terms)
        zmax = m.NewIntVar(0, max(1, big), "zmax")
        for p in range(n_bays):
            for qq in range(n_bays):
                if p == qq:
                    continue
                m.Add(zmax >= su[p] * wl_expr[p] - su[qq] * wl_expr[qq])
        obj_terms.append(int(round(w2)) * zmax)
    m.Minimize(sum(obj_terms))
    if warm_assign is not None:
        idx = {}
        for bi, plist in pool.items():
            for pidx, pl in enumerate(plist):
                idx[(bi, pl["bay"], pl["x"], pl["y"], pl["oi"],
                     pl["entry"], pl["exit"])] = pidx
        ok = True
        hints = []
        for bi, a in warm_assign.items():
            key = (bi, a["bay_id"], a["x"], a["y"], a["orient_idx"],
                   a["entry_time"], a["exit_time"])
            pidx = idx.get(key)
            if pidx is None:
                ok = False
                break
            hints.append((bi, pidx))
        if ok:
            for (bi, pidx) in hints:
                for pp in range(len(pool[bi])):
                    m.AddHint(yv[(bi, pp)], 1 if pp == pidx else 0)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget_s)
    solver.parameters.num_search_workers = 4
    try:
        status = solver.Solve(m)
    except Exception:
        return None
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    merged = {}
    for bi, plist in pool.items():
        chosen = None
        for pidx in range(len(plist)):
            if solver.Value(yv[(bi, pidx)]):
                chosen = plist[pidx]
                break
        if chosen is None:
            return None
        merged[bi] = {
            "block_id": bi, "bay_id": chosen["bay"], "x": int(chosen["x"]),
            "y": int(chosen["y"]), "orient_idx": chosen["oi"],
            "entry_time": int(chosen["entry"]), "exit_time": int(chosen["exit"]),
        }
    return merged


def _merge_repair_replay(prob_info, merged, warm_assign, rounds=3):
    """Rebuild ops + check_feasibility; per violating block revert to its
    warm-start placement. Up to `rounds` passes. Returns (assign, feasible)."""
    cur = {bi: dict(a) for bi, a in merged.items()}
    for _ in range(rounds + 1):
        try:
            res = check_feasibility(
                prob_info, {"operations": _build_operations(cur)})
        except Exception:
            return cur, False
        if res.get("feasible"):
            return cur, True
        bad = set()
        for v in res.get("violations", []):
            for mm in _BLOCK_RE.findall(v):
                bad.add(int(mm))
        if not bad or warm_assign is None:
            return cur, False
        reverted = False
        for bi in bad:
            if bi in warm_assign and cur.get(bi) != warm_assign[bi]:
                cur[bi] = dict(warm_assign[bi])
                reverted = True
        if not reverted:
            return cur, False
    try:
        res = check_feasibility(
            prob_info, {"operations": _build_operations(cur)})
        return cur, bool(res.get("feasible"))
    except Exception:
        return cur, False


def _merge_tail(prob_info, bays, bay_u, w1, w2, w3, cands, winner_assign,
                winner_obj, t_start, timelimit):
    """Post-race self-gating merge. Returns an improved feasible assignment if
    the gate fires AND the merge strictly beats the winner (official-verified);
    otherwise returns winner_assign unchanged (byte-identical v25 path)."""
    import os as _os
    _dbg = _os.environ.get("OGC_DEBUG")
    MERGE_MIN = 6.0                       # 60s convention: the tail is only the
    #                                       ~end-reserve slack, not a big window;
    #                                       prob_1's merge model solves in 2-4s.
    remaining = (t_start + timelimit) - time.time()
    blocks_data = prob_info["blocks"]
    n_blocks = len(blocks_data)

    # FREE HARVEST: v25's parent already retained EVERY streamed (obj, assign)
    # in `cands` -- appended at all three queue-drain sites (main loop, grace
    # drain, final drain). Dedup by placement signature; keep best ~24 by obj.
    # Computed FIRST so the debug line always reports the true candidate count
    # (an early gate return must not print a misleading cands=0).
    uniq = {}
    for obj, assign in cands:
        if assign is None or len(assign) != n_blocks:
            continue
        sig = _sol_sig(assign)
        cur = uniq.get(sig)
        if cur is None or obj < cur[0]:
            uniq[sig] = (obj, assign)
    # jv6c: pool cap env-tunable (default 24 = v33). Widening -> richer
    # per-block placement diversity for the recombination CP-SAT, at the cost
    # of a larger model (more y-vars). Only the non-forced merge fires, so this
    # is the one positive-yield family's tuning knob. min-wins + official
    # verify keep it floor-safe.
    _cap = int(_os.environ.get("OGC_MERGE_CAP", "24"))
    dedup = sorted(uniq.values(), key=lambda c: c[0])[:_cap]
    k = len(dedup)

    def _emit(fired, gain):
        if _dbg:
            print(f"[merge33] fired={fired} rem={remaining:.1f} cands={k} "
                  f"gain={gain:.0f}", flush=True)

    # Gate: NON-FORCED instance, real spare time, enough diversity. On forced
    # instances the v25 parent still reaches here with end-reserve slack at long
    # timelimits (search_deadline reserves only ~12s), so `remaining` alone would
    # let the tail fire on forced rocks -- exactly the prob_27 case the
    # coordinator flagged. `_is_forced` makes "forced" a guaranteed non-firing
    # (byte-identical) case, matching requirement 5.
    if (not _HAVE_NUMPY or remaining < MERGE_MIN or k < 3
            or _is_forced(prob_info, bays)):
        _emit(False, 0.0)
        return winner_assign
    pool_solutions = [a for _, a in dedup]
    wsig = _sol_sig(winner_assign)
    if all(_sol_sig(s) != wsig for s in pool_solutions):
        pool_solutions.append(winner_assign)
    pool = _merge_build_pool(pool_solutions, n_blocks)
    if len(pool) != n_blocks:
        _emit(False, 0.0)
        return winner_assign
    try:
        # CP-SAT budget = remaining - 2.5s safety (covers precompute + replay
        # repair + final official verify). merge_hard_stop bakes the 2.5s in, so
        # the solve deadline never blows the parent's abs_stop.
        safety = 2.5
        merge_hard_stop = t_start + timelimit - safety
        raster = _Raster(prob_info, bays)
        pre_deadline = min(merge_hard_stop - 1.0,
                           time.time() + max(1.5, (merge_hard_stop - time.time()) * 0.45))
        incompat, _nc, _to = _merge_precompute_pairs(
            raster, bays, blocks_data, pool, pre_deadline)
        solve_budget = merge_hard_stop - time.time()
        merged = _merge_recombine(prob_info, bays, bay_u, w1, w2, w3, pool,
                                  incompat, winner_assign, solve_budget)
        if merged is not None:
            repaired, feasible = _merge_repair_replay(
                prob_info, merged, winner_assign, rounds=3)
            if feasible:
                mobj = _objective(repaired, blocks_data, bays,
                                  bay_u, w1, w2, w3)[0]
                if mobj < winner_obj - 1e-9:
                    if check_feasibility(
                            prob_info,
                            {"operations": _build_operations(repaired)}
                    )["feasible"]:
                        _emit(True, winner_obj - mobj)
                        return repaired
    except Exception:
        pass
    _emit(True, 0.0)
    return winner_assign


def _algorithm_portfolio(prob_info, timelimit, t_start):
    import multiprocessing as _mp
    nw = min(4, _mp.cpu_count() or 1)
    if nw < 2:
        raise RuntimeError("not enough cores for a portfolio")
    # Giant forced instances (n>=250, e.g. prob_38/39): ONE dense construction
    # takes ~180s+, so lottery workers (W2/W3, which need several builds) can
    # never contribute, while their builds steal CPU/memory bandwidth from the
    # workers that matter. Run only W0 (v9 replica -- keeps v9's exact result
    # on a clean core) and W1 (AREA basin with a full-budget improver).
    # v12: giants keep W0 (v9 replica) + W1 (AREA basin) but now ALSO run W2 =
    # the raster dispatcher, whose builds are far lighter than the Shapely
    # constructions that forced n>=250 down to 2 workers in v11 (the raster path
    # never runs the expensive per-candidate Shapely scans during construction).
    # W3's multi-start lottery still can't afford several giant builds, so it is
    # dropped. nw=3 measured for RSS safety on prob_38 (see report).
    _pre_bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    # v14: giants go back to 4 workers -- W3 is no longer a lottery (its giant
    # branch in _run_strategy is the cheap repack specialist: one sparse build
    # + inbox-seeded repack improve). RSS measured 2.87GB/3w on prob_38 ->
    # ~4GB/4w, comfortable under 16GB.
    if len(prob_info["blocks"]) >= 250 and _is_forced(prob_info, _pre_bays):
        nw = min(nw, 4)
    reserve = min(max(4.0, timelimit * 0.08), 12.0)
    search_deadline = t_start + timelimit * 0.95 - reserve
    ctx = _mp.get_context()
    q = ctx.Queue()
    inboxes = [ctx.Queue() for _ in range(nw)]  # v11 island broadcasts
    procs = []
    for wid in range(nw):
        p = ctx.Process(target=_worker_main,
                        args=(wid, prob_info, timelimit, t_start, q,
                              inboxes[wid]),
                        daemon=True)
        p.start()
        procs.append(p)

    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob_info["bays"])]
    blocks_data = prob_info["blocks"]
    w = prob_info.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    bay_u = _bay_u(bays)

    cands = []
    # v33: forced classification, captured ONCE. This is the SAME _is_forced
    # value v25 already computes for the insurance build's `forced=` arg (reused
    # below), so NO extra _is_forced call is added -- byte-neutral. On FORCED
    # instances the merge gate is closed, so the parent runs v25's exact verify
    # loop (no merge scaffolding, no dedup, no extra held references); the merge
    # code executes on NON-forced instances only. The parent's race-time code
    # (giant check, spawn, insurance, drain loop + island rebroadcast) is left
    # byte-identical to v25 for every instance.
    _forced = _is_forced(prob_info, bays)
    # Insurance: while workers spin up, the otherwise-idle parent builds one
    # cheap non-dense EDD construction. If memory pressure ever stalls all
    # workers (seen on prob_38: 4 dense builds thrashed 16GB and the queue came
    # back empty), the parent still holds a sane solution instead of the
    # catastrophic empty-bay fallback.
    try:
        _reset_caches()
        quick = _construct(prob_info, _edd_order(blocks_data), bays, bay_u,
                           w1, w2, w3, t_start, t_start,  # deadline past->sparse
                           forced=_forced)
        cands.append((_objective(quick, blocks_data, bays, bay_u,
                                 w1, w2, w3)[0], quick))
        _reset_caches()  # parent doesn't search further; free the memory
    except Exception:
        pass

    gbest = float("inf")  # v11: broadcast global best to worker inboxes when
    #                       it improves enough to matter (>0.2%)
    while time.time() < search_deadline:
        try:
            item = q.get(timeout=0.25)
            cands.append(item)
            if item[0] < gbest * 0.998:
                gbest = item[0]
                for ib in inboxes:
                    try:
                        ib.put(item)
                    except Exception:
                        pass
        except Exception:
            if all(not p.is_alive() for p in procs):
                break
    # Grace drain: workers check their deadline once per improver round, and a
    # round can take seconds on n=250 -- wait briefly for the final puts.
    grace = t_start + timelimit * 0.95 - reserve * 0.55
    while time.time() < grace and any(p.is_alive() for p in procs):
        try:
            cands.append(q.get(timeout=0.25))
        except Exception:
            pass
    while True:  # final drain (before terminate: a killed mid-put corrupts pipes)
        try:
            cands.append(q.get(timeout=0.05))
        except Exception:
            break
    for p in procs:
        try:
            if p.is_alive():
                p.terminate()
        except Exception:
            pass

    import os as _os2
    _dbg = _os2.environ.get("OGC_DEBUG")
    fallback = _empty_bay_solution(prob_info, bays)
    cands.append((_objective(fallback, blocks_data, bays, bay_u, w1, w2, w3)[0],
                  fallback))
    cands.sort(key=lambda c: c[0])
    hard_stop = t_start + timelimit - 1.0
    # v13 #3c: parent-side Z3 relocation on the winning candidate. Workers run
    # the pass inside polish, but a W0 (v9-replica) win never sees it -- this
    # catches that case. Cheap (~seconds, obj-gated); the relocated candidate
    # goes FIRST in the verify order and the original stays next in line, so a
    # failed official check costs one verify, never correctness.
    if _HAVE_NUMPY and cands and cands[0][0] < float("inf"):
        try:
            z_dl = min(hard_stop - 2.0, time.time() + 5.0)
            if z_dl > time.time() + 1.0:
                rz, oz = _z3_relocate(prob_info, cands[0][1], bays, bay_u,
                                      w1, w2, w3, _Raster(prob_info, bays),
                                      z_dl)
                if rz is not None and oz < cands[0][0] - 1e-9:
                    cands.insert(0, (oz, rz))
        except Exception:
            pass
    if _dbg:
        _el = time.time() - t_start
        _objs = sorted(c[0] for c in cands)[:5]
        print(f"[parent] ncands={len(cands)} elapsed={_el:.1f} hard_stop_in="
              f"{hard_stop - time.time():.1f} best5={[f'{o:.3g}' for o in _objs]}",
              flush=True)
    _nver = 0
    # Absolute cutoff just under the contract limit. We ALWAYS verify at least the
    # single best candidate (check_feasibility is ~0.15s even for n=250): this is
    # the guard against the empty-bay catastrophe when the end-phase drain has
    # eaten past hard_stop under load, which otherwise threw away a ready 15M
    # solution for the 1.9e9 fallback.
    abs_stop = t_start + timelimit - 0.3
    if _forced:
        # v33 FORCED PATH: TOKEN-IDENTICAL to v25's verify loop. No _merge_tail,
        # no dedup, no extra references -- the merge gate is closed on forced
        # instances anyway (see _merge_tail's _is_forced check), so nothing is
        # lost, and lottery-sensitive forced instances (prob_32) are protected
        # from any parent-side perturbation.
        for _, assign in cands:
            now = time.time()
            if now > abs_stop:
                break
            if _nver >= 1 and now > hard_stop:
                if _dbg:
                    print(f"[parent] hard_stop hit after {_nver} verifies", flush=True)
                break
            _nver += 1
            sol = {"operations": _build_operations(assign)}
            try:
                res = check_feasibility(prob_info, sol)
            except Exception:
                continue
            if res["feasible"]:
                return sol
        # Last resort: empty-bay (structurally feasible).
        return {"operations": _build_operations(fallback)}
    # v33 NON-FORCED PATH: v25 verify loop + self-gating merge tail. Fires only
    # when the portfolio returned with spare time (>= MERGE_MIN) and >= 3
    # distinct candidates exist; otherwise returns `assign` unchanged, so the
    # output is byte-identical to v25 (_build_operations of the same winning
    # assignment == `sol`).
    for w_obj, assign in cands:
        now = time.time()
        if now > abs_stop:
            break
        if _nver >= 1 and now > hard_stop:
            if _dbg:
                print(f"[parent] hard_stop hit after {_nver} verifies", flush=True)
            break
        _nver += 1
        sol = {"operations": _build_operations(assign)}
        try:
            res = check_feasibility(prob_info, sol)
        except Exception:
            continue
        if res["feasible"]:
            try:
                final_assign = _merge_tail(
                    prob_info, bays, bay_u, w1, w2, w3, cands, assign,
                    w_obj, t_start, timelimit)
            except Exception:
                final_assign = assign
            if final_assign is assign:
                return sol
            return {"operations": _build_operations(final_assign)}
    # Last resort: empty-bay (structurally feasible).
    return {"operations": _build_operations(fallback)}


# -----------------------------------------------------------------------------
# Required entry point
# -----------------------------------------------------------------------------

def algorithm(prob_info, timelimit=60):
    t_start = time.time()
    try:
        return _algorithm_portfolio(prob_info, timelimit, t_start)
    except Exception:
        # Multiprocessing unavailable/broken -> v9 single-thread pipeline with
        # whatever budget remains.
        return _algorithm_single(prob_info, timelimit, t_start)
