#!/usr/bin/env bash
# Same-day v37 CONTROLS on the 5 cells that moved under v38, to separate
# mechanism from session lottery. Waits for the v38 spot bench to drain first.
cd "$(dirname "$0")"
PY=.venv_ogc/Scripts/python.exe
while pgrep -f "_v38_verify.py" > /dev/null 2>&1; do sleep 20; done
for k in 21 22 29 25 40; do
  echo "=== v37 control prob_$k start $(date +%H:%M:%S) ===" >> v38_ctrl.log
  "$PY" baseline/_v37_verify.py "$k" 900 >> v38_ctrl.log 2>&1
done
echo "=== CONTROLS DONE $(date +%H:%M:%S) ===" >> v38_ctrl.log
