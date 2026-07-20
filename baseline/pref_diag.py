"""Preference-penalty reducibility diagnostic. For a low-tardiness cell, run
jv9, then for each off-preference block check whether a MORE-preferred bay is
physically big enough (bbox fits) -- an upper bound on reducible w3*Z3."""
import json, sys, time, math
sys.path.insert(0, '.')
import importlib
M = importlib.import_module('myalgorithm_jv9')
from utils import check_feasibility

def orient_bbox(shape_o):
    layers = shape_o['layers']
    pts = [v for L in layers for v in L]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (max(xs)-min(xs), max(ys)-min(ys))

def fits_bay(bl, bay):
    W, H = bay['width'], bay['height']
    for o in bl['shape']:
        w, h = orient_bbox(o)
        if (w <= W and h <= H):
            return True
    return False

def run(prob, tl):
    d = json.load(open(f'../train/prob_{prob}.json', encoding='utf-8'))
    t0 = time.time()
    sol = M.algorithm(d, tl)
    rt = time.time()-t0
    res = check_feasibility(d, sol)
    assigned = {}
    for _t, lst in sol['operations'].items():
        for o in lst:
            if o['type'] == 'ENTRY':
                assigned[o['block_id']] = o
    blocks = d['blocks']; bays = d['bays']; w3 = d['weights']['w3']
    off = 0; offpen = 0; fit_pen = 0; fit_n = 0
    for bid, o in assigned.items():
        prefs = blocks[bid]['bay_preferences']
        bay = o['bay_id']
        pen = max(prefs) - prefs[bay]
        if pen > 0:
            off += 1; offpen += pen
            # a more-preferred bay that the block's bbox fits in?
            better = [j for j in range(len(prefs))
                      if prefs[j] > prefs[bay] and fits_bay(blocks[bid], bays[j])]
            if better:
                fit_n += 1
                best_pref = max(prefs[j] for j in better)
                fit_pen += (best_pref - prefs[bay])
    print(f'prob_{prob}: rt={rt:.0f}s feasible={res["feasible"]} obj={res.get("objective"):,}')
    print(f'  off-pref blocks: {off}/{len(assigned)}  w3*penalty={offpen*w3:,}')
    print(f'  off-pref blocks whose preferred bay FITS (bbox): {fit_n}  '
          f'-> reducible-upper-bound w3*Z3 = {fit_pen*w3:,}')

if __name__ == '__main__':
    prob = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 150
    run(prob, tl)
