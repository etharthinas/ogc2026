# Night chain 2: probe_tall (26) -> mid-tier A/B jv6 vs jv6b {31,33,26,23,30} @750s
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"

"=== probe_tall $(Get-Date -Format o) ===" | Out-File -Encoding utf8 night2.log
& $py probe_tall.py 2>&1 | Out-File -Encoding utf8 -Append night2.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

"=== A/B jv6 vs jv6b 750s midtier {31,33,26,23,30} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append night2.log
& $py compare.py myalgorithm_jv6 myalgorithm_jv6b 750 31 33 26 23 30 2>&1 | Out-File -Encoding utf8 -Append night2.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append night2.log
