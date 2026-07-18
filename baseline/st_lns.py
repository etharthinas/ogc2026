#!/usr/bin/env python3
"""arm 37a -- OFFLINE space-time reservation LNS improver.

Operates on a COMPLETE champion solution as a reservation table over (x, y, t).
Nonmonotone: any block can be moved to any feasible time slot (earlier OR later)
via an earliest-feasible insertion primitive built on myalgorithm_36's exact
placement gate (_can_place) and raster pre-filter (scan_scoped / _order_cells).

CLI: st_lns.py <k> <budget_s> [--capture v25_<k>.json] [--seed N] [--out lns_<k>.json]

Reuses (never reimplements) myalgorithm_36 geometry:
  _Raster.scan_scoped / mask_fp, _order_cells, _neighbor_field  -> anchor search
  _can_place / _mkblock / _unique_orients / _orient_fits        -> exact gate
  _objective / _bay_u                                           -> internal obj
  _build_operations                                             -> official ops
The official utils.check_feasibility gates every banked incumbent.
"""
import sys, os, json, time, random, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import myalgorithm_36 as M
from myalgorithm_36 import _Raster
from utils import Bay, check_feasibility

DEATH_TOL = 8.0          # exit-time window for death-clustering bonus
DEATH_W = 3.0            # weight of death-clustering vs contact
TIME_CAP = 24            # candidate entry times per block (earliest slice)
ANCHOR_CAP = 30          # exact-gated anchors per (bay, orient, time)
OPS = ["D1", "D2", "D3", "D4", "D5"]


def _adjacent(b1, b2):
    """True iff two bounding rects touch or sit within 1 unit on both axes."""
    ax0, ay0, ax1, ay1 = b1
    bx0, by0, bx1, by1 = b2
    xgap = max(bx0 - ax1, ax0 - bx1)
    ygap = max(by0 - ay1, ay0 - by1)
    return xgap <= 1.0 and ygap <= 1.0


class STLNS:
    def __init__(self, k, prob, capture, seed):
        self.k = k
        self.prob = prob
        self.bd = prob["blocks"]
        self.n = len(self.bd)
        self.bays = [Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
        self.nb = len(self.bays)
        w = prob.get("weights", {})
        self.w1 = w.get("w1", 1.0); self.w2 = w.get("w2", 1.0)
        self.w3 = w.get("w3", 1.0)
        self.bay_u = M._bay_u(self.bays)
        self.raster = _Raster(prob, self.bays)
        self.rng = random.Random(seed)

        self.rel = [int(b["release_time"]) for b in self.bd]
        self.due = [int(b["due_date"]) for b in self.bd]
        self.proc = [int(b["processing_time"]) for b in self.bd]
        self.slack = [self.due[i] - self.rel[i] - self.proc[i]
                      for i in range(self.n)]

        # unique orients that fit each bay, per block
        self.fit_orients = []
        for i in range(self.n):
            uo = M._unique_orients(self.bd[i])
            self.fit_orients.append(
                [[oi for oi in uo if M._orient_fits(self.bd[i], oi, self.bays[b])]
                 for b in range(self.nb)])

        # incumbent assignment (int bi -> placement dict), from the capture
        self.incumbent = {}
        for bi_s, a in capture.items():
            bi = int(bi_s)
            self.incumbent[bi] = {
                "block_id": bi, "bay_id": int(a["bay_id"]),
                "x": int(a["x"]), "y": int(a["y"]),
                "orient_idx": int(a["orient_idx"]),
                "entry_time": int(a["entry_time"]),
                "exit_time": int(a["exit_time"]),
            }
        self.orig_entry = {bi: self.incumbent[bi]["entry_time"]
                           for bi in self.incumbent}
        # adaptive roulette weights per destroy op
        self.op_w = {op: 1.0 for op in OPS}

    # -- objective ------------------------------------------------------------
    def iobj(self, assign):
        return M._objective(assign, self.bd, self.bays, self.bay_u,
                            self.w1, self.w2, self.w3)[0]

    def official(self, assign):
        ops = M._build_operations(assign)
        res = check_feasibility(self.prob, {"operations": ops})
        return res

    # -- schedule bookkeeping -------------------------------------------------
    def build_sched(self, assign):
        sched = [[] for _ in range(self.nb)]
        for bi, a in assign.items():
            nb = M._mkblock(bi, self.bd[bi], a["x"], a["y"], a["orient_idx"])
            sched[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"]))
        return sched

    # -- insertion primitive --------------------------------------------------
    def earliest_feasible(self, bi, sched):
        """Return earliest feasible (bay, oi, x, y, entry, exit, block) for bi
        against the current sched (bi already removed), or None. Candidate entry
        times = release, event times ascending, plus a guaranteed-late fallback
        (bay drained -> no overlap). Anchors from raster scan_scoped + near-miss,
        exact-gated by _can_place; earliest t wins, tie-break by anchor score
        (contact/perimeter + death-time clustering)."""
        blk = self.bd[bi]; proc = self.proc[bi]; rel = self.rel[bi]
        times = {rel, self.orig_entry.get(bi, rel)}
        late = []
        for bay in range(self.nb):
            mx = rel
            for (b, a, e) in sched[bay]:
                if e >= rel:
                    times.add(e)
                if a >= rel:
                    times.add(a)
                if e > mx:
                    mx = e
            late.append(mx)
        prim = sorted(t for t in times if t >= rel)[:TIME_CAP]
        order_times = prim + [t for t in sorted(set(late)) if t not in times]

        for t in order_times:
            exit_t = t + proc
            best = None; best_score = None
            for bay in range(self.nb):
                ojs = self.fit_orients[bi][bay]
                if not ojs:
                    continue
                relx = [(b, a, e) for (b, a, e) in sched[bay]
                        if a <= exit_t and t <= e]
                actives = [(b.block_id, b.orient_idx, b.x, b.y)
                           for (b, a, e) in relx]
                for oi in ojs:
                    feas, cx0, cy0, occ_fp, near = self.raster.scan_scoped(
                        bay, actives, bi, oi, want_near=True)
                    N = None
                    passed = False
                    # near-miss anchors only if the conservative grid gave none
                    for grid in (feas, near):
                        if grid is None or not grid.any():
                            continue
                        if passed and grid is near:
                            break
                        cells = M._order_cells(
                            self.raster, grid, cx0, cy0, bi, oi,
                            self.raster.W[bay], occ_fp, True, self.rng)
                        tried = 0
                        for (x, y) in cells:
                            nb = M._mkblock(bi, blk, x, y, oi)
                            if M._can_place(self.bays[bay], relx, nb, t, exit_t):
                                if N is None:
                                    N = M._neighbor_field(occ_fp)
                                sc = self._score(bi, oi, x, y, cx0, cy0,
                                                 exit_t, relx, N, nb)
                                if best_score is None or sc < best_score:
                                    best_score = sc
                                    best = (bay, oi, x, y, t, exit_t, nb)
                                passed = True
                            tried += 1
                            if tried >= ANCHOR_CAP:
                                break
            if best is not None:
                return best
        return None

    def _score(self, bi, oi, x, y, cx0, cy0, exit_t, relx, N, nb):
        fp = self.raster.mask_fp(bi, oi)
        MH, MW = fp.shape
        r = y + cy0; c = x + cx0
        contact = int((N[r:r + MH, c:c + MW] * fp).sum())
        cbb = nb.bounding_rect()
        death = 0.0
        for (b, a, e) in relx:
            if _adjacent(cbb, b.bounding_rect()):
                d = abs(e - exit_t)
                if d <= DEATH_TOL:
                    death += 1.0 - d / DEATH_TOL
        return -(contact + DEATH_W * death)   # lower = better

    # -- destroy operators ----------------------------------------------------
    def destroy(self, work, op):
        rng = self.rng
        if op == "D1":                                  # time-band x bay slab
            entries = [work[bi]["entry_time"] for bi in work]
            lo = rng.choice(entries); wd = rng.randint(4, 12)
            bset = set(rng.sample(range(self.nb),
                                  k=min(self.nb, rng.randint(1, 2))))
            rem = [bi for bi in work if work[bi]["bay_id"] in bset
                   and lo <= work[bi]["entry_time"] <= lo + wd]
            rng.shuffle(rem)
            return set(rem[:rng.randint(8, 30)])
        if op == "D2":                                  # tardy-chain
            tardy = [bi for bi in work
                     if work[bi]["exit_time"] > self.due[bi]]
            if not tardy:
                return set()
            seed = rng.choice(tardy)
            bay = work[seed]["bay_id"]
            r = self.rel[seed]; w = r + self.proc[seed]
            rem = [bi for bi in work if bi != seed
                   and work[bi]["bay_id"] == bay
                   and work[bi]["entry_time"] < w
                   and work[bi]["exit_time"] > r]
            rng.shuffle(rem)
            out = set(rem[:rng.randint(6, 24)]); out.add(seed)
            return out
        if op == "D3":                                  # exit-cohort defrag
            bay = rng.randrange(self.nb)
            exits = [work[bi]["exit_time"] for bi in work
                     if work[bi]["bay_id"] == bay]
            if not exits:
                return set()
            lo = rng.choice(exits); wd = rng.randint(4, 12)
            rem = [bi for bi in work if work[bi]["bay_id"] == bay
                   and lo <= work[bi]["exit_time"] <= lo + wd]
            rng.shuffle(rem)
            return set(rem[:rng.randint(8, 30)])
        if op == "D5":                                  # slack-waster swap
            entries = [work[bi]["entry_time"] for bi in work]
            lo = rng.choice(entries); wd = rng.randint(6, 16)
            t1, t2 = lo, lo + wd
            wasters = []
            for bi in work:
                a = work[bi]["entry_time"]; e = work[bi]["exit_time"]
                if a < t2 and t1 < e:                   # resident in band
                    us = self.slack[bi] - (a - self.rel[bi])
                    if us > 0:
                        wasters.append((bi, us))
            if not wasters:
                return set()
            wasters.sort(key=lambda z: -z[1])
            bset = set(work[bi]["bay_id"] for bi, _ in wasters[:10])
            tardy = [bi for bi in work if work[bi]["exit_time"] > self.due[bi]
                     and work[bi]["bay_id"] in bset
                     and work[bi]["entry_time"] >= t1]
            rng.shuffle(tardy)
            out = set(bi for bi, _ in wasters[:rng.randint(4, 10)])
            out |= set(tardy[:rng.randint(4, 10)])
            return out
        # D4 uniform random
        k = rng.randint(8, 30)
        return set(rng.sample(list(work), k=min(k, len(work))))

    # -- repair orderings -----------------------------------------------------
    def repair_orders(self, removed, work):
        rem = list(removed)
        due = self.due; proc = self.proc; slack = self.slack
        edd = sorted(rem, key=lambda i: (due[i], proc[i]))          # ATC-ish
        mslack = sorted(rem, key=lambda i: (slack[i], due[i]))      # min-slack
        # tardy-first (drives D5): tardy blocks first, then by due
        tfirst = sorted(rem, key=lambda i: (
            0 if work[i]["exit_time"] > due[i] else 1, due[i], proc[i]))
        # two orders keeps iters/s high; tfirst drives D5 slack transfer,
        # min-slack is a distinct packing basin. (edd kept for reference.)
        _ = edd
        return [tfirst, mslack]

    def repair(self, base_assign, base_sched, removed, order):
        trial = dict(base_assign)
        sched = [list(base_sched[b]) for b in range(self.nb)]
        for bi in order:
            res = self.earliest_feasible(bi, sched)
            if res is None:
                return None
            bay, oi, x, y, t, exit_t, nb = res
            trial[bi] = {"block_id": bi, "bay_id": bay, "x": x, "y": y,
                         "orient_idx": oi, "entry_time": t, "exit_time": exit_t}
            sched[bay].append((nb, t, exit_t))
        return trial

    # -- main loop ------------------------------------------------------------
    def run(self, budget_s):
        cur_obj = self.iobj(self.incumbent)
        start_obj = cur_obj
        res0 = self.official(self.incumbent)
        official_ok = bool(res0.get("feasible"))
        drift0 = None
        if official_ok:
            drift0 = res0["objective"] - start_obj
        print(f"start={int(round(start_obj))} "
              f"official_feasible={official_ok} "
              f"official_obj={None if res0['objective'] is None else int(round(res0['objective']))} "
              f"drift={None if drift0 is None else round(drift0, 3)}",
              flush=True)

        t0 = time.time(); last_print = t0
        iters = 0; accepts = 0
        while time.time() - t0 < budget_s:
            iters += 1
            op = self.rng.choices(OPS, weights=[self.op_w[o] for o in OPS])[0]
            work = self.incumbent
            removed = self.destroy(work, op)
            if not removed:
                continue
            base_assign = {bi: work[bi] for bi in work if bi not in removed}
            base_sched = self.build_sched(base_assign)
            best_trial = None; best_trial_obj = cur_obj
            for order in self.repair_orders(removed, work):
                trial = self.repair(base_assign, base_sched, removed, order)
                if trial is None:
                    continue
                o = self.iobj(trial)
                if o < best_trial_obj - 0.5:
                    best_trial_obj = o; best_trial = trial
            if best_trial is not None:
                # strict improvement found; verify with the official gate
                res = self.official(best_trial)
                if (res.get("feasible") and res["objective"] is not None
                        and abs(res["objective"] - best_trial_obj) < 1.0):
                    self.incumbent = best_trial
                    cur_obj = best_trial_obj
                    accepts += 1
                    official_ok = True
                    self.op_w[op] += 1.0
                # else: official rejected -> discard, keep incumbent
            now = time.time()
            if now - last_print >= 30.0:
                print(f"  t={now - t0:5.1f}s iters={iters} accepts={accepts} "
                      f"cur={int(round(cur_obj))} "
                      f"delta={int(round(start_obj - cur_obj))} "
                      f"ips={iters / (now - t0):.2f}", flush=True)
                last_print = now

        best_obj = self.iobj(self.incumbent)
        delta = int(round(start_obj - best_obj))
        print(f"LNS prob_{self.k}: start={int(round(start_obj))} "
              f"best={int(round(best_obj))} delta={delta} "
              f"iters={iters} accepts={accepts} official_ok={official_ok}",
              flush=True)
        return self.incumbent, start_obj, best_obj, iters, accepts, official_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("k", type=int)
    ap.add_argument("budget_s", type=float)
    ap.add_argument("--capture", default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cap = args.capture or f"v25_{args.k}.json"
    out = args.out or f"lns_{args.k}.json"
    prob = json.load(open(os.path.join(HERE, "..", "train", f"prob_{args.k}.json")))
    capture = json.load(open(os.path.join(HERE, cap)))

    lns = STLNS(args.k, prob, capture, args.seed)
    incumbent, start_obj, best_obj, iters, accepts, official_ok = lns.run(
        args.budget_s)

    save = {str(bi): a for bi, a in incumbent.items()}
    json.dump(save, open(os.path.join(HERE, out), "w"))
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
