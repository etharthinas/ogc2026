# heuristic_40 — Budget-scaled search + merge-on-forced (v40)

## Context (2026-07-21)

v39 (cross-fork merge, heuristic_39.md) banked a full same-day mac row of **123,229,003**
@900s. Goal <115M needs −8.2M more; the mass is prob_38 (38.1M), prob_27 (24.1M) and the
7-8M band. The contest permits time limits up to ~30 min, and rows have always recorded
their own budget — so budget is a legitimate axis.

## 1800s scaling probes (this mac, serial, caffeinated)

| run | prob_38 | prob_27 |
|---|---|---|
| jv9 @900 (control) | 38,206,026 | 24,074,569 |
| jv9 @1800 (uncapped search ~1700s) | **36,335,881 (−1,870,145)** | **23,560,982 (−513,587)** |
| v39 @1800 (search capped 600s + ~1200s tails) | 38,126,028 in 627s — tails won ~nothing, 1170s wasted | (measuring) |

Two facts: (a) **search compute-scaling is alive and huge on giants** — doubling budget
buys −1.87M on prob_38; (b) the v36-era flat 600s search cap, correct at 900s (tails cost
zero search and won −65k), is **catastrophic at 1800s**. Also: this mac @1800s ≈ the
Windows box @900s on prob_38 (36.34M vs banked 36.32M) — the mac is ~half-speed, which
explains the v39-row drift on giants.

## Three ideas

### 40a — Budget-scaled search cap (implemented)

`port_limit = timelimit` for TL<=600, else `max(600, timelimit - 300)`: search keeps
everything beyond a flat 300s tail window. At TL<=900 byte-identical pacing to v39; at
1800s search gets 1500s. Risk: v40 has ~200s less search than raw jv9 at 1800 — bounded,
tails are min-wins.

### 40b — Merge-on-forced (implemented; 39b carried over)

`_merge_tail(allow_forced=True)` on the forced-race champion, only when `_overflow`,
capped at half the remaining tail window, official-checker min-wins, before tail35/t37.
Rationale: jv8/9 giant replica workers give the forced pool real diversity (14-19 cands
observed) that the recombine CP-SAT was designed for.

### 40c — Second seeded race (reserve)

Unchanged from heuristic_39; only if 40a/40b leave budget on the table.

## RESULTS (2026-07-21)

**Row 40 = 120,123,174, 40/40 feasible — SOTA** (v39: 123,229,003; −3,105,829).
Top-15 cells @1800s serial caffeinated; 11 improved, 2 locked (30, 34, 39), 1 regressed
(35, kept 900s cell), 1 flat-ish (26 −13,709 but overran, see below).

| cell | v39 @900 | v40 @1800 | delta |
|---|---|---|---|
| 38 | 38,140,257 | **36,322,548** | −1,817,709 (= banked Windows cell exactly; jv9@1800 36,335,881 − t37's −13,333) |
| 27 | 24,074,569 | **23,560,982** | −513,587 (= jv9@1800 basin; tails 0) |
| 33 | 7,727,671 | 7,413,984 | −313,687 |
| 32 | 3,817,174 | 3,610,956 | −206,218 |
| 28 | 3,565,230 | 3,501,009 | −64,221 |
| 31 | 8,114,125 | 8,058,524 | −55,601 |
| 37 | 5,767,161 | 5,718,014 | −49,147 |
| 40 | 2,299,885 | 2,251,054 | −48,831 |
| 26 | 7,735,059 | 7,721,350 | −13,709 (ran 2104s! see overrun) |
| 23 | 2,389,645 | 2,376,086 | −13,559 (t37 quantum) |
| 21 | 1,308,647 | 1,299,087 | −9,560 |
| 39/30/34 | — | byte-equal | locked basins |
| 35 | 1,332,063 | 1,345,948 | +13,885 re-roll; row keeps 900s cell |

Findings:
- 40a is the payer (search scaling); 40b merge-on-forced showed no separate win on the
  giants' deterministic basins (38/27 land jv9-identical ± t37).
- **TIMELIMIT OVERRUN DEFECT:** prob_26 took 2104s against TL=1800 (and 900s-era prob_34
  ran 900.6s). Some tail stage (merge/order CP-SAT model build, Python-side, on this
  half-speed mac) blows through `abs_stop`. Contest-compliance fix needed in v41:
  hard-budget the model BUILD phases, not just the solver time.
- The 1800s re-pacing lottery is real but small (35: +13,885) — scaled cap re-rolls
  basins that the 600s cap froze; net across 15 cells it's hugely positive.
- Gap to <115M after row 40: −5.12M. Remaining mass: 38 (36.3M), 27 (23.6M), 39 (8.4M),
  31 (8.06M), 26 (7.72M), 33 (7.41M), 37 (5.72M). Next: recompute per-instance lower
  bounds (tardy_lb/lb_cumulative) to locate the true remaining slack.

## Campaign plan (row 40)

Re-measure the top 15 cells (38, 27, 39, 31, 26, 33, 37, 32, 28, 30, 23, 40, 34, 35, 21)
with v40 @1800s serial caffeinated; bank the remaining 25 cells from the same-machine
same-week v39 @900s row (v40 ≡ v39 at TL=900 on non-forced instances by construction).
Row label must state the mixed budget. Paired attribution: jv9 @1800 controls exist for
38/27; v39 @900 cells are the paired base for the rest.
