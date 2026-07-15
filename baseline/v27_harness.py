#!/usr/bin/env python3
"""v27 scan-kernel EXACTNESS + SPEED harness.

Records a realistic scan/scan_scoped call trace by running the W1 strategy
briefly on real instances, then replays it against BOTH the v26 (einsum) and
v27 (numba saturating) rasters, asserting feas AND near grids (near_k in
{3,32}) are array-equal on every call, and timing both paths per regime.

Windows spawn re-imports __main__ -> guard everything under __main__.
"""
import os, sys, json, time, copy

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "..", "train")
sys.path.insert(0, HERE)

import numpy as np


def record_trace(mod, prob, tl=8.0, wid=1, cap=6000):
    """Monkeypatch the raster at class level to log every occupancy mutation
    (add/remove/reset) and scan/scan_scoped call in order, then run one W1
    strategy for a few seconds to produce a realistic trace."""
    R = mod._Raster
    trace = []
    orig_add, orig_rem, orig_reset = R.add, R.remove, R.reset
    orig_scan, orig_scoped = R.scan, R.scan_scoped
    stop = [False]

    def add(self, bay, bi, oi, x, y):
        if not stop[0]:
            trace.append(("add", bay, bi, oi, x, y))
        return orig_add(self, bay, bi, oi, x, y)

    def remove(self, bay, bi, oi, x, y):
        if not stop[0]:
            trace.append(("remove", bay, bi, oi, x, y))
        return orig_rem(self, bay, bi, oi, x, y)

    def reset(self):
        if not stop[0]:
            trace.append(("reset",))
        return orig_reset(self)

    def scan(self, bay, bi, oi):
        if not stop[0]:
            trace.append(("scan", bay, bi, oi))
            if len(trace) >= cap:
                stop[0] = True
        return orig_scan(self, bay, bi, oi)

    def scan_scoped(self, bay, actives, bi, oi, want_near=False):
        if not stop[0]:
            trace.append(("scoped", bay, list(actives), bi, oi))
            if len(trace) >= cap:
                stop[0] = True
        return orig_scoped(self, bay, actives, bi, oi, want_near)

    R.add, R.remove, R.reset = add, remove, reset
    R.scan, R.scan_scoped = scan, scan_scoped
    try:
        t0 = time.time()
        try:
            mod._run_strategy(wid, prob, tl, t0, lambda *a, **k: None, inbox=None)
        except Exception as e:
            print(f"  (strategy ended: {type(e).__name__})")
    finally:
        R.add, R.remove, R.reset = orig_add, orig_rem, orig_reset
        R.scan, R.scan_scoped = orig_scan, orig_scoped
    return trace


def grids_scan(raster, bay, bi, oi, nk):
    raster._scan[bay].pop((bi, oi), None)
    raster._nearc[bay].pop((bi, oi), None)
    raster.near_enabled = True
    raster.near_k = nk
    feas, cx0, cy0 = raster.scan(bay, bi, oi)
    near = raster.scan_near(bay, bi, oi)
    return feas, near


def grids_scoped(raster, bay, actives, bi, oi, nk):
    raster.near_enabled = True
    raster.near_k = nk
    feas, cx0, cy0, fp, near = raster.scan_scoped(bay, actives, bi, oi,
                                                  want_near=True)
    return feas, near


def eq(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return np.array_equal(a, b)


def replay(mod_old, mod_new, prob, trace):
    rold = mod_old._Raster(prob, [mod_old.Bay.from_dict(d, i)
                                  for i, d in enumerate(prob["bays"])])
    rnew = mod_new._Raster(prob, [mod_new.Bay.from_dict(d, i)
                                  for i, d in enumerate(prob["bays"])])
    n_scan = n_scoped = 0
    bad = 0
    # timing accumulators (seconds) and counts, per regime
    t = {"scan_old": 0.0, "scan_new": 0.0, "scoped_old": 0.0, "scoped_new": 0.0}
    cnt = {"scan": 0, "scoped": 0}
    for op in trace:
        kind = op[0]
        if kind == "add":
            _, bay, bi, oi, x, y = op
            rold.add(bay, bi, oi, x, y); rnew.add(bay, bi, oi, x, y)
        elif kind == "remove":
            _, bay, bi, oi, x, y = op
            rold.remove(bay, bi, oi, x, y); rnew.remove(bay, bi, oi, x, y)
        elif kind == "reset":
            rold.reset(); rnew.reset()
        elif kind == "scan":
            _, bay, bi, oi = op
            for nk in (3, 32):
                fo, no = grids_scan(rold, bay, bi, oi, nk)
                fn, nn = grids_scan(rnew, bay, bi, oi, nk)
                if not (eq(fo, fn) and eq(no, nn)):
                    bad += 1
                    if bad <= 5:
                        print(f"  MISMATCH scan bay={bay} bi={bi} oi={oi} nk={nk}")
            # timing (force cache miss, near_k=3 which is the common path)
            rold._scan[bay].pop((bi, oi), None); rold._nearc[bay].pop((bi, oi), None)
            rold.near_k = 3
            t0 = time.perf_counter(); rold.scan(bay, bi, oi); rold.scan_near(bay, bi, oi)
            t["scan_old"] += time.perf_counter() - t0
            rnew._scan[bay].pop((bi, oi), None); rnew._nearc[bay].pop((bi, oi), None)
            rnew.near_k = 3
            t0 = time.perf_counter(); rnew.scan(bay, bi, oi); rnew.scan_near(bay, bi, oi)
            t["scan_new"] += time.perf_counter() - t0
            cnt["scan"] += 1; n_scan += 1
        elif kind == "scoped":
            _, bay, actives, bi, oi = op
            for nk in (3, 32):
                fo, no = grids_scoped(rold, bay, actives, bi, oi, nk)
                fn, nn = grids_scoped(rnew, bay, actives, bi, oi, nk)
                if not (eq(fo, fn) and eq(no, nn)):
                    bad += 1
                    if bad <= 5:
                        print(f"  MISMATCH scoped bay={bay} bi={bi} oi={oi} nk={nk} "
                              f"nact={len(actives)}")
            rold.near_k = 3
            t0 = time.perf_counter()
            rold.scan_scoped(bay, actives, bi, oi, want_near=True)
            t["scoped_old"] += time.perf_counter() - t0
            rnew.near_k = 3
            t0 = time.perf_counter()
            rnew.scan_scoped(bay, actives, bi, oi, want_near=True)
            t["scoped_new"] += time.perf_counter() - t0
            cnt["scoped"] += 1; n_scoped += 1
    return bad, n_scan, n_scoped, t, cnt


if __name__ == "__main__":
    import myalgorithm_26 as OLD
    import myalgorithm_27 as NEW
    instances = [38, 27, 39]
    all_bad = 0
    agg = {"scan_old": 0.0, "scan_new": 0.0, "scoped_old": 0.0, "scoped_new": 0.0}
    aggc = {"scan": 0, "scoped": 0}
    for k in instances:
        prob = json.load(open(os.path.join(TRAIN, f"prob_{k}.json")))
        print(f"\n=== prob_{k}: recording trace ===")
        trace = record_trace(NEW, copy.deepcopy(prob), tl=22.0, wid=1, cap=45000)
        nscan = sum(1 for o in trace if o[0] == "scan")
        nsc = sum(1 for o in trace if o[0] == "scoped")
        print(f"  trace: {len(trace)} ops ({nscan} scan, {nsc} scoped); replaying...")
        bad, n_scan, n_scoped, t, cnt = replay(OLD, NEW, prob, trace)
        all_bad += bad
        for kk in agg:
            agg[kk] += t[kk]
        for kk in aggc:
            aggc[kk] += cnt[kk]
        so = t["scan_old"]; sn = t["scan_new"]
        po = t["scoped_old"]; pn = t["scoped_new"]
        print(f"  exactness: {bad} mismatches over {(n_scan+n_scoped)*2} grid checks")
        if cnt["scan"]:
            print(f"  scan():   old {so*1e3:8.1f}ms  new {sn*1e3:8.1f}ms  "
                  f"x{so/max(sn,1e-9):5.2f}  ({cnt['scan']} calls)")
        if cnt["scoped"]:
            print(f"  scoped(): old {po*1e3:8.1f}ms  new {pn*1e3:8.1f}ms  "
                  f"x{po/max(pn,1e-9):5.2f}  ({cnt['scoped']} calls)")
        tot_old = so + po; tot_new = sn + pn
        print(f"  OVERALL:  old {tot_old*1e3:8.1f}ms  new {tot_new*1e3:8.1f}ms  "
              f"x{tot_old/max(tot_new,1e-9):5.2f}")

    print("\n" + "=" * 62)
    so = agg["scan_old"]; sn = agg["scan_new"]
    po = agg["scoped_old"]; pn = agg["scoped_new"]
    print(f"AGGREGATE scan():   x{so/max(sn,1e-9):5.2f}  "
          f"({so*1e3:.0f}->{sn*1e3:.0f}ms, {aggc['scan']} calls)")
    print(f"AGGREGATE scoped(): x{po/max(pn,1e-9):5.2f}  "
          f"({po*1e3:.0f}->{pn*1e3:.0f}ms, {aggc['scoped']} calls)")
    to = so + po; tn = sn + pn
    ov = to / max(tn, 1e-9)
    print(f"AGGREGATE OVERALL:  x{ov:5.2f}  ({to*1e3:.0f}->{tn*1e3:.0f}ms)")
    print(f"TOTAL MISMATCHES:   {all_bad}")
    ok = (all_bad == 0) and (ov >= 1.5)
    print(f"\nGATE {'PASS' if ok else 'FAIL'} (exact={all_bad==0}, speedup>=1.5x={ov>=1.5})")
    sys.exit(0 if ok else 1)
