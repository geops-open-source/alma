from datetime import datetime
from json import dumps

import pytest
import shapely
from freezegun import freeze_time
from geoalchemy2.shape import from_shape
from pytest import raises as assert_raises
from sqlalchemy import delete
from utils import (
    finish_wfs_update,
    make_flugplatz,
    make_gemeinde,
    make_parzelle,
    make_vflz,
    mock_busy_wfs_update,
)

from alma import constants
from alma.graphql.mutation import ValidationError, check_for_empty_objects
from alma.graphql.types.vflz import KompartimentStoffgruppeInput
from alma.models import cache as cache_models
from alma.models import codes as code_models
from alma.models import vflz as vflz_models


@pytest.mark.parametrize(
    ("obj", "is_empty"),
    [
        (
            KompartimentStoffgruppeInput(kksg_id=None, stoffgruppe=None, teilvol=None),
            True,
        ),
        (
            KompartimentStoffgruppeInput(kksg_id=None, stoffgruppe=None, teilvol=3.0),
            False,
        ),
    ],
)
def test_all_fields_are_unset(obj, is_empty):
    if is_empty:
        with assert_raises(ValidationError):
            check_for_empty_objects(obj)
    else:
        check_for_empty_objects(obj)


pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


@freeze_time("2012-01-14 12:00:01")
def test_validated_data_returns_cached_values_and_flugplatz(
    session, run_query, wfs_test_settings
):
    session.execute(delete(cache_models.WfsCache))

    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    parzelle_geom_ewkt = "SRID=2056;MULTIPOLYGON(((2600000 1200000, 2640000 1200000, 2640000 1120000, 2600000 1120000, 2600000 1200000)))"
    gws_zone_codeliste = session.get(
        code_models.CodeListe, constants.CodeListe.Gewaesserschutzzonen
    )
    gws_zone_ao = code_models.Code(codeliste=gws_zone_codeliste, code="Ao", sort_key=1)
    gws_bereich_codeliste = session.get(
        code_models.CodeListe, constants.CodeListe.Gewaesserschutzbereiche
    )
    gws_bereich_s2 = code_models.Code(
        codeliste=gws_bereich_codeliste, code="S2", sort_key=2
    )
    gws_bereich_s1 = code_models.Code(
        codeliste=gws_bereich_codeliste, code="S1", sort_key=1
    )
    session.add_all([gws_zone_ao, gws_bereich_s1, gws_bereich_s2])

    vflz = make_vflz(session, "My Site")
    gemeinde = make_gemeinde(session)
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    parzelle = make_parzelle(session, "1", parzelle_geom_ewkt, gemeinde)
    parzelle.egrid = "test egrid"
    session.commit()

    ort_plz_cache = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache.postleitzahl = "1234"
    ort_plz_cache.ort = "Freiburg"
    ort_plz_cache.wkb_geometry = vflz.vflgeo.wkb_geometry
    session.add(ort_plz_cache)

    gemeinde_cache = cache_models.WfsCache(wfs_service_name="gemeinde")
    gemeinde_cache.h_gem_id = gemeinde.h_gem_id
    gemeinde_cache.gemeinde_name = gemeinde.gemeinde
    gemeinde_cache.wkb_geometry = vflz.vflgeo.wkb_geometry
    session.add(gemeinde_cache)

    parzelle_cache = cache_models.WfsCache(wfs_service_name="parzelle")
    parzelle_cache.bfs_nummer = gemeinde.bfs_nummer
    parzelle_cache.h_nb_id = parzelle.h_nb_id
    assert parzelle.wkb_geometry
    parzelle_cache.wkb_geometry = parzelle.wkb_geometry
    parzelle_cache.egrid = parzelle.egrid
    parzelle_cache.gb_nummer = parzelle.gb_nummer
    session.add(parzelle_cache)

    gws_zone_cache = cache_models.WfsCache(wfs_service_name="gws_zone")
    gws_zone_cache.wkb_geometry = vflz.vflgeo.wkb_geometry
    gws_zone_cache.gws_zone = "code:10018:Ao"
    session.add(gws_zone_cache)

    gws_bereich_cache = cache_models.WfsCache(wfs_service_name="gws_bereich")
    gws_bereich_cache.wkb_geometry = vflz.vflgeo.wkb_geometry
    gws_bereich_cache.gws_bereich = "code:10017:S1"
    session.add(gws_bereich_cache)

    gws_bereich_cache_s2 = cache_models.WfsCache(wfs_service_name="gws_bereich")
    gws_bereich_cache_s2.wkb_geometry = vflz.vflgeo.wkb_geometry
    gws_bereich_cache_s2.gws_bereich = "code:10017:S2"
    session.add(gws_bereich_cache_s2)

    make_flugplatz(session, "Test", parzelle_geom_ewkt)
    finish_wfs_update(session, datetime.now(), vflz)

    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                ort
                postleitzahl
                gemeinde {
                    gemeinde
                }
                parzelle {
                    gemeinde {
                        hGemId
                    }
                    nummerierungsbereich
                    egrid
                    gbNummer
                }
                gwsBereich
                gwsZone
                flugplatz
            }
        }
    }
    """
    result = run_query(query, {"vflzId": str(vflz.vflz_id)})
    assert result.data["validateVflzData"] == {
        "ort": ["Freiburg"],
        "postleitzahl": ["1234"],
        "gemeinde": [{"gemeinde": gemeinde.gemeinde}],
        "parzelle": [
            {
                "gemeinde": {"hGemId": str(gemeinde.h_gem_id)},
                "nummerierungsbereich": None,
                "egrid": parzelle.egrid,
                "gbNummer": parzelle.gb_nummer,
            }
        ],
        "gwsBereich": ["code:10017:S1", "code:10017:S2"],
        "gwsZone": ["code:10018:Ao"],
        "flugplatz": ["code:600:Test"],
    }


@freeze_time("2012-01-14 12:00:01")
def test_return_distinct_values(session, run_query, wfs_test_settings):
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2638160, 1127775],
    }
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)
    session.commit()

    ort_plz_cache = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache.postleitzahl = "1234"
    ort_plz_cache.ort = "Freiburg"
    ort_plz_cache.wkb_geometry = vflz.vflgeo.wkb_geometry
    session.add(ort_plz_cache)

    ort_plz_cache2 = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache2.postleitzahl = "1234"
    ort_plz_cache2.ort = "Freiburg"
    ort_plz_cache2.wkb_geometry = vflz.vflgeo.wkb_geometry
    session.add(ort_plz_cache2)

    finish_wfs_update(session, datetime.now(), vflz)
    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                ort
                postleitzahl
                gemeinde {
                    hGemId
                }
            }
        }
    }
    """
    result = run_query(query, {"vflzId": str(vflz.vflz_id)})
    assert result.data["validateVflzData"] == {
        "ort": ["Freiburg"],
        "postleitzahl": ["1234"],
        "gemeinde": [],
    }


@freeze_time("2012-01-14 12:00:01")
def test_vflz_intersects_multiple_geometries(session, run_query, wfs_test_settings):
    vflz_extent_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600010, 1200000],
                    [2600010, 1200010],
                    [2600000, 1200010],
                    [2600000, 1200000],
                ]
            ]
        ],
    }

    first_cache_extent = {
        "type": "Polygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [2600005, 1200000],
                [2600010, 1200000],
                [2600010, 1200010],
                [2600005, 1200010],
                [2600005, 1200000],
            ]
        ],
    }
    second_cache_extent = {
        "type": "Polygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [2599998, 1200000],
                [2600002, 1200000],
                [2600002, 1200010],
                [2599998, 1200010],
                [2599998, 1200000],
            ]
        ],
    }
    third_cache_extent = {
        "type": "Polygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [2599985, 1200000],
                [2599995, 1200000],
                [2599995, 1200010],
                [2599985, 1200010],
                [2599985, 1200000],
            ]
        ],
    }
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(vflz_extent_geojson)
    session.commit()

    ort_plz_cache = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache.postleitzahl = "1234"
    ort_plz_cache.ort = "Freiburg"
    ort_plz_cache.wkb_geometry = from_shape(
        shapely.from_geojson(dumps(first_cache_extent)), srid=2056
    )
    session.add(ort_plz_cache)

    ort_plz_cache2 = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache2.postleitzahl = "4321"
    ort_plz_cache2.ort = "Bern"
    ort_plz_cache2.wkb_geometry = from_shape(
        shapely.from_geojson(dumps(second_cache_extent)), srid=2056
    )
    session.add(ort_plz_cache2)

    ort_plz_cache3 = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache3.postleitzahl = "7777"
    ort_plz_cache3.ort = "Basel"
    ort_plz_cache3.wkb_geometry = from_shape(
        shapely.from_geojson(dumps(third_cache_extent)), srid=2056
    )
    session.add(ort_plz_cache3)

    finish_wfs_update(session, datetime.now(), vflz)
    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                ort
                postleitzahl
                gemeinde {
                    hGemId
                }
            }
        }
    }
    """
    result = run_query(query, {"vflzId": str(vflz.vflz_id)})
    assert result.data["validateVflzData"] == {
        "ort": ["Freiburg", "Bern"],
        "postleitzahl": ["1234", "4321"],
        "gemeinde": [],
    }


@freeze_time("2012-01-14 12:00:01")
def test_vflz_intersects_ort_plz_over_1m_but_not_less_than_1m(
    session, run_query, wfs_test_settings
):
    vflz_extent_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600010, 1200000],
                    [2600010, 1200010],
                    [2600000, 1200010],
                    [2600000, 1200000],
                ]
            ]
        ],
    }

    # Overlaps the inner buffered geometry (ST_Buffer(..., -1)).
    first_cache_extent = {
        "type": "Polygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [2600008.5, 1200002],
                [2600011, 1200002],
                [2600011, 1200008],
                [2600008.5, 1200008],
                [2600008.5, 1200002],
            ]
        ],
    }

    # Touches only the outer 1m band and must not be returned.
    second_cache_extent = {
        "type": "Polygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [2600009.2, 1200002],
                [2600010.2, 1200002],
                [2600010.2, 1200008],
                [2600009.2, 1200008],
                [2600009.2, 1200002],
            ]
        ],
    }

    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(vflz_extent_geojson)
    session.commit()

    ort_plz_cache = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache.postleitzahl = "1234"
    ort_plz_cache.ort = "Freiburg"
    ort_plz_cache.wkb_geometry = from_shape(
        shapely.from_geojson(dumps(first_cache_extent)), srid=2056
    )
    session.add(ort_plz_cache)

    ort_plz_cache2 = cache_models.WfsCache(wfs_service_name="ort_plz")
    ort_plz_cache2.postleitzahl = "4321"
    ort_plz_cache2.ort = "Bern"
    ort_plz_cache2.wkb_geometry = from_shape(
        shapely.from_geojson(dumps(second_cache_extent)), srid=2056
    )
    session.add(ort_plz_cache2)

    finish_wfs_update(session, datetime.now(), vflz)
    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                ort
                postleitzahl
                gemeinde {
                    hGemId
                }
            }
        }
    }
    """
    result = run_query(query, {"vflzId": str(vflz.vflz_id)})
    assert result.data["validateVflzData"] == {
        "ort": ["Freiburg"],
        "postleitzahl": ["1234"],
        "gemeinde": [],
    }


@freeze_time("2012-01-14 12:00:01")
def test_validation_gws_returns_default_codes_for_missing_data(
    session, run_query, wfs_test_settings, as_lesen_sachdaten
):
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [10, 10],
                        [10, 11],
                        [11, 11],
                        [11, 10],
                        [10, 10],
                    ],
                ],
            ],
        }
    )
    session.commit()
    finish_wfs_update(session, datetime.now(), vflz)

    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                gwsZone
                gwsBereich
            }
        }
    }
    """
    result = run_query(
        query,
        variable_values={
            "vflzId": str(vflz.vflz_id),
        },
    )
    assert result.data["validateVflzData"] == {
        "gwsBereich": ["code:10017:keine"],
        "gwsZone": ["code:10018:keine"],
    }


@freeze_time("2012-01-14 12:00:01")
def test_gemeinde_not_duplicated_when_multiple_cache_rows_share_same_gemeinde(
    session, run_query, wfs_test_settings
):
    """Each gemeinde should appear exactly once even if multiple WfsCache rows
    reference the same h_gem_id (e.g. same gemeinde but different gws_zone)."""
    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [2600000, 1200000],
                        [2600010, 1200000],
                        [2600010, 1200010],
                        [2600000, 1200010],
                        [2600000, 1200000],
                    ]
                ]
            ],
        }
    )
    session.commit()

    gemeinde_a = make_gemeinde(session, name="Zürich", bfs_nummer=261)
    gemeinde_b = make_gemeinde(session, name="Bern", bfs_nummer=351)

    # Two cache rows for gemeinde_a (e.g. overlaps two different gws zones)
    for gws_zone in ("code:10018:Ao", "code:10018:S1"):
        cache_row = cache_models.WfsCache(wfs_service_name="gemeinde")
        cache_row.h_gem_id = gemeinde_a.h_gem_id
        cache_row.gemeinde_name = gemeinde_a.gemeinde
        cache_row.gws_zone = gws_zone
        cache_row.wkb_geometry = vflz.vflgeo.wkb_geometry
        session.add(cache_row)

    # One cache row for gemeinde_b
    cache_row_b = cache_models.WfsCache(wfs_service_name="gemeinde")
    cache_row_b.h_gem_id = gemeinde_b.h_gem_id
    cache_row_b.gemeinde_name = gemeinde_b.gemeinde
    cache_row_b.wkb_geometry = vflz.vflgeo.wkb_geometry
    session.add(cache_row_b)

    finish_wfs_update(session, datetime.now(), vflz)

    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ValidatedVflzData {
                gemeinde {
                    hGemId
                }
            }
        }
    }
    """
    result = run_query(query, {"vflzId": str(vflz.vflz_id)})
    gemeinde_ids = [g["hGemId"] for g in result.data["validateVflzData"]["gemeinde"]]
    assert len(gemeinde_ids) == 2
    assert str(gemeinde_a.h_gem_id) in gemeinde_ids
    assert str(gemeinde_b.h_gem_id) in gemeinde_ids


@freeze_time("2012-01-14 12:00:01")
def test_validation_still_busy_returns_code(
    session, run_query, wfs_test_settings, as_lesen_sachdaten
):
    vflz = make_vflz(session, "My Site")

    mock_busy_wfs_update(session, datetime.now(), vflz)

    query = """
    query q($vflzId: ID!) {
        validateVflzData(vflzId: $vflzId) {
            ... on ProblemGroup {
                problems {
                    problemCode
                }
            }
        }
    }
    """
    result = run_query(
        query,
        variable_values={
            "vflzId": str(vflz.vflz_id),
        },
    )
    assert result.data["validateVflzData"]["problems"] == [{"problemCode": "BUSY"}]
