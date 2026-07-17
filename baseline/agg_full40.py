#!/usr/bin/env python3
"""Aggregate a run_full40.ps1 log into a results.csv-style row.
Usage: python agg_full40.py <label> <logfile>"""
import re, sys

label, logf = sys.argv[1], sys.argv[2]
vals = {}
pat = re.compile(r"prob_\s*(\d+):\s+([\d,]+)\s+\(")
crash = re.compile(r"prob_\s*(\d+):\s+(CRASH|INFEASIBLE)")
for enc in ("utf-8-sig", "utf-16", "cp949"):
    try:
        text = open(logf, encoding=enc).read()
        break
    except (UnicodeDecodeError, UnicodeError):
        continue
for m in pat.finditer(text):
    vals[int(m.group(1))] = int(m.group(2).replace(",", ""))
bad = [(int(m.group(1)), m.group(2)) for m in crash.finditer(text)]
missing = [k for k in range(1, 41) if k not in vals]
if bad:
    print("BAD:", bad)
if missing:
    print("MISSING:", missing)
total = sum(vals.values())
row = ",".join(str(vals.get(k, "")) for k in range(1, 41))
print(f"{label},{row},{total}")
print(f"feasible {len(vals)}/40  TOTAL = {total:,}")
