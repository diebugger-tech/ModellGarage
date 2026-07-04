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

# 1. Podman-CLI installieren (RedHat.Podman = die Kommandozeile 'podman'.
#    ACHTUNG: RedHat.Podman-Desktop ist nur die GUI und liefert KEIN 'podman'.)
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
  Info "Installiere Podman (winget) ..."
  winget install -e --id RedHat.Podman --silent `
    --accept-package-agreements --accept-source-agreements
}

# 1b. Git installieren (fuer Klonen + spaetere Updates via 'git pull')
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Info "Installiere Git (winget) ..."
  winget install -e --id Git.Git --silent `
    --accept-package-agreements --accept-source-agreements
}

# PATH dieser Sitzung auffrischen, damit 'podman' und 'git' sofort gefunden werden
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [Environment]::GetEnvironmentVariable("Path", "User")
foreach ($d in @(
    "C:\Program Files\RedHat\Podman\usr\bin",
    "C:\Program Files\RedHat\Podman",
    "C:\Program Files\Git\cmd")) {
  if (Test-Path $d) { $env:Path += ";$d" }
}
# Falls immer noch nicht da: podman.exe unter Program Files gezielt suchen
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
  $exe = Get-ChildItem "C:\Program Files\RedHat" -Recurse -Filter podman.exe `
    -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($exe) { $env:Path += ";" + $exe.DirectoryName }
}

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
  Warn "Podman-CLI konnte nicht gefunden werden."
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

# 4. Projekt holen - per 'git clone' (Fallback: ZIP, falls git fehlt)
$parent = "$env:USERPROFILE\Desktop"
$repo = "https://github.com/diebugger-tech/ModellGarage.git"
if (Get-Command git -ErrorAction SilentlyContinue) {
  $proj = "$parent\ModellGarage"
  if (Test-Path "$proj\.git") {
    Info "Aktualisiere vorhandenes Projekt (git pull) ..."
    Set-Location $proj; git pull
  } else {
    Info "Klone ModellGarage (git) ..."
    if (Test-Path $proj) { Remove-Item $proj -Recurse -Force }
    git clone $repo $proj
  }
} else {
  Info "Lade ModellGarage als ZIP herunter (ohne git) ..."
  $zip = "$env:TEMP\modellgarage.zip"
  $proj = "$parent\ModellGarage-main"
  Invoke-WebRequest "https://github.com/diebugger-tech/ModellGarage/archive/refs/heads/main.zip" -OutFile $zip
  if (Test-Path $proj) { Remove-Item $proj -Recurse -Force }
  Expand-Archive $zip -DestinationPath $parent -Force
}

# 5. Starten (baut Container, wartet, oeffnet den Browser)
Ok "Alles bereit - starte die App ..."
Set-Location $proj
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\start-podman.ps1"
