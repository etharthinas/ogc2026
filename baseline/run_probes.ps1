# Probe chain: steal -> nm_compete -> cap widening (serial, isolated processes)
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"

"=== probe_steal $(Get-Date -Format o) ===" | Out-File -Encoding utf8 probes.log
& $py probe_steal.py 2>&1 | Out-File -Encoding utf8 -Append probes.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

"=== probe_nmc $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append probes.log
& $py probe_nmc.py 2>&1 | Out-File -Encoding utf8 -Append probes.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

"=== probe_cap $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append probes.log
& $py probe_cap.py 2>&1 | Out-File -Encoding utf8 -Append probes.log
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

"=== probes done $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append probes.log
