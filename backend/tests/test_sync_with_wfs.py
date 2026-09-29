from unittest.mock import Mock

import pytest
from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from utils import (
    make_beteiligter,
    make_eigentuemer_standort,
    make_gemeinde,
    make_parzelle,
    make_subj,
    make_vflz,
)

from alma import constants, wfs_cache
from alma.models import cache as cache_models
from alma.models import codes as code_models
from alma.models import grun as grun_models
from alma.models import vflz as vflz_models
from alma.settings import settings
from alma.task_queue.sync_with_wfs import (
    delete_dangling_grun,
    sync_gws_bereich_with_cache,
    sync_gws_zone_with_cache,
    update_grun_status,
)

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
]


def test_updating_parzelle_cache_creates_new_grun_entry_if_not_present(
    session, wfs_test_settings
):
    basel_gem = make_gemeinde(session, "Basel", 1)
    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600000, 1200000],
    }

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo
    session.flush()
    session.refresh(vflgeo)

    wfs_client_mock = Mock()
    wfs_client_mock.wfs_config = settings.wfs_config[settings.wfs_service_parzelle_name]
    wfs_client_mock.name = settings.wfs_service_parzelle_name
    wfs_client_mock.query = Mock(
        return_value=[
            {
                "h_gem_id": 1,
                "h_nb_id": "my_h_nb_id",
                "gb_nummer": "3",
                "egrid": "egrid",
                "wkb_geometry": "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            }
        ]
    )
    assert not session.scalars(select(grun_models.Parzelle)).all()

    wfs_cache.update_cache(
        session,
        wfs_client_mock,
        bbox=wfs_cache.get_bbox(vflgeo),
    )

    grun = session.scalars(select(grun_models.Parzelle)).one()

    assert grun.gemeinde == basel_gem
    assert grun.nummerierungsbereich == session.get_one(
        grun_models.Nummerierungsbereich, "my_h_nb_id"
    )
    assert grun.gb_nummer == "3"
    assert grun.egrid == "egrid"
    assert (
        to_shape(grun.wkb_geometry).wkt
        == "MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))"
    )
    assert grun.status.code == constants.StatusParzelle.AKTUELL


def test_updating_parzelle_cache_updates_grun_state_and_value_if_present(
    session, wfs_test_settings
):
    parzelle_geom = "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))"
    basel_gem = make_gemeinde(session, "Basel", 1)
    parzelle = make_parzelle(session, "1", parzelle_geom, basel_gem)
    parzelle.egrid = "4"
    parzelle.c_grun_status = "0"  # nicht aktuell

    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600000, 1200000],
    }

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo
    session.flush()
    session.refresh(vflgeo)

    wfs_client_mock = Mock()
    wfs_client_mock.wfs_config = settings.wfs_config[settings.wfs_service_parzelle_name]
    wfs_client_mock.name = settings.wfs_service_parzelle_name
    wfs_client_mock.query = Mock(
        return_value=[
            {
                "h_gem_id": 1,
                "h_nb_id": None,
                "gb_nummer": "2",
                "egrid": "4",
                "wkb_geometry": "SRID=2056;MULTIPOLYGON (((2600000 1200001, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200001)))",
            }
        ]
    )

    db_parzelle = session.get_one(grun_models.Parzelle, parzelle.grun_id)

    assert db_parzelle.status.code == constants.StatusParzelle.NICHT_AKTUELL
    assert db_parzelle.gb_nummer == "1"
    assert (
        to_shape(db_parzelle.wkb_geometry).wkt
        == "MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))"
    )

    wfs_cache.update_cache(
        session,
        wfs_client_mock,
        bbox=wfs_cache.get_bbox(vflgeo),
    )

    session.flush()
    session.refresh(db_parzelle)

    assert db_parzelle.status.code == constants.StatusParzelle.AKTUELL
    assert db_parzelle.gb_nummer == "2"
    assert (
        to_shape(db_parzelle.wkb_geometry).wkt
        == "MULTIPOLYGON (((2600000 1200001, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200001)))"
    )


def test_mark_parcel_as_nicht_aktuell_that_is_not_present_in_wfs(
    session, wfs_test_settings, monkeypatch
):
    parzelle = make_parzelle(session, gb_nummer="dummy-gb-nummer")
    parzelle.c_grun_status = constants.StatusParzelle.AKTUELL

    wfs_client_mock = Mock()
    wfs_client_mock.wfs_config = settings.wfs_config[settings.wfs_service_parzelle_name]
    wfs_client_mock.name = settings.wfs_service_parzelle_name
    wfs_client_mock.query = Mock(
        return_value=[
            {
                "h_gem_id": 1,
                "h_nb_id": 4,
                "gb_nummer": "2",
                "egrid": "4",
                "wkb_geometry": "SRID=2056;MULTIPOLYGON (((2600000 1200001, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200001)))",
            }
        ]
    )
    monkeypatch.setattr(
        "alma.task_queue.sync_with_wfs.get_wfs_client",
        lambda wfs_service_name: wfs_client_mock,
    )
    update_grun_status(session)

    session.refresh(parzelle)
    assert parzelle.status.code == constants.StatusParzelle.NICHT_AKTUELL


def test_mark_parcel_as_aktuell_that_is_found_in_wfs(
    session, wfs_test_settings, monkeypatch
):
    parzelle_geom = "SRID=2056;MULTIPOLYGON (((2600000 1200001, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200001)))"
    bern_gem = make_gemeinde(session, name="Bern", bfs_nummer=1)
    parzelle = make_parzelle(
        session, gb_nummer="dummy-gb-nummer", geom_ewkt=parzelle_geom, gemeinde=bern_gem
    )
    parzelle.egrid = "4"
    parzelle.c_grun_status = constants.StatusParzelle.NICHT_AKTUELL

    wfs_client_mock = Mock()
    wfs_client_mock.wfs_config = settings.wfs_config[settings.wfs_service_parzelle_name]
    wfs_client_mock.name = settings.wfs_service_parzelle_name
    wfs_client_mock.query = Mock(
        return_value=[
            {
                "h_gem_id": 1,
                "h_nb_id": None,
                "gb_nummer": "dummy-gb-nummer",
                "egrid": "4",
                "wkb_geometry": "SRID=2056;MULTIPOLYGON (((2600000 1200001, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200001)))",
            }
        ]
    )
    monkeypatch.setattr(
        "alma.task_queue.sync_with_wfs.get_wfs_client",
        lambda wfs_service_name: wfs_client_mock,
    )
    update_grun_status(session)

    session.refresh(parzelle)
    assert parzelle.status.code == constants.StatusParzelle.AKTUELL


def test_do_not_delete_parzelle_that_is_assigned_to_bet_standort(session):
    parzelle = make_parzelle(session, gb_nummer="dummy-gb-nummer")
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet.bet_id, parzelle.grun_id)

    parzelle.c_grun_status = "0"

    delete_dangling_grun(session)

    session.refresh(parzelle)


def test_delete_parzelle_that_is_not_assigned_to_bet_standort(session):
    parzelle = make_parzelle(session, gb_nummer="dummy-gb-nummer")
    parzelle.c_grun_status = "0"

    delete_dangling_grun(session)

    with pytest.raises(InvalidRequestError, match="Instance '<Parzelle"):
        session.refresh(parzelle)


def test_do_not_delete_parzelle_that_is_set_to_aktuell(session):
    parzelle = make_parzelle(session, gb_nummer="dummy-gb-nummer")
    parzelle.c_grun_status = "1"

    delete_dangling_grun(session)

    session.refresh(parzelle)


def test_sync_old_gws_zone_with_new_cache_value(session):
    gws_zone_code = session.scalars(
        select(code_models.Gewaesserschutzzone).where(
            code_models.Gewaesserschutzzone.code == "test"
        )
    ).one()
    keine_gws_zone_code = session.scalars(
        select(code_models.Gewaesserschutzzone).where(
            code_models.Gewaesserschutzzone.code == "keine"
        )
    ).one()

    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600000, 1200000],
    }

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo
    vflz.gws_zone = keine_gws_zone_code

    cache_entry = cache_models.WfsCache(
        wfs_service_name="gws_zone",
        gws_zone=str(gws_zone_code),
    )
    cache_entry.wkb_geometry = vflgeo.wkb_geometry

    session.add(cache_entry)
    session.commit()

    sync_gws_zone_with_cache(session)

    session.commit()

    assert vflz.gws_zone == gws_zone_code


def test_sync_old_gws_bereich_with_new_cache_value(session):
    gws_bereich_code = session.scalars(
        select(code_models.Gewaesserschutzbereich).where(
            code_models.Gewaesserschutzbereich.code == "test"
        )
    ).one()
    keine_gws_bereich_code = session.scalars(
        select(code_models.Gewaesserschutzbereich).where(
            code_models.Gewaesserschutzbereich.code == "keine"
        )
    ).one()

    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600000, 1200000],
    }

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo
    vflz.gws_bereich = keine_gws_bereich_code

    cache_entry = cache_models.WfsCache(
        wfs_service_name="gws_bereich",
        gws_bereich=str(gws_bereich_code),
    )
    cache_entry.wkb_geometry = vflgeo.wkb_geometry

    session.add(cache_entry)
    session.commit()

    sync_gws_bereich_with_cache(session)

    session.commit()

    assert vflz.gws_bereich == gws_bereich_code


def test_assign_keine_codes_for_sync_gws_zone_and_bereich_if_no_values_present(session):
    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600000, 1200000],
    }

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo

    session.commit()

    sync_gws_bereich_with_cache(session)
    sync_gws_zone_with_cache(session)

    session.commit()

    keine_gws_bereich_code = session.scalars(
        select(code_models.Gewaesserschutzbereich).where(
            code_models.Gewaesserschutzbereich.code == "keine"
        )
    ).one()
    keine_gws_zone_code = session.scalars(
        select(code_models.Gewaesserschutzzone).where(
            code_models.Gewaesserschutzzone.code == "keine"
        )
    ).one()

    assert vflz.gws_bereich == keine_gws_bereich_code
    assert vflz.gws_zone == keine_gws_zone_code
