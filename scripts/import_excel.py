"""CLI: Excel → SQLite importieren. Aufruf: python -m scripts.import_excel <pfad>"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, init_db  # noqa: E402
from app.services.excel_import import importiere_excel  # noqa: E402


async def main() -> None:
    pfad = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("2026-06-05 Modelle.xlsx")
    if not pfad.exists():
        print(f"FEHLER: {pfad} nicht gefunden")
        sys.exit(1)
    await init_db()
    async with SessionLocal() as session:
        stats = await importiere_excel(session, pfad)
    print("Import fertig:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
