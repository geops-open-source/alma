from datetime import date

import pytest
from utils import make_code, make_kbsinfo, make_vflz, prefill_optional_fields

from alma.graphql.types.vflz import BeurteilungInput, UpdateVflzEvaluationInput
from alma.models.codes import Beurteilung
from alma.models.vflz import Vflz

# Fixture required by all tests in this module
pytestmark = pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten")


def test_publication_status_is_intially_unset(session):
    vflz = make_vflz(session, "Mein Standort")
    vflz.dat_publizieren = None
    assert vflz.status_publikation is None


def test_publication_status_tracks_evaluation(session, run_query):
    vflz = make_vflz(session, "Mein Standort")
    belastet = make_code(session, Beurteilung, "B")
    unbelastet = make_code(session, Beurteilung, "U")
    make_kbsinfo(session, belastet, belastet=True, color="#ff0000")
    make_kbsinfo(session, unbelastet, belastet=False, color="#00ff00")
    pub_date_1 = date(2024, 1, 1)

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
      updateVflzEvaluation(data: $data) {
        ... on Vflz { vflzId }
      }
    }
    """
    variables = {
        "data": prefill_optional_fields(
            UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": prefill_optional_fields(
                    BeurteilungInput, {"beurteilung": str(belastet)}
                ),
                "datPublizieren": str(pub_date_1),
                "publizieren": True,
                "rechtskraft": True,
            },
        ),
    }
    run_query(mutation, variables)
    old_vflz_id = vflz.vflz_id
    vflz.historize("Did something")
    assert session.get_one(Vflz, old_vflz_id).dat_publizieren == pub_date_1
    assert vflz.status_publikation
    assert vflz.status_publikation.dat_publizieren == pub_date_1
    assert vflz.status_publikation.belastet is True

    pub_date_2 = date(2024, 2, 2)

    variables = {
        "data": prefill_optional_fields(
            UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": prefill_optional_fields(
                    BeurteilungInput, {"beurteilung": str(unbelastet)}
                ),
                "datPublizieren": str(pub_date_2),
                "publizieren": True,
                "rechtskraft": True,
            },
        ),
    }
    run_query(mutation, variables)

    assert vflz.status_publikation.dat_publizieren == pub_date_2
    assert vflz.status_publikation.belastet is False


def test_publication_status_is_not_reset_by_historization(session, run_query):
    belastet = make_code(session, Beurteilung, "B")
    unbelastet = make_code(session, Beurteilung, "U")
    make_kbsinfo(session, belastet, belastet=True, color="#ff0000")
    make_kbsinfo(session, unbelastet, belastet=False, color="#00ff00")

    vflz = make_vflz(session, "Mein Standort")
    vflz.historize("Historisierung initiale Version")
    session.commit()

    pub_date_1 = date(2024, 1, 1)
    pub_date_2 = date(2024, 2, 2)

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
      updateVflzEvaluation(data: $data) {
        ... on Vflz {
            vflzId
            datPublizieren
            statusPublikation { datPublizieren belastet }
        }
        ... on ProblemGroup {
            problems {
                message
            }
        }
      }
    }
    """
    variables = {
        "data": prefill_optional_fields(
            UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": prefill_optional_fields(
                    BeurteilungInput, {"beurteilung": str(belastet)}
                ),
                "datPublizieren": str(pub_date_1),
                "publizieren": True,
                "rechtskraft": True,
            },
        ),
    }
    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"] == {
        "vflzId": str(vflz.vflz_id),
        "datPublizieren": "2024-01-01",
        "statusPublikation": {"datPublizieren": str(pub_date_1), "belastet": True},
    }

    vflz.historize("Historisierung publizierte Version (belastet)")
    session.commit()

    assert vflz.status_publikation
    assert vflz.status_publikation.dat_publizieren == pub_date_1
    assert vflz.status_publikation.belastet is True

    variables = {
        "data": prefill_optional_fields(
            UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": prefill_optional_fields(
                    BeurteilungInput, {"beurteilung": str(unbelastet)}
                ),
                "datPublizieren": str(pub_date_2),
                "publizieren": True,
                "rechtskraft": True,
            },
        ),
    }
    run_query(mutation, variables)
    assert vflz.status_publikation.dat_publizieren == pub_date_2
    assert vflz.status_publikation.belastet is False

    vflz.historize("Historisierung publizierte Version (unbelastet)")
    session.commit()

    assert vflz.status_publikation.dat_publizieren == pub_date_2
    assert vflz.status_publikation.belastet is False
