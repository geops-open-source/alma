from logging import getLogger

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    delete,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.orm import Session

from alma import constants
from alma.models import cache as cache_models
from alma.models import codes as code_models
from alma.models import grun as grun_models
from alma.models import subj as subj_models
from alma.models import vflz as vflz_models
from alma.settings import settings
from alma.tools.wfs import WfsClient, get_wfs_client
from alma.wfs_cache import get_filter_xml, update_custom_code_mapping

logger = getLogger(__name__)


def _make_wfs_results_table(session: Session) -> Table:
    metadata = MetaData()
    tmp_table = Table(
        "tmp_wfs_results",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("h_gem_id", Integer),
        Column("h_nb_id", String),
        Column("gb_nummer", String),
        Column("egrid", String),
        Column("wkb_geometry", Geometry("Geometry", srid=constants.LV_95_SRID)),  # pyright: ignore[reportUnknownArgumentType]
        prefixes=["TEMPORARY"],
        postgresql_on_commit="DROP",
    )
    metadata.create_all(session.connection(), tables=[tmp_table])
    return tmp_table


def _dump_wfs_results_to_table(
    session: Session, wfs_client: WfsClient, wfs_results_table: Table
):
    no_current_vflgeo_ids = session.execute(
        select(func.count())
        .select_from(vflz_models.VflGeo)
        .join(vflz_models.Vflz)
        .where(vflz_models.Vflz.is_current)
    ).scalar_one()

    page_size = settings.wfs_update_batch_size
    no_pages = no_current_vflgeo_ids // page_size
    for page_idx in range(no_pages + 1):
        paginated_vflgeos_query = (
            select(
                func.ST_AsGML(
                    func.Box2D(func.ST_Envelope(vflz_models.VflGeo.wkb_geometry))
                )
            )
            .join(vflz_models.Vflz)
            .where(vflz_models.Vflz.is_current)
            .offset(page_idx * page_size)
            .limit(page_size)
            .order_by(vflz_models.Vflz.vflz_id)
        )
        vflgeos = session.execute(paginated_vflgeos_query).all()
        wfs_results = wfs_client.query(bbox=None, filter_gml=get_filter_xml(vflgeos))
        update_custom_code_mapping(wfs_client.wfs_config, wfs_results)
        session.execute(wfs_results_table.insert(), wfs_results)


def update_grun_status(session: Session):
    wfs_client = get_wfs_client(wfs_service_name=settings.wfs_service_parzelle_name)
    wfs_results_table = _make_wfs_results_table(session)
    _dump_wfs_results_to_table(session, wfs_client, wfs_results_table)

    grun_found_in_wfs = (
        select(grun_models.Parzelle.grun_id)
        .join(
            wfs_results_table,
            or_(
                grun_models.Parzelle.egrid == wfs_results_table.c.egrid,
                and_(
                    grun_models.Parzelle.h_nb_id == wfs_results_table.c.h_nb_id,
                    grun_models.Parzelle.h_gem_id == wfs_results_table.c.h_gem_id,
                    grun_models.Parzelle.gb_nummer == wfs_results_table.c.gb_nummer,
                ),
            ),
        )
        .subquery()
    )

    session.execute(
        update(grun_models.Parzelle)
        .where(~grun_models.Parzelle.grun_id.in_(select(grun_found_in_wfs)))
        .values(c_grun_status="0")
    )

    session.execute(
        update(grun_models.Parzelle)
        .where(grun_models.Parzelle.grun_id.in_(select(grun_found_in_wfs)))
        .values(c_grun_status="1")
    )


def delete_dangling_grun(session: Session):
    assigned_grun_ids = (
        select(grun_models.Parzelle.grun_id)
        .join(subj_models.BeteiligterStandort)
        .subquery()
    )

    session.execute(
        delete(grun_models.Parzelle).where(
            ~grun_models.Parzelle.grun_id.in_(select(assigned_grun_ids)),
            grun_models.Parzelle.c_grun_status
            == constants.StatusParzelle.NICHT_AKTUELL,
        )
    )


def sync_gws_bereich_with_cache(session: Session):
    session.execute(
        update(vflz_models.Vflz)
        .values(c_vflz_gws_bereich=None)
        .where(vflz_models.Vflz.is_current)
    )

    kein_gws_bereich_code = session.scalars(
        select(code_models.Code).where(
            code_models.Code.c_cli_id == constants.CodeListe.Gewaesserschutzbereiche,
            code_models.Code.is_null_code,
        )
    ).one()

    cache_gws_bereich = (
        select(
            func.split_part(cache_models.WfsCache.gws_bereich, ":", 3).label(
                "gws_bereich"
            ),
            vflz_models.Vflz.vflz_id,
        )
        .select_from(cache_models.WfsCache)
        .join(
            vflz_models.VflGeo,
            func.ST_Intersects(
                cache_models.WfsCache.wkb_geometry,
                vflz_models.VflGeo.wkb_geometry,
            ),
        )
        .join(vflz_models.Vflz)
        .where(
            vflz_models.Vflz.is_current,
            cache_models.WfsCache.wfs_service_name == "gws_bereich",
        )
        .cte("cache_gws_bereich")
    )

    result = session.execute(
        update(vflz_models.Vflz)
        .values(
            {
                "h_vflz_gws_bereich": constants.CodeListe.Gewaesserschutzbereiche,
                "c_vflz_gws_bereich": cache_gws_bereich.c.gws_bereich,
            }
        )
        .where(vflz_models.Vflz.vflz_id == cache_gws_bereich.c.vflz_id)
    )

    logger.info(
        "Updated gws_bereich of %s from cache.",
        result.rowcount,  # type: ignore
    )  # cf. https://github.com/sqlalchemy/sqlalchemy/issues/12913
    result = session.execute(
        update(vflz_models.Vflz)
        .values(
            {
                "h_vflz_gws_bereich": constants.CodeListe.Gewaesserschutzbereiche,
                "c_vflz_gws_bereich": kein_gws_bereich_code.code,
            }
        )
        .where(
            vflz_models.Vflz.c_vflz_gws_bereich.is_(None), vflz_models.Vflz.is_current
        )
    )
    logger.info("Set gws_bereich of %s to 'keine'.", result.rowcount)  # type: ignore


def sync_gws_zone_with_cache(session: Session):
    session.execute(
        update(vflz_models.Vflz)
        .values(c_vflz_gws_zone=None)
        .where(vflz_models.Vflz.is_current)
    )

    keine_gws_zone_code = session.scalars(
        select(code_models.Code).where(
            code_models.Code.c_cli_id == constants.CodeListe.Gewaesserschutzzonen,
            code_models.Code.is_null_code,
        )
    ).one()

    cache_gws_zone = (
        select(
            func.split_part(cache_models.WfsCache.gws_zone, ":", 3).label("gws_zone"),
            vflz_models.Vflz.vflz_id,
        )
        .select_from(cache_models.WfsCache)
        .join(
            vflz_models.VflGeo,
            func.ST_Intersects(
                cache_models.WfsCache.wkb_geometry, vflz_models.VflGeo.wkb_geometry
            ),
        )
        .join(vflz_models.Vflz)
        .where(
            vflz_models.Vflz.is_current,
            cache_models.WfsCache.wfs_service_name == "gws_zone",
        )
        .cte("cache_gws_zone")
    )

    result = session.execute(
        update(vflz_models.Vflz)
        .values(
            {
                "h_vflz_gws_zone": constants.CodeListe.Gewaesserschutzzonen,
                "c_vflz_gws_zone": cache_gws_zone.c.gws_zone,
            }
        )
        .where(vflz_models.Vflz.vflz_id == cache_gws_zone.c.vflz_id)
    )
    logger.info("Updated gws_zone of %s from cache.", result.rowcount)  # type: ignore

    result = session.execute(
        update(vflz_models.Vflz)
        .values(
            {
                "h_vflz_gws_zone": constants.CodeListe.Gewaesserschutzzonen,
                "c_vflz_gws_zone": keine_gws_zone_code.code,
            }
        )
        .where(vflz_models.Vflz.c_vflz_gws_zone.is_(None), vflz_models.Vflz.is_current)
    )
    logger.info("Set gws_zone of %s to 'keine'.", result.rowcount)  # type: ignore
