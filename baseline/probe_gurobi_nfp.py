#!/usr/bin/env python3
"""MOONSHOT PROTOTYPE (heuristics/moonshot_plan.md, 2026-07-21).

Question: can a Gurobi continuous-coordinate (NFP-class) nester find a
materially-lower-tardiness packing on a giant's worst (bay, window) than the
raster heuristic + OR-Tools CP-SAT (which measured zero yield)?

The genuinely-new angle vs every dead lever: CONTINUOUS (x, y).  The checker
accepts float placements (utils Block/shapely are float-exact); the raster
engine and both CP-SAT exact packers only ever try integer cells.

Model (sized to the restricted Gurobi license: <=2000 vars, <=2000 constrs):
  * Target = worst bay of prob_39 (or --bay), peak-tardiness window found with
    the same congestion spirit as _exact_pack_window.
  * Movers = the D most-tardy blocks intersecting the window (D adaptive to
    the license budget).  Everything else keeps its incumbent placement+times.
  * Per mover: continuous x,y (bay-bounds via hull bbox = checker's
    bounding_rect), integer entry e in [release, span_hi - proc], exit=e+proc,
    tardiness t >= e+proc-due.
  * Per interacting pair, a disjunction: time-before OR time-after OR
    spatially separate.  Separation uses the CONVEX NFP: hull(union of
    layers)_i (+) -hull(union)_j -- one binary + ONE linear big-M constraint
    per NFP edge ("relative vector outside edge e").  Conservative vs the true
    layered semantics (forbids hull-overlap interlocks: measured only ~2.6% of
    co-resident incumbent pairs, true-union interlocks 2-8 per bay), and
    strictly sound: union-hull separation implies no same-layer overlap and no
    entry/exit sweep obstruction; time-disjoint (closed ineqs) matches the
    checker's EXIT-before-ENTRY same-tick replay.
  * Warm start = incumbent (may violate the ~2.6% hull-overlap pairs; Gurobi
    repairs or drops the start -- the comparison metric is window tardiness).
  * Result is spliced into the full solution and check_feasibility-verified.

Usage:
  python probe_gurobi_nfp.py <dump.json> [--bay B] [--tl SEC] [--maxD D]
  e.g. python probe_gurobi_nfp.py dumps/prob_39.myalgorithm_jv9.json --tl 1800
"""
import sys, os, json, math, time, itertools, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import translate
import gurobipy as gp
from gurobipy import GRB

from utils import check_feasibility

VAR_BUDGET = 1950          # restricted license: 2000 vars / 2000 linear constrs
CON_BUDGET = 1950
# check_feasibility builds every Block with x=int(round(x)) -- the OFFICIAL
# CHECKER EVALUATES INTEGER POSITIONS ONLY (continuous placement is an
# illusion; measured: float solutions 5e-3 outside the NFP round INTO overlap).
# So X,Y are INTEGER vars and flush contact (v on the NFP boundary, area-0
# overlap) must stay legal => EPS_SEP = 0.
EPS_SEP = 0.0
EPS_BND = 1e-6             # keep the raw-vertex bbox strictly inside the bay


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def rel_union_hull(blocks_data, bid, oi):
    """Union-of-layers polygon + its convex hull, in coordinates RELATIVE to
    the placement anchor (utils.Block maps layers[0] first vertex -> (x,y))."""
    shp = blocks_data[bid]["shape"][oi]
    ps = [Polygon(l) for l in shp["layers"]]
    ps = [p if p.is_valid else p.buffer(0) for p in ps]
    u = unary_union(ps)
    rx, ry = shp["layers"][0][0]
    u = translate(u, xoff=-rx, yoff=-ry)
    return u, u.convex_hull


def rel_raw_bbox(blocks_data, bid, oi):
    """(xmin, ymin, xmax, ymax) over the RAW vertices of ALL layers, relative
    to the anchor -- exactly utils.Block.bounding_rect() / contains_block
    semantics (no shapely validity repair)."""
    shp = blocks_data[bid]["shape"][oi]
    rx, ry = shp["layers"][0][0]
    xs = [v[0] - rx for l in shp["layers"] for v in l]
    ys = [v[1] - ry for l in shp["layers"] for v in l]
    return min(xs), min(ys), max(xs), max(ys)


def hull_verts(h):
    cs = list(h.exterior.coords)[:-1]
    # ensure CCW
    a = sum(cs[i][0] * cs[(i + 1) % len(cs)][1] - cs[(i + 1) % len(cs)][0] * cs[i][1]
            for i in range(len(cs)))
    if a < 0:
        cs = cs[::-1]
    return cs


def minkowski_nfp(hi_verts, hj_verts):
    """Convex NFP of hulls i,j under translation: overlap(H_i+pi, H_j+pj)
    iff (pj-pi) in conv{a-b : a in H_i, b in H_j}. Returns CCW verts."""
    pts = [(a[0] - b[0], a[1] - b[1]) for a in hi_verts for b in hj_verts]
    return hull_verts(Polygon(pts).convex_hull)


# --------------------------------------------------------------------------
# true-shape NFP: convex decomposition + piecewise Minkowski
# --------------------------------------------------------------------------

def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _is_convex_loop(vs, tol=1e-9):
    n = len(vs)
    for k in range(n):
        if _cross(vs[k], vs[(k + 1) % n], vs[(k + 2) % n]) < -tol:
            return False
    return True


def _point_in_tri(p, a, b, c, tol=1e-12):
    d1 = _cross(a, b, p); d2 = _cross(b, c, p); d3 = _cross(c, a, p)
    return d1 >= -tol and d2 >= -tol and d3 >= -tol


def _ear_clip(vs):
    """Triangulate a simple CCW polygon (no holes). Returns triangle list."""
    idx = list(range(len(vs)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        clipped = False
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = vs[i0], vs[i1], vs[i2]
            if _cross(a, b, c) <= 1e-12:        # reflex or degenerate
                continue
            if any(_point_in_tri(vs[j], a, b, c)
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append([a, b, c])
            idx.pop(k)
            clipped = True
            break
        if not clipped:                          # numeric dead end: fall back
            return None
    if len(idx) == 3:
        a, b, c = (vs[idx[0]], vs[idx[1]], vs[idx[2]])
        if abs(_cross(a, b, c)) > 1e-12:
            tris.append([a, b, c])
    return tris


def _merge_convex(pieces):
    """Hertel-Mehlhorn-style greedy merge of convex pieces sharing an edge."""
    changed = True
    while changed:
        changed = False
        for x in range(len(pieces)):
            for y in range(x + 1, len(pieces)):
                A, B = pieces[x], pieces[y]
                shared = None
                for u in range(len(A)):
                    e = (A[u], A[(u + 1) % len(A)])
                    for v in range(len(B)):
                        f = (B[v], B[(v + 1) % len(B)])
                        if e[0] == f[1] and e[1] == f[0]:
                            shared = (u, v)
                            break
                    if shared:
                        break
                if not shared:
                    continue
                u, v = shared
                # walk ALL of A starting after the shared edge (wrapping back
                # to A[u] == B[v+1]), then B's vertices strictly between
                # B[v+1] and B[v]
                merged = ([A[(u + 1 + t) % len(A)] for t in range(len(A))]
                          + [B[(v + 2 + t) % len(B)] for t in range(len(B) - 2)])
                if _is_convex_loop(merged):
                    pieces[x] = merged
                    pieces.pop(y)
                    changed = True
                    break
            if changed:
                break
    return pieces


def convex_decompose(shapely_geom):
    """Convex pieces (CCW vertex loops) covering the geometry (holes filled --
    a conservative superset, sound for separation). Falls back to the convex
    hull on numeric failure."""
    geoms = getattr(shapely_geom, "geoms", [shapely_geom])
    out = []
    for g in geoms:
        ext = list(g.exterior.coords)[:-1]
        # drop near-duplicate consecutive vertices
        vs = []
        for p in ext:
            if not vs or (abs(p[0] - vs[-1][0]) + abs(p[1] - vs[-1][1])) > 1e-9:
                vs.append((p[0], p[1]))
        if len(vs) >= 3 and _cross(vs[0], vs[1], vs[2]) is not None:
            a = sum(vs[i][0] * vs[(i + 1) % len(vs)][1]
                    - vs[(i + 1) % len(vs)][0] * vs[i][1] for i in range(len(vs)))
            if a < 0:
                vs = vs[::-1]
        if _is_convex_loop(vs):
            out.append(vs)
            continue
        tris = _ear_clip(vs)
        if tris is None:
            out.append(hull_verts(g.convex_hull))
        else:
            out.extend(_merge_convex(tris))
    # replace each piece by its exact convex hull: merged loops can be
    # convex only up to tolerance, and a slightly-reflex loop's edge
    # half-plane intersection UNDER-covers near the reflex vertex (measured:
    # 0.03-0.3 area slivers leaking through separation).  hull(piece) is a
    # guaranteed-convex superset, so coverage stays sound.
    return [hull_verts(Polygon(p).convex_hull) for p in out]


def true_nfp_pieces(pieces_i, pieces_j):
    """True-shape NFP as a list of CONVEX polygons: overlap(S_i+pi, S_j+pj)
    iff (pj-pi) lies in SOME piece-pair Minkowski sum. Non-overlap iff the
    relative vector is outside EVERY returned convex polygon.

    The raw piece-pair Minkowski polys (n_i x n_j of them) are UNIONED and
    re-decomposed: the union usually needs far fewer convex pieces, and the
    model cost scales with piece count.  Union holes get filled by the
    exterior-only decomposition (conservative: forbids enclosed feasible
    pockets)."""
    raw = []
    for A in pieces_i:
        for B in pieces_j:
            pts = [(a[0] - b[0], a[1] - b[1]) for a in A for b in B]
            raw.append(Polygon(pts).convex_hull)
    if len(raw) == 1:
        return [hull_verts(raw[0])]
    u = unary_union(raw)
    dec = convex_decompose(u)
    if len(dec) < len(raw):
        # coverage safety net: the decomposition must be a SUPERSET of the
        # true NFP or separation leaks slivers (measured 0.03-1.4 area)
        cover = unary_union([Polygon(p) for p in dec])
        if u.difference(cover).area <= 1e-9:
            return dec
    return [hull_verts(p) for p in raw]


def nfp_edges(verts):
    """[(nx, ny, c)] outward edge normals: interior satisfies n.v <= c."""
    out = []
    n = len(verts)
    for k in range(n):
        (x1, y1), (x2, y2) = verts[k], verts[(k + 1) % n]
        nx, ny = (y2 - y1), -(x2 - x1)         # outward for CCW
        ln = math.hypot(nx, ny)
        if ln < 1e-12:
            continue
        out.append((nx / ln, ny / ln, (nx * x1 + ny * y1) / ln))
    return out


# --------------------------------------------------------------------------
# incumbent loading / window selection
# --------------------------------------------------------------------------

def load_incumbent(dump_path, prob):
    dump = json.load(open(dump_path))
    recs = {}
    for r in dump["blocks"]:
        if r.get("bay") is None:
            continue
        recs[r["id"]] = dict(id=r["id"], bay=r["bay"], x=float(r["x"]),
                             y=float(r["y"]), orient=int(r["orient"]),
                             entry=int(r["entry"]), exit=int(r["exit"]))
    return dump, recs


def pick_window(prob, recs, bay, win_w):
    blocks = prob["blocks"]
    items = [r for r in recs.values() if r["bay"] == bay]
    dues = {r["id"]: blocks[r["id"]]["due_date"] for r in items}
    cands = []
    for r in items:
        lo = r["entry"]; hi = lo + win_w
        score = sum(max(0, q["exit"] - dues[q["id"]]) for q in items
                    if q["entry"] < hi and q["exit"] > lo)
        cands.append((score, lo, hi))
    cands.sort(key=lambda z: -z[0])
    return cands[0]


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------

def build_and_solve(prob, recs, bay, movers, span_hi, tl, radius, log=print):
    """Returns (result_or_None, nvars, ncons, dropped_movers).
    result None + dropped non-empty => caller should retry without dropped."""
    blocks_data = prob["blocks"]
    W = prob["bays"][bay]["width"]; H = prob["bays"][bay]["height"]
    mset = set(movers)
    items = [r for r in recs.values() if r["bay"] == bay]

    geo, dec = {}, {}
    for r in items:
        u, h = rel_union_hull(blocks_data, r["id"], r["orient"])
        geo[r["id"]] = hull_verts(h)
        dec[r["id"]] = convex_decompose(u)

    rel = {i: blocks_data[i]["release_time"] for i in movers}
    due = {i: blocks_data[i]["due_date"] for i in movers}
    proc = {i: blocks_data[i]["processing_time"] for i in movers}
    e_lb = {i: int(rel[i]) for i in movers}
    e_ub = {i: max(int(span_hi) - proc[i], recs[i]["entry"]) for i in movers}

    # mover position boxes: incumbent +- radius, clipped to bay-fit bounds
    # (bay fit = RAW-vertex bbox, matching contains_block exactly)
    box = {}
    for i in movers:
        xmin, ymin, xmax, ymax = rel_raw_bbox(blocks_data, i, recs[i]["orient"])
        xlo = max(-xmin + EPS_BND, recs[i]["x"] - radius)
        xhi = min(W - xmax - EPS_BND, recs[i]["x"] + radius)
        ylo = max(-ymin + EPS_BND, recs[i]["y"] - radius)
        yhi = min(H - ymax - EPS_BND, recs[i]["y"] + radius)
        box[i] = (xlo, xhi, ylo, yhi)

    fixed = [r for r in items if r["id"] not in mset
             and r["entry"] < span_hi + 1]      # anything the movers could meet

    def classify_piece(C, vbox):
        """For one convex NFP piece: 'skip' (v-box never inside C),
        or (reachable_edges, all_edges)."""
        vx_lo, vx_hi, vy_lo, vy_hi = vbox
        edges = nfp_edges(C)
        for (nx, ny, c) in edges:
            mn = min(nx * vx_lo, nx * vx_hi) + min(ny * vy_lo, ny * vy_hi)
            if mn >= c:                    # whole box outside this half-plane
                return "skip"
        reach = []
        for (nx, ny, c) in edges:
            mx = max(nx * vx_lo, nx * vx_hi) + max(ny * vy_lo, ny * vy_hi)
            if mx >= c + EPS_SEP:
                reach.append((nx, ny, c))
        return reach

    m = gp.Model("nfp_window")
    m.Params.OutputFlag = 1
    m.Params.TimeLimit = tl
    m.Params.MIPFocus = 1
    m.Params.Threads = min(8, os.cpu_count() or 8)
    # tight tolerances: a binary at 1-1e-5 relaxes a big-M separation by
    # Me*1e-5 ~ 5e-3 -- the same scale as EPS_SEP (measured sliver leaks)
    m.Params.IntFeasTol = 1e-9
    m.Params.FeasibilityTol = 1e-9

    X, Y, E, T = {}, {}, {}, {}
    nvars = ncons = 0
    for i in movers:
        xlo, xhi, ylo, yhi = box[i]
        X[i] = m.addVar(lb=xlo, ub=xhi, vtype=GRB.INTEGER, name=f"x{i}")
        Y[i] = m.addVar(lb=ylo, ub=yhi, vtype=GRB.INTEGER, name=f"y{i}")
        E[i] = m.addVar(lb=e_lb[i], ub=e_ub[i], vtype=GRB.INTEGER, name=f"e{i}")
        T[i] = m.addVar(lb=0.0, name=f"t{i}")
        m.addConstr(T[i] >= E[i] + proc[i] - due[i])
        nvars += 4; ncons += 1
        # warm start
        X[i].Start = recs[i]["x"]; Y[i].Start = recs[i]["y"]
        E[i].Start = recs[i]["entry"]

    def add_spatial(vij_expr_x, vij_expr_y, pieces, vbox, orlits):
        """True-shape separation branch: binary z active => the relative
        vector lies outside EVERY convex NFP piece (one separating edge per
        piece).  Returns z (appended to orlits) or None if impossible within
        the v-box."""
        nonlocal nvars, ncons
        kept = []
        for C in pieces:
            r = classify_piece(C, vbox)
            if r == "skip":
                continue
            if not r:               # piece unavoidable in-box: no separation
                return "impossible"
            kept.append(r)
        if not kept:
            return "never_overlap"
        z = m.addVar(vtype=GRB.BINARY)
        nvars += 1
        for reach in kept:
            svars = []
            for (nx, ny, c) in reach:
                s = m.addVar(vtype=GRB.BINARY)
                nvars += 1
                Me = c + EPS_SEP + (abs(nx) * W + abs(ny) * H) * 2 + 1.0
                m.addConstr(nx * vij_expr_x + ny * vij_expr_y
                            >= c + EPS_SEP - Me * (1 - s))
                ncons += 1
                svars.append(s)
            m.addConstr(gp.quicksum(svars) >= z); ncons += 1
        orlits.append(z)
        return "ok"

    Ht = int(span_hi) + max(proc.values()) + 10
    npair_mm = npair_mf = 0
    dropped = []
    paircat = {}                       # (i, j) -> how the pair was handled
    for i, j in itertools.combinations(movers, 2):
        pieces = true_nfp_pieces(dec[i], dec[j])
        vbox = (box[j][0] - box[i][1], box[j][1] - box[i][0],
                box[j][2] - box[i][3], box[j][3] - box[i][2])
        orlits = []
        yij = m.addVar(vtype=GRB.BINARY); yji = m.addVar(vtype=GRB.BINARY)
        nvars += 2
        m.addConstr(E[i] + proc[i] <= E[j] + Ht * (1 - yij)); ncons += 1
        m.addConstr(E[j] + proc[j] <= E[i] + Ht * (1 - yji)); ncons += 1
        orlits += [yij, yji]
        st = add_spatial(X[j] - X[i], Y[j] - Y[i], pieces, vbox, orlits)
        paircat[(i, j)] = f"mm:{st}"
        if st == "never_overlap":
            continue                 # pair can never overlap: no constraint
        m.addConstr(gp.quicksum(orlits) >= 1); ncons += 1
        npair_mm += 1

    for i in movers:
        for f in fixed:
            fj = f["id"]
            # time-prune: can they ever co-reside?
            if f["exit"] <= e_lb[i] or f["entry"] >= e_ub[i] + proc[i]:
                paircat[(i, fj)] = "mf:timeprune"
                continue
            pieces = true_nfp_pieces(dec[i], dec[fj])
            vbox = (f["x"] - box[i][1], f["x"] - box[i][0],
                    f["y"] - box[i][3], f["y"] - box[i][2])
            orlits = []
            if f["entry"] >= e_lb[i] + proc[i]:
                yb = m.addVar(vtype=GRB.BINARY); nvars += 1
                m.addConstr(E[i] + proc[i] <= f["entry"] + Ht * (1 - yb))
                ncons += 1; orlits.append(yb)
            if f["exit"] <= e_ub[i]:
                ya = m.addVar(vtype=GRB.BINARY); nvars += 1
                m.addConstr(E[i] >= f["exit"] - Ht * (1 - ya))
                ncons += 1; orlits.append(ya)
            st = add_spatial(gp.LinExpr(f["x"]) - X[i],
                             gp.LinExpr(f["y"]) - Y[i], pieces, vbox, orlits)
            paircat[(i, fj)] = f"mf:{st}"
            if st == "never_overlap":
                continue
            if st == "impossible" and not orlits:
                # cannot separate within radius and no time option: the model
                # cannot hold this mover-fixed pair -> demote the mover
                dropped.append(i)
                break
            m.addConstr(gp.quicksum(orlits) >= 1); ncons += 1
            npair_mf += 1
        if i in dropped:
            continue

    log(f"  model: D={len(movers)} R={radius} mm_pairs={npair_mm} "
        f"mf_pairs={npair_mf} vars~{nvars} constrs~{ncons} "
        f"dropped={dropped}")
    if dropped:
        return None, nvars, ncons, dropped
    if nvars > VAR_BUDGET or ncons > CON_BUDGET:
        return None, nvars, ncons, []

    m.setObjective(gp.quicksum(T.values()), GRB.MINIMIZE)
    m.optimize()
    if m.SolCount == 0:
        return None, nvars, ncons, []
    sol = {i: (int(round(X[i].X)), int(round(Y[i].X)), int(round(E[i].X)))
           for i in movers}
    return (sol, m.ObjVal, m.ObjBound, paircat), nvars, ncons, []


# --------------------------------------------------------------------------
# splice + verify
# --------------------------------------------------------------------------

def splice_solution(prob, recs, movers_sol, movers_proc):
    ops = {}
    for r in recs.values():
        i = r["id"]
        if i in movers_sol:
            x, y, e = movers_sol[i]
            ex = e + movers_proc[i]
        else:
            x, y, e, ex = r["x"], r["y"], r["entry"], r["exit"]
        ops.setdefault(str(int(e)), []).append(
            dict(type="ENTRY", block_id=i, bay_id=r["bay"], x=float(x),
                 y=float(y), orient_idx=r["orient"]))
        ops.setdefault(str(int(ex)), []).append(
            dict(type="EXIT", block_id=i, bay_id=r["bay"]))
    # EXITs before ENTRYs at each tick (checker stage-5 replay order), and
    # keys inserted in ascending time order: the checker parses operations in
    # dict-insertion order and DROPS an EXIT seen before its ENTRY.
    out = {}
    for t in sorted(ops, key=int):
        out[t] = sorted(ops[t], key=lambda o: 0 if o["type"] == "EXIT" else 1)
    return {"operations": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--prob", type=int, default=39)
    ap.add_argument("--bay", type=int, default=-1)
    ap.add_argument("--tl", type=float, default=1500.0)
    ap.add_argument("--maxD", type=int, default=14)
    ap.add_argument("--radius", type=float, default=10.0)
    args = ap.parse_args()

    prob = json.load(open(os.path.join(HERE, "..", "train",
                                       f"prob_{args.prob}.json"),
                          encoding="utf-8"))
    blocks_data = prob["blocks"]
    dump, recs = load_incumbent(args.dump, prob)
    print(f"incumbent: obj={dump.get('objective'):,.0f} obj1={dump.get('obj1')}")

    dues = {i: b["due_date"] for i, b in enumerate(blocks_data)}
    bay_z1 = {}
    for r in recs.values():
        bay_z1[r["bay"]] = bay_z1.get(r["bay"], 0) + max(0, r["exit"] - dues[r["id"]])
    print(f"per-bay Z1: {bay_z1}")
    bay = args.bay if args.bay >= 0 else max(bay_z1, key=bay_z1.get)

    procs = [b["processing_time"] for b in blocks_data]
    win_w = int(2 * max(1, sum(procs) / len(procs)))
    score, lo, hi = pick_window(prob, recs, bay, win_w)
    print(f"target bay={bay} window=[{lo},{hi}) windowZ1={score}")

    items = [r for r in recs.values() if r["bay"] == bay]
    # pre-ban INTERLOCKED movers: blocks whose incumbent union-footprint
    # overlaps a co-resident block's (legal layer-order nesting) cannot be
    # represented by the union-separation model -- keeping them as movers
    # makes the model infeasible or strictly worse than the incumbent.
    inter = set()
    geos = {}
    for r in items:
        u, _h = rel_union_hull(prob["blocks"], r["id"], r["orient"])
        geos[r["id"]] = translate(u, xoff=r["x"], yoff=r["y"])
    for a in items:
        for b in items:
            if a["id"] >= b["id"]:
                continue
            if a["entry"] < b["exit"] and b["entry"] < a["exit"]:
                if geos[a["id"]].intersection(geos[b["id"]]).area > 1e-9:
                    inter.add(a["id"]); inter.add(b["id"])
    tardy = [(max(0, r["exit"] - dues[r["id"]]), r["id"]) for r in items
             if r["entry"] < hi and r["exit"] > lo
             and r["exit"] > dues[r["id"]]]
    tardy.sort(reverse=True)
    n_inter = sum(1 for _, i in tardy if i in inter)
    tardy = [(t, i) for t, i in tardy if i not in inter]
    print(f"interlocked movers banned: {n_inter} (bay-wide interlocked "
          f"blocks: {len(inter)})")
    span_hi = hi + win_w

    tard_of = dict((i, t) for t, i in tardy)
    pool = [i for _, i in tardy]
    D = min(args.maxD, len(pool))
    R = args.radius
    result = None
    banned = set()
    for _attempt in range(12):
        movers = [i for i in pool if i not in banned][:D]
        if len(movers) < 4:
            break
        before = sum(tard_of[i] for i in movers)
        print(f"trying D={len(movers)} R={R} "
              f"(movers hold {before} of {score} window Z1)")
        try:
            result, nv, nc, dropped = build_and_solve(
                prob, recs, bay, movers, span_hi, args.tl, R)
        except gp.GurobiError as ge:
            print(f"  GurobiError: {ge}")
            result, nv, nc, dropped = None, 99999, 99999, []
        if result is not None:
            break
        if dropped:
            banned.update(dropped)   # interlocked movers the model can't hold
            continue
        # over budget: shrink radius first (cheaper pairs), then D
        if R > 6:
            R = max(6, R - 3)
        else:
            D -= 2
    if result is None:
        print("NO MODEL FIT / NO SOLUTION -- report failure")
        return

    movers_sol, obj, bound, paircat = result
    proc = {i: blocks_data[i]["processing_time"] for i in movers_sol}
    after = int(round(obj))
    print(f"\nGUROBI window tardiness: before={before} after={after} "
        f"(bound={bound:.1f})")

    dbg = os.path.join(HERE, "dumps", f"prob_{args.prob}.gurobi_nfp.last.json")
    json.dump({str(i): movers_sol[i] for i in movers_sol}, open(dbg, "w"))
    sol = splice_solution(prob, recs, movers_sol, proc)
    res = check_feasibility(prob, sol)
    print(f"check_feasibility: feasible={res['feasible']} stage={res['stage']} "
          f"obj={res['objective'] and round(res['objective'])} "
          f"obj1={res['obj1']}")
    if not res["feasible"]:
        import re
        print(f"movers: {sorted(movers_sol)}")
        seen = set()
        for v in res["violations"][:12]:
            print("  ", v)
            ids = [int(z) for z in re.findall(r"block (\d+)", v)]
            for a in ids:
                for b in ids:
                    if a < b and (a, b) not in seen:
                        seen.add((a, b))
                        cat = (paircat.get((a, b)) or paircat.get((b, a))
                               or "NOT-A-PAIR(!)")
                        ma, mb = a in movers_sol, b in movers_sol
                        print(f"      pair ({a},{b}) mover=({ma},{mb}) "
                              f"cat={cat}")
    else:
        print(f"delta obj1 = {res['obj1'] - dump['obj1']:+.0f}  "
              f"delta obj = {res['objective'] - dump['objective']:+,.0f}")
        out = os.path.join(HERE, "dumps",
                           f"prob_{args.prob}.gurobi_nfp.bay{bay}.json")
        json.dump({"movers": {str(i): movers_sol[i] for i in movers_sol},
                   "before": before, "after": after, "bound": bound,
                   "feas": res["feasible"], "obj1": res["obj1"],
                   "objective": res["objective"]}, open(out, "w"))
        print(f"saved {out}")


if __name__ == "__main__":
    main()
