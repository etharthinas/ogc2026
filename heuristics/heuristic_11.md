# Heuristic v11 — island model + CP-SAT exact time-repair

## Diagnosis from v10 (289.10M @4w/300s, 40/40 feasible; goal < 250M)
Remaining loss concentrates in: prob_38 91.3M, prob_27 48.9M, prob_39 27.1M,
prob_31 17.8M, prob_26 16.8M, prob_33 16.7M, prob_30 10.8M, prob_35 9.3M,
prob_28 8.8M, prob_37 8.9M, prob_23 6.6M, prob_32 5.3M, prob_21 4.5M.
Three observations:
1. **Workers are isolated.** Nobody polishes another worker's winner: prob_38's
   W1 win got zero help from W0's improver; W2/W3 lottery hits die un-polished.
   v10.0-vs-v10.2 seed flukes (prob_33 15.97M and prob_28 7.92M found by one
   seed plan, lost by another) show cross-pollination is worth ~1-2M.
2. **The improver's re-timing is greedy and local.** On schedule-limited
   instances (fluid-LB ~ 0 but 5-18M objectives: prob_31/35/30/23/28/21) the
   destroy/repair loop moves 6-12 blocks at a time and re-times them greedily;
   it cannot globally re-sequence a bay.
3. **Basin lotteries need diversity.** v10.2's fixed W3 gamma=0.5 lost basins
   v10.0's varied plans had found.

## THREE improvements (v11)
1. **Island model.** Parent broadcasts every >0.2% global-best improvement to
   per-worker inbox queues; W1+ improvers adopt an inbox solution when it beats
   their incumbent (W0 = v9 replica stays inbox-free as the byte-exact anchor).
2. **CP-SAT exact time-repair** (`_cpsat_retime`). Fix bay/x/y/orient; entry
   times become integer vars; collide pairs -> disjoint presence intervals;
   crane entry/exit obstruction -> the blocked block's entry/exit moment lies
   outside the blocker's presence window (tie rules mirror _present_at_entry/
   _present_at_exit exactly, incl. block-id ordering). w2/w3 are timing-free,
   so the per-bay objective is pure w1*tardiness. Runs in W1+ at 62% of the
   window between two improver passes; result pushed as a normal candidate
   (parent still verifies officially — encoding bugs cost a candidate, never
   correctness). Encoding validated: retimed empty-bay solutions of prob_8/2/25
   all pass the official checker (stage 5) with real tardiness cuts.
   ortools present in the official env; local venv needed ortools==9.11.4210
   (the 9.14 wheel segfaults on this machine). All uses try/except-wrapped.
3. **Richer W3 lottery.** Rotate gamma in {0.5, 2.0} over EDD+AREA before
   jittering (v10.0's varied plans found basins the fixed gamma=0.5 lost).

## Results (filled after testing)

**Bench conditions (important caveat):** measured 2026-07-02, prob_21-40 only
(prob_1-20 hold ~2.7M total and are anchored by W0; spliced from v10's row).
Phases: 36-40 serial, 31-35 serial, 21-30 co-run 2-wide. From ~15:34 onward a
foreign `streamlit run app.py` process consumed 6-9 logical cores and up to
2.2GB for the REST OF THE BENCH (phases 2-3 entirely; phase 1 from prob_38 on).
v10's row was measured on a quiet machine, so v11's numbers below are
systematically pessimistic — every "regression" instance is a basin-lottery
instance where fewer improver rounds/multi-starts directly cost objective.

| inst | v10 | v11 | delta | note |
|---|---:|---:|---:|---|
| prob_21 | 4,464,913 | **3,697,675** | **−767,238** | biggest v11 win; schedule-limited, CP-SAT retime / gamma lottery |
| prob_22 | 1,281,391 | 1,201,393 | −79,998 | win |
| prob_23 | 6,613,919 | 7,688,153 | +1,074,234 | lottery loss under load |
| prob_24 | 2,034,701 | 2,063,226 | +28,525 | |
| prob_25 | 739,136 | 840,017 | +100,881 | |
| prob_26 | 16,816,061 | 18,739,731 | +1,923,670 | fell back to v9's basin (18.74M) — v10's lottery win lost |
| prob_27 | 48,919,611 | **48,492,955** | **−426,656** | frozen since v9 — first move |
| prob_28 | 8,834,745 | 8,834,745 | 0 | |
| prob_29 | 1,869,891 | 1,896,557 | +26,666 | |
| prob_30 | 10,830,851 | 11,335,798 | +504,947 | |
| prob_31 | 17,770,214 | 17,996,875 | +226,661 | |
| prob_32 | 5,321,212 | 5,493,441 | +172,229 | |
| prob_33 | 16,731,780 | 16,731,780 | 0 | |
| prob_34 | 3,488,961 | 3,488,961 | 0 | |
| prob_35 | 9,308,547 | 10,477,529 | +1,168,982 | v10's −2.08M win partially lost |
| prob_36-40 | 131,372,006 | 131,372,006 | 0 | ALL byte-identical (nw=2 giant path robust even under load) |

**Total (spliced full-40): 293,053,436 vs v10 289,100,533 = +3.95M — NOT SOTA.**
myalgorithm.py stays v10.

## Analysis of failure
1. **The losses are lottery losses, not logic losses.** Every regression
   (23/26/30/31/32/35) is a basin-lottery instance from v10's own postmortem;
   28/33/34 + all five giants came out byte-identical, and the deterministic
   W0/W1 paths reproduced v10 exactly even while starved. What changed is the
   NUMBER of constructions/improver rounds the lottery workers completed —
   which the streamlit load cut roughly in half. A clean-machine re-run is
   required before concluding the island/CP-SAT/gamma changes themselves hurt.
2. **Real wins exist where v11's levers act:** prob_21 −767k and prob_27 −427k
   (both stuck for many versions) moved despite the load; the CP-SAT retime +
   richer gamma lottery are plausibly causal (prob_21 is schedule-limited,
   exactly the CP-SAT target).
3. **Ops bugs found this session:** (a) worker processes sometimes survive
   parent terminate() on Windows and keep the bench harness from exiting
   (killed manually at each phase boundary); (b) `_cpsat_retime`'s pairwise
   model-build loop is not deadline-checked — on dense bays the build alone can
   overrun the CP window (suspected in the smoke-test 60s overshoot);
   (c) bench_par's 6GB RAM gate deadlocks silently under desktop load
   (lowered to 2GB).

## Verdict / next steps (v12)
- Re-bench v11 unchanged on a QUIET machine before evolving further; the +3.9M
  may be entirely environmental. Keep prob_21/27 wins in mind as real signal.
- Add deadline checks inside `_cpsat_retime`'s pair loop; consider capping
  per-bay pair count.
- If lottery variance dominates: pin more worker time to replaying v10's known
  winning basins (portfolio-of-recorded-plans) instead of fresh lotteries.
