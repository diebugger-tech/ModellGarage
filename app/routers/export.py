"""Router: Excel-Export (DB → xlsx, ein Blatt pro Hersteller)."""
from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Katalog, Modell

router = APIRouter(prefix="/api/export", tags=["export"])

SPALTEN = [
    "Nr.", "Min", "Max", "Typ", "Farbe", "Zustand",
    "Bemerkung", "bezahlt", "Schätzwert", "Anzahl", "Kaufdatum",
]


@router.get("/excel")
async def export_excel(session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    stmt = select(Modell).join(Katalog).options(selectinload(Modell.katalog)).order_by(
        Katalog.hersteller, Katalog.katalog_nr
    )
    modelle = (await session.execute(stmt)).scalars().all()

    wb = Workbook()
    default_sheet = wb.active
    if default_sheet is not None:
        wb.remove(default_sheet)
    sheets: dict[str, Worksheet] = {}

    for m in modelle:
        h = m.katalog.hersteller or "Unbekannt"
        # Excel-Sheet-Namen: max 31 Zeichen, keine Sonderzeichen
        name = "".join(c for c in h if c not in "[]:*?/\\")[:31] or "Unbekannt"
        ws = sheets.get(name)
        if ws is None:
            ws = wb.create_sheet(name)
            ws.append(SPALTEN)
            sheets[name] = ws
        ws.append([
            m.katalog.katalog_nr, m.katalog.min_euro, m.katalog.max_euro,
            m.katalog.typ, m.farbe, m.zustand, m.bemerkung,
            m.bezahlt, m.schaetzwert, m.anzahl, m.kaufdatum,
        ])

    if not sheets:
        wb.create_sheet("Leer").append(SPALTEN)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    dateiname = f"ModellGarage_Export_{datetime.now():%Y-%m-%d}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{dateiname}"'},
    )
