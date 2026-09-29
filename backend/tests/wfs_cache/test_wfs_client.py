from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon

from alma.settings import FieldMapping, WfsSettings
from alma.tools.wfs import WfsClient


@pytest.fixture
def wfs_client():
    wfs_settings = WfsSettings(
        url="http://example.invalid/wfs",
        layers=["ms:test_layer"],
        field_mappings=[FieldMapping(wfs="name", cache_table="gemeinde_name")],
    )
    with patch("alma.tools.wfs.WebFeatureService"):
        return WfsClient(wfs_config=wfs_settings, name="test")


def _fake_collection(features):
    coll = MagicMock()
    coll.crs.to_epsg.return_value = 2056
    coll.__iter__.return_value = iter(features)
    coll.__enter__.return_value = coll
    coll.__exit__.return_value = False
    return coll


def _make_feature(geometry_type, coordinates, name="Test"):
    return SimpleNamespace(
        geometry=SimpleNamespace(type=geometry_type, coordinates=coordinates),
        properties={"name": name},
    )


def test_parse_response_preserves_polygon_holes(wfs_client):
    exterior = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    hole = [(2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0), (2.0, 2.0)]
    feature = _make_feature("Polygon", [exterior, hole])

    with patch("alma.tools.wfs.fiona.open", return_value=_fake_collection([feature])):
        rows = wfs_client._parse_response(BytesIO(b""), ["ms:test_layer"])

    assert len(rows) == 1
    srid_prefix, geom_wkt = rows[0]["wkb_geometry"].split(";", 1)
    assert srid_prefix == "SRID=2056"

    geom = wkt.loads(geom_wkt)
    assert isinstance(geom, Polygon)
    assert len(geom.interiors) == 1


def test_parse_response_preserves_multipolygon_holes(wfs_client):
    poly1 = [
        [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
        [(2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0), (2.0, 2.0)],
    ]
    poly2 = [
        [(20.0, 0.0), (30.0, 0.0), (30.0, 10.0), (20.0, 10.0), (20.0, 0.0)],
    ]
    feature = _make_feature("MultiPolygon", [poly1, poly2])

    with patch("alma.tools.wfs.fiona.open", return_value=_fake_collection([feature])):
        rows = wfs_client._parse_response(BytesIO(b""), ["ms:test_layer"])

    geom = wkt.loads(rows[0]["wkb_geometry"].split(";", 1)[1])
    assert isinstance(geom, MultiPolygon)
    parts = list(geom.geoms)
    assert len(parts) == 2
    holes_per_part = sorted(len(p.interiors) for p in parts)
    assert holes_per_part == [0, 1]
