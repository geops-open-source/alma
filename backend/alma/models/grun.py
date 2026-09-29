from typing import NamedTuple

from geoalchemy2 import Geometry, WKBElement, functions
from sqlalchemy import ForeignKey, and_, or_, select
from sqlalchemy.orm import Mapped, Session, column_property, mapped_column, relationship

from .. import constants
from . import codes
from .base import Base, CodeForeignKeyConstraint
from .gem import Gemeinde
from .mixins import ErfassungMutationMixin


class Nummerierungsbereich(Base, ErfassungMutationMixin):
    __tablename__ = "h_nb"
    __table_args__ = {"schema": "alma"}

    # Primary key
    h_nb_id: Mapped[str] = mapped_column(primary_key=True)

    # Fields
    bezeichnung: Mapped[str | None] = mapped_column(default=None)
    wkb_geometry: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="MultiPolygon", srid=constants.LV_95_SRID), default=None
    )
    wkb_geometry_geojson: Mapped[str | None] = column_property(
        functions.ST_AsGeoJSON(wkb_geometry)
    )


class Parzelle(Base, ErfassungMutationMixin):
    __tablename__ = "grun"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_grun_status", "c_grun_status"]),
        {"schema": "alma"},
    )

    # Primary key
    grun_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    h_gem_id: Mapped[int | None] = mapped_column(
        ForeignKey("alma.h_gem.h_gem_id"), init=False
    )
    h_nb_id: Mapped[str | None] = mapped_column(
        ForeignKey("alma.h_nb.h_nb_id"), init=False
    )

    # Codewerte
    h_grun_status: Mapped[int] = mapped_column(init=False)
    c_grun_status: Mapped[str] = mapped_column(init=False)

    # fields
    gb_nummer: Mapped[str]

    status: Mapped[codes.StatusParzelle] = relationship(
        codes.StatusParzelle,
        foreign_keys=[h_grun_status, c_grun_status],
        lazy="joined",
    )
    gemeinde: Mapped[Gemeinde | None] = relationship(Gemeinde, default=None)
    nummerierungsbereich: Mapped[Nummerierungsbereich | None] = relationship(
        Nummerierungsbereich, default=None
    )

    egrid: Mapped[str | None] = mapped_column(default=None)
    wkb_geometry: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="MultiPolygon", srid=constants.LV_95_SRID), default=None
    )
    wkb_geometry_geojson: Mapped[str | None] = column_property(
        functions.ST_AsGeoJSON(wkb_geometry)
    )


class ParzelleKey(NamedTuple):
    h_gem_id: int | None
    gb_nummer: str
    h_nb_id: str | None
    egrid: str | None
    wkb_geometry: WKBElement | None


def get_parzelle(session: Session, key: ParzelleKey) -> Parzelle | None:
    condition = Parzelle.gb_nummer == key.gb_nummer

    if key.h_gem_id:
        condition = and_(condition, Parzelle.h_gem_id == key.h_gem_id)

    if key.h_nb_id:
        condition = and_(condition, Parzelle.h_nb_id == key.h_nb_id)

    if key.egrid:
        condition = or_(condition, Parzelle.egrid == key.egrid)

    if key.wkb_geometry:
        condition = or_(condition, Parzelle.wkb_geometry == key.wkb_geometry)

    parzelle = session.scalars(select(Parzelle).where(condition)).one_or_none()
    return parzelle


def get_or_create_parzelle(session: Session, key: ParzelleKey) -> Parzelle:
    if parzelle := get_parzelle(session, key):
        return parzelle
    else:
        status_parzelle_nicht_aktuell = session.get_one(
            codes.StatusParzelle,
            (
                constants.CodeListe.StatusParzelle,
                constants.StatusParzelle.NICHT_AKTUELL,
            ),
        )
        parzelle = Parzelle(
            status=status_parzelle_nicht_aktuell,
            gb_nummer=key.gb_nummer,
        )
        if key.h_gem_id:
            gemeinde = session.get_one(Gemeinde, key.h_gem_id)
            parzelle.gemeinde = gemeinde

        if key.h_nb_id:
            nummerierungsbereich = session.scalars(
                select(Nummerierungsbereich).where(
                    Nummerierungsbereich.h_nb_id == key.h_nb_id
                )
            ).one_or_none()
            if not nummerierungsbereich:
                nummerierungsbereich = Nummerierungsbereich(h_nb_id=key.h_nb_id)
            parzelle.nummerierungsbereich = nummerierungsbereich
        parzelle.egrid = key.egrid
        parzelle.wkb_geometry = key.wkb_geometry
        session.add(parzelle)
        return parzelle
