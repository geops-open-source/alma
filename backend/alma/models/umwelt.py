from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from . import bem, codes
from .base import Base, CodeForeignKeyConstraint
from .mixins import ErfassungMutationMixin
from .snapshots import SupportsSnapshots


class Grundwasser(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "gwas"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_gwas_relzugw", "c_gwas_relzugw"]),
        CodeForeignKeyConstraint(["h_gwas_nutzung", "c_gwas_nutzung"]),
        {"schema": "alma"},
    )
    # Primary keys
    gwas_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_gwas_relzugw: Mapped[int | None] = mapped_column(init=False)
    c_gwas_relzugw: Mapped[str | None] = mapped_column(init=False)

    h_gwas_nutzung: Mapped[int | None] = mapped_column(init=False)
    c_gwas_nutzung: Mapped[str | None] = mapped_column(init=False)

    # Relationships
    relative_lage: Mapped[codes.RelativeLageGrundwasser | None] = relationship(
        codes.RelativeLageGrundwasser,
        foreign_keys=[h_gwas_relzugw, c_gwas_relzugw],
        lazy="joined",
        default=None,
    )
    nutzung: Mapped[codes.NutzungGrundwasserAbstrom | None] = relationship(
        codes.NutzungGrundwasserAbstrom,
        foreign_keys=[h_gwas_nutzung, c_gwas_nutzung],
        lazy="joined",
        default=None,
    )

    # Actual fields
    flurabstand: Mapped[float | None] = mapped_column("gwas_flurabstand", default=None)
    distanz: Mapped[int | None] = mapped_column("gwas_distanz", default=None)


class OberflaechenGewaesser(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "ogw"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_ogw_art_gewaesser", "c_ogw_art_gewaesser"]),
        CodeForeignKeyConstraint(["h_ogw_bau_gewaesser", "c_ogw_bau_gewaesser"]),
        CodeForeignKeyConstraint(["h_ogw_rellage", "c_ogw_rellage"]),
        {"schema": "alma"},
    )
    # Primary Keys
    ogw_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_ogw_art_gewaesser: Mapped[int | None] = mapped_column(init=False)
    c_ogw_art_gewaesser: Mapped[str | None] = mapped_column(init=False)

    h_ogw_bau_gewaesser: Mapped[int | None] = mapped_column(init=False)
    c_ogw_bau_gewaesser: Mapped[str | None] = mapped_column(init=False)

    h_ogw_rellage: Mapped[int | None] = mapped_column(init=False)
    c_ogw_rellage: Mapped[str | None] = mapped_column(init=False)

    # Relationship
    art_gewaesser: Mapped[codes.GewaesserArt | None] = relationship(
        codes.GewaesserArt,
        foreign_keys=[h_ogw_art_gewaesser, c_ogw_art_gewaesser],
        lazy="joined",
        default=None,
    )
    bau_gewaesser: Mapped[codes.GewaesserBau | None] = relationship(
        codes.GewaesserBau,
        foreign_keys=[h_ogw_bau_gewaesser, c_ogw_bau_gewaesser],
        lazy="joined",
        default=None,
    )
    relative_lage: Mapped[codes.RelativeLageOberflaechenGewaesser | None] = (
        relationship(
            codes.RelativeLageOberflaechenGewaesser,
            foreign_keys=[h_ogw_rellage, c_ogw_rellage],
            lazy="joined",
            default=None,
        )
    )

    # Actual fields
    distanz: Mapped[int | None] = mapped_column("ogw_distanz", default=None)
    name: Mapped[str | None] = mapped_column("ogw_name", default=None)


class NutzungBoden(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "nubo"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_nubo_nutzungsart", "c_nubo_nutzungsart"]),
        CodeForeignKeyConstraint(["h_nubo_akt_nutzung", "c_nubo_akt_nutzung"]),
        {"schema": "alma"},
    )
    # Primary Keys
    nubo_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign Keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_nubo_nutzungsart: Mapped[int | None] = mapped_column(init=False)
    c_nubo_nutzungsart: Mapped[str | None] = mapped_column(init=False)

    h_nubo_akt_nutzung: Mapped[int | None] = mapped_column(init=False)
    c_nubo_akt_nutzung: Mapped[str | None] = mapped_column(init=False)

    # Relationship
    nutzungsart: Mapped[codes.Flaechennutzung | None] = relationship(
        codes.Flaechennutzung,
        foreign_keys=[h_nubo_nutzungsart, c_nubo_nutzungsart],
        lazy="joined",
        default=None,
    )
    aktuelle_nutzung: Mapped[codes.FlaechennutzungVariante | None] = relationship(
        codes.FlaechennutzungVariante,
        foreign_keys=[h_nubo_akt_nutzung, c_nubo_akt_nutzung],
        lazy="joined",
        default=None,
    )


class UmweltStoff(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "stoffe"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_stoffe_umweltbereich", "c_stoffe_umweltbereich"]),
        CodeForeignKeyConstraint(["h_stoffe_gruppe", "c_stoffe_gruppe"]),
        CodeForeignKeyConstraint(["h_stoffe_stoff", "c_stoffe_stoff"]),
        CodeForeignKeyConstraint(["h_stoffe_beurteilung", "c_stoffe_beurteilung"]),
        {"schema": "alma"},
    )
    # Primary Keys
    stoffe_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign Keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_stoffe_umweltbereich: Mapped[int | None] = mapped_column(init=False)
    c_stoffe_umweltbereich: Mapped[str | None] = mapped_column(init=False)

    h_stoffe_gruppe: Mapped[int | None] = mapped_column(init=False)
    c_stoffe_gruppe: Mapped[str | None] = mapped_column(init=False)

    h_stoffe_stoff: Mapped[int | None] = mapped_column(init=False)
    c_stoffe_stoff: Mapped[str | None] = mapped_column(init=False)

    h_stoffe_beurteilung: Mapped[int | None] = mapped_column(init=False)
    c_stoffe_beurteilung: Mapped[str | None] = mapped_column(init=False)

    # Relationship
    gefaehrdete_bereiche: Mapped[codes.GefaehrdeteUmweltbereiche | None] = relationship(
        codes.GefaehrdeteUmweltbereiche,
        foreign_keys=[h_stoffe_umweltbereich, c_stoffe_umweltbereich],
        lazy="joined",
        default=None,
    )
    stoff_gruppe: Mapped[codes.UmweltStoffgruppe | None] = relationship(
        codes.UmweltStoffgruppe,
        foreign_keys=[h_stoffe_gruppe, c_stoffe_gruppe],
        lazy="joined",
        default=None,
    )
    stoff: Mapped[codes.UmweltStoffgruppeVariante | None] = relationship(
        codes.UmweltStoffgruppeVariante,
        foreign_keys=[h_stoffe_stoff, c_stoffe_stoff],
        lazy="joined",
        default=None,
    )
    beurteilung: Mapped[codes.UmweltStoffBeurteilung | None] = relationship(
        codes.UmweltStoffBeurteilung,
        foreign_keys=[h_stoffe_beurteilung, c_stoffe_beurteilung],
        lazy="joined",
        default=None,
    )


class Einzelereignis(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "veen"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_veen_natuerlich", "c_veen_natuerlich"]),
        {"schema": "alma"},
    )
    # Primary keys
    veen_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_veen_natuerlich: Mapped[int | None] = mapped_column(init=False)
    c_veen_natuerlich: Mapped[str | None] = mapped_column(init=False)

    # Relationships
    einzelereignis: Mapped[codes.Einzelereignis | None] = relationship(
        codes.Einzelereignis,
        foreign_keys=[h_veen_natuerlich, c_veen_natuerlich],
        lazy="joined",
        default=None,
    )
    bemerkung: Mapped[bem.BemerkungEinzelereignis | None] = relationship(
        bem.BemerkungEinzelereignis,
        primaryjoin=foreign(bem.BemerkungEinzelereignis.key_value) == veen_id,
        init=False,
        default=None,
        cascade="all, delete-orphan",
    )

    # Actual fields
    datum: Mapped[date | None] = mapped_column("veen_datum", default=None)


class Umweltschaden(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "vfus"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_vfus_art_schaden", "c_vfus_art_schaden"]),
        CodeForeignKeyConstraint(["h_vfus_schaeden", "c_vfus_schaeden"]),
        {"schema": "alma"},
    )
    # Primary Keys
    vfus_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign Keys
    vflz_id: Mapped[int] = mapped_column(ForeignKey("alma.vflz.vflz_id"), init=False)

    # Codewerte
    h_vfus_art_schaden: Mapped[int | None] = mapped_column(init=False)
    c_vfus_art_schaden: Mapped[str | None] = mapped_column(init=False)

    h_vfus_schaeden: Mapped[int | None] = mapped_column(init=False)
    c_vfus_schaeden: Mapped[str | None] = mapped_column(init=False)

    # Relationships
    art_schaden: Mapped[codes.Umweltbereich | None] = relationship(
        codes.Umweltbereich,
        foreign_keys=[h_vfus_art_schaden, c_vfus_art_schaden],
        lazy="joined",
        default=None,
    )
    schaeden: Mapped[codes.UmweltschaedenVariante | None] = relationship(
        codes.UmweltschaedenVariante,
        foreign_keys=[h_vfus_schaeden, c_vfus_schaeden],
        lazy="joined",
        default=None,
    )
    bemerkung: Mapped[bem.BemerkungUmweltschaden | None] = relationship(
        bem.BemerkungUmweltschaden,
        primaryjoin=foreign(bem.BemerkungUmweltschaden.key_value) == vfus_id,
        init=False,
        default=None,
        cascade="all, delete-orphan",
    )
