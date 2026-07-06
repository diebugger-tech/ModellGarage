@echo off
REM ModellGarage - Doppelklick-Stopp unter Windows
REM WICHTIG: Podman-Volumes modellgarage-media (Fotos) und modellgarage-data (DB)
REM NIEMALS loeschen (podman volume rm / machine reset / system prune --volumes),
REM sonst sind Fotos und Datenbank weg. Backup laeuft ueber den App-Export (Excel).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-podman.ps1"
