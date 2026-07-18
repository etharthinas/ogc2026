$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location -LiteralPath $PSScriptRoot
"=== smoke jv6b 60s prob_1 $(Get-Date -Format o) ===" | Out-File -Encoding utf8 r7_ab.log
& $py bench.py myalgorithm_jv6b 60 1 2>&1 | Out-File -Encoding utf8 -Append r7_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
"=== A/B jv6 vs jv6b-r7 (FORCED drain seed) 750s {27 38 39} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append r7_ab.log
& $py compare.py myalgorithm_jv6 myalgorithm_jv6b 750 27 38 39 2>&1 | Out-File -Encoding utf8 -Append r7_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append r7_ab.log
