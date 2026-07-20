#!/usr/bin/env bash
# v38 spot bench: serial @900s, mass-ordered. Non-forced first, then the
# never-measured forced cells (40, 25), then band-widening bonus checks.
cd "$(dirname "$0")"
PY=.venv_ogc/Scripts/python.exe
for k in 28 40 34 21 35 22 24 29 25 36 37; do
  echo "=== prob_$k start $(date +%H:%M:%S) ===" >> v38_spots.log
  "$PY" baseline/_v38_verify.py "$k" 900 >> v38_spots.log 2>&1
done
echo "=== ALL DONE $(date +%H:%M:%S) ===" >> v38_spots.log
