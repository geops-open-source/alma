from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from functools import cmp_to_key
from typing import Any, Protocol, Self, runtime_checkable

from sqlalchemy import UnaryExpression, func
from sqlalchemy.orm import InstrumentedAttribute, Mapped

from alma.models import codes
from alma.models.base import Jsonb


@runtime_checkable
class ErfassungMutationProtocol(Protocol):
    erfassungs_datum: Mapped[datetime | None]
    erfasser: Mapped[str | None]
    mutations_datum: Mapped[datetime | None]
    mutierer: Mapped[str | None]


@runtime_checkable
class AuditinProtocol(Protocol):
    created_at: Mapped[datetime | None]
    created_by: Mapped[str | None]
    updated_at: Mapped[datetime | None]
    updated_by: Mapped[str | None]


class ZeitraumProtocol(Protocol):
    zeitraum_von: Mapped[date | None]
    zeitraum_bis: Mapped[date | None]
    zeitraum_vonjahr: Mapped[bool]
    zeitraum_bisjahr: Mapped[bool]
    zeitraum_bisheute: Mapped[bool]


class ZeitraumMitGenauigkeitProtocol(ZeitraumProtocol, Protocol):
    genauigkeit_von: Mapped[codes.Genauigkeit | None]
    genauigkeit_bis: Mapped[codes.Genauigkeit | None]


class KeyValueProtocol(Protocol):
    key: Mapped[str]
    value: Mapped[Jsonb]


@dataclass
class ZeitraumData:
    zeitraum_vonjahr: bool = False
    zeitraum_bisjahr: bool = False
    zeitraum_bisheute: bool = False
    zeitraum_von: date | None = None
    zeitraum_bis: date | None = None

    @classmethod
    def from_model(cls, model: ZeitraumProtocol) -> Self:
        return cls(
            zeitraum_vonjahr=model.zeitraum_vonjahr,
            zeitraum_bisjahr=model.zeitraum_bisjahr,
            zeitraum_bisheute=model.zeitraum_bisheute,
            zeitraum_von=model.zeitraum_von,
            zeitraum_bis=model.zeitraum_bis,
        )


def lower_von_date(a: ZeitraumProtocol, b: ZeitraumProtocol) -> int:
    """Returns 1 if b has a later 'von' date than a, 0 if equal, -1 else.
    `None` values are considered to be infinite in the future."""
    if (
        not a.zeitraum_von
        and not b.zeitraum_von
        or not a.zeitraum_von
        and b.zeitraum_von
    ):
        return 0
    elif a.zeitraum_von and not b.zeitraum_von:
        return -1
    elif not a.zeitraum_von and b.zeitraum_von:
        return 1
    elif a.zeitraum_von and b.zeitraum_von:
        if a.zeitraum_von > b.zeitraum_von:
            return 1
        elif a.zeitraum_von == b.zeitraum_von:
            return 0
        else:
            return -1
    else:
        return 0


def lower_bis_date(a: ZeitraumProtocol, b: ZeitraumProtocol) -> int:
    """Returns -1 if b has a later 'bis' date than a, 0 if equal, -1 else.
    `None` values are considered to be infinite in the past.
    'bisheute' is considered to be infinite in the future"""
    if a.zeitraum_bisheute:
        return 1
    elif b.zeitraum_bisheute:
        return -1
    elif not a.zeitraum_bis and not b.zeitraum_bis:
        return 0
    elif a.zeitraum_bis and not b.zeitraum_bis:
        return 1
    elif not a.zeitraum_bis and b.zeitraum_bis:
        return -1
    elif a.zeitraum_bis and b.zeitraum_bis:
        if a.zeitraum_bis > b.zeitraum_bis:
            return 1
        elif a.zeitraum_bis == b.zeitraum_bis:
            return 0
        else:
            return -1
    else:
        return 0


def merge(objs: Sequence[ZeitraumProtocol]) -> ZeitraumData:
    """Merges the Zeitraum's of objs into one Zeitraum."""
    if objs:
        objs_sorted_by_lower_von_date = sorted(objs, key=cmp_to_key(lower_von_date))
        objs_sorted_by_lower_bis_date = sorted(objs, key=cmp_to_key(lower_bis_date))
        return ZeitraumData(
            zeitraum_von=objs_sorted_by_lower_von_date[0].zeitraum_von,
            zeitraum_bis=objs_sorted_by_lower_bis_date[-1].zeitraum_bis,
            zeitraum_vonjahr=objs_sorted_by_lower_von_date[0].zeitraum_vonjahr,
            zeitraum_bisjahr=objs_sorted_by_lower_bis_date[-1].zeitraum_bisjahr,
            zeitraum_bisheute=objs_sorted_by_lower_bis_date[-1].zeitraum_bisheute,
        )
    else:
        return ZeitraumData()


def order_by_start_date_criteria(
    class_type: type[ZeitraumProtocol] | type[ZeitraumMitGenauigkeitProtocol],
    pk_callable: InstrumentedAttribute[int] | UnaryExpression[int],
) -> list[
    UnaryExpression[Any]
    | UnaryExpression[bool]
    | InstrumentedAttribute[int]
    | UnaryExpression[int]
]:
    """Returns order by sql statement for classes that follow Zeitraum Protocol.

    Sort criteria is as follows (year, <year_flag>, month, day, id) descending."""
    return [
        func.date_part("year", class_type.zeitraum_von).desc().nulls_last(),
        class_type.zeitraum_vonjahr.desc(),
        func.date_part("month", class_type.zeitraum_von).desc(),
        func.date_part("day", class_type.zeitraum_von).desc(),
        pk_callable,
    ]
