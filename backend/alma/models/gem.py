import json
from typing import Any

from geoalchemy2 import Geometry, WKBElement, functions
from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from ..constants import LV_95_SRID
from . import codes
from .base import Base, CodeForeignKeyConstraint


class Gemeinde(Base):
    __tablename__ = "h_gem"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_kanton", "c_kanton"]),
        {"schema": "alma"},
    )

    h_gem_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    h_kanton: Mapped[int] = mapped_column(init=False)
    c_kanton: Mapped[str] = mapped_column(init=False)

    kanton: Mapped[codes.Kanton] = relationship(
        codes.Kanton,
        foreign_keys=[h_kanton, c_kanton],
        lazy="joined",
    )

    bfs_nummer: Mapped[int | None]
    gemeinde: Mapped[str]

    # Actual fields
    wkb_geometry: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="MultiPolygon", srid=LV_95_SRID), init=False
    )

    def __post_init__(self) -> None:
        if self.bfs_nummer is not None:
            self.h_gem_id = self.bfs_nummer


def from_geom(session: Session, geojson: dict[str, Any]) -> list[Gemeinde]:
    query = (
        select(Gemeinde)
        .where(
            functions.ST_Intersects(
                Gemeinde.wkb_geometry,
                functions.ST_SetSRID(
                    functions.ST_GeomFromGeoJSON(json.dumps(geojson)),
                    LV_95_SRID,
                ),
            )
        )
        .order_by(Gemeinde.h_gem_id)
    )
    return list(session.scalars(query).all())
