# ModellGarage — Stoppen (Podman auf Windows)
$ErrorActionPreference = "SilentlyContinue"
Set-Location -Path $PSScriptRoot
Write-Host "Stoppe ModellGarage ..." -ForegroundColor Yellow
# 'podman rm -f' entfernt NUR den Container. Die benannten Volumes
# (modellgarage-media, modellgarage-data) bleiben erhalten -> Fotos + DB sicher.
podman rm -f modellgarage | Out-Null
Write-Host "Gestoppt. Daten (DB + Fotos) bleiben in den Podman-Volumes erhalten." -ForegroundColor Green
Write-Host ""
Write-Host "WICHTIG - diese Volumes NIEMALS loeschen, sonst sind Fotos UND DB weg:" -ForegroundColor Red
Write-Host "  modellgarage-media  (Fotos)      modellgarage-data  (Datenbank)" -ForegroundColor Gray
Write-Host "  Gefaehrlich:  podman volume rm modellgarage-media" -ForegroundColor Gray
Write-Host "                podman volume rm modellgarage-data" -ForegroundColor Gray
Write-Host "                podman machine reset" -ForegroundColor Gray
Write-Host "                podman system prune --volumes" -ForegroundColor Gray
Write-Host "Backup laeuft ueber den App-Export (Excel), NICHT ueber Git." -ForegroundColor Yellow
Read-Host "Enter zum Schliessen"
