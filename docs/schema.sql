-- ModellGarage — SQLite Schema (MVP)
-- Serverlos, eine Datei. Referenz-DDL; die produktive Version entsteht als
-- Alembic-Migration. Foreign Keys müssen pro Connection aktiviert werden.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- katalog: die Wertquelle. Ein Eintrag pro Hersteller-Katalognummer.
-- min/max leben HIER, nicht am Einzelmodell (sonst mehrfach gepflegt).
-- ---------------------------------------------------------------------------
CREATE TABLE katalog (
    id          INTEGER PRIMARY KEY,
    hersteller  TEXT    NOT NULL,                    -- 'Wiking' | 'Siku' | 'Majorette' | ...
    katalog_nr  TEXT    NOT NULL,                    -- '30/6K.' | '1050' | ...
    typ         TEXT    NOT NULL,                    -- 'VW Käfer, ovale Heckscheibe'
    serie       TEXT,                                -- Blatt/Segment, z.B. 'UV500'
    min_euro    REAL,
    max_euro    REAL,
    quelle      TEXT,                                -- 'GK' | 'Rawe' | ...
    UNIQUE (hersteller, katalog_nr)                  -- Nr. je Hersteller eindeutig
);

CREATE INDEX ix_katalog_hersteller ON katalog (hersteller);
CREATE INDEX ix_katalog_typ        ON katalog (typ);

-- ---------------------------------------------------------------------------
-- konvolut: Sammelkauf (Eltern). Kinder = modell-Zeilen mit konvolut_id.
-- ---------------------------------------------------------------------------
CREATE TABLE konvolut (
    id           INTEGER PRIMARY KEY,
    quelle       TEXT,                               -- 'eBay 30.06.'
    gesamtpreis  REAL,
    datum        TEXT                                -- ISO-8601 'YYYY-MM-DD'
);

-- ---------------------------------------------------------------------------
-- modell: das konkrete Exemplar des Sammlers.
-- WICHTIG: katalog_id ist 1:n — Dubletten sind gewollt, NICHT unique.
-- ---------------------------------------------------------------------------
CREATE TABLE modell (
    id           INTEGER PRIMARY KEY,
    katalog_id   INTEGER NOT NULL REFERENCES katalog (id)   ON DELETE RESTRICT,
    farbe        TEXT,
    zustand      TEXT CHECK (zustand IN ('z0', 'z1', 'z2')),-- aus Freitext extrahiert
    bemerkung    TEXT,
    bezahlt      REAL,                               -- tatsächlich gezahlt (ggf. gewichtet)
    schaetzwert  REAL,
    kaufdatum    TEXT,                               -- ISO-8601, beim Import normalisiert
    anzahl       INTEGER NOT NULL DEFAULT 1,
    konvolut_id  INTEGER REFERENCES konvolut (id)    ON DELETE SET NULL  -- nullable
);

CREATE INDEX ix_modell_katalog_id  ON modell (katalog_id);
CREATE INDEX ix_modell_konvolut_id ON modell (konvolut_id);
CREATE INDEX ix_modell_zustand     ON modell (zustand);

-- ---------------------------------------------------------------------------
-- foto: eigene Tabelle (kein Array am Modell).
-- Genau EINE Zuordnung: entweder modell_id ODER konvolut_id (Gesamtfoto).
-- Bilder werden lokal gespeichert (pfad), nie nur als externe URL.
-- ---------------------------------------------------------------------------
CREATE TABLE foto (
    id           INTEGER PRIMARY KEY,
    modell_id    INTEGER REFERENCES modell   (id) ON DELETE CASCADE,
    konvolut_id  INTEGER REFERENCES konvolut (id) ON DELETE CASCADE,
    pfad         TEXT    NOT NULL,                   -- lokaler Pfad unter media/
    quelle       TEXT    NOT NULL CHECK (quelle IN ('ebay', 'manuell')),
    -- genau eine Bindung: XOR über die beiden FKs
    CHECK ( (modell_id IS NOT NULL) <> (konvolut_id IS NOT NULL) )
);

CREATE INDEX ix_foto_modell_id   ON foto (modell_id);
CREATE INDEX ix_foto_konvolut_id ON foto (konvolut_id);
