# Overnight classifier: does WHOLE-BAY exact repack+retime (_exact_pack_bay)
# yield ANYTHING on the mid cells whose area-LB Z1 = 0 (26/33/31/30/28)?
# The jv13-era "zero yield" proof exists only for prob_39. One instance per
# process (cache protocol). Usage:
#   probe_exactpack_mid.py <prob> <dumpname> [budget_s=600] [ranks=3] [draws=2]
import importlib, json, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TRAIN = os.path.join(HERE, '..', 'train')
DUMPS = os.path.join(HERE, 'dumps')

def main():
    pnum = int(sys.argv[1])
    dumpname = sys.argv[2] if len(sys.argv) > 2 else f'prob_{pnum}.myalgorithm.json'
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
    ranks = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    draws = int(sys.argv[5]) if len(sys.argv) > 5 else 2

    M = importlib.import_module('myalgorithm')
    from utils import Bay
    prob = json.load(open(os.path.join(TRAIN, f'prob_{pnum}.json')))
    dump = json.load(open(os.path.join(DUMPS, dumpname)))
    M._reset_caches()
    try:
        M._MREL.clear()
    except Exception:
        pass

    bays = [Bay.from_dict(d, i) for i, d in enumerate(prob['bays'])]
    w = prob.get('weights', {})
    w1, w2, w3 = w.get('w1', 1.0), w.get('w2', 1.0), w.get('w3', 1.0)
    bay_u = M._bay_u(bays)
    src = {}
    for r in dump['blocks']:
        src[r['id']] = {
            'block_id': r['id'], 'bay_id': r['bay'], 'x': r['x'], 'y': r['y'],
            'orient_idx': r['orient'], 'entry_time': r['entry'],
            'exit_time': r['exit'],
        }
    base_obj = M._objective(src, prob['blocks'], bays, bay_u, w1, w2, w3)[0]
    print(f'prob_{pnum} base internal obj = {base_obj:,.0f} '
          f'(dump official {dump["objective"]:,.0f})', flush=True)
    raster = M._Raster(prob, bays)

    best_gain = 0.0
    for rank in range(ranks):
        for d in range(draws):
            rng = random.Random(1000 * rank + d * 77 + 5)
            t0 = time.time()
            deadline = time.time() + budget + 60
            res = M._exact_pack_bay(prob, src, bays, bay_u, w1, w2, w3,
                                    raster, rng, deadline, forced=True,
                                    budget_s=budget, bay_rank=rank,
                                    n_movers=28, K=10)
            el = time.time() - t0
            if res is None:
                print(f'  rank={rank} draw={d}: None ({el:.0f}s)', flush=True)
                continue
            o = M._objective(res, prob['blocks'], bays, bay_u, w1, w2, w3)[0]
            gain = base_obj - o
            print(f'  rank={rank} draw={d}: obj {o:,.0f} gain {gain:,.0f} ({el:.0f}s)',
                  flush=True)
            best_gain = max(best_gain, gain)
    print(f'prob_{pnum} BEST EXACT-PACK GAIN: {best_gain:,.0f}', flush=True)

if __name__ == '__main__':
    main()
