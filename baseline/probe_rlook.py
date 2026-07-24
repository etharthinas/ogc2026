#!/usr/bin/env python3
"""Signal probe jv19 RELEASE-LOOKAHEAD MODES on the giants.

probe_dm_giants 07-24 (budget 120s): additive rlook = 27 raw -1,765,971
(SIGNAL) but 38 overran the budget (d8 alone needs ~107s; +50% look cost hit
the deadline and force-placed the tail, +446M artifact). This probe re-runs
with headroom and adds the cost-neutral BLEND mode (imminent releases replace
the last K queued-tail look entries; look stays `drain` entries).

Arms (raw single-worker non-beam dispatch, k=1.0 g=0.5 a=0.0, drain=8):
  d8     rlook off (baseline)
  add    rlook additive (_RLOOK=2, K=4, MODE=0)
  blend  rlook blend    (_RLOOK=2, K=2, MODE=1)  -- cost == d8

Usage: python probe_rlook.py [budget_s] [prob_indices...]
       default budget 240s/arm, cells 38 27
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv19 as M

DEFAULT = [38, 27]
KAP, GAM, AL = 1.0, 0.5, 0.0
ARMS = (("d8", (0, 4, 0)), ("add", (2, 4, 0)), ("blend", (2, 2, 1)))


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, rl, rk, rm, budget):
    raster.reset()
    raster.near_k = 3
    M._RLOOK = rl
    M._RLOOK_K = rk
    M._RLOOK_MODE = rm
    M._HOLD = 0
    dl = time.time() + budget
    drng = random.Random(9099)
    t0 = time.time()
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=KAP, gamma=GAM, rng=drng, alpha=AL,
                              score_pos=True, targets=None, beam=False,
                              nearmiss=8, drain=8)
    el = time.time() - t0
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3), el


def probe(k, budget):
    M._reset_caches()
    M._MREL.clear()
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    raster = M._Raster(prob, bays)
    print(f"\nprob_{k}: w1={w1}", flush=True)
    out = {}
    for tag, (rl, rk, rm) in ARMS:
        (tot, o1, _, _), el = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                           raster, rl, rk, rm, budget)
        out[tag] = tot
        cut = "  **BUDGET-CUT**" if el >= budget - 1.0 else ""
        print(f"  {tag:>5}: obj={tot:,.0f} (o1={o1:,.0f})  [{el:.0f}s]{cut}",
              flush=True)
    da = out["add"] - out["d8"]
    db = out["blend"] - out["d8"]
    print(f"  => add {da:+,.0f} [{'SIGNAL' if da < -1000 else 'flat'}]"
          f" | blend {db:+,.0f} [{'SIGNAL' if db < -1000 else 'flat'}]",
          flush=True)
    return k, da, db


if __name__ == "__main__":
    args = sys.argv[1:]
    budget = 240.0
    if args and ("." in args[0] or int(float(args[0])) > 50):
        budget = float(args.pop(0))
    idx = [int(x) for x in args] if args else DEFAULT
    rows = []
    for k in idx:
        try:
            rows.append(probe(k, budget))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"prob_{k}: FATAL {type(e).__name__}: {e}", flush=True)
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY (rlook modes vs plain drain=8, raw non-beam dispatch):",
          flush=True)
    for k, da, db in rows:
        print(f"  prob_{k:>2}: add {da:+,.0f} | blend {db:+,.0f}", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
