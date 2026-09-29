import pytest
from sqlalchemy import select
from utils import make_gemeinde, make_nummerierungsbereich, make_parzelle, make_vflz

from alma.models import codes
from alma.models import vflz as vflz_models

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_get_parzellen_from_vflgeo(session, run_query):
    vflgeo_ewkt_both_parzellen = "SRID=2056;MULTIPOLYGON (((2600050 1200000, 2600050 1200100, 2600150 1200100, 2600150 1200000, 2600050 1200000)))"
    vflgeo_ewkt_first_parzelle = "SRID=2056;MULTIPOLYGON (((2600010 1200000, 2600010 1200100, 260040 1200100, 260040 1200000, 2600010 1200000)))"
    parzelle1_ewkt = "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))"
    parzelle1_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600000, 1200100],
                    [2600100, 1200100],
                    [2600100, 1200000],
                    [2600000, 1200000],
                ]
            ]
        ],
    }
    parzelle2_ewkt = "SRID=2056;MULTIPOLYGON (((2600100 1200000, 2600100 1200100, 2600200 1200100, 2600200 1200000, 2600100 1200000)))"
    parzelle2_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600100, 1200000],
                    [2600100, 1200100],
                    [2600200, 1200100],
                    [2600200, 1200000],
                    [2600100, 1200000],
                ]
            ]
        ],
    }

    vflz = make_vflz(session, "My Site")
    vflgeo = vflz_models.VflGeo()
    vflgeo.wkb_geometry = vflgeo_ewkt_both_parzellen  # type: ignore[assignment]
    session.add(vflgeo)
    vflz.vflgeo = vflgeo
    session.commit()

    parzelle1_gemeinde = make_gemeinde(
        session=session, name="New Gemeinde", bfs_nummer=4
    )
    parzelle2_gemeinde = make_gemeinde(
        session=session, name="New new gemeinde", bfs_nummer=5
    )
    parzelle1_nummerierungsbereich = make_nummerierungsbereich(
        session=session, geom_ewkt=parzelle1_ewkt, bezeichnung="my nb", h_nb_id="1"
    )

    parzelle1 = make_parzelle(session, "1", parzelle1_ewkt)
    parzelle1.gemeinde = parzelle1_gemeinde
    parzelle1.nummerierungsbereich = parzelle1_nummerierungsbereich
    parzelle1.nummerierungsbereich.bezeichnung = "my new bezeichnung"
    parzelle1.status = session.scalars(
        select(codes.StatusParzelle).where(codes.StatusParzelle.code == "1")
    ).one()
    parzelle1.gb_nummer = "4"
    parzelle1.egrid = "34"
    parzelle1.gb_nummer = "4"

    parzelle2 = make_parzelle(session, "2", parzelle2_ewkt)
    parzelle2.gemeinde = parzelle2_gemeinde
    parzelle2.status = session.scalars(
        select(codes.StatusParzelle).where(codes.StatusParzelle.code == "0")
    ).one()
    parzelle2.egrid = "egrid"
    parzelle2.gb_nummer = "5"

    query = """{
        latestVflz {
            parzellen {
                grunId
                gemeinde {
                    hGemId
                }
                nummerierungsbereich {
                    hNbId
                    bezeichnung
                    geometry
                }
                status
                egrid
                geometry
                gbNummer
            }
        }
    }
    """
    result = run_query(query)
    assert result.data["latestVflz"][0]["parzellen"] == [
        {
            "grunId": str(parzelle1.grun_id),
            "gemeinde": {"hGemId": str(parzelle1_gemeinde.h_gem_id)},
            "nummerierungsbereich": {
                "hNbId": "1",
                "bezeichnung": "my new bezeichnung",
                "geometry": parzelle1_geojson,
            },
            "egrid": "34",
            "geometry": parzelle1_geojson,
            "status": "code:26000:1",
            "gbNummer": "4",
        },
        {
            "grunId": str(parzelle2.grun_id),
            "gemeinde": {
                "hGemId": str(parzelle2_gemeinde.h_gem_id),
            },
            "nummerierungsbereich": None,
            "egrid": "egrid",
            "geometry": parzelle2_geojson,
            "status": "code:26000:0",
            "gbNummer": "5",
        },
    ]

    vflgeo.wkb_geometry = vflgeo_ewkt_first_parzelle  # type: ignore[assignment]
    result = run_query(query)
    assert result.data["latestVflz"][0]["parzellen"][0]["grunId"] == str(
        parzelle1.grun_id
    )
    assert len(result.data["latestVflz"][0]["parzellen"]) == 1


@pytest.mark.parametrize(
    "gem1_geom, gem2_geom, nb1_geom, nb2_geom, vflz_geom, results",
    [
        # All geometries intersect - should return all combinations
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            [
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
                {
                    "gemeinde": {"hGemId": "11"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb2"},
                },
                {
                    "gemeinde": {"hGemId": "11"},
                    "nummerierungsbereich": {"hNbId": "nb2"},
                },
            ],
        ),
        # VFLZ only intersects with gem1 and nb1
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            [
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
            ],
        ),
        # VFLZ intersects with both gemeinden but only nb1
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            [
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
                {
                    "gemeinde": {"hGemId": "11"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
            ],
        ),
        # VFLZ doesn't intersect with any gemeinden or nummerierungsbereiche
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600100 1200000, 2600100 1200100, 2600200 1200100, 2600200 1200000, 2600100 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600300 1200000, 2600300 1200100, 2600400 1200100, 2600400 1200000, 2600300 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600500 1200000, 2600500 1200100, 2600600 1200100, 2600600 1200000, 2600500 1200000)))",
            [],
        ),
        # VFLZ partially overlaps - intersects with gem1+nb2 and gem2+nb1
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600050 1200000, 2600050 1200100, 2600150 1200100, 2600150 1200000, 2600050 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600050 1200000, 2600050 1200100, 2600150 1200100, 2600150 1200000, 2600050 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600025 1200000, 2600025 1200100, 2600125 1200100, 2600125 1200000, 2600025 1200000)))",
            [
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
                {
                    "gemeinde": {"hGemId": "11"},
                    "nummerierungsbereich": {"hNbId": "nb1"},
                },
                {
                    "gemeinde": {"hGemId": "10"},
                    "nummerierungsbereich": {"hNbId": "nb2"},
                },
                {
                    "gemeinde": {"hGemId": "11"},
                    "nummerierungsbereich": {"hNbId": "nb2"},
                },
            ],
        ),
        # VFLZ overlaps with gem1 but with no nummerierungsbereich
        (
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600300 1200000, 2600300 1200100, 2600400 1200100, 2600400 1200000, 2600300 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600400 1200000, 2600400 1200100, 2600500 1200100, 2600500 1200000, 2600400 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            [{"gemeinde": {"hGemId": "10"}, "nummerierungsbereich": None}],
        ),
        # VFLZ overlaps with nb1 but with no gemeinde
        (
            "SRID=2056;MULTIPOLYGON (((2600200 1200000, 2600200 1200100, 2600300 1200100, 2600300 1200000, 2600200 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600300 1200000, 2600300 1200100, 2600400 1200100, 2600400 1200000, 2600300 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600400 1200000, 2600400 1200100, 2600500 1200100, 2600500 1200000, 2600400 1200000)))",
            "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))",
            [{"gemeinde": None, "nummerierungsbereich": {"hNbId": "nb1"}}],
        ),
    ],
)
def test_get_gemeinden_und_nummerierungsbereich(
    session, run_query, gem1_geom, gem2_geom, nb1_geom, nb2_geom, vflz_geom, results
):
    gemeinde1 = make_gemeinde(session, "Gemeinde 1", bfs_nummer=10)
    gemeinde1.wkb_geometry = gem1_geom

    gemeinde2 = make_gemeinde(session, "Gemeinde 2", bfs_nummer=11)
    gemeinde2.wkb_geometry = gem2_geom

    nummerierungsbereich1 = make_nummerierungsbereich(
        session, bezeichnung="NB 1", h_nb_id="nb1"
    )
    nummerierungsbereich1.wkb_geometry = nb1_geom

    nummerierungsbereich2 = make_nummerierungsbereich(
        session, bezeichnung="NB 2", h_nb_id="nb2"
    )
    nummerierungsbereich2.wkb_geometry = nb2_geom

    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.wkb_geometry = vflz_geom
    session.commit()

    query = """{
        latestVflz {
            gemeindenUndNummerierungsbereiche {
                gemeinde {
                    hGemId
                }
                nummerierungsbereich {
                    hNbId
                }
            }
        }
    }
    """

    response = run_query(query)
    assert (
        response.data["latestVflz"][0]["gemeindenUndNummerierungsbereiche"] == results
    )
