#!/usr/bin/env bash
# jv15 evening pipeline 2026-07-22: dumps -> A/Bs -> exact-pack marathon.
# Sequential on purpose: bench numbers need an uncontended machine.
cd "$(dirname "$0")"
PY=/c/Users/user/anaconda3/envs/ogc2026/python.exe
LOG=evening_jv15.log
echo "=== pipeline start $(date) ===" >> "$LOG"

echo "--- stage 1: dumps 28 30 33 26 ---" >> "$LOG"
"$PY" bench_dump.py myalgorithm 750 28 30 33 26 >> "$LOG" 2>&1

echo "--- stage 2: NG_DEAF A/B @750s on 31 33 ---" >> "$LOG"
OGC_NG_DEAF=1 "$PY" compare.py myalgorithm myalgorithm_jv15 750 31 33 >> "$LOG" 2>&1

echo "--- stage 3: Z3-bias A/B @750s on 37 ---" >> "$LOG"
OGC_Z3_TARGET=dumps/prob_37.z3target.json OGC_Z3_BONUS=1e9 \
  "$PY" compare.py myalgorithm myalgorithm_jv15 750 37 >> "$LOG" 2>&1

echo "--- stage 4: exact-pack marathon (600s x 3 ranks x 2 draws) ---" >> "$LOG"
for k in 26 33 31 30 28; do
  "$PY" probe_exactpack_mid.py "$k" "prob_${k}.myalgorithm.json" 600 3 2 >> "$LOG" 2>&1
done
echo "=== pipeline done $(date) ===" >> "$LOG"
