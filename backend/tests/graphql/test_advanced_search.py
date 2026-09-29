import pytest
from utils import (
    make_betrieb,
    make_gemeinde,
    make_pool,
    make_translation,
    make_vflz,
    make_vflz_beurteilung,
)

from alma import constants
from alma.constants import Language
from alma.models.vflz import EvaluationStatusData

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


@pytest.mark.parametrize(
    ("search", "fields", "search_result"),
    [
        (
            'Firma-Name/Schiessanlage-Name ~ "foo"',
            ["FIRMA_NAME"],
            [
                (
                    1,
                    "foo",
                    EvaluationStatusData().to_dict(),
                )
            ],
        ),
        (
            'Firma-Name/Schiessanlage-Name ~ "foo" AND Standorttyp = "Betriebsstandort"',
            ["FIRMA_NAME", "STANDORTTYP"],
            [
                (
                    1,
                    "foo",
                    "code:63:02",
                    EvaluationStatusData().to_dict(),
                )
            ],
        ),
        (
            'Firma-Name/Schiessanlage-Name ~ "foo" AND Standorttyp = "Ablagerungsstandort"',
            ["FIRMA_NAME", "STANDORTTYP"],
            [],
        ),
        (
            'Standorttyp != "Ablagerungsstandort"',
            ["FIRMA_NAME", "STANDORTTYP"],
            [
                (
                    1,
                    "foo",
                    "code:63:02",
                    EvaluationStatusData().to_dict(),
                )
            ],
        ),
    ],
)
def test_advanced_search(session, run_query, search, fields, search_result):
    vflz = make_vflz(session, "My Vflz Site", 1, "34asfadsf")
    vflz.publizieren = False
    vflz.gemeinde = make_gemeinde(session, bfs_nummer=99)
    vflz.gemeinde.gemeinde = "Freiburg"
    vflz.beurteilung = make_vflz_beurteilung(session, vflz)
    betrieb = make_betrieb(session, vflz)
    betrieb.firma_name = "foo"
    betrieb.firma_strasse = "bar"
    make_translation(
        session,
        Language.DE,
        f"code:{constants.CodeListe.StandortTyp}:{constants.StandortTyp.ABLAGERUNG}",
        "Ablagerungsstandort",
    )
    make_translation(
        session,
        Language.DE,
        f"code:{constants.CodeListe.StandortTyp}:{constants.StandortTyp.BETRIEB}",
        "Betriebsstandort",
    )
    session.commit()

    query = """
    query q($search: String!, $fields: [SearchField!]!) {
        search(query: $search, advanced: true, fields: $fields) {
            tabular { results }
        }
    }
    """

    variables = {"search": search, "fields": fields}

    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] == search_result


def test_add_search_results_to_pool(session, run_query, as_bearbeiten_sachdaten):
    pool = make_pool(session, "My pool")
    vflz_vfl1 = make_vflz(session, "My fist site", 1)
    vflz_vfl2 = make_vflz(session, "My second site", 2)

    pool.add_vfl(2)

    mutation = """
    mutation m($data: AddSearchResultsToPoolInput!) {
        addSearchResultsToPool(data: $data) {
            poolId
            standorte {
                results {
                    vflzId
                }
            }
        }
    }
    """

    result = run_query(
        mutation, {"data": {"poolId": str(pool.pool_id), "query": 'Bezeichnung ~ "My"'}}
    )
    assert result.data["addSearchResultsToPool"] == {
        "poolId": str(pool.pool_id),
        "standorte": {
            "results": [
                {"vflzId": str(vflz_vfl1.vflz_id)},
                {"vflzId": str(vflz_vfl2.vflz_id)},
            ]
        },
    }
