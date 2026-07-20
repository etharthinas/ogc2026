"""Lower-bound + packing-density analysis on the giants (jv13-era, 2026-07-21).
Finding: giant tardiness is 2D-irregular-packing-limited, NOT capacity-limited.
Area-relaxation CP-SAT gives Z1_LB: 38>=135, 27>=55, 39=37=0 (OPTIMAL) vs
heuristic-achieved Z1 2598/1628/553/899. Peak release demand 38/27 = 139/141%
cap (some tardiness forced), 39/37 <=92% (fully packing-caused). The gap
between achieved and the area-floor is the cost of imperfect irregular nesting,
which local exact-pack (windows + whole-bay) already failed to close.
Conclusion: <120M is packing-limited, not proven foreclosed; closing it needs a
global irregular nester (No-Fit-Polygon class) integrated with the time
schedule -- the high-risk multi-day moonshot. Run: python lb_analysis.py
"""
import json
from ortools.sat.python import cp_model
def shoelace(p):
    a=0.0
    for i in range(len(p)):
        x1,y1=p[i]; x2,y2=p[(i+1)%len(p)]; a+=x1*y2-x2*y1
    return abs(a)/2.0
def barea(bl): return min(shoelace(o['layers'][0]) for o in bl['shape'])
def analyze(prob, tl=45.0):
    d=json.load(open(f'../train/prob_{prob}.json',encoding='utf-8'))
    B=d['blocks']; bays=d['bays']; w=d['weights']
    cap=sum(int(b['width']*b['height']) for b in bays)
    proc=[int(b['processing_time']) for b in B]; rel=[int(b['release_time']) for b in B]
    due=[int(b['due_date']) for b in B]; area=[max(1,int(round(barea(b)))) for b in B]
    H=max(due)+sum(proc)+50; m=cp_model.CpModel(); ivs=[]; tards=[]
    for i in range(len(B)):
        s=m.NewIntVar(rel[i],H,f's{i}'); e=m.NewIntVar(rel[i],H+max(proc),f'e{i}')
        m.Add(e==s+proc[i]); ivs.append(m.NewIntervalVar(s,proc[i],e,f'iv{i}'))
        t=m.NewIntVar(0,H,f't{i}'); m.Add(t>=e-due[i]); tards.append(t)
    m.AddCumulative(ivs,area,cap); m.Minimize(sum(tards))
    so=cp_model.CpSolver(); so.parameters.max_time_in_seconds=tl; so.parameters.num_search_workers=8
    st=so.Solve(m)
    print(f'prob_{prob}: Z1_LB(area)>= {so.best_objective_bound:.0f}  incumbent={so.objective_value:.0f}  '
          f'w1*incumbent={w["w1"]*so.objective_value:,.0f}  status={so.status_name(st)}')
if __name__=='__main__':
    for p in (38,27,39,37): analyze(p)
