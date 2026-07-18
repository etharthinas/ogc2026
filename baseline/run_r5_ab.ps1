# r5 A/B: smoke prob_1 (byte-identity) -> A/B jv6 vs jv6b {39 31 38} @750s
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location -LiteralPath $PSScriptRoot
"=== smoke jv6b 60s prob_1 (expect 1,499) $(Get-Date -Format o) ===" | Out-File -Encoding utf8 r5_ab.log
& $py bench.py myalgorithm_jv6b 60 1 2>&1 | Out-File -Encoding utf8 -Append r5_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
"=== A/B jv6 vs jv6b-r5 750s {39 31 38} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append r5_ab.log
& $py compare.py myalgorithm_jv6 myalgorithm_jv6b 750 39 31 38 2>&1 | Out-File -Encoding utf8 -Append r5_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append r5_ab.log
