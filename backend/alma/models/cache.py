from datetime import datetime

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WfsCache(Base):
    __tablename__ = "wfs_cache"
    __table_args__ = {"schema": "alma_external"}

    # Primary Key
    wfs_cache_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Actual fields
    wfs_service_name: Mapped[str]
    wkb_geometry: Mapped[WKBElement] = mapped_column(Geometry, init=False, repr=False)

    postleitzahl: Mapped[str | None] = mapped_column(default=None)
    ort: Mapped[str | None] = mapped_column(default=None)
    h_gem_id: Mapped[int | None] = mapped_column(default=None)
    gemeinde_name: Mapped[str | None] = mapped_column(default=None)
    bfs_nummer: Mapped[int | None] = mapped_column(default=None)
    h_nb_id: Mapped[str | None] = mapped_column(default=None)
    egrid: Mapped[str | None] = mapped_column(default=None)
    gb_nummer: Mapped[str | None] = mapped_column(default=None)
    gws_zone: Mapped[str | None] = mapped_column(default=None)
    gws_bereich: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        init=False, default_factory=datetime.now
    )


class WfsUpdate(Base):
    __tablename__ = "wfs_update"
    __table_args__ = {"schema": "alma_external"}

    # Primary keys
    vflz_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    last_update: Mapped[datetime] = mapped_column(init=False)
