from unittest.mock import Mock

import pytest
from sqlalchemy import select
from utils import make_vflz

import alma.wfs_cache
from alma import wfs_cache
from alma.exceptions import WfsError
from alma.models.cache import WfsCache
from alma.models.vflz import VflGeo
from alma.settings import settings
from alma.tools.wfs import get_wfs_client

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "bearbeiten sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


def test_update_of_one_cache_entry(session, wfs_test_settings):
    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    vflz.vflgeo = VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()

    wfs_client = get_wfs_client("gemeinde")
    wfs_cache.update_cache(session, wfs_client, bbox=wfs_cache.get_bbox(vflz.vflgeo))

    old_cache_entry = session.scalars(
        select(WfsCache).where(WfsCache.wfs_service_name == "gemeinde")
    ).one()

    wfs_cache.refresh_wfs(session, "gemeinde")
    new_cache_entry = session.scalars(
        select(WfsCache).where(WfsCache.wfs_service_name == "gemeinde")
    ).one()

    assert new_cache_entry.created_at > old_cache_entry.created_at


def test_do_not_touch_cache_table_if_wfs_throws_error(session, wfs_test_settings):
    settings.wfs_config["gemeinde"].url = "I do not exist"

    vflz = make_vflz(session, "My Site")
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    vflz.vflgeo = VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()

    assert not session.scalars(select(WfsCache)).all()
    with pytest.raises(WfsError):
        wfs_cache.refresh_wfs(session, "gemeinde")
    assert not session.scalars(select(WfsCache)).all()


def test_refresh_wfs_cache_pagination_with_full_pages_does_not_raise(
    session, wfs_test_settings
):
    settings.wfs_update_batch_size = 2
    num_vflz = 4
    for i in range(num_vflz):
        vflz = make_vflz(session, f"My Site {i}")
        extent_geojson = {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [2638160 + i * 10, 1127775 + i * 10],
        }
        vflz.vflgeo = VflGeo()
        vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()
    wfs_cache.refresh_wfs(session, "gemeinde")


def test_refresh_wfs_cache_pagination_with_partial_page_calls_query_correct_number_of_times(
    session, wfs_test_settings, monkeypatch
):
    settings.wfs_update_batch_size = 2
    num_vflz = 7  # 7 items / 2 per page = 4 pages (3 full pages and 1 partial)

    for i in range(num_vflz):
        vflz = make_vflz(session, f"My Site {i}")
        extent_geojson = {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [2638160 + i * 10, 1127775 + i * 10],
        }
        vflz.vflgeo = VflGeo()
        vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()

    mock_query = Mock()
    mock_query.return_value = 0

    monkeypatch.setattr(alma.wfs_cache, "update_cache", mock_query)

    wfs_cache.refresh_wfs(session, "gemeinde")
    assert mock_query.call_count == 4


def test_refresh_wfs_cache_pagination_with_full_pages_calls_query_correct_number_of_times(
    session, wfs_test_settings, monkeypatch
):
    settings.wfs_update_batch_size = 2
    num_vflz = 8

    for i in range(num_vflz):
        vflz = make_vflz(session, f"My Site {i}")
        extent_geojson = {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [2638160 + i * 10, 1127775 + i * 10],
        }
        vflz.vflgeo = VflGeo()
        vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()

    mock_query = Mock()
    mock_query.return_value = 0

    monkeypatch.setattr(alma.wfs_cache, "update_cache", mock_query)

    wfs_cache.refresh_wfs(session, "gemeinde")
    assert mock_query.call_count == 4
