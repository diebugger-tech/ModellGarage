"""Testet Excel-Upload-Endpoint + Foto-Upload-Endpoint per HTTP."""
import io
import json
import urllib.request

from openpyxl import Workbook

BASE = "http://127.0.0.1:8003"


def post_multipart(path, field, filename, content, ctype):
    boundary = "----MGTEST123"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read())


# 1) Mini-Excel bauen (ein Wiking-Blatt mit einer Zeile)
wb = Workbook()
ws = wb.active
ws.title = "TestBlatt"
ws.append(["Nr.", "Min.", "Max.", "Model", "Bemerkung", "bezahlt", "Schätzwert", "Anzahl", "Kaufdatum"])
ws.append([None, "Euro", "Euro", "Typ", "Zustand, Farbe etc", "Euro", "Euro", None, None])
ws.append(["999/9T.", 10, 20, "Test-Modell Upload", "z1, testfarbe grün", 12.5, None, 1, None])
buf = io.BytesIO()
wb.save(buf)

s, d = post_multipart("/api/import/excel", "datei", "test.xlsx", buf.getvalue(),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
print(f"IMPORT   → {s} | modelle={d.get('modelle')} katalog_neu={d.get('katalog_neu')} blaetter={d.get('blaetter')}")

# 2) Foto-Upload an Modell 6312 (1x1 PNG)
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da6360000002000154a24f8f0000000049454e44ae426082"
)
s2, d2 = post_multipart("/api/modelle/6312/foto", "datei", "test.png", png, "image/png")
print(f"FOTO     → {s2} | id={d2.get('id')} pfad={d2.get('pfad')} quelle={d2.get('quelle')}")

# 3) Verifizieren: Foto-Liste
with urllib.request.urlopen(BASE + "/api/modelle/6312/fotos", timeout=10) as r:
    fotos = json.loads(r.read())
print(f"FOTOLIST → {len(fotos)} Foto(s) an Modell 6312")
