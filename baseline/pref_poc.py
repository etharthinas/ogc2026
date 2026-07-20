"""POC: does _z3_relocate recover the reducible preference penalty on a
zero-tardiness cell (prob_22) where the repack gate (best_tardy>0) blocks it?"""
import json, sys, time
sys.path.insert(0, '.')
import importlib
M = importlib.import_module('myalgorithm_jv9')
from utils import check_feasibility

def run(prob, tl):
    d = json.load(open(f'../train/prob_{prob}.json', encoding='utf-8'))
    sol = M.algorithm(d, tl)
    res0 = check_feasibility(d, sol)
    # reconstruct internal assign: op-dict key IS the time; ENTRY has geometry,
    # EXIT gives exit_time.
    assign = {}
    for t, lst in sol['operations'].items():
        for o in lst:
            bid = o['block_id']
            a = assign.setdefault(bid, {'block_id': bid})
            if o['type'] == 'ENTRY':
                a.update({'bay_id': o['bay_id'], 'x': o['x'], 'y': o['y'],
                          'orient_idx': o['orient_idx'], 'entry_time': int(t)})
            else:
                a['exit_time'] = int(t)
    bays = [M.Bay.from_dict(bd, i) for i, bd in enumerate(d['bays'])]
    bay_u = M._bay_u(bays)
    w = d['weights']; w1, w2, w3 = w['w1'], w['w2'], w['w3']
    obj0 = M._objective(assign, d['blocks'], bays, bay_u, w1, w2, w3)[0]
    raster = M._Raster(d, bays)
    t0 = time.time()
    r, oz = M._z3_relocate(d, assign, bays, bay_u, w1, w2, w3, raster,
                           deadline=time.time() + 40, pos_cap=32,
                           max_passes=6, time_cap=40)
    dt = time.time() - t0
    print(f'prob_{prob}: jv9 obj={res0.get("objective"):,}  internal_obj0={obj0:,.0f}')
    if r is not None:
        # verify the relocated solution is officially feasible
        ops = {'operations': M._build_operations(r)}
        res1 = check_feasibility(d, ops)
        print(f'  _z3_relocate -> obj={oz:,.0f}  gain={obj0-oz:,.0f}  '
              f'feasible={res1["feasible"]}  official_obj={res1.get("objective"):,}  ({dt:.0f}s)')
    else:
        print(f'  _z3_relocate returned None (no improvement) ({dt:.0f}s)')

if __name__ == '__main__':
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 22,
        float(sys.argv[2]) if len(sys.argv) > 2 else 150)
