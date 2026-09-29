from datetime import date
from typing import Self

import strawberry

from alma.models import umwelt as umwelt_models

from ..utils.schema import Info, to_id
from .bem import Bemerkung, BemerkungInput
from .codes import Code, CodeInput
from .misc import ErfassungMutation


@strawberry.type
class Grundwasser:
    gwas_id: strawberry.ID
    relative_lage: Code | None
    flurabstand: float | None
    nutzung: Code | None
    distanz: int | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, grundwasser: umwelt_models.Grundwasser) -> Self:
        return cls(
            gwas_id=to_id(grundwasser.gwas_id),
            relative_lage=Code.from_db_or_none(grundwasser.relative_lage),
            flurabstand=grundwasser.flurabstand,
            nutzung=Code.from_db_or_none(grundwasser.nutzung),
            distanz=grundwasser.distanz,
            erfassung_mutation=ErfassungMutation.from_db(grundwasser),
        )


@strawberry.input
class GrundwasserInput:
    gwas_id: strawberry.ID | None
    relative_lage: CodeInput | None
    flurabstand: float | None
    nutzung: CodeInput | None
    distanz: int | None


@strawberry.type
class OberflaechenGewaesser:
    ogw_id: strawberry.ID
    art_gewaesser: Code | None
    bau_gewaesser: Code | None
    relative_lage: Code | None
    distanz: int | None
    name: str | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(
        cls, oberflaechen_gewaesser: umwelt_models.OberflaechenGewaesser
    ) -> Self:
        return cls(
            ogw_id=to_id(oberflaechen_gewaesser.ogw_id),
            art_gewaesser=Code.from_db_or_none(oberflaechen_gewaesser.art_gewaesser),
            bau_gewaesser=Code.from_db_or_none(oberflaechen_gewaesser.bau_gewaesser),
            relative_lage=Code.from_db_or_none(oberflaechen_gewaesser.relative_lage),
            distanz=oberflaechen_gewaesser.distanz,
            name=oberflaechen_gewaesser.name,
            erfassung_mutation=ErfassungMutation.from_db(oberflaechen_gewaesser),
        )


@strawberry.input
class OberflaechenGewaesserInput:
    ogw_id: strawberry.ID | None
    art_gewaesser: CodeInput | None
    bau_gewaesser: CodeInput | None
    relative_lage: CodeInput | None
    distanz: int | None
    name: str | None


@strawberry.type
class NutzungBoden:
    nubo_id: strawberry.ID
    nutzungsart: Code | None
    aktuelle_nutzung: Code | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, nutzung_boden: umwelt_models.NutzungBoden) -> Self:
        return cls(
            nubo_id=to_id(nutzung_boden.nubo_id),
            nutzungsart=Code.from_db_or_none(nutzung_boden.nutzungsart),
            aktuelle_nutzung=Code.from_db_or_none(nutzung_boden.aktuelle_nutzung),
            erfassung_mutation=ErfassungMutation.from_db(nutzung_boden),
        )


@strawberry.input
class NutzungBodenInput:
    nubo_id: strawberry.ID | None
    nutzungsart: CodeInput | None
    aktuelle_nutzung: CodeInput | None


@strawberry.input
class UmweltStoffInput:
    stoffe_id: strawberry.ID | None
    gefaehrdete_bereiche: CodeInput | None
    stoff_gruppe: CodeInput | None
    stoff: CodeInput | None
    beurteilung: CodeInput | None


@strawberry.type
class UmweltStoff:
    stoffe_id: strawberry.ID
    gefaehrdete_bereiche: Code | None
    stoff_gruppe: Code | None
    stoff: Code | None
    beurteilung: Code | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, umwelt_stoff: umwelt_models.UmweltStoff) -> Self:
        return cls(
            stoffe_id=to_id(umwelt_stoff.stoffe_id),
            gefaehrdete_bereiche=Code.from_db_or_none(
                umwelt_stoff.gefaehrdete_bereiche
            ),
            stoff_gruppe=Code.from_db_or_none(umwelt_stoff.stoff_gruppe),
            stoff=Code.from_db_or_none(umwelt_stoff.stoff),
            beurteilung=Code.from_db_or_none(umwelt_stoff.beurteilung),
            erfassung_mutation=ErfassungMutation.from_db(umwelt_stoff),
        )


@strawberry.type
class Einzelereignis:
    _einzelereignis: strawberry.Private[umwelt_models.Einzelereignis]
    veen_id: strawberry.ID
    einzelereignis: Code | None
    datum: date | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, einzelereignis: umwelt_models.Einzelereignis) -> Self:
        return cls(
            _einzelereignis=einzelereignis,
            veen_id=to_id(einzelereignis.veen_id),
            einzelereignis=Code.from_db_or_none(einzelereignis.einzelereignis),
            datum=einzelereignis.datum,
            erfassung_mutation=ErfassungMutation.from_db(einzelereignis),
        )

    @strawberry.field
    def bemerkung(self, info: Info) -> Bemerkung | None:
        if bemerkung := self._einzelereignis.bemerkung:
            return Bemerkung.from_db(bemerkung)


@strawberry.input
class EinzelereignisInput:
    veen_id: strawberry.ID | None
    einzelereignis: Code | None
    datum: date | None
    bemerkung: BemerkungInput | None


@strawberry.type
class Umweltschaden:
    _umweltschaden: strawberry.Private[umwelt_models.Umweltschaden]
    vfus_id: strawberry.ID
    art_schaden: Code | None
    schaeden: Code | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, umweltschaden: umwelt_models.Umweltschaden) -> Self:
        return cls(
            _umweltschaden=umweltschaden,
            vfus_id=to_id(umweltschaden.vfus_id),
            art_schaden=Code.from_db_or_none(umweltschaden.art_schaden),
            schaeden=Code.from_db_or_none(umweltschaden.schaeden),
            erfassung_mutation=ErfassungMutation.from_db(umweltschaden),
        )

    @strawberry.field
    def bemerkung(self, info: Info) -> Bemerkung | None:
        if bemerkung := self._umweltschaden.bemerkung:
            return Bemerkung.from_db(bemerkung)


@strawberry.input
class UmweltschadenInput:
    vfus_id: strawberry.ID | None
    art_schaden: Code | None
    schaeden: Code | None
    bemerkung: BemerkungInput | None
