# jv15 target-assignment generator: per-instance CP-SAT bay assignment
# minimizing w3*Z3 + w2*Z2max subject to bucketed area-time capacity at the
# blocks' release windows. Instance-only inputs => can be embedded in
# algorithm() later. Writes dumps/prob_k.z3target.json = {block_id: bay_id}.
#
# Usage: z3_target.py <prob_num> [capfrac=0.85] [maxsec=20]
import json, os, sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
from ortools.sat.python import cp_model

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, '..', 'train')
DUMPS = os.path.join(HERE, 'dumps')


def bbox_area(block, oi=0):
    xs, ys = [], []
    for layer in block['shape'][oi]['layers']:
        for x, y in layer:
            xs.append(x)
            ys.append(y)
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def min_bbox_area(block):
    return min(bbox_area(block, oi) for oi in range(len(block['shape'])))


def solve(pnum, capfrac=0.85, maxsec=20.0):
    p = json.load(open(os.path.join(TRAIN, f'prob_{pnum}.json')))
    blocks, bays, w = p['blocks'], p['bays'], p['weights']
    nb, nbay = len(blocks), len(bays)
    A = [b['width'] * b['height'] for b in bays]
    avgA = sum(A) / nbay
    u = [avgA / a for a in A]
    w1, w2, w3 = w['w1'], w['w2'], w['w3']

    area = [min_bbox_area(b) for b in blocks]
    procs = sorted(b['processing_time'] for b in blocks)
    g = max(1, int(round(procs[len(procs) // 2] / 2)))
    H = max(b['due_date'] for b in blocks)
    nbuck = H // g + 2

    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f'x{i}_{j}') for j in range(nbay)] for i in range(nb)]
    for i in range(nb):
        m.AddExactlyOne(x[i])
        # forbid bays the block cannot fit (bbox min side check, any orient)
        for j in range(nbay):
            fits = any(
                _fits(blocks[i], oi, bays[j]) for oi in range(len(blocks[i]['shape'])))
            if not fits:
                m.Add(x[i][j] == 0)

    # bucketed release-window capacity: window_i = [rel, rel+proc).
    # capfrac > 1 tolerates release-peak oversubscription that real schedules
    # smooth by delaying entries; capfrac <= 0 disables buckets entirely.
    SC = 100
    if capfrac > 0:
        for j in range(nbay):
            cap = int(capfrac * A[j] * g * SC)
            for b in range(nbuck):
                lo, hi = b * g, (b + 1) * g
                terms = []
                for i in range(nb):
                    rel = blocks[i]['release_time']
                    en, ex = rel, rel + blocks[i]['processing_time']
                    ov = max(0, min(ex, hi) - max(en, lo))
                    if ov > 0:
                        terms.append(int(area[i] * ov * SC) * x[i][j])
                if terms:
                    m.Add(sum(terms) <= cap)

    # aggregate horizon capacity too (matches z3_floor screen)
    for j in range(nbay):
        m.Add(sum(int(area[i] * blocks[i]['processing_time'] * SC) * x[i][j]
                  for i in range(nb)) <= int(A[j] * H * SC))

    # Z2max via aux var (scaled)
    S = 10 ** 4
    L = []
    for j in range(nbay):
        lj = m.NewIntVar(0, 10 ** 9, f'L{j}')
        m.Add(lj == sum(int(blocks[i]['workload']) * x[i][j] for i in range(nb)))
        L.append(lj)
    z2 = m.NewIntVar(0, 10 ** 12, 'z2')
    for j in range(nbay):
        for k in range(j + 1, nbay):
            uj, uk = int(round(u[j] * S)), int(round(u[k] * S))
            m.Add(uj * L[j] - uk * L[k] <= z2)
            m.Add(uk * L[k] - uj * L[j] <= z2)

    z3 = sum((max(blocks[i]['bay_preferences']) - blocks[i]['bay_preferences'][j]) * x[i][j]
             for i in range(nb) for j in range(nbay))
    m.Minimize(w3 * S * z3 + w2 * z2)

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = maxsec
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f'prob_{pnum}: NO SOLUTION (capfrac={capfrac})')
        return None
    tgt = {}
    for i in range(nb):
        for j in range(nbay):
            if s.Value(x[i][j]):
                tgt[i] = j
    z3v = sum(max(blocks[i]['bay_preferences']) - blocks[i]['bay_preferences'][tgt[i]]
              for i in range(nb))
    z2v = s.Value(z2) / S
    out = os.path.join(DUMPS, f'prob_{pnum}.z3target.json')
    json.dump({str(k): v for k, v in tgt.items()}, open(out, 'w'))
    print(f'prob_{pnum}: target Z3={z3v} (w3*Z3={w3 * z3v:,}) Z2~{z2v:.0f} '
          f'opt={st == cp_model.OPTIMAL} capfrac={capfrac} -> {os.path.basename(out)}')
    return out


def _fits(block, oi, bay):
    xs, ys = [], []
    for layer in block['shape'][oi]['layers']:
        for x, y in layer:
            xs.append(x)
            ys.append(y)
    return (max(xs) - min(xs)) <= bay['width'] and (max(ys) - min(ys)) <= bay['height']


if __name__ == '__main__':
    pnum = int(sys.argv[1])
    if len(sys.argv) > 2:
        solve(pnum, float(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 20.0)
    else:
        # relaxation ladder: tightest feasible bucket cap wins
        for cf in (0.95, 1.1, 1.3, 1.6, -1.0):
            if solve(pnum, cf) is not None:
                break
