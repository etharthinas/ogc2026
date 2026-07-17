# Night chain 3: A/B jv6 vs jv6b-r3 {31} + protect {33} @750s (~50 min)
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location -LiteralPath $PSScriptRoot
"=== A/B jv6 vs jv6b-r3 750s {31 33} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 night3.log
& $py compare.py myalgorithm_jv6 myalgorithm_jv6b 750 31 33 2>&1 | Out-File -Encoding utf8 -Append night3.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append night3.log
