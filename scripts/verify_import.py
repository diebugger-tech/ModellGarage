"""Verifikation v2 — nach header-getriebenem Import."""
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parent.parent / "data" / "modellgarage.db")
c = db.cursor()

print("=== Hersteller-Verteilung ===")
for r in c.execute("SELECT hersteller, COUNT(*) FROM katalog GROUP BY hersteller ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]}: {r[1]} Katalog-Einträge")

print("=== Zustand ===")
for r in c.execute("SELECT COALESCE(zustand,'(leer)'), COUNT(*) FROM modell GROUP BY zustand ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]}: {r[1]}")

print("=== Farbe erfasst (Siku/Majorette-Blätter) ===")
print("  mit Farbe:", c.execute("SELECT COUNT(*) FROM modell WHERE farbe IS NOT NULL").fetchone()[0])

print("=== Kaufdatum — jetzt sauber? (Top 8) ===")
for r in c.execute("SELECT kaufdatum, COUNT(*) FROM modell WHERE kaufdatum IS NOT NULL GROUP BY kaufdatum ORDER BY kaufdatum DESC LIMIT 8"):
    print(f"  {r[0]}: {r[1]}")

print("=== Datum-Müll-Check (darf 0 sein) ===")
bad = c.execute("SELECT COUNT(*) FROM modell WHERE kaufdatum IS NOT NULL AND kaufdatum NOT GLOB '____-__-__'").fetchone()[0]
print(f"  Nicht-ISO-Datumswerte: {bad}")

print("=== Stichprobe Käfer 30/6* ===")
for r in c.execute("SELECT k.katalog_nr, k.min_euro, k.max_euro, m.zustand, m.bezahlt, m.kaufdatum FROM modell m JOIN katalog k ON m.katalog_id=k.id WHERE k.katalog_nr LIKE '30/6%' LIMIT 5"):
    print(f"  nr={r[0]} min={r[1]} max={r[2]} zustand={r[3]} bezahlt={r[4]} datum={r[5]}")

print("=== Stichprobe Siku ===")
for r in c.execute("SELECT k.katalog_nr, k.typ, m.farbe, m.zustand, m.bezahlt FROM modell m JOIN katalog k ON m.katalog_id=k.id WHERE k.hersteller='Siku' LIMIT 4"):
    print(f"  nr={r[0]} typ={r[1][:25]} farbe={r[2]} zustand={r[3]} bezahlt={r[4]}")

print("=== Summen ===")
print("  Modelle:", c.execute("SELECT COUNT(*) FROM modell").fetchone()[0])
print("  Katalog:", c.execute("SELECT COUNT(*) FROM katalog").fetchone()[0])
sb = c.execute("SELECT SUM(bezahlt) FROM modell").fetchone()[0] or 0
print(f"  Summe bezahlt: {sb:.2f}")
db.close()
