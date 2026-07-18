# Merge-cap A/B: cap24 (control) vs cap40 on high-harvest non-forced cells.
# Same module (jv6b); the only diff is OGC_MERGE_CAP. Adjacent runs per cell.
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location -LiteralPath $PSScriptRoot
$log = "mergecap.log"
"=== merge-cap A/B jv6b cap24 vs cap40 {9 12 16 18} @750s $(Get-Date -Format o) ===" | Out-File -Encoding utf8 $log
foreach ($k in 9,12,16,18) {
    $env:OGC_MERGE_CAP = "24"
    "--- prob_$k cap24 ---" | Out-File -Encoding utf8 -Append $log
    & $py bench.py myalgorithm_jv6b 750 $k 2>&1 | Out-File -Encoding utf8 -Append $log
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $env:OGC_MERGE_CAP = "40"
    "--- prob_$k cap40 ---" | Out-File -Encoding utf8 -Append $log
    & $py bench.py myalgorithm_jv6b 750 $k 2>&1 | Out-File -Encoding utf8 -Append $log
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append $log
