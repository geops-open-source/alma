import json
from typing import Any

from geoalchemy2 import Geometry, WKBElement, functions
from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from alma import constants
from alma.models import codes
from alma.models.base import Base, CodeForeignKeyConstraint


class Flugplatz(Base):
    __tablename__ = "flugplatz"
    __table_args__ = (
        CodeForeignKeyConstraint(
            ["h_flugplatz_bezeichnung", "c_flugplatz_bezeichnung"]
        ),
        {"schema": "alma"},
    )

    # Primary key
    flugplatz_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Codewerte
    h_flugplatz_bezeichnung: Mapped[str] = mapped_column(init=False)
    c_flugplatz_bezeichnung: Mapped[str] = mapped_column(init=False)

    # Relationships
    bezeichnung: Mapped[codes.FlugplatzBezeichnung] = relationship(
        codes.FlugplatzBezeichnung,
        foreign_keys=[h_flugplatz_bezeichnung, c_flugplatz_bezeichnung],
        lazy="joined",
    )

    # Actual fields
    icao: Mapped[str]
    art: Mapped[str]
    c_kt: Mapped[str]
    abk: Mapped[str]
    zusatz: Mapped[str]

    wkb_geometry: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="Geometry", srid=constants.LV_95_SRID), init=False
    )


def from_geom(session: Session, geojson: dict[str, Any]) -> list[Flugplatz]:
    query = (
        select(Flugplatz)
        .where(
            functions.ST_Intersects(
                Flugplatz.wkb_geometry,
                functions.ST_SetSRID(
                    functions.ST_GeomFromGeoJSON(json.dumps(geojson)),
                    constants.LV_95_SRID,
                ),
            )
        )
        .order_by(Flugplatz.flugplatz_id)
    )
    return list(session.scalars(query).all())
