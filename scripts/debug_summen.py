"""Findet verdächtige Summen-/Meta-Zeilen, die als Modell durchrutschten."""
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parent.parent / "data" / "modellgarage.db")
c = db.cursor()

print("=== Verdächtige typ-Werte (Summen/Meta) ===")
for r in c.execute("""SELECT k.typ, COUNT(*), SUM(m.bezahlt)
    FROM modell m JOIN katalog k ON m.katalog_id=k.id
    WHERE k.typ IN ('Summe','Typ','Gesamt','Model','Modell') OR k.typ LIKE '%umme%'
    GROUP BY k.typ"""):
    print(f"  typ='{r[0]}' anzahl={r[1]} summe_bezahlt={r[2]}")

print("=== Modelle mit bezahlt > 1000 (verdächtig hoch) ===")
for r in c.execute("""SELECT m.id, k.hersteller, k.typ, m.bezahlt, m.kaufdatum
    FROM modell m JOIN katalog k ON m.katalog_id=k.id
    WHERE m.bezahlt > 1000 ORDER BY m.bezahlt DESC LIMIT 10"""):
    print(f"  id={r[0]} {r[1]} '{r[2]}' bezahlt={r[3]} datum={r[4]}")

print("=== Jahr 1900 (Datumsfehler) ===")
for r in c.execute("""SELECT m.id, k.typ, m.kaufdatum FROM modell m JOIN katalog k ON m.katalog_id=k.id
    WHERE m.kaufdatum LIKE '1900%' LIMIT 5"""):
    print(f"  id={r[0]} '{r[1]}' datum={r[2]}")
db.close()
