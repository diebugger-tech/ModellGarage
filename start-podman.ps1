# ModellGarage — Start unter Podman auf Windows
# Baut den Container und startet ihn auf http://localhost:8003.
# Doppelklick: start-podman.bat  (oder in PowerShell: .\start-podman.ps1)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "== ModellGarage - Podman-Start ==" -ForegroundColor Cyan

# 1. Podman verfuegbar? Falls gerade erst installiert, PATH auffrischen + suchen.
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    foreach ($d in @("C:\Program Files\RedHat\Podman\usr\bin", "C:\Program Files\RedHat\Podman")) {
        if (Test-Path $d) { $env:Path += ";$d" }
    }
    if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
        $exe = Get-ChildItem "C:\Program Files\RedHat" -Recurse -Filter podman.exe `
            -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($exe) { $env:Path += ";" + $exe.DirectoryName }
    }
}
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Host "Podman-CLI wurde nicht gefunden." -ForegroundColor Red
    Write-Host "Bitte einmal installieren:  winget install -e --id RedHat.Podman" -ForegroundColor Yellow
    Write-Host "Danach PowerShell neu oeffnen und start-podman.bat erneut ausfuehren." -ForegroundColor Yellow
    Read-Host "Enter zum Beenden"
    exit 1
}

# 2. Podman-Maschine sicherstellen (einrichten falls noetig) + starten
$machines = (podman machine list --format "{{.Name}}" 2>$null)
if (-not $machines) {
    Write-Host "Richte die Podman-Maschine ein (einmalig) ..." -ForegroundColor Yellow
    podman machine init
}
$running = (podman machine list --format "{{.Running}}" 2>$null) -join " "
if ($running -notmatch "true|running|Currently") {
    Write-Host "Starte die Podman-Maschine ..." -ForegroundColor Yellow
    try { podman machine start | Out-Null } catch { }
}

# 3. Image bauen (ohne 'podman compose' - braucht keinen Extra-Provider)
Write-Host "Baue das Image (erster Build dauert ein paar Minuten) ..." -ForegroundColor Yellow
podman build -t modellgarage:latest -f Containerfile .

# 4. Volumes + Container starten
podman volume create modellgarage-data 2>$null | Out-Null
podman volume create modellgarage-media 2>$null | Out-Null
podman rm -f modellgarage 2>$null | Out-Null
podman run -d --name modellgarage --restart=unless-stopped `
    -p 8003:8003 `
    -v modellgarage-data:/app/data `
    -v modellgarage-media:/app/media `
    -e APP_ENV=production `
    -e "DATABASE_URL=sqlite+aiosqlite:////app/data/modellgarage.db" `
    -e MEDIA_DIR=/app/media `
    modellgarage:latest

# 4. Auf Erreichbarkeit warten
$url = "http://localhost:8003"
Write-Host "Warte, bis die App bereit ist ..." -ForegroundColor Yellow
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$url/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}

Write-Host ""
if ($ok) {
    Write-Host "ModellGarage laeuft:  $url" -ForegroundColor Green
} else {
    Write-Host "Container gestartet, aber $url antwortet noch nicht." -ForegroundColor Yellow
    Write-Host "Logs ansehen:  podman logs -f modellgarage" -ForegroundColor Gray
}
Write-Host "Excel importieren:    im Browser auf 'Import' gehen und die .xlsx-Datei hochladen." -ForegroundColor Green
Write-Host "Stoppen:              stop-podman.bat  (oder: podman rm -f modellgarage)" -ForegroundColor Gray
Write-Host ""

try { Start-Process $url } catch { }
Read-Host "Enter zum Schliessen dieses Fensters (die App laeuft im Hintergrund weiter)"
