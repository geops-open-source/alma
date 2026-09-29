import pytest
from sqlalchemy import select
from sqlalchemy.sql import functions as sql_functions
from utils import make_gemeinde, make_vflz

from alma.models import vflz as vflz_models

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


parent_vflz_geom = {
    "type": "MultiPolygon",
    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
    "coordinates": [
        [
            [
                [2600000, 1200010],
                [2600010, 1200010],
                [2600010, 1200000],
                [2600005, 1200000],
                [2600005, 1200005],
                [2600000, 1200005],
                [2600000, 1200010],
            ]
        ]
    ],
}

teilstandort_geom = {
    "type": "MultiPolygon",
    "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
    "coordinates": [
        [
            [
                [2600000, 1200000],
                [2600000, 1200005],
                [2600005, 1200005],
                [2600005, 1200000],
                [2600000, 1200000],
            ]
        ]
    ],
}


def test_create_new_teilstandort_creates_new_vflz(session):
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz = make_vflz(session, "My Site", 1, "A:001")

    highest_vflz_id = session.execute(
        select(sql_functions.max(vflz_models.Vflz.vflz_id))
    ).one()[0]
    highest_vfl_id = session.execute(
        select(sql_functions.max(vflz_models.Vflz.vfl_id))
    ).one()[0]

    assert vflz.is_current

    vflz.create_teilstandort(
        combined_id="A:001.001",
        gemeinde=gem_brig_glis,
        bezeichnung="neue Bezeichnung",
        parent_geometry=parent_vflz_geom,
        parent_zentroid=None,
        teilstandort_geometry=teilstandort_geom,
        teilstandort_zentroid=None,
    )
    assert vflz.vflz_id > highest_vflz_id
    assert vflz.vfl_id > highest_vfl_id
    assert vflz.bezeichnung == "neue Bezeichnung"
    assert vflz.is_current


def test_create_new_teilstandort_takes_values_of_vflz(session):
    vflz = make_vflz(session, "My Site", 1, "B:001")
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz.strasse = "My Strasse"
    vflz.postleitzahl = "12345"
    vflz.ort = "Freiburg"
    old_vflz_id = vflz.vflz_id
    session.commit()

    vflz.create_teilstandort(
        combined_id="A:001.001",
        gemeinde=gem_brig_glis,
        bezeichnung="foo",
        parent_geometry=parent_vflz_geom,
        parent_zentroid=None,
        teilstandort_geometry=teilstandort_geom,
        teilstandort_zentroid=None,
    )
    session.commit()
    assert old_vflz_id != vflz.vflz_id
    assert vflz.strasse == "My Strasse"
    assert vflz.postleitzahl == "12345"
    assert vflz.ort == "Freiburg"
    assert vflz.bezeichnung == "foo"


def test_parent_vflz_is_still_current(session):
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz = make_vflz(session, "My Site", 1, "A:001")

    grand_parent_vflz_id = vflz.vflz_id
    assert vflz.is_current

    vflz.create_teilstandort(
        combined_id="A:001.001",
        gemeinde=gem_brig_glis,
        bezeichnung="foo",
        parent_geometry=parent_vflz_geom,
        parent_zentroid=None,
        teilstandort_geometry=teilstandort_geom,
        teilstandort_zentroid=None,
    )

    assert vflz.is_current
    assert vflz.vflz_id != grand_parent_vflz_id
