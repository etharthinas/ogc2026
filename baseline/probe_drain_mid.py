#!/usr/bin/env python3
"""Signal probe jv19 (Route A2 + A1 preview): DRAIN on the MID-CELLS, and
RELEASE LOOKAHEAD on any cell.

The shipping drain build only runs on the nm_elig reclaim giants {27,38,39};
the ~34M area-LB=0 mid-cell pool (26/31/33/30/28) never sees it. Arms, on the
raw single-worker non-beam dispatch (probe_drain convention, config
k=1.0 g=0.5 a=0.0 -- the shipped drain build's config):

  d0     drain=0                  (baseline)
  d8     drain=8, _RLOOK=0        (jv6b drain, queued-only look-set)
  d8r2   drain=8, _RLOOK=2, K=4   (jv19 release lookahead on top)

If d8 sharply cuts raw obj on a mid-cell, Route A2 (drain on mid-cells) gets
a worker-config arm. If d8r2 beats d8 anywhere, the jv19 full A/B is
prioritized. Deltas < -1000 = SIGNAL (probe_drain convention).

Usage: python probe_drain_mid.py [budget_s] [prob_indices...]
       default budget 120s/arm, cells 26 31 33 30 28
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv19 as M

DEFAULT = [26, 31, 33, 30, 28]
KAP, GAM, AL = 1.0, 0.5, 0.0


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, drain, rlook,
                 budget):
    raster.reset()
    raster.near_k = 3
    M._RLOOK = rlook
    M._RLOOK_K = 4
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=KAP, gamma=GAM, rng=drng, alpha=AL,
                              score_pos=True, targets=None, beam=False,
                              nearmiss=8, drain=drain)
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
    for tag, (dm, rl) in (("d0", (0, 0)), ("d8", (8, 0)), ("d8r2", (8, 2))):
        tot, o1, _, _ = one_dispatch(prob, bays, bay_u, w1, w2, w3, raster,
                                     dm, rl, budget)
        out[tag] = (tot, o1)
        print(f"  {tag:>5}: obj={tot:,.0f} (o1={o1:,.0f})"
              f"  [{time.time() - t0:.0f}s elapsed]", flush=True)
    d_drain = out["d8"][0] - out["d0"][0]
    d_rlook = out["d8r2"][0] - out["d8"][0]
    print(f"  => drain delta {d_drain:+,.0f}"
          f"  [{'SIGNAL' if d_drain < -1000 else 'flat'}]"
          f" | rlook delta {d_rlook:+,.0f}"
          f"  [{'SIGNAL' if d_rlook < -1000 else 'flat'}]", flush=True)
    return k, d_drain, d_rlook


if __name__ == "__main__":
    args = sys.argv[1:]
    budget = 120.0
    if args and "." in args[0] or (args and int(float(args[0])) > 50):
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
    print("SUMMARY (single-worker raw dispatch, deltas vs previous arm):",
          flush=True)
    for k, dd, dr in rows:
        print(f"  prob_{k:>2}: drain {dd:+,.0f} | rlook {dr:+,.0f}",
              flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
