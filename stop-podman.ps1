# ModellGarage — Stoppen (Podman auf Windows)
$ErrorActionPreference = "SilentlyContinue"
Set-Location -Path $PSScriptRoot
Write-Host "Stoppe ModellGarage ..." -ForegroundColor Yellow
podman compose down
Write-Host "Gestoppt. Daten (DB + Fotos) bleiben in den Podman-Volumes erhalten." -ForegroundColor Green
Read-Host "Enter zum Schliessen"
