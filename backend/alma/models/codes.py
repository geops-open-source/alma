from typing import Self

from sqlalchemy import ColumnElement, ForeignKey, String, cast, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .. import constants
from .base import Base, CodeForeignKeyConstraint


class CodeListe(Base):
    __tablename__ = "c_cli"
    __table_args__ = {"schema": "alma"}

    c_cli_id: Mapped[int] = mapped_column(primary_key=True)

    @property
    def read_only(self):
        return constants.CodeListe(self.c_cli_id) in constants.READ_ONLY_CODE_LISTS


class Code(Base, kw_only=True):
    __tablename__ = "cod"
    __table_args__ = {"schema": "alma"}

    __mapper_args__ = {"polymorphic_on": "c_cli_id"}

    c_cli_id: Mapped[int] = mapped_column(
        ForeignKey("alma.c_cli.c_cli_id"), primary_key=True, init=False
    )
    code: Mapped[str] = mapped_column(primary_key=True)
    sort_key: Mapped[int | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column("c_status", default=True)
    """Inactive codes can no longer be used for new objects."""
    is_null_code: Mapped[bool] = mapped_column("c_is_null_code", default=False)
    codeliste: Mapped[CodeListe] = relationship(CodeListe)

    def __str__(self) -> str:
        return f"code:{self.c_cli_id}:{self.code}"

    @classmethod
    def search_key(cls) -> ColumnElement[str]:
        return "code:" + cast(cls.c_cli_id, String) + ":" + cls.code

    @classmethod
    def from_db(cls, session: Session, code: str) -> Self:
        prefix, codeliste, code_value = code.split(":")
        assert prefix == "code"
        db_code = session.scalars(
            select(Code).where(Code.c_cli_id == int(codeliste), Code.code == code_value)
        ).one()

        assert isinstance(db_code, cls), (
            f"Object of type {type(db_code)} is not an instance of {cls}"
        )
        return db_code

    @classmethod
    def from_db_or_none(cls, session: Session, code: str | None) -> Self | None:
        return cls.from_db(session, code) if code is not None else None


class Land(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Land}


class Kanton(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Kanton}


class StandortTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StandortTyp}


class JaNeinUnbekannt(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.JaNeinUnbekannt}


class Genauigkeit(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Genauigkeit}


class Stoffklasse(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Stoffklasse}


class StoffgruppeVariante(Code):
    """
    Base class for all variants of Stoffgruppe.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class Stoffgruppen(StoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Stoffgruppen}


class StoffeKlasseI(StoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffeKlasseI}


class StoffeKlasseII(StoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffeKlasseII}


class StoffeKlasseIII(StoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffeKlasseIII}


class StoffeKlasseIV(StoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffeKlasseIV}


class BrancheASW(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.BrancheASW}


class BrancheNOGA(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.BrancheNOGA}


class UntersuchungsStand(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.UntersuchungsStand}


class Beurteilung(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Beurteilung}

    kbs_info: Mapped["KbsInfo | None"] = relationship(
        "KbsInfo",
        viewonly=True,
        lazy="joined",
        init=False,
        foreign_keys="[KbsInfo.h_bere_res_abwbewe, KbsInfo.c_bere_res_abwbewe]",
    )


class BeurteilungGruppe(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.BeurteilungGruppe}


class RechtlicherBezug(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.RechtlicherBezug}


class Handlungsbedarf(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Handlungsbedarf}


class Stoff(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Stoff}


class NutzungGrundwasserAbstrom(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.NutzungGrundwasserAbstrom
    }


class RelativeLageGrundwasser(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.RelativeLageGrundwasser
    }


class RelativeLageOberflaechenGewaesser(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.RelativeLageOberflaechenGewaesser
    }


class GewaesserArt(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.GewaesserArt}


class GewaesserBau(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.GewaesserBau}


class Flaechennutzung(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Flaechennutzung}


class FlaechennutzungVariante(Code):
    """
    Base class for all variants of Flaechennutzung.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class FlaechennutzungWald(FlaechennutzungVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.FlaechennutzungWald}


class FlaechennutzungLandwirtschaft(FlaechennutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.FlaechennutzungLandwirtschaft
    }


class FlaechennutzungSiedlungsgebiet(FlaechennutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.FlaechennutzungSiedlungsgebiet
    }


class FlaechennutzungUngenutz(FlaechennutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.FlaechennutzungUngenutz
    }


class GefaehrdeteUmweltbereiche(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.GefaehrdeteUmweltbereiche
    }


class UmweltStoffgruppe(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.UmweltStoffgruppe}


class UmweltStoffgruppeVariante(Code):
    """
    Base class for all variants of Stoffgruppe.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class StoffgruppeCKW(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeCKW}


class StoffgruppeSchwermetalle(UmweltStoffgruppeVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.StoffgruppeSchwermetalle
    }


class StoffgruppeMKW(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeMKW}


class StoffgruppeBTEX(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeBTEX}


class StoffgruppePAK(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppePAK}


class StoffgruppeDioxine(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeDioxine}


class StoffgruppePCB(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppePCB}


class StoffgruppePFAS(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppePFAS}


class StoffgruppeNichtmetalle(UmweltStoffgruppeVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.StoffgruppeNichtmetalle
    }


class StoffgruppeHalogenierteKW(UmweltStoffgruppeVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.StoffgruppeHalogenierteKW
    }


class StoffgruppeFreone(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeFreone}


class StoffgruppeSonstige(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppeSonstige}


class StoffgruppeBenzinartige(UmweltStoffgruppeVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.StoffgruppeBenzinartige
    }


class StoffgruppePhenole(UmweltStoffgruppeVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StoffgruppePhenole}


class UmweltStoffBeurteilung(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.UmweltStoffBeurteilung
    }


class Einzelereignis(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Einzelereignis}


class Umweltbereich(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Umweltbereich}


class UmweltschaedenVariante(Code):
    """
    Base class for all variants of Umweltschaeden.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class UmweltschaedenBoden(UmweltschaedenVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.UmweltschaedenBoden}


class UmweltschaedenLuft(UmweltschaedenVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.UmweltschaedenLuft}


class UmweltschaedenWasser(UmweltschaedenVariante):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.UmweltschaedenWasser}


class Massnahme(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Massnahme}


class Sanierungsziel(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Sanierungsziel}


class SchiessanlageTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.SchiessanlageTyp}


class DeponieTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.DeponieTyp}


class Gewaesserschutzbereich(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.Gewaesserschutzbereiche
    }


class Gewaesserschutzzone(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Gewaesserschutzzonen}


class Durchlaessigkeit(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Durchlaessigkeit}


class Bearbeitungsstand(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Bearbeitungsstand}


class StatusParzelle(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.StatusParzelle}


class BeziehungsartVariante(Code):
    """
    Base class for all variants of Beziehungsart.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class BeziehungsartEigentum(BeziehungsartVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.BeziehungsartEigentum
    }


class BeziehungsartSonstige(BeziehungsartVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.BeziehungsartSonstige
    }


class BeziehungsartSachbearbeitung(BeziehungsartVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.BeziehungsartSachbearbeitung
    }


class BeziehungsartGeschaefte(BeziehungsartVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.BeziehungsartGeschaefte
    }


class KontaktTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.KontaktTyp}


class PrioUntersuchung(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.PrioUntersuchung}


class PrioSanierung(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.PrioSanierung}


class KbsInfo(Base):
    __tablename__ = "cod_kbsinfo"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_bere_res_abwbewe", "c_bere_res_abwbewe"]),
        CodeForeignKeyConstraint(["h_bewe_gruppe", "c_bewe_gruppe"]),
        {"schema": "alma"},
    )

    # Primary key
    cod_kbsinfo_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Codewerte
    h_bere_res_abwbewe: Mapped[int] = mapped_column(init=False)
    c_bere_res_abwbewe: Mapped[str] = mapped_column(init=False)

    h_bewe_gruppe: Mapped[int] = mapped_column(init=False)
    c_bewe_gruppe: Mapped[str] = mapped_column(init=False)

    # Fields
    color: Mapped[str]
    belastet: Mapped[bool]
    color_rgb: Mapped[str | None]

    # Relationships
    beurteilung: Mapped[Beurteilung] = relationship(
        Beurteilung,
        foreign_keys=[h_bere_res_abwbewe, c_bere_res_abwbewe],
        lazy="joined",
        back_populates="kbs_info",
    )
    beurteilung_gruppe: Mapped[BeurteilungGruppe] = relationship(
        BeurteilungGruppe,
        foreign_keys=[h_bewe_gruppe, c_bewe_gruppe],
        lazy="joined",
    )


class SubjektKategorie(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.SubjektKategorie}


class Anrede(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Anrede}


class BehoerdenKuerzel(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.BehoerdenKuerzel}


class BehoerdenLangBezeichnung(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.BehoerdenLangBezeichnung
    }


class TaskTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.TaskTyp}


class TaskStatus(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.TaskStatus}


class TaskKategorie(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.TaskKategorie}


class PFASTyp(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.PFASTyp}


class BranchePFAS(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.BranchePFAS}


class LoeschmittelPFASHaltig(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.LoeschmittelPFASHaltig
    }


class LoeschmittelPFASFrei(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.LoeschmittelPFASFrei}


class LoeschschaumEinsatz(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.LoeschschaumEinsatz}


class HaeufigkeitNutzungVariante(Code):
    """
    Base class for all variants of HaeufigkeitNutzung.
    """

    __mapper_args__ = {"polymorphic_abstract": True}


class HaeufigkeitNutzungHandfeuerloescher(HaeufigkeitNutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.HaeufigkeitNutzungHandfeuerloescher
    }


class HaeufigkeitNutzungBeimischer(HaeufigkeitNutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.HaeufigkeitNutzungBeimischer
    }


class HaeufigkeitNutzungTankloescher(HaeufigkeitNutzungVariante):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.HaeufigkeitNutzungTankloescher
    }


class KTU(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.KTU}


class KinderspielplatzGruenflaecheTyp(Code):
    __mapper_args__ = {
        "polymorphic_identity": constants.CodeListe.KinderspielplatzGruenflaecheTyp
    }


class Eigentumsform(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.Eigentumsform}


class AltersstufeKinder(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.AltersstufeKinder}


class FlugplatzBezeichnung(Code):
    __mapper_args__ = {"polymorphic_identity": constants.CodeListe.FlugplatzBezeichnung}
