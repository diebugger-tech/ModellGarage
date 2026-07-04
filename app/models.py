"""SQLAlchemy 2.x ORM-Models: katalog, konvolut, modell, foto.

Entspricht docs/schema.sql. Relationale Kernregeln:
- katalog_nr:modell = 1:n (Dubletten gewollt)
- foto hat XOR-Bindung an modell ODER konvolut
- Werte (min/max) leben im katalog, nicht am modell
"""
from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Katalog(Base):
    __tablename__ = "katalog"
    __table_args__ = (
        UniqueConstraint("hersteller", "katalog_nr", name="uq_katalog_hersteller_nr"),
        Index("ix_katalog_hersteller", "hersteller"),
        Index("ix_katalog_typ", "typ"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hersteller: Mapped[str] = mapped_column(String, nullable=False)
    katalog_nr: Mapped[str] = mapped_column(String, nullable=False)
    typ: Mapped[str] = mapped_column(String, nullable=False)
    serie: Mapped[str | None] = mapped_column(String)
    min_euro: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_euro: Mapped[float | None] = mapped_column(Numeric(10, 2))
    quelle: Mapped[str | None] = mapped_column(String)

    modelle: Mapped[list[Modell]] = relationship(back_populates="katalog")


class Konvolut(Base):
    __tablename__ = "konvolut"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quelle: Mapped[str | None] = mapped_column(String)
    gesamtpreis: Mapped[float | None] = mapped_column(Numeric(10, 2))
    datum: Mapped[str | None] = mapped_column(String)  # ISO-8601

    modelle: Mapped[list[Modell]] = relationship(back_populates="konvolut")
    fotos: Mapped[list[Foto]] = relationship(
        back_populates="konvolut", cascade="all, delete-orphan"
    )


class Modell(Base):
    __tablename__ = "modell"
    __table_args__ = (
        CheckConstraint("zustand IN ('z0','z1','z2')", name="ck_modell_zustand"),
        Index("ix_modell_katalog_id", "katalog_id"),
        Index("ix_modell_konvolut_id", "konvolut_id"),
        Index("ix_modell_zustand", "zustand"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    katalog_id: Mapped[int] = mapped_column(
        ForeignKey("katalog.id", ondelete="RESTRICT"), nullable=False
    )
    farbe: Mapped[str | None] = mapped_column(String)
    zustand: Mapped[str | None] = mapped_column(String)
    bemerkung: Mapped[str | None] = mapped_column(Text)
    bezahlt: Mapped[float | None] = mapped_column(Numeric(10, 2))
    schaetzwert: Mapped[float | None] = mapped_column(Numeric(10, 2))
    kaufdatum: Mapped[str | None] = mapped_column(String)  # ISO-8601
    anzahl: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    konvolut_id: Mapped[int | None] = mapped_column(
        ForeignKey("konvolut.id", ondelete="SET NULL")
    )

    katalog: Mapped[Katalog] = relationship(back_populates="modelle")
    konvolut: Mapped[Konvolut | None] = relationship(back_populates="modelle")
    fotos: Mapped[list[Foto]] = relationship(
        back_populates="modell", cascade="all, delete-orphan"
    )


class Wunsch(Base):
    """Manuelle Merkliste: Nummern, die der Sammler noch sucht.

    Unabhängig von katalog/modell (kein FK) — ein Wunsch darf auf eine Nummer
    zeigen, die es in der Sammlung/im Katalog noch gar nicht gibt. Status
    wandert von 'gesucht' → 'gekauft'.
    """

    __tablename__ = "wunsch"
    __table_args__ = (
        CheckConstraint("status IN ('gesucht','gekauft')", name="ck_wunsch_status"),
        Index("ix_wunsch_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hersteller: Mapped[str] = mapped_column(String, nullable=False)
    katalog_nr: Mapped[str | None] = mapped_column(String)
    typ: Mapped[str | None] = mapped_column(String)
    notiz: Mapped[str | None] = mapped_column(Text)
    max_euro: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String, nullable=False, default="gesucht")
    erstellt_am: Mapped[str | None] = mapped_column(String)  # ISO-8601 (Datum)


class Foto(Base):
    __tablename__ = "foto"
    __table_args__ = (
        CheckConstraint(
            "(modell_id IS NOT NULL) <> (konvolut_id IS NOT NULL)",
            name="ck_foto_xor_bindung",
        ),
        CheckConstraint("quelle IN ('ebay','manuell')", name="ck_foto_quelle"),
        Index("ix_foto_modell_id", "modell_id"),
        Index("ix_foto_konvolut_id", "konvolut_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modell_id: Mapped[int | None] = mapped_column(
        ForeignKey("modell.id", ondelete="CASCADE")
    )
    konvolut_id: Mapped[int | None] = mapped_column(
        ForeignKey("konvolut.id", ondelete="CASCADE")
    )
    pfad: Mapped[str] = mapped_column(String, nullable=False)
    quelle: Mapped[str] = mapped_column(String, nullable=False)

    modell: Mapped[Modell | None] = relationship(back_populates="fotos")
    konvolut: Mapped[Konvolut | None] = relationship(back_populates="fotos")
