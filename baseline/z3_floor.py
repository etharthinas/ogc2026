# Z3-floor screen: per-instance assignment relaxation.
# min w3*Z3  s.t.  one bay per block; per-bay area*time <= bay_area * horizon;
# pairwise normalized workload imbalance <= incumbent obj2 (from full40_jv9.log).
# Optimistic (geometry-free) => a floor. Cells with floor << current Z3 are live
# targets for workload-neutral swap reassignment; floor ~= current => forced.
import json, math, re, sys, os
from shapely.geometry import Polygon
from shapely.ops import unary_union
from ortools.sat.python import cp_model

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# incumbent obj2/obj3 per instance from the honest single-shot log
log = open(os.path.join(HERE, 'full40_jv9.log'), encoding='utf-8', errors='replace').read()
cur = {}
for n, tote, o1, o2, o3 in re.findall(
        r'prob_\s*(\d+):\s*([\d,]+)\s*\(\s*[\d.]+s\)\s*obj1=([\d.]+) obj2=(\d+) obj3=([\d.]+)', log):
    cur[int(n)] = dict(total=int(tote.replace(',', '')), obj1=float(o1), obj2=int(o2), obj3=float(o3))

def footprint_area(block):
    polys = []
    for layer in block['shape'][0]['layers']:
        p = Polygon(layer)
        if not p.is_valid:
            p = p.buffer(0)
        polys.append(p)
    return unary_union(polys).area

def solve_one(pnum, z2_slack=1.0, time_s=30):
    p = json.load(open(os.path.join(ROOT, f'train/prob_{pnum}.json')))
    blocks, bays, w = p['blocks'], p['bays'], p['weights']
    nb, nbay = len(blocks), len(bays)
    A = [b['width'] * b['height'] for b in bays]
    avgA = sum(A) / nbay
    u = [avgA / a for a in A]
    H = max(b['due_date'] for b in blocks)  # no-new-tardiness horizon
    area = [footprint_area(b) for b in blocks]

    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f'x{i}_{j}') for j in range(nbay)] for i in range(nb)]
    for i in range(nb):
        m.AddExactlyOne(x[i])
    # capacity: sum area_i*proc_i*x <= A_b*H   (scale to int)
    for j in range(nbay):
        m.Add(sum(int(round(area[i] * blocks[i]['processing_time'] * 100)) * x[i][j]
                  for i in range(nb)) <= int(A[j] * H * 100))
    # Z2 cap: |u_j*L_j - u_k*L_k| <= obj2_cur * slack, scaled 10^4
    S = 10 ** 4
    L = []
    for j in range(nbay):
        lj = m.NewIntVar(0, 10 ** 9, f'L{j}')
        m.Add(lj == sum(int(blocks[i]['workload']) * x[i][j] for i in range(nb)))
        L.append(lj)
    z2cap = int((cur[pnum]['obj2'] + 1) * z2_slack * S)
    for j in range(nbay):
        for k in range(j + 1, nbay):
            uj, uk = int(round(u[j] * S)), int(round(u[k] * S))
            m.Add(uj * L[j] - uk * L[k] <= z2cap)
            m.Add(uk * L[k] - uj * L[j] <= z2cap)
    # objective: Z3
    m.Minimize(sum((max(blocks[i]['bay_preferences']) - blocks[i]['bay_preferences'][j]) * x[i][j]
                   for i in range(nb) for j in range(nbay)))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_search_workers = 4
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return dict(z3_floor=s.ObjectiveValue(), bound=s.BestObjectiveBound(),
                opt=(st == cp_model.OPTIMAL))

if __name__ == '__main__':
    targets = [int(a) for a in sys.argv[1:]] or sorted(
        cur, key=lambda n: -cur[n]['obj3'])
    print(f"{'inst':>5} {'Z3cur':>8} {'Z3floor':>8} {'bound':>8} {'opt':>4} "
          f"{'w3':>5} {'pool(w3*(cur-floor))':>20}")
    tot_pool = 0
    for n in targets:
        w3 = json.load(open(os.path.join(ROOT, f'train/prob_{n}.json')))['weights']['w3']
        r = solve_one(n)
        if r is None:
            print(f"{n:>5} {cur[n]['obj3']:>8.0f} {'INFEAS':>8}")
            continue
        pool = w3 * max(0, cur[n]['obj3'] - r['z3_floor'])
        tot_pool += pool
        print(f"{n:>5} {cur[n]['obj3']:>8.0f} {r['z3_floor']:>8.0f} {r['bound']:>8.0f} "
              f"{str(r['opt'])[:1]:>4} {w3:>5} {pool:>20,.0f}", flush=True)
    print(f"TOTAL recoverable Z3 pool (optimistic): {tot_pool:,.0f}")
