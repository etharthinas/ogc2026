# jv6 gate chain: warmup (Defender scan) -> prob_1 gate -> hot A/B @750s {38,27}
# Serial, one python at a time; logs flushed per instance.
$py = "C:\Users\user\anaconda3\envs\ogc2026\python.exe"
Set-Location "c:\Users\user\OneDrive\문서\ogc2026\baseline"

"=== warmup jv6 30s prob_1 $(Get-Date -Format o) ===" | Out-File -Encoding utf8 jv6_gate.log
& $py bench.py myalgorithm_jv6 30 1 2>&1 | Out-File -Encoding utf8 -Append jv6_gate.log
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID } | Out-Null

"=== gate jv6 60s prob_1 $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append jv6_gate.log
& $py bench.py myalgorithm_jv6 60 1 2>&1 | Out-File -Encoding utf8 -Append jv6_gate.log

"=== hot A/B v33 vs jv6 750s {38,27} $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append jv6_gate.log
& $py compare.py myalgorithm_v33_ref myalgorithm_jv6 750 38 27 2>&1 | Out-File -Encoding utf8 -Append jv6_gate.log
"=== DONE $(Get-Date -Format o) ===" | Out-File -Encoding utf8 -Append jv6_gate.log
