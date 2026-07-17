# jv6b A/B chain: smoke prob_1 byte-identity -> A/B @750s on touched cells {38,39,37}
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"

"=== smoke jv6b 60s prob_1 (expect 1,499) $(Get-Date -Format o) ===" | Out-File -Encoding utf8 jv6b_ab.log
& $py bench.py myalgorithm_jv6b 60 1 2>&1 | Out-File -Encoding utf8 -Append jv6b_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

"=== A/B jv6 vs jv6b 750s {38,39,37} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append jv6b_ab.log
& $py compare.py myalgorithm_jv6 myalgorithm_jv6b 750 38 39 37 2>&1 | Out-File -Encoding utf8 -Append jv6b_ab.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append jv6b_ab.log
