from collections.abc import Callable, Iterable
from enum import Enum, auto
from itertools import filterfalse, groupby, tee
from typing import Self, TypeVar, cast

import strawberry

from alma.models import grun as grun_models

from ..scalars import GeoJSONMultiPolygon
from ..utils.schema import to_id
from .codes import Code, CodeInput
from .gem import Gemeinde
from .misc import ErfassungMutation
from .subj import Subjekt

T = TypeVar("T")


# See https://docs.python.org/3.11/library/itertools.html#itertools-recipes
def partition(
    pred: Callable[[T], bool], iterable: Iterable[T]
) -> tuple[Iterable[T], Iterable[T]]:
    """
    Use a predicate to partition entries into false entries and true entries
    """
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


@strawberry.type
class Nummerierungsbereich:
    h_nb_id: str
    bezeichnung: str | None
    geometry: GeoJSONMultiPolygon | None
    erfassung_mutation: ErfassungMutation | None

    @classmethod
    def from_db(cls, nb: grun_models.Nummerierungsbereich) -> Self:
        return cls(
            h_nb_id=nb.h_nb_id,
            bezeichnung=nb.bezeichnung,
            geometry=cast(GeoJSONMultiPolygon | None, nb.wkb_geometry_geojson),
            erfassung_mutation=ErfassungMutation.from_db(nb),
        )


@strawberry.type
class GemeindeNummerierungsbereich:
    gemeinde: Gemeinde | None
    nummerierungsbereich: Nummerierungsbereich | None


@strawberry.type
class Parzelle:
    grun_id: strawberry.ID
    gemeinde: Gemeinde | None
    nummerierungsbereich: Nummerierungsbereich | None
    status: Code
    egrid: str | None
    geometry: GeoJSONMultiPolygon | None
    erfassung_mutation: ErfassungMutation | None
    gb_nummer: str

    @classmethod
    def from_db(cls, obj: grun_models.Parzelle) -> Self:
        return cls(
            grun_id=to_id(obj.grun_id),
            gemeinde=Gemeinde.from_db(obj.gemeinde) if obj.gemeinde else None,
            nummerierungsbereich=(
                Nummerierungsbereich.from_db(obj.nummerierungsbereich)
                if obj.nummerierungsbereich
                else None
            ),
            status=Code.from_db(obj.status),
            egrid=obj.egrid,
            geometry=cast(GeoJSONMultiPolygon | None, obj.wkb_geometry_geojson),
            erfassung_mutation=ErfassungMutation.from_db(obj),
            gb_nummer=obj.gb_nummer,
        )


@strawberry.enum
class EigentumStatus(Enum):
    ZUGEORDNET = auto()
    FEHLEND = auto()
    UEBERZAEHLIG = auto()


@strawberry.input
class EigentumInput:
    status: EigentumStatus
    subj_id: strawberry.ID | None
    beziehungsart: CodeInput | None
    h_gem_id: strawberry.ID | None
    h_nb_id: str | None
    parzellen: list[str]


@strawberry.type
class Eigentum:
    status: EigentumStatus
    subjekt: Subjekt | None
    beziehungsart: Code | None
    gemeinde: Gemeinde | None
    nummerierungsbereich: Nummerierungsbereich | None
    parzellen: list[str]
    erfassung_mutation: ErfassungMutation | None

    @staticmethod
    def apply_grouping(ets: list["Eigentum"]) -> list["Eigentum"]:
        def key_func_groupby(et: Eigentum) -> tuple[int, int, str, int, str]:
            return (
                et.status.value,
                int(et.subjekt.subj_id) if et.subjekt is not None else 0,
                str(et.beziehungsart) if et.beziehungsart is not None else "",
                int(et.gemeinde.h_gem_id) if et.gemeinde is not None else 0,
                et.nummerierungsbereich.h_nb_id
                if et.nummerierungsbereich is not None
                else "",
            )

        def key_func_sort(et: Eigentum) -> tuple[int, int, str, int, str, list[str]]:
            return key_func_groupby(et) + (sorted(et.parzellen),)

        ets = sorted(ets, key=key_func_sort)

        others, zugeordnet = partition(
            lambda et: et.status is EigentumStatus.ZUGEORDNET, ets
        )
        zugeordnet_grouped: list[Eigentum] = []

        for _, group_iter in groupby(zugeordnet, key=key_func_groupby):
            first_row = next(group_iter)
            for next_row in group_iter:
                first_row.parzellen.extend(next_row.parzellen)
            zugeordnet_grouped.append(first_row)

        others, ueberzeaehlig = partition(
            lambda et: et.status is EigentumStatus.UEBERZAEHLIG, others
        )
        ueberzaehlig_grouped: list[Eigentum] = []

        for _, group_iter in groupby(ueberzeaehlig, key=key_func_groupby):
            first_row = next(group_iter)
            for next_row in group_iter:
                first_row.parzellen.extend(next_row.parzellen)
            ueberzaehlig_grouped.append(first_row)

        return zugeordnet_grouped + ueberzaehlig_grouped + list(others)
