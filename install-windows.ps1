# ModellGarage - Ein-Kommando-Installer fuer Windows
# ---------------------------------------------------------------------------
# In einer PowerShell ALS ADMINISTRATOR ausfuehren (Rechtsklick auf PowerShell
# -> "Als Administrator ausfuehren") und dann EINE Zeile einfuegen:
#
#   irm https://raw.githubusercontent.com/diebugger-tech/ModellGarage/main/install-windows.ps1 | iex
#
# Der Installer: installiert Podman Desktop, richtet WSL/die Podman-Maschine ein,
# laedt das Projekt (ohne git, per ZIP) und startet die App auf http://localhost:8003.
# ---------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }

Info "== ModellGarage - Windows-Installer =="

# 0. Administrator?
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
  ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Warn "Bitte PowerShell ALS ADMINISTRATOR oeffnen und den Befehl erneut einfuegen."
  return
}

# 1. Podman Desktop installieren (falls noch nicht vorhanden)
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
  Info "Installiere Podman Desktop (winget) ..."
  winget install -e --id RedHat.Podman-Desktop --silent `
    --accept-package-agreements --accept-source-agreements
}

# PATH dieser Sitzung auffrischen, damit 'podman' sofort gefunden wird
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [Environment]::GetEnvironmentVariable("Path", "User")
$podmanDir = "C:\Program Files\RedHat\Podman"
if (Test-Path $podmanDir) { $env:Path += ";$podmanDir" }

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
  Warn "Podman ist installiert, aber in dieser Sitzung noch nicht verfuegbar."
  Warn "Bitte den Rechner EINMAL NEU STARTEN und diesen Befehl erneut einfuegen."
  return
}

# 2. WSL2 vorhanden? (Podman braucht es auf Windows)
$wslOk = $true
try { wsl.exe --status *> $null } catch { $wslOk = $false }
if (-not $wslOk) {
  Warn "WSL2 fehlt - installiere es jetzt (danach ist ein NEUSTART noetig) ..."
  try { wsl.exe --install } catch { }
  Warn "Bitte Windows NEU STARTEN und diesen Befehl danach erneut einfuegen."
  return
}

# 3. Podman-Maschine einrichten + starten
$machines = (podman machine list --format "{{.Name}}" 2>$null)
if (-not $machines) {
  Info "Richte die Podman-Maschine ein (einmalig) ..."
  podman machine init
}
Info "Starte die Podman-Maschine ..."
try { podman machine start *> $null } catch { }

# 4. Projekt holen - ohne git, per ZIP von GitHub
$parent = "$env:USERPROFILE\Desktop"
$zip = "$env:TEMP\modellgarage.zip"
$proj = "$parent\ModellGarage-main"
Info "Lade ModellGarage herunter ..."
Invoke-WebRequest "https://github.com/diebugger-tech/ModellGarage/archive/refs/heads/main.zip" -OutFile $zip
if (Test-Path $proj) { Remove-Item $proj -Recurse -Force }
Expand-Archive $zip -DestinationPath $parent -Force

# 5. Starten (baut Container, wartet, oeffnet den Browser)
Ok "Alles bereit - starte die App ..."
Set-Location $proj
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\start-podman.ps1"
