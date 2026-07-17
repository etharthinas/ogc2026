# Full-40 bench with per-instance process isolation (orphan-leak-proof).
# Usage: powershell -ExecutionPolicy Bypass -NoProfile -File run_full40.ps1 <module> <timelimit> <label>
param(
    [string]$Module = "myalgorithm_jv6",
    [double]$TimeLimit = 750,
    [string]$Label = "jv6"
)
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"
$log = "full40_$Label.log"

"=== full-40 $Module @${TimeLimit}s start $(Get-Date -Format o) ===" | Out-File -Encoding utf8 $log
foreach ($k in 1..40) {
    & $py bench.py $Module $TimeLimit $k 2>&1 | Out-File -Encoding utf8 -Append $log
    # belt-and-braces: reap any straggler workers between instances
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}
"=== full-40 done $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append $log

# aggregate: parse per-instance objectives into a results.csv-style row
& $py agg_full40.py $Label $log 2>&1 | Out-File -Encoding utf8 -Append $log
& $py agg_full40.py $Label $log
