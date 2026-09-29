from sqlalchemy import (
    Column,
    ColumnElement,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from . import codes
from .auth import User
from .base import Base, CodeForeignKeyConstraint
from .bem import BemerkungSubjekt
from .grun import Parzelle
from .mixins import ErfassungMutationMixin
from .snapshots import SupportsSnapshots

subjekt_kategorie_mapping_table = Table(
    "subj_category",
    Base.metadata,
    Column("subj_category_id", Integer, primary_key=True),
    Column("subj_id", Integer, ForeignKey("alma.subj.subj_id")),
    Column("h_subj_category", Integer),
    Column("c_subj_category", Integer),
    Column("erfassungs_datum", DateTime),
    Column("erfasser", String),
    Column("mutations_datum", DateTime),
    Column("mutierer", String),
    CodeForeignKeyConstraint(["h_subj_category", "c_subj_category"]),
)
subjekt_kategorie_mapping_table.schema = "alma"


class Subjekt(Base, ErfassungMutationMixin):
    __tablename__ = "subj"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_land", "c_land"]),
        CodeForeignKeyConstraint(["h_anrede", "c_anrede"]),
        {"schema": "alma"},
    )

    # Primary key
    subj_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    h_land: Mapped[int] = mapped_column(init=False)
    c_land: Mapped[str | None] = mapped_column(init=False)

    h_anrede: Mapped[int] = mapped_column(init=False)
    c_anrede: Mapped[str | None] = mapped_column(init=False)

    land: Mapped[codes.Land | None] = relationship(
        codes.Land, foreign_keys=[h_land, c_land], lazy="joined", init=False
    )
    anrede: Mapped[codes.Anrede | None] = relationship(
        codes.Anrede, foreign_keys=[h_anrede, c_anrede], lazy="joined", init=False
    )

    # Fields
    name: Mapped[str] = mapped_column(default="")
    vorname: Mapped[str] = mapped_column(default="")
    taetigkeit: Mapped[str] = mapped_column(default="")
    kuerzel: Mapped[str | None] = mapped_column(default=None)
    ident_nr: Mapped[str | None] = mapped_column(default=None)
    import_key: Mapped[str | None] = mapped_column(default=None)
    ort: Mapped[str] = mapped_column(default="")
    postleitzahl: Mapped[str] = mapped_column(default="")
    strasse: Mapped[str] = mapped_column(default="")

    # Relationships
    kategorien: Mapped[list[codes.SubjektKategorie]] = relationship(
        codes.SubjektKategorie,
        init=False,
        secondary=subjekt_kategorie_mapping_table,
    )
    kontakte: Mapped[list["Kontakt"]] = relationship(
        "Kontakt", init=False, cascade="all, delete-orphan"
    )
    bemerkung: Mapped[BemerkungSubjekt | None] = relationship(
        BemerkungSubjekt,
        primaryjoin=foreign(BemerkungSubjekt.key_value) == subj_id,
        init=False,
        cascade="all, delete-orphan",
        order_by=BemerkungSubjekt.bem_id,
    )
    user: Mapped[User | None] = relationship(User, init=False, back_populates="subjekt")

    @classmethod
    def search_key(cls) -> ColumnElement[str]:
        return (
            cls.name
            + " "
            + cls.vorname
            + ", "
            + cls.taetigkeit
            + ", "
            + cls.strasse
            + ", "
            + cls.ort
        )


class Beteiligter(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "bet"
    __table_args__ = {"schema": "alma"}

    # Primary key
    bet_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)
    subj_id: Mapped[int] = mapped_column(ForeignKey("alma.subj.subj_id"), init=False)

    # Relationships
    subjekt: Mapped[Subjekt] = relationship(Subjekt, init=False)
    beteiligte_standort: Mapped[list["BeteiligterStandort"]] = relationship(
        "BeteiligterStandort",
        init=False,
        cascade="all, delete-orphan",
        order_by="BeteiligterStandort.bet_art_id",
        back_populates="beteiligter",
    )

    # Fields
    is_eigentuemer: Mapped[bool] = mapped_column(default=False)
    is_sachbearbeiter: Mapped[bool] = mapped_column(default=False)


class BeteiligterStandort(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "bet_art"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_bez_art", "c_bez_art"]),
        {"schema": "alma"},
    )

    # Primary key
    bet_art_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    bet_id: Mapped[int] = mapped_column(ForeignKey("alma.bet.bet_id"), init=False)
    grun_id: Mapped[int | None] = mapped_column(
        ForeignKey("alma.grun.grun_id"), init=False
    )

    # Codewerte
    h_bez_art: Mapped[int] = mapped_column(init=False)
    c_bez_art: Mapped[str] = mapped_column(init=False)

    # Relationships
    beziehungsart: Mapped[codes.BeziehungsartVariante] = relationship(
        codes.BeziehungsartVariante,
        foreign_keys=[h_bez_art, c_bez_art],
        lazy="joined",
    )
    beteiligter: Mapped[Beteiligter] = relationship(
        Beteiligter, init=False, back_populates="beteiligte_standort"
    )
    parzelle: Mapped[Parzelle | None] = relationship(Parzelle, init=False)


class Kontakt(Base, ErfassungMutationMixin):
    __tablename__ = "kontakt"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_kontakt_typ", "c_kontakt_typ"]),
        {"schema": "alma"},
    )

    # Primary key
    kontakt_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    subj_id: Mapped[int] = mapped_column(ForeignKey("alma.subj.subj_id"), init=False)

    # Codewerte
    h_kontakt_typ: Mapped[int] = mapped_column(init=False)
    c_kontakt_typ: Mapped[str] = mapped_column(init=False)

    # Relationships
    kontakt_typ: Mapped[codes.KontaktTyp] = relationship(
        codes.KontaktTyp,
        foreign_keys=[h_kontakt_typ, c_kontakt_typ],
        lazy="joined",
        init=False,
    )

    # Fields
    kontakt: Mapped[str] = mapped_column(init=False)


class ParzelleEigentuemer(Base, ErfassungMutationMixin):
    __tablename__ = "grun_subj"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_eigentums_art", "c_eigentums_art"]),
        {"schema": "alma"},
    )

    # Primary key
    grun_subj_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    grun_id: Mapped[int] = mapped_column(ForeignKey("alma.grun.grun_id"), init=False)
    subj_id: Mapped[int] = mapped_column(ForeignKey("alma.subj.subj_id"), init=False)

    # Codewerte
    h_eigentums_art: Mapped[int] = mapped_column(init=False)
    c_eigentums_art: Mapped[str] = mapped_column(init=False)

    # Relationships
    eigentums_art: Mapped[codes.BeziehungsartEigentum] = relationship(
        codes.BeziehungsartEigentum,
        foreign_keys=[h_eigentums_art, c_eigentums_art],
        lazy="joined",
    )

    c_status: Mapped[bool] = mapped_column(default=True)
    bemerkungen: Mapped[str | None] = mapped_column(default=None)
