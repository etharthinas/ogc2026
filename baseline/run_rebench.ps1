# Isolated re-bench of disputed tail cells after the full-40: 38 then 37 @750s
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"
"=== rebench 38 @750s $(Get-Date -Format o) ===" | Out-File -Encoding utf8 rebench.log
& $py bench.py myalgorithm_jv6 750 38 2>&1 | Out-File -Encoding utf8 -Append rebench.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
"=== rebench 37 @750s $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append rebench.log
& $py bench.py myalgorithm_jv6 750 37 2>&1 | Out-File -Encoding utf8 -Append rebench.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append rebench.log
