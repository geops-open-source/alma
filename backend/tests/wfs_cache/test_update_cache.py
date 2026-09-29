import json

import pytest
from sqlalchemy import select
from utils import make_vflz

from alma import wfs_cache
from alma.models import cache as cache_models
from alma.models import vflz as vflz_models
from alma.tools.wfs import get_wfs_client

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "bearbeiten sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


def test_creating_new_geometry_updates_cache_for_gemeinde_ort_and_plz(
    session, wfs_test_settings
):
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    vflz = make_vflz(session, "My Site")

    vflgeo = vflz_models.VflGeo()
    vflgeo.set_geometry(extent_geojson)
    vflz.vflgeo = vflgeo
    session.flush()
    session.refresh(vflgeo)

    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflgeo)
    )
    wfs_cache.update_cache(
        session, get_wfs_client("ort_plz"), bbox=wfs_cache.get_bbox(vflgeo)
    )

    gemeinde_cache = session.scalars(
        select(cache_models.WfsCache).where(
            cache_models.WfsCache.wfs_service_name == "gemeinde"
        )
    ).one()
    assert gemeinde_cache.gemeinde_name == "Brig-Glis"
    assert not gemeinde_cache.ort
    assert not gemeinde_cache.postleitzahl

    ort_plz_cache = session.scalars(
        select(cache_models.WfsCache).where(
            cache_models.WfsCache.wfs_service_name == "ort_plz"
        )
    ).one()
    assert not ort_plz_cache.gemeinde_name
    assert ort_plz_cache.ort == "Gamsen"
    assert ort_plz_cache.postleitzahl == "3900"


def test_updating_geometry_always_updates_cache(session, wfs_test_settings):
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    extent_geojson2 = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2642355, 1246706],
    }
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.flush()
    session.refresh(vflz)

    # first change in geometry
    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )
    wfs_cache.update_cache(
        session, get_wfs_client("ort_plz"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )

    first_update_no_rows_gemeinde_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "gemeinde"
            )
        ).all()
    )
    first_update_no_rows_ort_plz_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "ort_plz"
            )
        ).all()
    )
    assert first_update_no_rows_gemeinde_cache
    assert first_update_no_rows_ort_plz_cache
    assert json.loads(vflz.vflgeo.wkb_geometry_geojson) == extent_geojson

    # second update
    vflz.vflgeo.set_geometry(extent_geojson2)
    session.flush()
    session.refresh(vflz)
    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )
    wfs_cache.update_cache(
        session, get_wfs_client("ort_plz"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )

    second_update_no_rows_gemeinde_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "gemeinde"
            )
        ).all()
    )
    second_update_no_rows_ort_plz_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "ort_plz"
            )
        ).all()
    )
    assert second_update_no_rows_gemeinde_cache > first_update_no_rows_gemeinde_cache
    assert second_update_no_rows_ort_plz_cache > first_update_no_rows_ort_plz_cache
    assert vflz.vflgeo
    assert json.loads(vflz.vflgeo.wkb_geometry_geojson) == extent_geojson2

    # change to first geom
    vflz.vflgeo.set_geometry(extent_geojson)
    session.flush()
    session.refresh(vflz)
    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )
    wfs_cache.update_cache(
        session, get_wfs_client("ort_plz"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )

    third_update_no_rows_gemeinde_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "gemeinde"
            )
        ).all()
    )
    third_update_no_rows_ort_plz_cache = len(
        session.scalars(
            select(cache_models.WfsCache).where(
                cache_models.WfsCache.wfs_service_name == "ort_plz"
            )
        ).all()
    )
    assert third_update_no_rows_gemeinde_cache > second_update_no_rows_gemeinde_cache
    assert third_update_no_rows_ort_plz_cache > second_update_no_rows_ort_plz_cache
    assert json.loads(vflz.vflgeo.wkb_geometry_geojson) == extent_geojson


def test_wfs_does_not_yield_any_features(session, wfs_test_settings):
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [0, 0],
    }
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.flush()
    session.refresh(vflz)

    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )
    assert not session.scalars(select(cache_models.WfsCache)).one_or_none()


def test_wfs_yields_multiple_features(session, wfs_test_settings):
    extent_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2735519.98637385, 1269420.55215919],
                    [2735519.98637385, 1274000.92154453],
                    [2743645.530627524, 1274000.92154453],
                    [2743645.530627524, 1269420.55215919],
                    [2735519.98637385, 1269420.55215919],
                ]
            ]
        ],
    }
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.flush()
    session.refresh(vflz)

    wfs_cache.update_cache(
        session, get_wfs_client("gemeinde"), bbox=wfs_cache.get_bbox(vflz.vflgeo)
    )
    wfs_gemeinden = list(
        session.scalars(
            select(cache_models.WfsCache.gemeinde_name).order_by(
                cache_models.WfsCache.gemeinde_name
            )
        ).all()
    )
    assert wfs_gemeinden == [
        "Altnau",
        "Amriswil",
        "Birwinken",
        "Bodensee (TG)",
        "Dozwil",
        "Erlen",
        "Güttingen",
        "Hefenhofen",
        "Kesswil",
        "Langrickenbach",
        "Romanshorn",
        "Sommeri",
        "Uttwil",
    ]
