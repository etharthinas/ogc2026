# Heuristic v26 — near_k depth into the DEEP-polish pipelines (goal < 112,500,000; v25 = 124,581,895)

Departure: v25 (baseline/myalgorithm.py, commit c407ac1). Remaining ask: −12.08M
(goal re-set 2026-07-15 from <115M to <112.5M).
Mass is two giants: prob_38 = 36,351,493 (obj1≈2965 vs relax@0.7 target 1219,
~16M floor → ~20M headroom) and prob_27 = 24,972,962 (obj1 1899 vs 615). The
other 18 instances sum to 63.3M and are largely converged.

## What v25 established

The DEEP-NESTLE near_k family (raster `near_k` ∈ {16,24,32}, nearmiss = nk+8)
recovers exact-feasible anchors the conservative dilated masks hide by up to a
block perimeter (~40 cells on 38-class blocks). Wired ONLY in the **W1 explorer
rotation** (myalgorithm.py:5004-5016), whose polish is the *shallow* `polish()`
envelope. It bought −10.80M in one rung (38 −5.29M, 39 −1.86M, 31 −0.91M,
27 −0.67M, 33 −0.64M, 26 −0.61M, 23 −0.43M, 30 −0.36M).

The **W0-reclaimed deep pipeline** (myalgorithm.py:4640-4695) and the W3-giant
specialist still build at near_k=3 / nearmiss=8, yet they own the *deepest*
polish (improve → whole_bay exact-pack → xbay improve → Z3 relocation, full
window). On the reclaimed set {27,38,39}, prob_27's deep winner comes ONLY from
this stream's build2 (the v23 MPC variant, source of 27 −1.52M); 38/39 also run
here AND in W1. **Gap: no near_k build ever reaches the deep polish.**

## Improvement A — near_k build1 in the W0-reclaimed deep pipeline (primary)

Replace the reclaimed stream's build1 (plain nm+beam, near_k=3) with a
near_k=32 nm+beam build (nearmiss=40). Keep build2 EXACTLY as v25 (MPC,
near_k=3) at its 0.38w deadline, and the 2-build / 0.22w-0.38w pacing verbatim
(v24 law: never re-pace a winning deep pipeline). Take raw-min → deep polish
unchanged. Safety: 38/39 are floor-protected by the UNCHANGED W1 explorer
(their near_k shallow builds still bank); 27's mpc build2 is byte-identical, so
27 can only move if the near_k raw beats mpc raw (measured in spot). Expect the
deep polish to compound the near_k basin beyond W1's shallow envelope on 38/39.
Spot {38,27,39}. Kill: all three ≥ −100k after an nk sweep {24,32,40}.

## Improvement B — near_k in the W3-giant specialist deep pipeline

The W3 giant repack-specialist (nw=3 giants) builds near_k=3. Give it a near_k
build variant (min-wins ticket, no re-pace). Diversifies the deep-polish basin
for 38 specifically (its co-residency with 27 is extreme). Spot {38}. Only
pursue if A moves 38 but leaves headroom.

## Improvement C — deeper near_k (40-48) + per-instance nk adaptation

38-class blocks have 40+ cell perimeters; nk=32 may still clip the deepest
nestle. Sweep nk ∈ {40,48} as W1 tickets and in the reclaimed build1; adapt nk
to the instance's median block perimeter. Cheap: one more ticket each. Spot
{38}. Kill if nk>32 is flat vs 32.

## Ladder (revised 2026-07-15 after 26a failure)

- 26a = A (near_k=32 build1 replacing W0-reclaimed build1). **DONE — FAILED, see Results.**
- 26b = B refined: REVERT A (W0-reclaimed byte-exact = v25); W3-giant specialist's
  FIRST seed build becomes near_k=32/nearmiss=40 (the ovh second seed stays
  byte-exact). W3's improve is obj-gated and mostly repacks the inbox leader, so
  worst case it contributes nothing — the true floor-safe home for a deep-ish
  near_k basin (repack_every=2 + xbay). Spot {38,39}. Kill: both ≥ −100k.
- 26c = W1 rotation APPEND (after the ovh ticket group, before the jitter tail —
  never prepend): (i) two mpc×near_k tickets (mpc=True, nk=32, kappa∈{0.5,2.0}) —
  the untried combination; MPC's CP-SAT compatible-set fill has only ever seen
  near_k=3 candidate menus, and prob_27's winner is an MPC build; (ii) two deeper
  plain tickets nk∈{48,64} (Improvement C — 38-class perimeters may exceed 32).
  Spot {38,27}. Kill: all four tickets flat on both.
- 26d = EJECTION-CHAIN ADMISSION (new mechanism family): during the near-miss
  scan, for anchors blocked by ≤2 resident blocks, test exact single-depth
  relocation of each blocker to its own exact-feasible anchor in the same
  bay/layer (_can_place-gated both moves, obj-gated accept). near_k recovers
  dilation loss; this recovers FRAGMENTATION loss (the residual 0.05–0.15 of
  bay area in the admission loss stack). Wire as one W1 ticket first. Spot
  {38,27}. Kill: flat on both after a blocker-count sweep {1,2}.
- Full-40 row after whichever rungs land. Protect every rung: {prob_1 @60s byte,
  prob_26 byte}.

## Results

**26a (2026-07-14/15): FAILED — reverted.** Spot {38,27,39} @600s
(baseline/v26a_spot.log): 27 = 24,972,962 byte-flat (MPC build2 still won
raw-min even vs the near_k=32 build1 raw); 39 = 8,389,519 byte-flat (winner
lives outside this stream); **38 = 38,241,510 = +1,890,017 REGRESSION** vs the
banked 36,351,493. Diagnosis: on the n≥250 giant the near_k=32 scan is ~10x
costlier per admission event, so build1 truncated at its 0.22w deadline AND the
raw-min fed the deep polish a different (raw-better, polish-worse) basin —
v25's 38 winner was this stream's own deep polish of the v25 raw-min, and
replacing the build input displaced it. The v24 law replayed exactly: never
swap/re-pace a winning deep pipeline's build phase; feed near_k diversity to
deep polish only through streams that are obj-gated/min-wins-protected (W3
specialist, appended W1 tickets).

**26b (2026-07-15): NEUTRAL — kept (floor-safe).** 26a reverted first
(W0-reclaimed verified code-identical to v25 via git diff, comment-only
deltas); W3 giant specialist's first seed build made near_k=32/nearmiss=40
(ovh second seed byte-exact, near_k restored after and in the except path).
Spot {38,39} @600s (baseline/v26b_spot.log): 38 = 36,351,493 byte-flat,
39 = 8,389,519 byte-flat. Diagnosis: the min-wins design worked exactly as
intended — the near_k seed's obj-gated improve never beat the inbox leader
on either giant, so the specialist contributed nothing and displaced
nothing. The W3 specialist's polish basin is apparently already dominated
by the inbox leader it repacks; a different *seed* can't reach past the
leader-repack pathway. Kept per floor-safe rule (worst case zero cost to
the lottery, and byte-flat reproduction confirms zero displacement).

**26c (2026-07-15): FAILED — reverted (kill criterion met).** Four tickets
appended to the W1 explorer rotation after the v23 ovh group, before the
jitter tail (mpc×near_k=32 at kappa {0.5, 2.0}; plain nk=48/nm=56 and
nk=64/nm=72), tick_dl-gated like their neighbors. Spot {38,27} @600s twice:
- First spot (baseline/v26c_spot.log) had an EDIT BUG: `raster.near_k`
  could be left at 32-64 when tick_dl expired mid-group, leaking into
  polish's near-miss scans. 38 = 38,219,282 (+1,867,789), 27 = 24,972,962
  byte-flat.
- Leak fixed with a byte-neutral save/restore around the group (a blanket
  reset-to-3 is NOT v25-byte-compatible: a family build can run to tick_dl
  and skip every later group, so v25's polish legitimately sees nk 16-32).
  Fixed re-spot (baseline/v26c_spot2.log): **38 = 38,241,510 = +1,890,017
  REGRESSION**, 27 = 24,972,962 byte-flat. Kill criterion (flat/regressed
  on both) met → all four tickets AND the guard reverted; W1 byte-exact v25.

Diagnosis — the decisive observation: the fixed 26c's prob_38 output is
byte-identical to the failed 26a spot (38,241,510, obj1=2698 obj2=538
obj3=7560), though the two perturbations touch different code (26a swapped
the W0-reclaimed build1; 26c only appended time-consuming W1 tickets ahead
of the jitter tail). Two independent perturbations collapsing to the same
fallback value means prob_38's banked 36,351,493 winner is a CROSS-WORKER
COUPLING: W1's rotation pushes a near_k build into the island inbox at a
specific time, and W0-reclaimed's deep polish drains it; perturbing EITHER
side of the handoff — even append-only time consumption after all v25
tickets — loses the coupled winner and both regress to the same secondary
basin. NEW LAW: the W1 ticket list AND the W0-reclaimed pacing are both
FROZEN for 38; basin diversity must come from outside this coupling
(26d ejection-chain, or a new worker slot that never touches W1/W0 timing).

## v26 outcome (2026-07-15)

**Fully neutral.** Surviving delta vs v25: only the 26b W3-giant first-seed
near_k=32/nearmiss=40 change (measured byte-flat on {38,39}; floor-safe by
min-wins). 26a and 26c reverted. Outputs are byte-identical to v25 on every
measured cell: 38/39 (26b spot), 27/38 (26c spots, flat cells), and the
protect check prob_1 @60s = 18,357 exact (baseline/v26_protect1.log).
myalgorithm.py stays v25; results.csv gets a flat v26 row in the v24 style
(== v25 cells) for ladder bookkeeping; total unchanged at 124,581,895.
Remaining route to <112.5M: 26d ejection-chain admission (outside the
W1↔W0 coupling), or an entirely new stream for 38's ~20M headroom.
