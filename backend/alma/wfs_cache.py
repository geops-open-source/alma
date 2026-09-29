import logging
import math
from collections.abc import Sequence
from datetime import datetime
from threading import Thread
from typing import Any

from geoalchemy2.shape import to_shape
from shapely import envelope  # type: ignore[reportUnknownVariableType]
from sqlalchemy import Row, delete, func, select
from sqlalchemy.orm import Session

from alma.db import get_session
from alma.exceptions import WfsError
from alma.models import codes
from alma.models import vflz as vflz_models
from alma.models.cache import WfsCache, WfsUpdate
from alma.models.grun import (
    Nummerierungsbereich,
    ParzelleKey,
    get_or_create_parzelle,
)
from alma.models.task_status import TaskCategory
from alma.models.vflz import Vflz
from alma.monitoring import monitor_task_status
from alma.settings import WfsSettings, settings
from alma.tools.wfs import WfsClient, get_wfs_client

logger = logging.getLogger(__name__)


FILTER_TEMPLATE = "<fes:Filter xmlns:fes='http://www.opengis.net/fes/2.0' xmlns:gml='http://www.opengis.net/gml'>{filter_body}</fes:Filter>"
FILTER_BODY_TEMPLATE = "<fes:Intersects><fes:ValueReference>geometry</fes:ValueReference>{extent_gml}</fes:Intersects>"


def get_bbox(vflgeo: vflz_models.VflGeo) -> tuple[float, float, float, float]:
    bbox = envelope(to_shape(vflgeo.wkb_geometry))
    return bbox.bounds


def get_filter_xml(vflgeos: Sequence[Row[tuple[str]]]) -> str:
    filter_body = ""
    for gml in vflgeos:
        filter_body += FILTER_BODY_TEMPLATE.format(extent_gml=gml[0])
    if len(vflgeos) > 1:
        filter_body = f"<fes:Or>{filter_body}</fes:Or>"
    return FILTER_TEMPLATE.format(filter_body=filter_body)


def update_custom_code_mapping(
    wfs_config: WfsSettings, wfs_results: list[dict[str, Any]]
) -> None:
    for row in wfs_results:
        for field_config in wfs_config.field_mappings:
            if field_config.code_mappings:
                field_name = field_config.cache_table
                value = row[field_name]
                if code := field_config.code_mappings.get(value):
                    row[field_name] = code


def update_cache(
    session: Session,
    wfs_client: WfsClient,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    filter_gml: str | None = None,
) -> int:
    wfs_results = wfs_client.query(bbox=bbox, filter_gml=filter_gml)
    if not wfs_results:
        return 0
    update_custom_code_mapping(wfs_client.wfs_config, wfs_results)
    for row in wfs_results:
        cache = WfsCache(wfs_service_name=wfs_client.name)
        for field_name, field_value in row.items():
            if field_value == "":
                field_value = None
            setattr(cache, field_name, field_value)
        session.add(cache)

        if wfs_client.name == settings.wfs_service_parzelle_name:
            with monitor_task_status(
                session, "sync_grun_with_cache", TaskCategory.IMPORT
            ):
                sync_grun_with_cache(session, cache)
    return len(wfs_results)


def sync_grun_with_cache(session: Session, cache: WfsCache):
    if not cache.gb_nummer:
        raise WfsError(
            "Parzelle cannot be uniquely referenced, cache values are: %s.", cache
        )

    assert cache.gb_nummer

    parzelle_key = ParzelleKey(
        h_gem_id=cache.h_gem_id,
        gb_nummer=cache.gb_nummer,
        h_nb_id=cache.h_nb_id,
        egrid=cache.egrid,
        wkb_geometry=cache.wkb_geometry,
    )

    aktuell_status_code = session.scalars(
        select(codes.StatusParzelle).where(codes.StatusParzelle.code == "1")
    ).one()
    parzelle = get_or_create_parzelle(session, parzelle_key)

    if parzelle_key.h_nb_id:
        nb = session.scalars(
            select(Nummerierungsbereich).where(
                Nummerierungsbereich.h_nb_id == parzelle_key.h_nb_id
            )
        ).one_or_none()
        if not nb:
            nb = Nummerierungsbereich(h_nb_id=parzelle_key.h_nb_id)
        parzelle.nummerierungsbereich = nb
    parzelle.h_gem_id = parzelle_key.h_gem_id
    parzelle.status = aktuell_status_code
    parzelle.egrid = parzelle_key.egrid
    parzelle.gb_nummer = parzelle_key.gb_nummer
    parzelle.wkb_geometry = parzelle_key.wkb_geometry
    parzelle.status = aktuell_status_code


def update_for_vflz(session: Session, vflz: Vflz):
    """
    Update all cached WFS data for a given VFLZ perimeter.
    """
    session.flush()
    session.refresh(vflz)
    if not vflz.vflgeo:
        return

    last_wfs_update = session.get(WfsUpdate, vflz.vflz_id)

    # Make sure geom properties are refreshed after an update.
    # TODO find a better solution to updating geometry fields that does not rely on
    # assigning SQLalchemy expressions to fields.
    def thread_worker(vflz_id: int):
        with get_session() as thread_local_session:
            vflz = thread_local_session.get(vflz_models.Vflz, vflz_id)
            # This will not happen in production code. In order to avoid exceptions in test
            # code due to multithreading, we have to deal with vflz not found in database
            # although we have its primary key.
            if not vflz or not vflz.vflgeo:
                return
            for wfs_service_name in settings.wfs_config:
                wfs_client = get_wfs_client(wfs_service_name)
                update_cache(
                    thread_local_session, wfs_client, bbox=get_bbox(vflz.vflgeo)
                )
            thread_local_session.commit()

    if not wfs_update_is_active(last_wfs_update):
        if not last_wfs_update:
            last_wfs_update = WfsUpdate()
        last_wfs_update.vflz_id = vflz.vflz_id
        last_wfs_update.last_update = datetime.now()
        session.add(last_wfs_update)
        t = Thread(group=None, target=thread_worker, args=(vflz.vflz_id,), daemon=True)
        t.start()


def refresh_wfs(session: Session, wfs_service_name: str):
    """
    Refresh all cached WFS data for a given service.
    """
    logger.info("Refreshing WFS cache for service %s.", wfs_service_name)

    wfs_client = get_wfs_client(wfs_service_name)

    vflzs = list(
        session.scalars(
            select(vflz_models.Vflz).where(vflz_models.Vflz.is_current)
        ).all()
    )
    num_rows = 0
    try:
        session.execute(
            delete(WfsCache).where(WfsCache.wfs_service_name == wfs_service_name)
        )

        # paginate vflgeos
        no_current_vflgeo_ids = session.execute(
            select(func.count())
            .select_from(vflz_models.VflGeo)
            .join(vflz_models.Vflz)
            .where(vflz_models.Vflz.is_current)
        ).scalar_one()

        page_size = settings.wfs_update_batch_size
        no_pages = math.ceil(no_current_vflgeo_ids / page_size)

        for page_idx in range(1, no_pages + 1):
            paginated_vflgeos_query = (
                select(
                    func.ST_AsGML(
                        func.Box2D(func.ST_Envelope(vflz_models.VflGeo.wkb_geometry))
                    )
                )
                .join(vflz_models.Vflz)
                .where(vflz_models.Vflz.is_current)
                .offset((page_idx - 1) * page_size)
                .limit(page_size)
                .order_by(vflz_models.Vflz.vflz_id)
            )
            vflgeos = session.execute(paginated_vflgeos_query).all()
            num_rows += update_cache(
                session, wfs_client, filter_gml=get_filter_xml(vflgeos)
            )

    except WfsError as e:
        logger.error(
            "WFS update failed for service %s. Error message: %s",
            wfs_service_name,
            str(e),
        )
        session.rollback()
        raise e
    logger.info(
        "Refreshed WFS cache for service %s: wrote %d cache entries for %d sites.",
        wfs_service_name,
        num_rows,
        len(vflzs),
    )
    session.commit()


def refresh_all(session: Session):
    """
    Refresh all cached WFS data.
    """
    for wfs_service_name in settings.wfs_config:
        with monitor_task_status(
            session, f"wfs_cache_{wfs_service_name}", TaskCategory.IMPORT
        ):
            refresh_wfs(session, wfs_service_name)
    session.commit()


def wfs_update_is_active(wfs_update: WfsUpdate | None) -> bool:
    if not wfs_update:
        return False
    return (
        datetime.now() - wfs_update.last_update
    ).total_seconds() < settings.wfs_max_update_interval_in_seconds
