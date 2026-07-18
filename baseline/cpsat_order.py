#!/usr/bin/env python3
# =============================================================================
# cpsat_order.py -- arm 37c: REPLAY-ORDER-AWARE windowed CP-SAT repack.
#
# Motivation (heuristic_32 "Pool-diversity ceiling experiment" + heuristic_37
# 37c): the prior pairwise space-time-crane merge model could not represent the
# champion of prob_26 -- its best was WORSE than its own warm hint. Stated
# cause: crane feasibility on dense instances depends on same-tick REPLAY ORDER
# that a static pairwise abstraction over fixed (entry,exit) candidates cannot
# choose.
#
# Ground truth (from reading utils.check_entry/check_exit): they are PURELY
# PAIRWISE -- every existing block is tested independently; there is no
# cross-block sweep. So crane feasibility == OR over present blocks ==
# conjunction of pairwise relations, EXACT once the presence set is known.
# Presence is fully determined by the two blocks' chosen times plus their
# same-tick order. Hence an order-aware pairwise model is COMPLETE.
#
# The genuine new capability vs the merge / frozen-time models: intra-tick
# SEQUENCING. The official checker (Stage-5) replays ops in the LISTED order at
# each tick (all EXITs, then ENTRYs). _build_operations hard-codes block_id
# order, but nothing forces that -- the emitter chooses the within-type order.
# Two window blocks at the same tick can be sequenced either way, unlocking
# dense pairs infeasible in block_id order. The model exposes this as booleans
# (oe_ij entries / ox_ij exits) with crane constraints conditional on order.
#
# REALIZATION (_build_ops_ordered) is CRANE-AWARE: within each (bay,tick) it
# topo-orders ALL same-tick ops -- window AND frozen -- from the exact
# entry_blocked / exit_blocked relations, so window ops sequence correctly
# around frozen ops. A lazy no-good repair loop (<=3 rounds) backstops any
# residual unrealizable pick. Official check_feasibility is always the final
# gate; nothing unsound is banked (a MISSED incompatibility only lets an
# infeasible pick through, which the checker catches -- so capping the pairwise
# build is SOUND, never unsound, exactly as radical_s4_merge argues).
#
# WINDOW SCOPING:
#   entry-band (default)  window = blocks ENTERING in [t1,t2]. Frees only
#                         entrants; residents holding the floor stay frozen ->
#                         no multi-block slack-transfer chain can form (measured
#                         ceiling: exactly 1 obj1 unit per giant).
#   presence (--presence) window = blocks whose [entry,exit) INTERSECTS
#                         [t1,t2] -- residents INCLUDED. Frees the floor so
#                         chains can form. ~100 blocks on prob_38's peak;
#                         everything else frozen.
#
# Modes: default single window (Gate 0 then optimize); --gate0-only;
# --sweep (overlapping bands, apply+re-derive, multi-pass, adaptive skip).
#
# OFFLINE / STANDALONE. Never mutates any existing file. __main__ guard is
# mandatory (Windows spawn). Single process.
# =============================================================================
import os
import sys
import re
import json
import time
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
os.chdir(_HERE)  # myalgorithm_36 does `from utils import ...` relative to cwd

import myalgorithm_36 as M
from ortools.sat.python import cp_model

# ---- tunables ---------------------------------------------------------------
CAND_CAP = 48          # candidates per window block (entry-band mode)
PER_BAY_ANCHORS = 10   # raster anchors sampled per (bay, orient), entry-band
PRESENCE_CAND_CAP = 32     # candidates per block in presence mode (bound size)
PRESENCE_ANCHORS = 8       # anchors per (bay,orient) in presence mode
PRESENCE_WIN_CAP = 140     # max window blocks in presence mode
BUILD_CAP_S = 300.0        # hard cap on pairwise-constraint build (presence)
MAX_EARLY = 9          # earlier-entry candidate times for tardy blocks
MAX_LATE = 12          # later-entry candidate times within free slack
SU = 1000              # imbalance (u_j ratio) scale
WSCALE = 1000          # weight scale (preserves small w2 precisely)
WIN_MIN, WIN_MAX = 20, 40
BAND_MIN = 4           # skip bands with fewer window blocks than this


# ---- capture / window helpers ----------------------------------------------

def _load_champion(path):
    raw = json.load(open(path))
    champ = {}
    for _bid, a in raw.items():
        bi = int(a["block_id"])
        champ[bi] = {"block_id": bi, "bay_id": int(a["bay_id"]),
                     "x": int(a["x"]), "y": int(a["y"]),
                     "orient_idx": int(a["orient_idx"]),
                     "entry_time": int(a["entry_time"]),
                     "exit_time": int(a["exit_time"])}
    return champ


def _auto_window(champ):
    """Densest burst band: smallest [t1,t2] whose entry count is in
    [WIN_MIN, WIN_MAX], max count as tie-break."""
    ents = sorted(a["entry_time"] for a in champ.values())
    uniq = sorted(set(ents))
    best = None
    for i, t1 in enumerate(uniq):
        for t2 in uniq[i:]:
            cnt = sum(1 for e in ents if t1 <= e <= t2)
            if cnt > WIN_MAX:
                break
            if cnt >= WIN_MIN:
                key = (t2 - t1, -cnt)
                if best is None or key < best[0]:
                    best = (key, t1, t2, cnt)
    if best is not None:
        return best[1], best[2]
    from collections import Counter
    c = Counter(ents)
    peak = max(c, key=lambda t: c[t])
    return max(0, peak - 5), peak + 6


def _window_ids(base, t1, t2, presence, win_cap):
    if presence:
        ids = sorted(bi for bi, a in base.items()
                     if a["entry_time"] <= t2 and a["exit_time"] >= t1)
    else:
        ids = sorted(bi for bi, a in base.items()
                     if t1 <= a["entry_time"] <= t2)
    if len(ids) > win_cap:
        ids = ids[:win_cap]
    return ids


def _champ_order(bi, bj):
    """_build_operations same-tick tie-break: lower block_id first."""
    return bi < bj


# ---- candidate pool (asymmetric slack-aware) -------------------------------

def _entry_choices(a, blk):
    """Asymmetric time menu for a window block given its current assignment `a`
    (base -- champion / working / resident). Tardy blocks get EARLIER times
    biased toward release; slack-rich blocks get LATER times up to their free
    (on-time) slack; all keep base. Applies to residents too."""
    release = int(blk["release_time"])
    due = int(blk["due_date"])
    proc = a["exit_time"] - a["entry_time"]
    base = a["entry_time"]
    tard = max(0, a["exit_time"] - due)

    early = []
    if base > release:
        span = base - release
        if tard > 0:
            if span <= MAX_EARLY:
                early = list(range(release, base))
            else:
                early = [release + i for i in range(0, 6)]
                early += [release + int(span * f) for f in (0.5, 0.7, 0.85)]
                early = sorted({t for t in early if release <= t < base})
        else:
            early = [base - 1]                 # small on-time nudge

    late = []
    unused_slack = (due - proc) - base     # room to enter later, still on time
    if unused_slack > 0:
        late = list(range(base + 1, base + unused_slack + 1))[:MAX_LATE]

    return sorted({base, *early, *late}), base


def _build_pool(base_assign, blocks_data, bays, raster, window_ids, fixed_ids,
                cand_cap=CAND_CAP, per_bay_anchors=PER_BAY_ANCHORS):
    """One combined-candidate pool per window block: each candidate bundles
    (bay, oi, x, y, entry, exit) and is exact-gated feasible vs the FROZEN
    schedule (block_id tie-break). base candidate (current placement+time) is
    index 0. exit keeps the dwell (exit = entry + proc). Cross-bay allowed."""
    n_bays = len(bays)

    fixed_by_bay = [[] for _ in range(n_bays)]
    for bi in fixed_ids:
        a = base_assign[bi]
        nb = M._mkblock(bi, blocks_data[bi], a["x"], a["y"], a["orient_idx"])
        fixed_by_bay[a["bay_id"]].append((nb, a["entry_time"], a["exit_time"]))

    pool = {}
    for bi in window_ids:
        a = base_assign[bi]
        blk = blocks_data[bi]
        proc = a["exit_time"] - a["entry_time"]
        prefs = blk["bay_preferences"]
        s_max = max(prefs)
        due = int(blk["due_date"])
        orients = M._unique_orients(blk)
        choices, base_entry = _entry_choices(a, blk)

        seen = set()
        cands = []

        def _gate(bay_id, x, y, oi, entry):
            if len(cands) >= cand_cap:
                return
            exit_t = entry + proc
            key = (bay_id, x, y, oi, entry)
            if key in seen:
                return
            bay = bays[bay_id]
            nb = M._mkblock(bi, blk, x, y, oi)
            rel = [(fb, fe, fx) for (fb, fe, fx) in fixed_by_bay[bay_id]
                   if M._overlaps(entry, exit_t, fe, fx)
                   or fe in (entry, exit_t) or fx in (entry, exit_t)]
            if not M._can_place(bay, rel, nb, entry, exit_t):
                return
            seen.add(key)
            cands.append({"bi": bi, "bay": bay_id, "x": int(x), "y": int(y),
                          "oi": oi, "entry": int(entry), "exit": int(exit_t),
                          "proc": proc, "pen3": s_max - prefs[bay_id],
                          "tard": max(0, exit_t - due)})

        # 1) base candidate ALWAYS index 0 (feasible fallback / warm hint)
        _gate(a["bay_id"], a["x"], a["y"], a["orient_idx"], base_entry)
        # 2) base placement x every time choice (cheap, high obj1 value)
        for et in choices:
            _gate(a["bay_id"], a["x"], a["y"], a["orient_idx"], et)

        # 3) raster anchors in pref-descending bays (cross-bay) x time choices
        bay_order = sorted(range(n_bays), key=lambda j: -prefs[j])
        time_priority = [base_entry] + [t for t in choices if t != base_entry]
        for bay_id in bay_order:
            if len(cands) >= cand_cap:
                break
            bay = bays[bay_id]
            for oi in orients:
                if not M._orient_fits(blk, oi, bay):
                    continue
                actives = [(fb.block_id, fb.orient_idx, fb.x, fb.y)
                           for (fb, fe, fx) in fixed_by_bay[bay_id]
                           if M._overlaps(base_entry, base_entry + proc, fe, fx)]
                res = raster.scan_scoped(bay_id, actives, bi, oi)
                feas, cx0, cy0, occ_fp = res
                if feas is None or not feas.any():
                    continue
                cells = M._order_cells(raster, feas, cx0, cy0, bi, oi,
                                       raster.W[bay_id], occ_fp, True, None)
                stride = max(1, len(cells) // (per_bay_anchors * 3))
                anchors = cells[::stride][:per_bay_anchors]
                for et in time_priority:
                    for (x, y) in anchors:
                        _gate(bay_id, x, y, oi, et)
                        if len(cands) >= cand_cap:
                            break
                    if len(cands) >= cand_cap:
                        break
        pool[bi] = cands
    return pool


# ---- pairwise exact relation -----------------------------------------------

def _pair_rel(raster, bays, blocks_data, ca, cb):
    bay = bays[ca["bay"]]
    return M._exact_pair_rel(
        raster, bay, blocks_data,
        ca["bi"], ca["oi"], ca["x"], ca["y"],
        cb["bi"], cb["oi"], cb["x"], cb["y"])


# =============================================================================
# MODEL
# =============================================================================

class Model:
    def __init__(self, prob, base, window_ids, fixed_ids, pool, bays, bay_u,
                 raster):
        self.prob = prob
        self.base = base
        self.window_ids = window_ids
        self.fixed_ids = fixed_ids
        self.pool = pool
        self.bays = bays
        self.bay_u = bay_u
        self.raster = raster
        self.blocks_data = prob["blocks"]
        w = prob.get("weights", {})
        self.w1 = w.get("w1", 1.0)
        self.w2 = w.get("w2", 1.0)
        self.w3 = w.get("w3", 1.0)
        self.m = cp_model.CpModel()
        self.z = {}
        self.oe = {}
        self.ox = {}
        self.n_pair_combos = 0
        self.n_hard = 0
        self.n_ordcon = 0
        self._records = []
        self._nogoods = 0
        self.pairs_capped = False
        self.pairs_done = 0
        self.pairs_total = 0

    def _oe_var(self, bi, bj):
        k = (bi, bj) if bi < bj else (bj, bi)
        v = self.oe.get(k)
        if v is None:
            v = self.m.NewBoolVar(f"oe_{k[0]}_{k[1]}")
            self.oe[k] = v
        return k, v

    def _ox_var(self, bi, bj):
        k = (bi, bj) if bi < bj else (bj, bi)
        v = self.ox.get(k)
        if v is None:
            v = self.m.NewBoolVar(f"ox_{k[0]}_{k[1]}")
            self.ox[k] = v
        return k, v

    def build(self, build_deadline=None, progress=False, t0=None):
        m = self.m
        t0 = t0 or time.time()
        for bi in self.window_ids:
            vs = [m.NewBoolVar(f"z_{bi}_{c}") for c in range(len(self.pool[bi]))]
            for c, v in enumerate(vs):
                self.z[(bi, c)] = v
            m.AddExactlyOne(vs)

        # per-block candidate time ranges for cheap block-pair pruning
        trng = {}
        for bi in self.window_ids:
            es = [c["entry"] for c in self.pool[bi]]
            xs = [c["exit"] for c in self.pool[bi]]
            trng[bi] = (min(es), max(es), min(xs), max(xs))  # min_e,max_e,min_x,max_x

        wl = list(self.window_ids)
        self.pairs_total = len(wl) * (len(wl) - 1) // 2
        done = 0
        last = t0
        for ii in range(len(wl)):
            bi = wl[ii]
            min_ei, _me, _mxi, max_xi = trng[bi]
            for jj in range(ii + 1, len(wl)):
                bj = wl[jj]
                done += 1
                min_ej, _mej, _mxj, max_xj = trng[bj]
                # closed-interval possible overlap over ANY candidate combo
                if min_ei > max_xj or min_ej > max_xi:
                    continue
                self._pair_constraints(bi, bj)
            if build_deadline is not None and time.time() > build_deadline:
                self.pairs_capped = True
                self.pairs_done = done
                if progress:
                    print(f"    [build] CAP hit at pairs {done}/{self.pairs_total}"
                          f" combos={self.n_pair_combos} hard={self.n_hard} "
                          f"order={self.n_ordcon} ({time.time()-t0:.0f}s)",
                          flush=True)
                break
            if progress and time.time() - last > 20:
                print(f"    [build] pairs {done}/{self.pairs_total} "
                      f"combos={self.n_pair_combos} hard={self.n_hard} "
                      f"order={self.n_ordcon} ({time.time()-t0:.0f}s)", flush=True)
                last = time.time()
        self.pairs_done = done
        self._objective()

    def _pair_constraints(self, bi, bj):
        ci, cj = self.pool[bi], self.pool[bj]
        bd = self.blocks_data
        for ai, ca in enumerate(ci):
            ei, xi = ca["entry"], ca["exit"]
            bay_a = ca["bay"]
            for aj, cb in enumerate(cj):
                if bay_a != cb["bay"]:
                    continue
                ej, xj = cb["entry"], cb["exit"]
                # closed-interval disjoint -> no crane/collision interaction
                if ei > xj or ej > xi:
                    continue
                col, e_ab, x_ab, e_ba, x_ba = _pair_rel(
                    self.raster, self.bays, bd, ca, cb)
                if not (col or e_ab or x_ab or e_ba or x_ba):
                    continue
                self.n_pair_combos += 1
                za, zb = self.z[(bi, ai)], self.z[(bj, aj)]

                if col and (ei < xj and ej < xi):
                    self.m.Add(za + zb <= 1)
                    self.n_hard += 1
                    self._records.append(("col", bi, bj, ai, aj))
                    continue

                if e_ab:
                    if ej < ei < xj:
                        self.m.Add(za + zb <= 1); self.n_hard += 1
                        self._records.append(("e_ab_forced", bi, bj, ai, aj))
                    elif ej == ei and xj > ei:
                        self._require_entry_order(bi, bj, bi, za, zb)
                        self._records.append(("e_ab_order", bi, bj, ai, aj))
                if e_ba:
                    if ei < ej < xi:
                        self.m.Add(za + zb <= 1); self.n_hard += 1
                        self._records.append(("e_ba_forced", bi, bj, ai, aj))
                    elif ei == ej and xi > ej:
                        self._require_entry_order(bi, bj, bj, za, zb)
                        self._records.append(("e_ba_order", bi, bj, ai, aj))
                if x_ab:
                    if ej < xi < xj:
                        self.m.Add(za + zb <= 1); self.n_hard += 1
                        self._records.append(("x_ab_forced", bi, bj, ai, aj))
                    elif xj == xi and ej < xi:
                        self._require_exit_order(bi, bj, bj, za, zb)
                        self._records.append(("x_ab_order", bi, bj, ai, aj))
                if x_ba:
                    if ei < xj < xi:
                        self.m.Add(za + zb <= 1); self.n_hard += 1
                        self._records.append(("x_ba_forced", bi, bj, ai, aj))
                    elif xi == xj and ei < xj:
                        self._require_exit_order(bi, bj, bi, za, zb)
                        self._records.append(("x_ba_order", bi, bj, ai, aj))

    def _require_entry_order(self, bi, bj, first, za, zb):
        k, v = self._oe_var(bi, bj)
        want = v if first == k[0] else v.Not()
        self.m.AddBoolOr([za.Not(), zb.Not(), want])
        self.n_ordcon += 1

    def _require_exit_order(self, bi, bj, first, za, zb):
        k, v = self._ox_var(bi, bj)
        want = v if first == k[0] else v.Not()
        self.m.AddBoolOr([za.Not(), zb.Not(), want])
        self.n_ordcon += 1

    def _objective(self):
        m = self.m
        n_bays = len(self.bays)
        bd = self.blocks_data
        cost_terms = []
        wl_terms = [[] for _ in range(n_bays)]
        for bi in self.window_ids:
            wkl = int(round(bd[bi]["workload"]))
            for cidx, c in enumerate(self.pool[bi]):
                v = self.z[(bi, cidx)]
                cst = int(round(WSCALE * (self.w1 * c["tard"]
                                          + self.w3 * c["pen3"])))
                if cst:
                    cost_terms.append(cst * v)
                wl_terms[c["bay"]].append((wkl, v))
        base_load = [0.0] * n_bays
        for bi in self.fixed_ids:
            base_load[self.base[bi]["bay_id"]] += bd[bi]["workload"]

        obj = [SU * t for t in cost_terms]
        if n_bays >= 2 and self.w2 != 0:
            su = [int(round(SU * self.bay_u[j])) for j in range(n_bays)]
            load_expr, big = [], 0
            for j in range(n_bays):
                base = int(round(base_load[j]))
                terms = [su[j] * base]; cap = su[j] * base
                for (coef, var) in wl_terms[j]:
                    terms.append(su[j] * coef * var); cap += su[j] * coef
                load_expr.append(sum(terms)); big = max(big, cap)
            zmax = m.NewIntVar(0, max(1, big), "zmax")
            for p in range(n_bays):
                for q in range(n_bays):
                    if p != q:
                        m.Add(zmax >= load_expr[p] - load_expr[q])
            obj.append(int(round(WSCALE * self.w2)) * zmax)
        m.Minimize(sum(obj))

    def _champ_hints(self):
        oevals = {k: (1 if _champ_order(k[0], k[1]) else 0) for k in self.oe}
        oxvals = {k: (1 if _champ_order(k[0], k[1]) else 0) for k in self.ox}
        return oevals, oxvals

    def add_warm_start(self):
        oevals, oxvals = self._champ_hints()
        for bi in self.window_ids:
            for cidx in range(len(self.pool[bi])):
                self.m.AddHint(self.z[(bi, cidx)], 1 if cidx == 0 else 0)
        for k, v in self.oe.items():
            self.m.AddHint(v, oevals[k])
        for k, v in self.ox.items():
            self.m.AddHint(v, oxvals[k])


# =============================================================================
# GATE 0
# =============================================================================

def _diagnose_champion(mdl):
    zsel = {bi: 0 for bi in mdl.window_ids}
    for (kind, bi, bj, ai, aj) in mdl._records:
        if zsel[bi] != ai or zsel[bj] != aj:
            continue
        ca = mdl.pool[bi][ai]; cb = mdl.pool[bj][aj]
        oij = _champ_order(bi, bj)
        if kind == "col":
            return (False, "collision",
                    f"blocks {bi}&{bj} champ placements collide, intervals "
                    f"[{ca['entry']},{ca['exit']})/[{cb['entry']},{cb['exit']}) "
                    f"bay {ca['bay']}")
        if kind.endswith("_forced"):
            cls = "crane-entry" if kind.startswith("e_") else "crane-exit"
            return (False, cls,
                    f"{kind}: {bi}<->{bj} bay {ca['bay']} forced-present block, "
                    f"[{ca['entry']},{ca['exit']})/[{cb['entry']},{cb['exit']})")
        if kind == "e_ab_order" and not oij:
            return (False, "crane-entry/ordering",
                    f"e_ab_order: champ has {bj} before {bi} at t={ca['entry']}"
                    f" but {bj} obstructs {bi}'s entry")
        if kind == "e_ba_order" and oij:
            return (False, "crane-entry/ordering",
                    f"e_ba_order: champ has {bi} before {bj} at t={ca['entry']}"
                    f" but {bi} obstructs {bj}'s entry")
        if kind == "x_ab_order" and oij:
            return (False, "crane-exit/ordering",
                    f"x_ab_order: champ has {bi} exiting before {bj} at "
                    f"t={ca['exit']} but {bj} obstructs {bi}'s exit")
        if kind == "x_ba_order" and not oij:
            return (False, "crane-exit/ordering",
                    f"x_ba_order: champ has {bj} exiting before {bi} at "
                    f"t={ca['exit']} but {bi} obstructs {bj}'s exit")
    return (True, None, None)


def gate0(mdl):
    ok, cls, triple = _diagnose_champion(mdl)
    if not ok:
        print(f"GATE0 FAIL  (class={cls})")
        print(f"  offending: {triple}")
        return False
    m2 = mdl.m.Clone()
    oevals, oxvals = mdl._champ_hints()
    for bi in mdl.window_ids:
        for cidx in range(len(mdl.pool[bi])):
            m2.Add(mdl.z[(bi, cidx)] == (1 if cidx == 0 else 0))
    for k, v in mdl.oe.items():
        m2.Add(v == oevals[k])
    for k, v in mdl.ox.items():
        m2.Add(v == oxvals[k])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 4
    st = solver.Solve(m2)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("GATE0 PASS")
        return True
    print(f"GATE0 FAIL  (CP-SAT rejected fixed champion: {solver.StatusName(st)}"
          f"; python diagnostic found no offending crane/order clause -> "
          f"objective/linearization or hint infeasibility)")
    return False


# =============================================================================
# CRANE-AWARE ORDER REALIZATION
# =============================================================================

def _topo(ids, edges):
    """Kahn topo sort with block_id tie-break. edges: set of (u,v) meaning u
    before v. Returns ordered list, or None on cycle."""
    adj = {u: set() for u in ids}
    indeg = {u: 0 for u in ids}
    for (u, v) in edges:
        if v not in adj[u]:
            adj[u].add(v); indeg[v] += 1
    out = []
    avail = sorted(u for u in ids if indeg[u] == 0)
    while avail:
        u = avail.pop(0)
        out.append(u)
        for w in sorted(adj[u]):
            indeg[w] -= 1
            if indeg[w] == 0:
                avail.append(w); avail.sort()
    return out if len(out) == len(ids) else None


def _build_ops_ordered(assign, blocks_data, bays):
    """Emit operations with a crane-aware within-tick order. For each (bay,tick)
    group, precedence edges come from the EXACT entry_blocked/exit_blocked
    relations over ALL same-tick ops (window + frozen), so window ops sequence
    correctly around frozen ones. block_id order is the tie-break (reproduces
    _build_operations when no crane forcing). Cycle -> block_id fallback (the
    official checker is the final gate)."""
    blk = {bid: M._mkblock(bid, blocks_data[bid], a["x"], a["y"], a["orient_idx"])
           for bid, a in assign.items()}
    entries_bt, exits_bt = {}, {}
    for a in assign.values():
        entries_bt.setdefault((a["bay_id"], a["entry_time"]), []).append(
            a["block_id"])
        exits_bt.setdefault((a["bay_id"], a["exit_time"]), []).append(
            a["block_id"])

    def order_entries(bay_id, ids):
        bay = bays[bay_id]
        edges = set()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                u, v = ids[i], ids[j]
                buv = M._entry_blocked(bay, blk[v], blk[u])   # v obstructs u
                bvu = M._entry_blocked(bay, blk[u], blk[v])   # u obstructs v
                if buv:
                    edges.add((u, v))   # u before v
                if bvu:
                    edges.add((v, u))
                if not buv and not bvu:
                    edges.add((min(u, v), max(u, v)))
        r = _topo(ids, edges)
        return r if r is not None else sorted(ids)

    def order_exits(bay_id, ids):
        bay = bays[bay_id]
        edges = set()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                u, v = ids[i], ids[j]
                buv = M._exit_blocked(bay, blk[v], blk[u])    # v obstructs u
                bvu = M._exit_blocked(bay, blk[u], blk[v])    # u obstructs v
                if buv:
                    edges.add((v, u))   # v before u
                if bvu:
                    edges.add((u, v))
                if not buv and not bvu:
                    edges.add((min(u, v), max(u, v)))
        r = _topo(ids, edges)
        return r if r is not None else sorted(ids)

    operations = {}
    ticks = sorted({t for (_, t) in entries_bt} | {t for (_, t) in exits_bt})
    n_bays = len(bays)
    for t in ticks:
        lst = []
        for bay_id in range(n_bays):
            ids = exits_bt.get((bay_id, t))
            if ids:
                for bid in order_exits(bay_id, ids):
                    a = assign[bid]
                    lst.append({"type": "EXIT", "block_id": bid,
                                "bay_id": a["bay_id"]})
        for bay_id in range(n_bays):
            ids = entries_bt.get((bay_id, t))
            if ids:
                for bid in order_entries(bay_id, ids):
                    a = assign[bid]
                    lst.append({"type": "ENTRY", "block_id": bid,
                                "bay_id": a["bay_id"], "x": a["x"], "y": a["y"],
                                "orient_idx": a["orient_idx"]})
        operations[str(t)] = lst
    return operations


# =============================================================================
# BUILD + SOLVE (single window) with lazy no-good repair
# =============================================================================

def build_band(prob, base, bays, bay_u, raster, t1, t2, presence=False,
               cand_cap=CAND_CAP, anchors=PER_BAY_ANCHORS, win_cap=WIN_MAX,
               build_deadline=None, progress=False):
    """Construct the pool + CP-SAT model for the window. Returns
    (mdl|None, pool, window_ids, info)."""
    bd = prob["blocks"]
    window_ids = _window_ids(base, t1, t2, presence, win_cap)
    if len(window_ids) < 2:
        return None, None, window_ids, {"reason": "too_few",
                                        "window": len(window_ids)}
    win_set = set(window_ids)
    fixed_ids = [bi for bi in base if bi not in win_set]
    t0 = time.time()
    pool = _build_pool(base, bd, bays, raster, window_ids, fixed_ids,
                       cand_cap=cand_cap, per_bay_anchors=anchors)
    if progress:
        print(f"    [build] pool ready: window={len(window_ids)} "
              f"total_cand={sum(len(v) for v in pool.values())} "
              f"avg={sum(len(v) for v in pool.values())/len(window_ids):.1f} "
              f"({time.time()-t0:.0f}s)", flush=True)
    mdl = Model(prob, base, window_ids, fixed_ids, pool, bays, bay_u, raster)
    mdl.build(build_deadline=build_deadline, progress=progress, t0=t0)
    info = {"window": len(window_ids),
            "total_cand": sum(len(v) for v in pool.values()),
            "z": len(mdl.z), "oe": len(mdl.oe), "ox": len(mdl.ox),
            "pair_combos": mdl.n_pair_combos, "hard": mdl.n_hard,
            "order": mdl.n_ordcon, "pairs_capped": mdl.pairs_capped,
            "pairs_done": mdl.pairs_done, "pairs_total": mdl.pairs_total,
            "build_s": time.time() - t0}
    return mdl, pool, window_ids, info


def solve_model(prob, base, mdl, pool, window_ids, bays, bay_u, budget_s):
    """Solve, realize crane-aware, verify official; lazy no-good repair (<=3
    rounds). Returns (new_assign|None, delta, info). new_assign strictly
    improves and passes check_feasibility, else None."""
    bd = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    win_set = set(window_ids)
    base_obj = M._objective(base, bd, bays, bay_u, w1, w2, w3)[0]
    info = {"nogoods": 0}

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(budget_s)
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 1

    for rnd in range(3):
        st = solver.Solve(mdl.m)
        info["status"] = solver.StatusName(st)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None, 0.0, info
        new_assign = {bi: dict(a) for bi, a in base.items()}
        sel = {}
        for bi in window_ids:
            chosen = None
            for cidx, c in enumerate(pool[bi]):
                if solver.Value(mdl.z[(bi, cidx)]) == 1:
                    chosen = c; sel[bi] = cidx; break
            if chosen is None:
                chosen = pool[bi][0]; sel[bi] = 0
            a = new_assign[bi]
            a["bay_id"] = chosen["bay"]; a["x"] = chosen["x"]
            a["y"] = chosen["y"]; a["orient_idx"] = chosen["oi"]
            a["entry_time"] = chosen["entry"]; a["exit_time"] = chosen["exit"]

        ops = _build_ops_ordered(new_assign, bd, bays)
        res = M.check_feasibility(prob, {"operations": ops})
        if res["feasible"]:
            delta = res["objective"] - base_obj
            info["internal"] = M._objective(new_assign, bd, bays, bay_u,
                                             w1, w2, w3)[0]
            if delta < -0.5:
                return new_assign, delta, info
            return None, delta, info

        bad = set()
        for vtext in res.get("violations", []):
            for mtc in re.findall(r"block (\d+)", vtext):
                b = int(mtc)
                if b in win_set:
                    bad.add(b)
        if not bad:
            info["reason"] = "infeasible_no_parse"
            break
        mdl.m.Add(sum(mdl.z[(b, sel[b])] for b in bad) <= len(bad) - 1)
        mdl._nogoods += 1
        info["nogoods"] = mdl._nogoods

    return None, 0.0, info


def solve_band(prob, base, bays, bay_u, raster, t1, t2, budget_s,
               presence=False, cand_cap=CAND_CAP, anchors=PER_BAY_ANCHORS,
               win_cap=WIN_MAX, build_deadline=None, progress=False):
    """build_band + solve_model. Used by sweep and default optimize."""
    mdl, pool, window_ids, binfo = build_band(
        prob, base, bays, bay_u, raster, t1, t2, presence=presence,
        cand_cap=cand_cap, anchors=anchors, win_cap=win_cap,
        build_deadline=build_deadline, progress=progress)
    if mdl is None:
        return None, 0.0, binfo
    mdl.add_warm_start()
    na, delta, sinfo = solve_model(prob, base, mdl, pool, window_ids,
                                   bays, bay_u, budget_s)
    binfo.update(sinfo)
    return na, delta, binfo


# =============================================================================
# SINGLE-WINDOW OPTIMIZE (default / presence)
# =============================================================================

def optimize(prob, champ, bays, bay_u, raster, t1, t2, budget_s, k,
             presence=False, gate0_only=False):
    bd = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    base_obj, b1, b2, b3 = M._objective(champ, bd, bays, bay_u, w1, w2, w3)
    print(f"  champion recomputed obj={base_obj:,.0f} "
          f"(obj1={b1:.0f} obj2={b2:.0f} obj3={b3:.0f})")

    cand_cap = PRESENCE_CAND_CAP if presence else CAND_CAP
    anchors = PRESENCE_ANCHORS if presence else PER_BAY_ANCHORS
    win_cap = PRESENCE_WIN_CAP if presence else WIN_MAX
    bdl = time.time() + BUILD_CAP_S if presence else None

    mdl, pool, window_ids, info = build_band(
        prob, champ, bays, bay_u, raster, t1, t2, presence=presence,
        cand_cap=cand_cap, anchors=anchors, win_cap=win_cap,
        build_deadline=bdl, progress=presence)
    if mdl is None:
        print(f"  build aborted: {info}")
        return
    print(f"  model: window={info['window']} total_cand={info['total_cand']} "
          f"z={info['z']} oe={info['oe']} ox={info['ox']} "
          f"pair_combos={info['pair_combos']} hard={info['hard']} "
          f"order={info['order']} pairs={info['pairs_done']}/{info['pairs_total']}"
          f" capped={info['pairs_capped']} build={info['build_s']:.0f}s")

    print("-" * 78)
    passed = gate0(mdl)
    print("-" * 78)
    if gate0_only or not passed:
        return

    mdl.add_warm_start()
    remaining = max(5.0, budget_s - info["build_s"])
    na, delta, sinfo = solve_model(prob, champ, mdl, pool, window_ids,
                                   bays, bay_u, remaining)
    print(f"  solve: status={sinfo.get('status')} nogoods={sinfo.get('nogoods')}"
          f" delta={delta:+,.0f}")
    if na is None:
        print("  NO VERIFIED IMPROVEMENT")
        return
    out = {str(bi): {"block_id": bi, **{kk: a[kk] for kk in
            ("bay_id", "x", "y", "orient_idx", "entry_time", "exit_time")}}
           for bi, a in na.items()}
    outpath = os.path.join(_HERE, f"cpsat_order_{k}.json")
    json.dump(out, open(outpath, "w"))
    print(f"  VERIFIED IMPROVEMENT delta={delta:+,.0f} "
          f"({base_obj:,.0f} -> {base_obj + delta:,.0f})  saved -> {outpath}")


# =============================================================================
# SWEEP (overlapping bands, apply + re-derive, multi-pass, adaptive skip)
# =============================================================================

def sweep(prob, champ, bays, bay_u, raster, k, budget_s, W=12,
          presence=False):
    bd = prob["blocks"]
    w = prob.get("weights", {})
    w1, w2, w3 = w.get("w1", 1.0), w.get("w2", 1.0), w.get("w3", 1.0)
    working = {bi: dict(a) for bi, a in champ.items()}
    start_obj = M._objective(working, bd, bays, bay_u, w1, w2, w3)[0]

    cand_cap = PRESENCE_CAND_CAP if presence else CAND_CAP
    anchors = PRESENCE_ANCHORS if presence else PER_BAY_ANCHORS
    win_cap = PRESENCE_WIN_CAP if presence else WIN_MAX

    ents = [a["entry_time"] for a in champ.values()]
    t_lo, t_hi = min(ents), max(ents)
    stride = max(1, W // 2)

    def band_n(t1, t2):
        return len(_window_ids(working, t1, t2, presence, win_cap))

    bands = [(s, s + W) for s in range(t_lo, t_hi + 1, stride)]
    bands = [(t1, t2) for (t1, t2) in bands if band_n(t1, t2) >= BAND_MIN]
    dirty = [True] * len(bands)

    print(f"  sweep tiling: W={W} stride={stride} bands={len(bands)} "
          f"presence={presence} span=[{t_lo},{t_hi}] start_obj={start_obj:,.0f}")

    deadline = time.time() + budget_s
    passno = 0
    total_accepts = 0
    while time.time() < deadline:
        passno += 1
        pass_accepts = 0
        pass_delta = 0.0
        for idx, (t1, t2) in enumerate(bands):
            if time.time() >= deadline:
                break
            if not dirty[idx]:
                continue
            remaining = deadline - time.time()
            active = sum(1 for d in dirty if d)
            per = max(3.0, min(120.0, remaining / max(1, active)))
            bdl = time.time() + min(BUILD_CAP_S, per) if presence else None
            new_assign, delta, info = solve_band(
                prob, working, bays, bay_u, raster, t1, t2, per,
                presence=presence, cand_cap=cand_cap, anchors=anchors,
                win_cap=win_cap, build_deadline=bdl)
            if new_assign is not None and delta < -0.5:
                working = new_assign
                pass_accepts += 1
                total_accepts += 1
                pass_delta += delta
                dirty[idx] = True
                for j, (u1, u2) in enumerate(bands):
                    if j != idx and not (u2 < t1 or u1 > t2):
                        dirty[j] = True
            else:
                dirty[idx] = False
        cur = M._objective(working, bd, bays, bay_u, w1, w2, w3)[0]
        print(f"SWEEP prob_{k}: pass={passno} accepts={pass_accepts} "
              f"delta={pass_delta:+,.0f} total={cur:,.0f}")
        if pass_accepts == 0:
            break

    best_obj = M._objective(working, bd, bays, bay_u, w1, w2, w3)[0]
    ops = _build_ops_ordered(working, bd, bays)
    res = M.check_feasibility(prob, {"operations": ops})
    official_ok = bool(res["feasible"]) and abs(res["objective"] - best_obj) < 1.0
    if res["feasible"]:
        best_obj = res["objective"]
    if total_accepts > 0 and official_ok:
        out = {str(bi): {"block_id": bi, **{kk: a[kk] for kk in
                ("bay_id", "x", "y", "orient_idx", "entry_time", "exit_time")}}
               for bi, a in working.items()}
        outpath = os.path.join(_HERE, f"cpsat_order_{k}.json")
        json.dump(out, open(outpath, "w"))
        print(f"  saved -> {outpath}")
    delta_total = int(round(best_obj - start_obj))
    print(f"SWEEP prob_{k}: start={int(round(start_obj))} "
          f"best={int(round(best_obj))} delta={delta_total} passes={passno} "
          f"accepts={total_accepts} official_ok={official_ok}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("k", type=int)
    ap.add_argument("budget_s", type=float)
    ap.add_argument("--capture", default=None)
    ap.add_argument("--t1", type=int, default=None)
    ap.add_argument("--t2", type=int, default=None)
    ap.add_argument("--gate0-only", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--presence", action="store_true")
    ap.add_argument("--width", type=int, default=12)
    args = ap.parse_args()

    k = args.k
    capture = args.capture or f"v25_{k}.json"
    capture_path = os.path.join(_HERE, capture)
    prob = json.load(open(os.path.join(_HERE, "..", "train", f"prob_{k}.json")))
    champ = _load_champion(capture_path)

    bays = [M.Bay.from_dict(d, i) for i, d in enumerate(prob["bays"])]
    bay_u = M._bay_u(bays)
    M._reset_caches()
    raster = M._Raster(prob, bays)

    print("=" * 78)
    mode = 'sweep' if args.sweep else ('gate0' if args.gate0_only else 'single')
    print(f"[cpsat_order] prob_{k}  capture={capture}  "
          f"budget={args.budget_s:.0f}s  mode={mode}  presence={args.presence}")

    if args.sweep:
        sweep(prob, champ, bays, bay_u, raster, k, args.budget_s,
              W=args.width, presence=args.presence)
        return

    if args.t1 is not None and args.t2 is not None:
        t1, t2 = args.t1, args.t2
    else:
        t1, t2 = _auto_window(champ)
    wn = len(_window_ids(champ, t1, t2, args.presence,
                         PRESENCE_WIN_CAP if args.presence else WIN_MAX))
    print(f"  window [t1,t2]=[{t1},{t2}]  window_blocks={wn}  bays={len(bays)}")
    optimize(prob, champ, bays, bay_u, raster, t1, t2, args.budget_s, k,
             presence=args.presence, gate0_only=args.gate0_only)


if __name__ == "__main__":
    main()
