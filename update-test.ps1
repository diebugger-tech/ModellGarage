# update-test.ps1 — im Repo, wird per git verteilt
# NUR für Test-VMs! Nicht auf dem Entwickler-PC (reset --hard verwirft lokale Arbeit)
$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Write-Host "== 1/3  Update von GitHub ==" -ForegroundColor Cyan
git fetch origin
git reset --hard origin/main
Write-Host "== 2/3  Neu starten ==" -ForegroundColor Cyan
.\start-podman.ps1
Write-Host "== 3/3  Healthcheck ==" -ForegroundColor Cyan
$ok = $false
foreach ($i in 1..30) {
    try {
        $r = Invoke-WebRequest http://localhost:8003 -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if ($ok) { Write-Host "OK - ModellGarage laeuft auf http://localhost:8003" -ForegroundColor Green }
else     { Write-Host "FEHLER - kam nicht hoch, Logs pruefen" -ForegroundColor Red }
