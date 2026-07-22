# Z3 reassignment probe (offline): fixed-times bay reassignment on a dumped
# incumbent. Times never change => Z1 is provably unchanged; only Z3 falls and
# Z2 moves within a cap. Geometry is validated with the OFFICIAL utils
# primitives (check_entry / check_exit / same-layer collision) plus a final
# check_feasibility on the rebuilt ops.
#
# Pass 0: CP-SAT fixed-times assignment => theoretical ceiling at bucketed
#         area capacity (reported, guides pass 1/2).
# Pass 1: single-block objective-descent moves (w3 gain beats w2 spike).
# Pass 2: pair swaps between bays (workload-matched cyclic exchange, the move
#         class _z3_relocate lacked).
#
# Usage: z3_reassign.py <prob_num> [dumpname] [--capfrac F] [--maxsec S]
import json, os, sys, time
from shapely.geometry import Polygon
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import utils
from utils import Bay, Block, check_entry, check_exit, check_feasibility

TRAIN = os.path.join(HERE, '..', 'train')
DUMPS = os.path.join(HERE, 'dumps')


def load(pnum, dumpname):
    prob = json.load(open(os.path.join(TRAIN, f'prob_{pnum}.json')))
    dump = json.load(open(os.path.join(DUMPS, dumpname)))
    recs = {r['id']: dict(bay=r['bay'], x=r['x'], y=r['y'], orient=r['orient'],
                          entry=r['entry'], exit=r['exit'])
            for r in dump['blocks']}
    return prob, dump, recs


def build_ops(recs):
    ops = {}
    for bid, r in recs.items():
        ops.setdefault(r['entry'], []).append(
            dict(type='ENTRY', block_id=bid, bay_id=r['bay'],
                 x=r['x'], y=r['y'], orient_idx=r['orient']))
        ops.setdefault(r['exit'], []).append(dict(type='EXIT', block_id=bid, bay_id=r['bay']))
    out = {}
    for t in sorted(ops):
        evs = sorted(ops[t], key=lambda e: 0 if e['type'] == 'EXIT' else 1)
        out[str(t)] = evs
    return {'operations': out}


def objective_parts(prob, recs):
    blocks = prob['blocks']
    bays = prob['bays']
    nbay = len(bays)
    w = prob['weights']
    o1 = sum(max(0, r['exit'] - blocks[i]['due_date']) for i, r in recs.items())
    loads = [0.0] * nbay
    o3 = 0.0
    for i, r in recs.items():
        loads[r['bay']] += blocks[i]['workload']
        o3 += max(blocks[i]['bay_preferences']) - blocks[i]['bay_preferences'][r['bay']]
    A = [b['width'] * b['height'] for b in bays]
    avgA = sum(A) / nbay
    u = [avgA / a for a in A]
    import math
    o2 = math.floor(max(abs(u[j] * loads[j] - u[k] * loads[k])
                        for j in range(nbay) for k in range(nbay) if j != k)) if nbay > 1 else 0
    return o1, o2, o3, w['w1'] * o1 + w['w2'] * o2 + w['w3'] * o3, loads


class GeomState:
    """Per-bay residents with utils.Block objects; fixed times."""
    def __init__(self, prob, recs):
        self.prob = prob
        self.bays = [Bay.from_dict(b, j) for j, b in enumerate(prob['bays'])]
        self.recs = recs
        self.blk = {}
        for i, r in recs.items():
            self.blk[i] = Block(i, prob['blocks'][i], r['x'], r['y'], r['orient'])
        self.residents = {j: set() for j in range(len(self.bays))}
        for i, r in recs.items():
            self.residents[r['bay']].add(i)
        self._pcache = {}   # (id,x,y,orient) -> [Polygon|None per layer]
        self._prep = {}     # same key -> [prepared|None per layer]

    def _polys(self, i):
        key = (i, self.blk[i].x, self.blk[i].y, self.blk[i].orient_idx)
        if key not in self._pcache:
            self._pcache[key] = [Polygon(l) if len(l) >= 3 else None
                                 for l in self.blk[i].layers_at_pos()]
            self._prep[key] = [prep(p) if p is not None else None
                               for p in self._pcache[key]]
        return self._pcache[key], self._prep[key]

    def overlapping(self, bay, entry, exit_, skip=()):
        out = []
        for k in self.residents[bay]:
            if k in skip:
                continue
            rk = self.recs[k]
            if rk['entry'] < exit_ and entry < rk['exit']:
                out.append(k)
        return out

    def present_at_entry(self, bay, t, skip=()):
        # conservative: same-tick entrants counted as present
        return [k for k in self.residents[bay] if k not in skip
                and self.recs[k]['entry'] <= t < self.recs[k]['exit']]

    def present_at_exit(self, bay, t, skip=()):
        # exits process before entries at t; same-tick exiters kept (conservative)
        return [k for k in self.residents[bay] if k not in skip
                and self.recs[k]['entry'] < t and self.recs[k]['exit'] >= t]

    def collision_free(self, cand, bay, entry, exit_, skip=(), overl=None):
        cl = [Polygon(l) if len(l) >= 3 else None for l in cand.layers_at_pos()]
        cbb = cand.bounding_rect()
        if overl is None:
            overl = self.overlapping(bay, entry, exit_, skip=skip)
        for k in overl:
            b = self.blk[k].bounding_rect()
            if not (cbb[0] < b[2] and b[0] < cbb[2] and cbb[1] < b[3] and b[1] < cbb[3]):
                continue
            kl, kprep = self._polys(k)
            for li in range(min(len(cl), len(kl))):
                p, q = cl[li], kprep[li]
                if p is None or q is None:
                    continue
                if q.intersects(p):
                    inter = cl[li].intersection(kl[li])
                    if inter.area > 1e-9:
                        return False
        return True

    def crane_ok(self, cand, i, bay, entry, exit_, skip=()):
        bayo = self.bays[bay]
        pres_e = [self.blk[k] for k in self.present_at_entry(bay, entry, skip=(i,) + tuple(skip))]
        if check_entry(bayo, pres_e, cand, fast=True):
            return False
        pres_x = [self.blk[k] for k in self.present_at_exit(bay, exit_, skip=(i,) + tuple(skip))]
        if check_exit(bayo, pres_x, cand, fast=True):
            return False
        # reverse: residents entering/exiting during cand's stay must stay feasible
        for k in self.residents[bay]:
            if k == i or k in skip:
                continue
            rk = self.recs[k]
            if entry < rk['entry'] < exit_:
                pres = [self.blk[m] for m in self.present_at_entry(bay, rk['entry'], skip=(k, i) + tuple(skip))]
                pres.append(cand)
                if check_entry(bayo, pres, self.blk[k], fast=True):
                    return False
            if entry < rk['exit'] <= exit_:
                pres = [self.blk[m] for m in self.present_at_exit(bay, rk['exit'], skip=(k, i) + tuple(skip))]
                pres.append(cand)
                if check_exit(bayo, pres, self.blk[k], fast=True):
                    return False
        return True

    def find_position(self, i, bay, skip=(), step=1, max_crane_tries=25,
                      time_budget=20.0, entry=None, exit_=None):
        """Bottom-left search for block i in bay (any orientation), optionally
        at alternative times. Fast path: AABB occupancy prefilter against
        time-overlapping residents, exact polygon + crane checks only on
        surviving anchors."""
        import math
        t0 = time.time()
        bd = self.prob['blocks'][i]
        r = self.recs[i]
        if entry is None:
            entry = r['entry']
        if exit_ is None:
            exit_ = r['exit']
        bayd = self.prob['bays'][bay]
        overl = self.overlapping(bay, entry, exit_, skip=(i,) + tuple(skip))
        boxes = [self.blk[k].bounding_rect() for k in overl]
        tried = 0
        for oi in range(len(bd['shape'])):
            probe = Block(i, bd, 0, 0, oi)
            bb = probe.bounding_rect()
            xlo, xhi = -bb[0], bayd['width'] - bb[2]
            ylo, yhi = -bb[1], bayd['height'] - bb[3]
            if xhi < xlo or yhi < ylo:
                continue
            w_, h_ = bb[2] - bb[0], bb[3] - bb[1]
            anchors = []
            for y in range(math.ceil(ylo), math.floor(yhi) + 1, step):
                for x in range(math.ceil(xlo), math.floor(xhi) + 1, step):
                    # candidate footprint bbox in world coords
                    cb = (x + bb[0], y + bb[1], x + bb[2], y + bb[3])
                    nfree = sum(1 for b in boxes
                                if cb[0] < b[2] and b[0] < cb[2]
                                and cb[1] < b[3] and b[1] < cb[3])
                    anchors.append((nfree, y, x))
            # bbox-free first (nfree==0 passes collision trivially), then low-overlap
            anchors.sort()
            for nfree, y, x in anchors:
                if time.time() - t0 > time_budget:
                    return None
                cand = Block(i, bd, x, y, oi)
                if nfree > 0 and not self.collision_free(
                        cand, bay, entry, exit_, skip=skip, overl=overl):
                    continue
                tried += 1
                if self.crane_ok(cand, i, bay, entry, exit_, skip=skip):
                    return cand
                if tried >= max_crane_tries:
                    break
        return None

    def apply_move(self, i, bay, cand, entry=None, exit_=None):
        old = self.recs[i]['bay']
        self.residents[old].discard(i)
        self.residents[bay].add(i)
        self.recs[i]['bay'] = bay
        self.recs[i]['x'] = cand.x
        self.recs[i]['y'] = cand.y
        self.recs[i]['orient'] = cand.orient_idx
        if entry is not None:
            self.recs[i]['entry'] = entry
            self.recs[i]['exit'] = exit_
        self.blk[i] = cand

    def restore(self, i, saved):
        """Exact rollback of block i to a saved rec (state otherwise unchanged)."""
        cur_bay = self.recs[i]['bay']
        self.residents[cur_bay].discard(i)
        self.residents[saved['bay']].add(i)
        self.recs[i] = dict(saved)
        self.blk[i] = Block(i, self.prob['blocks'][i], saved['x'], saved['y'], saved['orient'])


def main():
    pnum = int(sys.argv[1])
    dumpname = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') \
        else f'prob_{pnum}.myalgorithm.json'
    maxsec = 600.0
    for a in sys.argv:
        if a.startswith('--maxsec'):
            maxsec = float(a.split('=')[1])
    t0 = time.time()
    prob, dump, recs = load(pnum, dumpname)
    blocks = prob['blocks']
    w = prob['weights']
    w1, w2, w3 = w['w1'], w['w2'], w['w3']
    nbay = len(prob['bays'])
    A = [b['width'] * b['height'] for b in prob['bays']]
    avgA = sum(A) / nbay
    u = [avgA / a for a in A]

    o1, o2, o3, obj, loads = objective_parts(prob, recs)
    print(f'prob_{pnum} incumbent: obj={obj:,.0f} o1={o1} o2={o2} o3={o3} '
          f'(dump said obj={dump["objective"]:,.0f} o3={dump["obj3"]})', flush=True)

    st = GeomState(prob, recs)

    def z2_of(loads_):
        import math
        return math.floor(max(abs(u[j] * loads_[j] - u[k] * loads_[k])
                              for j in range(nbay) for k in range(nbay) if j != k)) if nbay > 1 else 0

    def pen(i, b):
        return max(blocks[i]['bay_preferences']) - blocks[i]['bay_preferences'][b]

    applied = []
    fail_time, fail_geom = 0, 0

    def cand_times(i, b, limit=8):
        """Candidate (delta, entry, exit) tuples for moving i to bay b, sorted
        by exact objective delta (w1 tardiness + w2 z2 + w3 pref)."""
        bd = blocks[i]
        r = recs[i]
        rel, proc, due = bd['release_time'], bd['processing_time'], bd['due_date']
        g3 = pen(i, r['bay']) - pen(i, b)
        nl = list(loads)
        nl[r['bay']] -= bd['workload']
        nl[b] += bd['workload']
        dz2 = w2 * (z2_of(nl) - z2_of(loads))
        tard0 = max(0, r['exit'] - due)
        ts = {r['entry'], rel, max(rel, due - proc)}
        for k in st.residents[b]:
            e = recs[k]['exit']
            if e >= rel:
                ts.add(e)
        out = []
        for t in ts:
            ex = t + proc
            delta = w1 * (max(0, ex - due) - tard0) + dz2 - w3 * g3
            if delta < 0:
                out.append((delta, t, ex))
        out.sort()
        return out[:limit], nl

    # ---- Pass 1: single objective-descent moves (time-flexible) ----------
    improved = True
    while improved and time.time() - t0 < maxsec * 0.6:
        improved = False
        order = sorted(((pen(i, recs[i]['bay']), i) for i in recs), reverse=True)
        for peni, i in order:
            if peni <= 0 or time.time() - t0 > maxsec * 0.6:
                break
            r = recs[i]
            for b in sorted(range(nbay), key=lambda bb: pen(i, bb)):
                if b == r['bay'] or pen(i, b) >= peni:
                    continue
                tries, nl = cand_times(i, b)
                if not tries:
                    fail_time += 1
                    continue
                done = False
                for delta, t, ex in tries[:4]:
                    cand = st.find_position(i, b, entry=t, exit_=ex, time_budget=10.0)
                    if cand is not None:
                        st.apply_move(i, b, cand, entry=t, exit_=ex)
                        loads[:] = nl
                        applied.append(('move', i, b, delta))
                        improved = True
                        done = True
                        break
                if done:
                    break
                fail_geom += 1
    n1 = len(applied)
    o1b, o2b, o3b, objb, _ = objective_parts(prob, recs)
    print(f'pass1: {n1} moves (fail_time={fail_time} fail_geom={fail_geom}), '
          f'obj {obj:,.0f} -> {objb:,.0f} (d={objb - obj:,.0f}) '
          f'o1 {o1}->{o1b} o3 {o3}->{o3b} [{time.time() - t0:.0f}s]', flush=True)

    # ---- Pass 2: pair swaps ----------------------------------------------
    pairs_tried = 0
    improved = True
    while improved and time.time() - t0 < maxsec:
        improved = False
        # blocks that still want another bay, by remaining penalty
        wanting = sorted(((pen(i, recs[i]['bay']), i) for i in recs
                          if pen(i, recs[i]['bay']) > 0), reverse=True)
        for peni, i in wanting[:60]:
            if time.time() - t0 > maxsec:
                break
            ri = recs[i]
            # best target bay for i
            tb = min(range(nbay), key=lambda b: pen(i, b))
            if tb == ri['bay']:
                continue
            # partner candidates in tb: swapping reduces combined penalty
            best = None
            for j in list(st.residents[tb]):
                rj = recs[j]
                g = (pen(i, ri['bay']) + pen(j, tb)) - (pen(i, tb) + pen(j, ri['bay']))
                if g <= 0:
                    continue
                nl = list(loads)
                nl[ri['bay']] += blocks[j]['workload'] - blocks[i]['workload']
                nl[tb] += blocks[i]['workload'] - blocks[j]['workload']
                delta = -w3 * g + w2 * (z2_of(nl) - z2_of(loads))
                if delta < 0 and (best is None or delta < best[0]):
                    best = (delta, j, nl)
            if best is None:
                continue
            delta, j, nl = best
            pairs_tried += 1
            src = ri['bay']
            saved_i, saved_j = dict(recs[i]), dict(recs[j])
            # geometry: place i in tb (j hypothetically absent), then j in src
            ci = st.find_position(i, tb, skip=(j,), time_budget=10.0)
            if ci is None:
                continue
            st.apply_move(i, tb, ci)
            cj = st.find_position(j, src, time_budget=10.0)
            if cj is None:
                st.restore(i, saved_i)
                continue
            st.apply_move(j, src, cj)
            loads[:] = nl
            applied.append(('swap', i, j, delta))
            improved = True

    o1c, o2c, o3c, objc, _ = objective_parts(prob, recs)
    print(f'pass2: total {len(applied)} ops ({pairs_tried} pair-geoms tried), '
          f'obj {objb:,.0f} -> {objc:,.0f} o3 {o3b}->{o3c} [{time.time() - t0:.0f}s]', flush=True)

    # ---- official verification -------------------------------------------
    sol = build_ops(recs)
    res = check_feasibility(prob, sol)
    print(f'CHECKER: feasible={res["feasible"]} obj={res["objective"]:,.0f} '
          f'o1={res["obj1"]} o2={res["obj2"]} o3={res["obj3"]}'
          if res['feasible'] else f'CHECKER: INFEASIBLE stage={res["stage"]} {res["violations"][:3]}',
          flush=True)
    if res['feasible']:
        gain = dump['objective'] - res['objective']
        print(f'prob_{pnum} REALIZED GAIN vs dump: {gain:,.0f}', flush=True)
        out = os.path.join(DUMPS, f'prob_{pnum}.z3re.json')
        json.dump({'instance': pnum, 'objective': res['objective'],
                   'recs': {str(k): v for k, v in recs.items()}}, open(out, 'w'))


if __name__ == '__main__':
    main()
