#!/usr/bin/env bash
# Continuation: v37 controls for prob_25 and prob_40 (the wrapper for the
# first control batch was killed after prob_29 started). tasklist guard --
# pgrep does NOT see Windows processes under git-bash.
cd "$(dirname "$0")"
PY=.venv_ogc/Scripts/python.exe
while tasklist //FI "IMAGENAME eq python.exe" 2>/dev/null | grep -qi python; do
  sleep 20
done
for k in 25 40; do
  echo "=== v37 control prob_$k start $(date +%H:%M:%S) ===" >> v38_ctrl.log
  "$PY" baseline/_v37_verify.py "$k" 900 >> v38_ctrl.log 2>&1
done
echo "=== CONTROLS DONE $(date +%H:%M:%S) ===" >> v38_ctrl.log
