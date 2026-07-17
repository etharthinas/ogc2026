#!/usr/bin/env python3
"""Signal probe: does jv6b's RESERVATION-STEAL admission move (jay heuristic_31
Improvement B, translated to construction time: evict a same-tick slack-rich
admission to place a strictly-blocked urgent block) FIRE and HELP?

Method = jay's own offline ablation (probe_w3nm.py template): a single raw
dispatch construction (NO portfolio, NO polish), steal=0 vs steal={2,4}, same
(kappa,gamma,alpha). Probed on:
  37 = the design target (9x lenient/strict gap in diag37);
  27, 38 = the giant tardiness rocks (mechanism class never tested there);
  39 = giant, should be near-flat (saturated), sanity;
  40 = oversubscribed non-w1 cell, curiosity.

Also prints steal fire counts via OGC_DEBUG capture (set OGC_DEBUG=1 to see
[steal] lines inline).

Usage: python probe_steal.py [prob_indices...]   (default: 37 27 38 39)
"""
import sys, os, json, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [37, 27, 38, 39]
# the measured hot region on the tardy rocks (kappa, gamma, alpha)
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]


def one_dispatch(prob, bays, bay_u, w1, w2, w3, raster, kap, gam, al, beam,
                 steal, budget=90.0):
    raster.reset()
    raster.near_k = 3
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=beam,
                              nearmiss=0, steal=steal)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


def probe(k):
    # CRITICAL (2026-07-18): module caches (_BLK/_CC/_CE/_CX/_MREL) are
    # keyed by block_id, NOT instance -- multi-instance probe processes
    # cross-contaminate geometry without this reset. Every cross-instance
    # probe number produced before this fix is GARBAGE (only each
    # process's FIRST instance was clean).
    M._reset_caches()
    M._MREL.clear()
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    forced = M._is_forced(prob, bays)
    overload = M._overload_ratio(prob, bays)
    raster = M._Raster(prob, bays)
    steal37 = forced and len(prob["blocks"]) >= 250 and w1 <= 3400 \
        and overload <= 1.05

    print(f"\nprob_{k}: w1={w1} w3={w3} forced={forced} "
          f"overload={overload:.2f} steal37-gate={'IN' if steal37 else 'out'}",
          flush=True)
    best = None
    for (kap, gam, al) in CONFIGS:
        try:
            t0, o1_0, _, o3_0 = one_dispatch(prob, bays, bay_u, w1, w2, w3,
                                             raster, kap, gam, al, False, 0)
            row = (f"  cfg(k={kap},a={al}): s0 tot={t0:,.0f}"
                   f"(o1={o1_0:,.0f} o3={o3_0:,.0f})")
            for mg in (2, 4):
                ts, o1_s, _, o3_s = one_dispatch(prob, bays, bay_u, w1, w2,
                                                 w3, raster, kap, gam, al,
                                                 False, mg)
                d = ts - t0
                row += (f" | s{mg} tot={ts:,.0f}(o1={o1_s:,.0f} "
                        f"o3={o3_s:,.0f}) d={d:+,.0f}")
                if best is None or d < best:
                    best = d
            print(row, flush=True)
        except Exception as e:
            print(f"  cfg(k={kap},a={al}): ERR {type(e).__name__}: {e}",
                  flush=True)
            continue
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best steal delta = {best:+,.0f}  [{verdict}]", flush=True)
    return k, best, verdict


if __name__ == "__main__":
    idx = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT
    rows = []
    for k in idx:
        try:
            rows.append(probe(k))
        except Exception as e:
            print(f"prob_{k}: FATAL {type(e).__name__}: {e}", flush=True)
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY (steal vs off, best config, raw single dispatch):", flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
