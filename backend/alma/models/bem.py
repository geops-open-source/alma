from sqlalchemy.orm import Mapped, mapped_column

from .. import constants
from .base import Base
from .mixins import ErfassungMutationMixin
from .snapshots import SupportsSnapshots


class BasisBemerkung(Base, SupportsSnapshots, ErfassungMutationMixin):
    __tablename__ = "bem"
    __table_args__ = {"schema": "alma"}
    __mapper_args__ = {
        "polymorphic_on": "bemgrp_id",
        "polymorphic_abstract": True,
    }

    bem_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    bemgrp_id: Mapped[int] = mapped_column(init=False)
    key_value: Mapped[int] = mapped_column(init=False)

    bem: Mapped[str]
    public: Mapped[bool] = mapped_column(default=False)
    sort: Mapped[int | None] = mapped_column(default=None)


class BemerkungStandort(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Standort}


class BemerkungUmwelt(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Umwelt}


class BemerkungIntern(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Intern}


class BegruendungBewertung(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Bewertung}


class BegruendungPrioUntersuchungsbedarf(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.PrioUntersuchung
    }


class BegruendungPrioSanierungsbedarf(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.PrioSanierung
    }


class BemerkungBetrieb(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Betrieb}


class BemerkungAblagerung(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Ablagerung}


class BemerkungUnfall(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Unfall}


class BemerkungMassnahme(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Massnahme}


class BemerkungSanierung(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Sanierung}


class BemerkungUmweltschaden(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.Umweltschaden
    }


class BemerkungEinzelereignis(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.Einzelereignis
    }


class BegruendungBewertungBetrieb(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.BegruendungBewertungBetrieb
    }


class BemerkungSubjekt(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.Subjekt}


class BemerkungPFAS(BasisBemerkung):
    __mapper_args__ = {"polymorphic_identity": constants.KategorieBemerkung.PFAS}


class BegruendungBewertungPFAS(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.BegruendungBewertungPFAS
    }


class BemerkungKinderspielplatzGruenflaeche(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.KinderspielplatzGruenflaeche
    }


class BegruendungBewertungKinderspielplatzGruenflaeche(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.BegruendungBewertungKinderspielplatzGruenflaeche
    }


class BemerkungDatenimportSchiessanlage(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportSchiessanlage
    }


class BemerkungDatenimportAblagerung(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportAblagerung
    }


class BemerkungDatenimportBetrieb(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportBetrieb
    }


class BemerkungDatenimportUnfall(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportUnfall
    }


class BemerkungDatenimportKinderspielplatzGruenflaeche(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportKinderspielplatzGruenflaeche
    }


class BemerkungDatenimportPFAS(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportPFAS
    }


class BemerkungDatenimportStandort(BasisBemerkung):
    __mapper_args__ = {
        "polymorphic_identity": constants.KategorieBemerkung.DatenimportStandort
    }
