#!/usr/bin/env python3
"""Signal probe jv19 STARVATION GUARD (OGC_HOLD) on the giants.

Deferral audit 07-24: 98-100% of giant tardiness is genuine FULLness; tardy
blocks are ~1.9x mean footprint, on-time 0.75x; larges starve 55-85 ticks
while slack-rich small releases eat every freed fragment. The guard skips
slack-rich admissions while a late large claimant is failing, banking freed
space across exit waves.

Arms (raw single-worker non-beam dispatch, k=1.0 g=0.5 a=0.0):
  h0    HOLD off (baseline)
  h1    HOLD on, K=1.0 pbar, AMIN=1.4  (conservative)
  h1a   HOLD on, K=0.5 pbar, AMIN=1.2  (aggressive banking)

Delta < -1000 = SIGNAL (probe_drain convention).

Usage: python probe_hold.py [budget_s] [prob_indices...]
       default budget 120s/arm, cells 38 27
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv19 as M

DEFAULT = [38, 27]
KAP, GAM, AL = 1.0, 0.5, 0.0
ARMS = (("h0", (0, 1.0, 1.4)), ("h1", (1, 1.0, 1.4)), ("h1a", (1, 0.5, 1.2)))


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, hold, hk, ha, budget):
    raster.reset()
    raster.near_k = 3
    M._RLOOK = 0          # isolate the guard from the release lookahead
    M._HOLD = hold
    M._HOLD_K = hk
    M._HOLD_AMIN = ha
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=KAP, gamma=GAM, rng=drng, alpha=AL,
                              score_pos=True, targets=None, beam=False,
                              nearmiss=8, drain=0)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


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
    t0 = time.time()
    for tag, (h, hk, ha) in ARMS:
        tot, o1, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3, raster,
                                     h, hk, ha, budget)
        out[tag] = tot
        print(f"  {tag:>4}: obj={tot:,.0f} (o1={o1:,.0f})"
              f"  [{time.time() - t0:.0f}s elapsed]", flush=True)
    d1 = out["h1"] - out["h0"]
    d1a = out["h1a"] - out["h0"]
    print(f"  => h1 {d1:+,.0f} [{'SIGNAL' if d1 < -1000 else 'flat'}]"
          f" | h1a {d1a:+,.0f} [{'SIGNAL' if d1a < -1000 else 'flat'}]",
          flush=True)
    return k, d1, d1a


if __name__ == "__main__":
    args = sys.argv[1:]
    budget = 120.0
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
    print("SUMMARY (starvation guard vs off, raw non-beam dispatch):",
          flush=True)
    for k, d1, d1a in rows:
        print(f"  prob_{k:>2}: h1 {d1:+,.0f} | h1a {d1a:+,.0f}", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
