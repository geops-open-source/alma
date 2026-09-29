from unittest.mock import patch

import pytest
from pydantic import HttpUrl
from sqlalchemy import select
from utils import QueryError, make_flugplatz, make_gemeinde, make_ktu, make_vflz

from alma.models import vflz as vflz_models
from alma.settings import settings

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


def test_new_teilstandort_is_returned_from_teilstandort_query(session, run_query):
    original_vflz_geom = {
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

    teilstandort_geometry = {
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
    gem_bern = make_gemeinde(session, "Bern", 1)
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    make_flugplatz(session)

    vflz = make_vflz(session, "My Site", 1, "B:001")
    make_ktu(session)

    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on Vflz {
                teilstandorte {
                    vflgeo {
                        geometry
                    }
                    gemeinde {
                        gemeinde
                    }
                    bezeichnung
                    flugplatz
                    ktu
                }
                vflgeo {
                    geometry
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": teilstandort_geometry,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": "code:600:Test",
                "ktu": "code:210:bls",
            }
        },
    )

    assert result.data["createTeilstandort"]["teilstandorte"] == [
        {
            "vflgeo": {"geometry": teilstandort_geometry},
            "gemeinde": {"gemeinde": "Brig Glis"},
            "bezeichnung": "Teilstandort von A:001",
            "flugplatz": "code:600:Test",
            "ktu": "code:210:bls",
        },
        {
            "vflgeo": {
                "geometry": original_vflz_geom,
            },
            "gemeinde": {"gemeinde": "Bern"},
            "bezeichnung": "My Site",
            "flugplatz": None,
            "ktu": None,
        },
    ]
    assert (
        result.data["createTeilstandort"]["vflgeo"]["geometry"] == teilstandort_geometry
    )


def test_ignore_whitespaces_for_combined_id_exists_check(session, run_query):
    original_vflz_geom = {
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

    teilstandort_geometry = {
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
    gem_bern = make_gemeinde(session, "Bern", 1)
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz = make_vflz(session, "My Site", 1, "B:001")
    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on Vflz {
                teilstandorte {
                    vflgeo {
                        geometry
                    }
                    gemeinde {
                        gemeinde
                    }
                    bezeichnung
                }
                vflgeo {
                    geometry
                }
            }
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": teilstandort_geometry,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                "combinedId": " B:001 ",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    assert result.data["createTeilstandort"]["problems"] == [
        {"problemCode": "EXISTS", "field": "combinedId"}
    ]


def test_parent_standort_is_historized(session, run_query):
    original_vflz_geom = {
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

    teilstandort_geometry = {
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
    gem_bern = make_gemeinde(session, "Bern", 1)
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz = make_vflz(session, "My Site", 1, "B:001")
    old_vflz_id = vflz.vflz_id
    vfl_id = vflz.vfl_id
    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on Vflz {
                teilstandorte {
                    vflzId
                }
            }
        }
    }
    """

    run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": teilstandort_geometry,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    parent_vflz = session.scalars(
        select(vflz_models.Vflz).where(
            vflz_models.Vflz.is_current, vflz_models.Vflz.vfl_id == vfl_id
        )
    ).one()
    assert parent_vflz.vflz_id > old_vflz_id
    assert parent_vflz.message == "vflz.historization.teilflaecheSeparated"


def test_error_occurs_does_not_change_anything(session, run_query):
    with patch("alma.models.vflz.Vflz.set_geometry") as fun:
        fun.side_effect = ValueError("foo")

        original_vflz_geom = {
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

        teilstandort_geometry = {
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
        gem_bern = make_gemeinde(session, "Bern", 1)
        gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
        vflz = make_vflz(session, "My Site", 1, "B:001")
        old_vflz_id = vflz.vflz_id
        vfl_id = vflz.vfl_id
        vflz.gemeinde = gem_bern
        vflz.vflgeo = vflz_models.VflGeo()
        vflz.vflgeo.set_geometry(original_vflz_geom)

        session.commit()
        mutation = """
        mutation m($data: CreateTeilstandortInput!) {
            createTeilstandort(data: $data) {
                ... on Vflz {
                    teilstandorte {
                        vflzId
                        vflgeo {
                            geometry
                        }
                    }
                    vflzId
                }
            }
        }
        """

        with pytest.raises(QueryError):
            result = run_query(
                mutation,
                {
                    "data": {
                        "parentGeometry": original_vflz_geom,
                        "parentZentroid": None,
                        "geometry": teilstandort_geometry,
                        "zentroid": None,
                        "parentVflzId": str(vflz.vflz_id),
                        "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                        "combinedId": "A:001.001",
                        "bezeichnung": "Teilstandort von A:001",
                        "flugplatz": None,
                        "ktu": None,
                    }
                },
            )

            assert result.data["createTeilstandort"]["teilstandorte"] == [
                {
                    "vflzId": str(vflz.vflz_id),
                    "vflgeo": {"geometry": original_vflz_geom},
                }
            ]

            assert result.data["createTeilstandort"]["vflzId"] == str(vflz.vflz_id)

            parent_vflz = session.scalars(
                select(vflz_models.Vflz).where(
                    vflz_models.Vflz.is_current, vflz_models.Vflz.vfl_id == vfl_id
                )
            ).one()
            assert parent_vflz.vflz_id == old_vflz_id
            assert parent_vflz.message != "Teilfläche abgetrennt"


def test_height_zentroid_and_area_are_recalculated(
    session, run_query, test_settings, httpx2_mock
):
    settings.height_api = HttpUrl("https://api3.geo.admin.ch/rest/services/height")
    httpx2_mock.add_response(
        url=f"{settings.height_api}?easting=2600005&northing=1200003",
        json={"height": 553},
    )
    httpx2_mock.add_response(
        url=f"{settings.height_api}?easting=2600005&northing=1200005",
        json={"height": 553},
    )
    original_vflz_geom = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600000, 1200010],
                    [2600010, 1200010],
                    [2600010, 1200000],
                    [2600000, 1200000],
                ]
            ]
        ],
    }

    teilstandort_geometry = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600000, 1200006],
                    [2600010, 1200006],
                    [2600010, 1200000],
                    [2600000, 1200000],
                ]
            ]
        ],
    }

    expected_teilstandort_zentroid = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2600005, 1200003, 553],
    }
    gem_bern = make_gemeinde(session, "Bern", 1)
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)
    vflz = make_vflz(session, "My Site", 1, "A:001")
    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on Vflz {
                vflgeo {
                    geometry
                }
                zentroid
                flaeche
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": teilstandort_geometry,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    assert result.data["createTeilstandort"] == {
        "vflgeo": {
            "geometry": teilstandort_geometry,
        },
        "zentroid": expected_teilstandort_zentroid,
        "flaeche": 60,
    }
    settings.height_api = None


@pytest.mark.parametrize(
    "input_data, gemeinde, combined_id_created",
    [
        (
            {"parentCombinedId": "bla", "combinedId": None, "gemeinde": None},
            [{"hGemId": "6002"}, {"hGemId": "6003"}],
            False,
        ),
        (
            {
                "parentCombinedId": "bla",
                "combinedId": None,
                "gemeinde": {"hGemId": "6002"},
            },
            [{"hGemId": "6002"}],
            True,
        ),
        (
            {
                "parentCombinedId": "bla",
                "combinedId": None,
                "gemeinde": {"hGemId": "6005"},
            },
            [{"hGemId": "6002"}, {"hGemId": "6003"}],
            False,
        ),
    ],
)
def test_create_validation(
    session, run_query, input_data, gemeinde, combined_id_created
):
    flugplatz_ewkt = "SRID=2056;MULTIPOLYGON(((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765)))"

    gem = make_gemeinde(session, name="Brig-Glis", bfs_nummer=6002)
    gem.wkb_geometry = "SRID=2056;POLYGON((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765))"  # type: ignore[assignment]
    gem2 = make_gemeinde(session, name="Basel", bfs_nummer=6003)
    gem2.wkb_geometry = "SRID=2056;POLYGON((2638170 1127765,2638170 1127785,2638190 1127785,2638190 1127765,2638170 1127765))"  # type: ignore[assignment]

    flugplatz = make_flugplatz(session)
    flugplatz.wkb_geometry = flugplatz_ewkt  # type: ignore[assignment]

    session.commit()
    query = """
    query q($data: ValidateCreateTeilstandortInput!) {
        validateCreateTeilstandort(data: $data) {
            ... on ValidatedCreateVflzData {
                combinedId
                gemeinde {
                    hGemId
                }
                flugplatz
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [2638160, 1127765],
                        [2638160, 1127785],
                        [2638180, 1127785],
                        [2638180, 1127765],
                        [2638160, 1127765],
                    ]
                ],
            },
            **input_data,
        }
    }

    result = run_query(query=query, variable_values=variables)

    assert result.data["validateCreateTeilstandort"]["gemeinde"] == gemeinde
    assert (
        result.data["validateCreateTeilstandort"]["combinedId"] != []
    ) == combined_id_created
    assert result.data["validateCreateTeilstandort"]["flugplatz"] == ["code:600:Test"]


def test_create_teilstandort_validation_returns_new_number_if_combinedId_exists(
    session, run_query
):
    make_vflz(
        session, bezeichnung="My Site", vfl_id=1, combined_id="THIS IS ALREADY TAKEN.01"
    )
    make_vflz(
        session, bezeichnung="My Site 2", vfl_id=2, combined_id="THIS IS ALREADY TAKEN"
    )
    gem = make_gemeinde(session, name="Brig-Glis", bfs_nummer=6002)
    gem.wkb_geometry = "SRID=2056;POLYGON((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765))"  # type: ignore[assignment]
    session.commit()
    query = """
    query q($data: ValidateCreateTeilstandortInput!) {
        validateCreateTeilstandort(data: $data) {
            ... on ValidatedCreateVflzData {
                combinedId
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": {
                "type": "Point",
                "coordinates": [2638150, 1127765],
            },
            "parentCombinedId": "THIS IS ALREADY TAKEN",
            "combinedId": "THIS IS ALREADY TAKEN.01",
            "gemeinde": {"hGemId": "6002"},
        }
    }

    result = run_query(query=query, variable_values=variables)
    assert result.data["validateCreateTeilstandort"]["combinedId"] == [
        "THIS IS ALREADY TAKEN.02"
    ]


def test_cannot_create_teilstandort_with_invalid_geometry(session, run_query):
    original_vflz_geom = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [0, 0],
                    [1, 1],
                    [0, 2],
                    [-1, 1],
                    [0, 0],
                ]
            ]
        ],
    }

    invalid_geom = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [[[[0, 0], [1, 1], [1, 2], [1, 1], [0, 0]]]],
    }
    gem_bern = make_gemeinde(session, "Bern", 1)
    vflz = make_vflz(session, "My Site", 1, "B:001")
    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": invalid_geom,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_bern.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    assert result.data["createTeilstandort"]["problems"] == [
        {"problemCode": "VALIDATION_GEOM", "field": "geometry"}
    ]

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": invalid_geom,
                "parentZentroid": None,
                "geometry": original_vflz_geom,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_bern.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    assert result.data["createTeilstandort"]["problems"] == [
        {"problemCode": "VALIDATION_GEOM", "field": "parentGeometry"}
    ]
