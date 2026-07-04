"""Unit-Tests für den eBay-Text-Parser (Titel + optional Beschreibung).

Fokus: die Beschreibungs-Erfassung — Katalog-/Wiking-Nr. und Farbe stehen
selten im Titel, aber oft in der Artikelbeschreibung.
"""
from app.services.ebay_parse import parse_text


def test_titel_only_bleibt_kompatibel():
    r = parse_text("Wiking VW T2 Bus 1:87 OVP")
    assert r["hersteller"] == "Wiking"
    assert r["massstab"] == "1:87"
    assert r["katalog_nr"] is None  # Titel enthält keine Nr.


def test_wiking_nr_aus_beschreibung():
    r = parse_text(
        "Wiking VW Käfer ovale Heckscheibe 1:87",
        "EUR 39,00 gebraucht",
        "Wiking Nr. 30/6K., Farbe blaugrau, Zustand Z1, kleine Kratzer",
    )
    assert r["katalog_nr"] == "30/6K."
    assert r["farbe"] == "blaugrau"
    assert r["zustand"] == "z1"          # explizites "Z1" hat Vorrang
    assert r["bezahlt"] == 39.0
    assert r["massstab"] == "1:87"


def test_kontext_nr_ohne_schraegstrich():
    r = parse_text("Wiking VW Käfer", "", "Kat.-Nr 1050, dunkelrot, unbespielt")
    assert r["katalog_nr"] == "1050"
    assert r["farbe"] == "dunkelrot"
    assert r["zustand"] == "z0"


def test_massstab_nicht_als_katalog_nr():
    # "1/87" (Maßstab als Schrägstrich) darf nicht als Nr. gelesen werden
    r = parse_text("Herpa LKW 1/87 grün", "", "Artikelnummer: 8/1 a, blassgelb")
    assert r["katalog_nr"] == "8/1a"
    assert r["massstab"] == "1:87"
    assert r["farbe"] == "blassgelb"


def test_bare_nummer_nur_im_titel():
    # Siku-Stil: bloße Nummer im Titel wird als Fallback erkannt
    r = parse_text("Siku Mercedes 1050 Feuerwehr rot", "19,99 EUR")
    assert r["katalog_nr"] == "1050"
    assert r["farbe"] == "rot"
    assert r["bezahlt"] == 19.99


def test_jahreszahl_ist_keine_katalog_nr():
    r = parse_text("Konvolut Wiking Baujahr 1963", "", "diverse Modelle")
    assert r["katalog_nr"] is None


def test_leerer_titel_wirft():
    import pytest

    with pytest.raises(ValueError):
        parse_text("", "", "nur Beschreibung")
