import pytest
from pytest import raises as assert_raises
from sqlalchemy.orm import Session
from utils import (
    QueryError,
    make_beteiligter,
    make_eigentuemer_standort,
    make_parzelle,
    make_sachbearbeiter_standort,
    make_sonstiger_beteiligte_standort,
    make_subj,
    make_vflz,
)

# Fixture required by all tests in this module
pytestmark = pytest.mark.usefixtures("generate_codes")


def test_historization_requires_edit_permission(
    session: Session, run_query, as_lesen_sachdaten
):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: HistorizeVflzInput!) {
        historizeVflz(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    with assert_raises(QueryError, match="not allowed"):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    "message": "My message",
                }
            },
        )


def test_historization_returns_new_current_version(
    session: Session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site", vfl_id=1)
    original_vflz_id = vflz.vflz_id

    mutation = """
    mutation m($data: HistorizeVflzInput!) {
        historizeVflz(data: $data) {
            ... on Vflz {
                vflId
                vflzId
                isCurrent
                message
                versionen {
                    vflId
                    vflzId
                    isCurrent
                    message
                }
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": {"vflzId": str(vflz.vflz_id), "message": "My message"}
        },
    )
    new_vflz_id = int(result.data["historizeVflz"]["vflzId"])
    assert new_vflz_id > original_vflz_id

    assert result.data == {
        "historizeVflz": {
            "vflId": "1",
            "vflzId": str(new_vflz_id),
            "isCurrent": True,
            "message": "My message",
            "versionen": [
                {
                    "vflId": "1",
                    "vflzId": str(new_vflz_id),
                    "isCurrent": True,
                    "message": "My message",
                },
                {
                    "vflId": "1",
                    "vflzId": str(original_vflz_id),
                    "isCurrent": False,
                    "message": "Initial version",
                },
            ],
        }
    }


def test_historization_keeps_beteiligte_in_graphql_response(
    session: Session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site", vfl_id=1)
    sachbearbeitung_subj = make_subj(session, "Sachbearbeitung")
    sonstige_subj = make_subj(session, "Sonstige")
    eigentuemer_subj = make_subj(session, "Eigentuemer")
    parzelle = make_parzelle(session, "1000")

    sachbearbeitung = make_beteiligter(
        session,
        vflz.vflz_id,
        sachbearbeitung_subj.subj_id,
        is_sachbearbeiter=True,
    )
    sonstige_beteiligte = make_beteiligter(
        session,
        vflz.vflz_id,
        sonstige_subj.subj_id,
    )
    eigentuemer = make_beteiligter(
        session,
        vflz.vflz_id,
        eigentuemer_subj.subj_id,
        is_eigentuemer=True,
    )

    make_sonstiger_beteiligte_standort(
        session, bet_id=sonstige_beteiligte.bet_id, bez_art_code="test"
    )
    make_sachbearbeiter_standort(
        session, bet_id=sachbearbeitung.bet_id, bez_art_code="sachbearbeitung"
    )
    make_eigentuemer_standort(
        session, bet_id=eigentuemer.bet_id, grun_id=parzelle.grun_id
    )

    mutation = """
    mutation m($data: HistorizeVflzInput!) {
        historizeVflz(data: $data) {
            ... on Vflz {
                vflzId
                isCurrent
                sachbearbeitung {
                    beteiligter {
                        subjekt { name }
                    }
                }
                sonstigeBeteiligte {
                    beteiligter {
                        subjekt { name }
                    }
                }
                eigentum {
                    status
                    subjekt { name }
                    parzellen
                }
                versionen {
                    vflzId
                    isCurrent
                    sachbearbeitung {
                        beteiligter {
                            subjekt { name }
                        }
                    }
                    sonstigeBeteiligte {
                        beteiligter {
                            subjekt { name }
                        }
                    }
                    eigentum {
                        status
                        subjekt { name }
                        parzellen
                    }
                }
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": {"vflzId": str(vflz.vflz_id), "message": "My message"}
        },
    )

    historized = result.data["historizeVflz"]

    assert historized["isCurrent"] is True
    assert historized["sachbearbeitung"] == [
        {"beteiligter": {"subjekt": {"name": "Sachbearbeitung"}}}
    ]
    assert historized["sonstigeBeteiligte"] == [
        {"beteiligter": {"subjekt": {"name": "Sonstige"}}}
    ]
    assert historized["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "Eigentuemer"},
            "parzellen": ["1000"],
        }
    ]

    assert historized["versionen"][0]["vflzId"] == historized["vflzId"]
    assert historized["versionen"][0]["isCurrent"] is True
    assert historized["versionen"][1]["isCurrent"] is False
    assert historized["versionen"][0]["sachbearbeitung"] == [
        {"beteiligter": {"subjekt": {"name": "Sachbearbeitung"}}}
    ]
    assert historized["versionen"][0]["sonstigeBeteiligte"] == [
        {"beteiligter": {"subjekt": {"name": "Sonstige"}}}
    ]
    assert historized["versionen"][0]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "Eigentuemer"},
            "parzellen": ["1000"],
        }
    ]
