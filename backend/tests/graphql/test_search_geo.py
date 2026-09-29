import pytest
from sqlalchemy.orm import Session
from utils import make_vflz

from alma.models.vflz import VflGeo

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_can_retrieve_vflz_zentroid_as_geojson(session: Session, run_query):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.set_zentroid({"type": "Point", "coordinates": [0, 0, 0]})

    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz2.set_zentroid({"type": "Point", "coordinates": [1000, 1000, 1000]})

    session.commit()

    query = """
        {
            search(query: "") {
                geo(extent: null) { zentroid } }
        }
    """

    response = run_query(query, {})
    result = response.data["search"]["geo"]

    assert result["zentroid"] == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [0, 0, 0],
                },
                "properties": {
                    "vflzId": vflz1.vflz_id,
                    "color": None,
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [1000, 1000, 1000],
                },
                "properties": {
                    "vflzId": vflz2.vflz_id,
                    "color": None,
                },
            },
        ],
    }


def test_can_filter_vflz_zentroid_by_extent(session: Session, run_query):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.set_zentroid({"type": "Point", "coordinates": [0, 0, 0]})

    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz2.set_zentroid({"type": "Point", "coordinates": [1000, 1000, 1000]})

    session.commit()

    query = """
        {
            search(query: "") {
                geo(extent: [-10, -10, 10, 10]) { zentroid } }
        }
    """

    response = run_query(query, {})
    result = response.data["search"]["geo"]

    assert result["zentroid"] == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [0, 0, 0],
                },
                "properties": {
                    "vflzId": vflz1.vflz_id,
                    "color": None,
                },
            },
        ],
    }


def test_can_retrieve_vflz_vflgeom_as_geojson(session: Session, run_query):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.set_zentroid({"type": "Point", "coordinates": [0, 0, 0]})
    vflz1.vflgeo = VflGeo()
    vflz1.vflgeo.set_geometry({"type": "Point", "coordinates": [0, 1000]})

    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz2.set_zentroid({"type": "Point", "coordinates": [1000, 1000, 1000]})
    vflz2.vflgeo = VflGeo()
    vflz2.vflgeo.set_geometry({"type": "Point", "coordinates": [1000, 0]})

    session.commit()

    query = """
        {
            search(query: "") {
                geo(extent: null) { vflgeo } }
        }
    """

    response = run_query(query, {})
    result = response.data["search"]["geo"]

    assert result["vflgeo"] == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [0, 1000],
                },
                "properties": {
                    "vflzId": vflz1.vflz_id,
                    "color": None,
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [1000, 0],
                },
                "properties": {
                    "vflzId": vflz2.vflz_id,
                    "color": None,
                },
            },
        ],
    }


def test_can_filter_vflz_vflgeom_by_extent(session: Session, run_query):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.set_zentroid({"type": "Point", "coordinates": [0, 0, 0]})
    vflz1.vflgeo = VflGeo()
    vflz1.vflgeo.set_geometry({"type": "Point", "coordinates": [0, 0]})

    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz2.set_zentroid({"type": "Point", "coordinates": [1000, 1000, 1000]})
    vflz2.vflgeo = VflGeo()
    vflz2.vflgeo.set_geometry({"type": "Point", "coordinates": [1000, 1000]})

    session.commit()

    query = """
        {
            search(query: "") {
                geo(extent: [-10, -10, 10, 10]) { vflgeo } }
        }
    """

    response = run_query(query, {})
    result = response.data["search"]["geo"]

    assert result["vflgeo"] == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                    "coordinates": [0, 0],
                },
                "properties": {
                    "vflzId": vflz1.vflz_id,
                    "color": None,
                },
            },
        ],
    }


def test_empty_feature_collection_is_not_null(session: Session, run_query):
    query = """
        {
            search(query: "") {
                geo { vflgeo zentroid } }
        }
    """

    response = run_query(query, {})
    result = response.data["search"]["geo"]

    assert result["vflgeo"] == {"type": "FeatureCollection", "features": []}
    assert result["zentroid"] == {"type": "FeatureCollection", "features": []}
