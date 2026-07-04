"""Rotierendes DB-Backup.

Beim App-Start wird eine datierte Kopie der SQLite-DB nach ``data/backups/``
gelegt und nur die neuesten ``keep`` Kopien behalten. Ein Backup pro Tag.

Vorbehalt: Läuft nur, wenn die App gestartet wird. Für Backups bei dauerhaft
laufender App zusätzlich einen OS-Task einplanen (siehe README).
"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path


def rotiere_backup(db_path: Path, keep: int = 7) -> Path | None:
    """Kopiert die DB nach data/backups/modellgarage_<datum>.db und rotiert.

    Gibt den Pfad des Backups zurück (oder None, wenn keine DB existiert).
    """
    if not db_path.exists():
        return None

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ziel = backup_dir / f"modellgarage_{date.today().isoformat()}.db"
    if not ziel.exists():
        shutil.copy2(db_path, ziel)

    # Nur die neuesten `keep` Backups behalten (Dateiname sortiert = chronologisch)
    backups = sorted(backup_dir.glob("modellgarage_*.db"))
    for alt in backups[:-keep] if keep > 0 else backups:
        alt.unlink(missing_ok=True)

    return ziel
