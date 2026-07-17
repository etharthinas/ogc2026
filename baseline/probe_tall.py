#!/usr/bin/env python3
"""Signal probe: HARD tall-orientation forcing on prob_26-class (height-
fragmentation-bound: bays half-empty yet median free rect 23x7 vs needed
22x14 -- wide-short orientation choices shred shallow strip bays into
unusable bands; diag_gaps26). 30a/30b tried SOFT steering (scoring/tie-break)
and lost the W2 race; this measures the mechanism ceiling with HARD forcing:
drop every orientation whose bbox height < FRAC * block's tallest-fitting
orientation height (always keeping at least one orientation that fits some
bay). If tall forcing packs denser, raw total drops.

Usage: python probe_tall.py [prob_indices...]   (default: 26 23 30)
"""
import sys, os, json, time, random, copy

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import myalgorithm_jv6b as M

DEFAULT = [26, 23, 30]
CONFIGS = [(0.5, 0.5, 0.5), (1.0, 0.5, 0.0)]
FRACS = (0.75, 0.9)


def _bbox(o):
    xs = [v[0] for layer in o["layers"] for v in layer]
    ys = [v[1] for layer in o["layers"] for v in layer]
    return (max(xs) - min(xs), max(ys) - min(ys))


def tall_filtered(prob, frac):
    """Copy of prob with each block's orientation list filtered to tall ones
    (bbox h >= frac * tallest orientation h that fits some bay)."""
    q = copy.deepcopy(prob)
    bays = q["bays"]

    def fits_some(w, h):
        return any(w <= b["width"] and h <= b["height"] for b in bays)

    for blk in q["blocks"]:
        shapes = blk["shape"]
        dims = [_bbox(o) for o in shapes]
        fit_hs = [h for (w, h) in dims if fits_some(w, h)]
        if not fit_hs:
            continue
        hmax = max(fit_hs)
        keep = [o for o, (w, h) in zip(shapes, dims)
                if h >= frac * hmax and fits_some(w, h)]
        if keep:
            blk["shape"] = keep
    return q


def one_dispatch(prob, kap, gam, al, budget=90.0):
    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    raster = M._Raster(prob, bays)
    raster.reset()
    raster.near_k = 3
    dl = time.time() + budget
    drng = random.Random(9099)
    a = M._dispatch_construct(prob, bays, bay_u, w1, w2, w3, dl, raster,
                              kappa=kap, gamma=gam, rng=drng, alpha=al,
                              score_pos=True, targets=None, beam=True,
                              nearmiss=8)
    return M._objective(a, prob["blocks"], bays, bay_u, w1, w2, w3)


def probe(k):
    prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
    print(f"\nprob_{k}:", flush=True)
    best = None
    for (kap, gam, al) in CONFIGS:
        try:
            t0, o1_0, _, _ = one_dispatch(prob, kap, gam, al)
            row = f"  cfg(k={kap},a={al}): base={t0:,.0f}(o1={o1_0:,.0f})"
            for frac in FRACS:
                tp = tall_filtered(prob, frac)
                tt, o1_t, _, _ = one_dispatch(tp, kap, gam, al)
                d = tt - t0
                row += f" | tall{frac} {tt:,.0f}(o1={o1_t:,.0f}) d={d:+,.0f}"
                if best is None or d < best:
                    best = d
            print(row, flush=True)
        except Exception as e:
            print(f"  cfg(k={kap},a={al}): ERR {type(e).__name__}: {e}",
                  flush=True)
    verdict = ("SIGNAL" if best is not None and best < -1000 else
               "flat" if best is not None else "err")
    print(f"  => best tall delta = {best:+,.0f}  [{verdict}]", flush=True)
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
    print("SUMMARY (tall-forced vs base, best config, raw dispatch):",
          flush=True)
    for k, best, verdict in rows:
        print(f"  prob_{k:>2}: {best:+,.0f}  [{verdict}]" if best is not None
              else f"  prob_{k:>2}: err", flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
