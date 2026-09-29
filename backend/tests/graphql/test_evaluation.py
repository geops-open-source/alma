from datetime import datetime

import pytest
from freezegun import freeze_time
from sqlalchemy import select
from utils import (
    make_code,
    make_massnahme,
    make_sanierungsziel,
    make_vflz,
    prefill_optional_fields,
)

from alma.graphql.types.vflz import UpdateVflzEvaluationInput
from alma.models import codes as code_models
from alma.models import vflz as vflz_models

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


@pytest.mark.parametrize(
    "vflz_beurteilung,input_beurteilung,historized",
    [
        ("code:103:beurt1", "code:103:beurt2", True),
        ("code:103:beurt1", "code:103:beurt1", False),
        (None, "code:103:beurt1", True),
        (None, None, False),
        ("code:103:beurt1", None, True),
    ],
)
def test_beurteilung_change_triggers_historization(
    vflz_beurteilung, input_beurteilung, historized, session, run_query
):
    vflz = make_vflz(session, "My Site")
    beurteilung1_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung2_code = make_code(session, code_models.Beurteilung, "beurt2")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    if vflz_beurteilung:
        vflz.beurteilung = vflz_models.Beurteilung(
            beurteilung=code_models.Beurteilung.from_db(session, vflz_beurteilung)
        )
    vflz.dat_rechtskraft = None
    vflz.rechtskraft = False
    vflz.dat_publizieren = None
    vflz.publizieren = False

    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=beurteilung1_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=beurteilung2_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """
    old_vflz_id = int(vflz.vflz_id)

    result = run_query(
        mutation,
        variable_values={
            "data": prefill_optional_fields(
                UpdateVflzEvaluationInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "beurteilung": {
                        "beurteilung": str(
                            code_models.Beurteilung.from_db(session, input_beurteilung)
                        ),
                        "prioUntersuch": None,
                        "prioSanier": None,
                    }
                    if input_beurteilung
                    else None,
                    "rechtskraft": False,
                    "publizieren": False,
                },
            )
        },
    )

    if historized:
        assert int(result.data["updateVflzEvaluation"]["vflzId"]) > old_vflz_id
    else:
        assert int(result.data["updateVflzEvaluation"]["vflzId"]) == old_vflz_id


def test_no_beurteilung_change_does_not_trigger_historization(session, run_query):
    beurteilung1_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz = make_vflz(session, "My Site")
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=beurteilung1_code)
    vflz.dat_rechtskraft = None
    vflz.rechtskraft = False
    vflz.dat_publizieren = None
    vflz.publizieren = False
    kbs_info = code_models.KbsInfo(
        beurteilung=beurteilung1_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    session.add(kbs_info)
    session.commit()
    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """
    old_vflz_id = int(vflz.vflz_id)

    result = run_query(
        mutation,
        variable_values={
            "data": prefill_optional_fields(
                UpdateVflzEvaluationInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "beurteilung": {
                        "beurteilung": str(beurteilung1_code),
                        "prioUntersuch": None,
                        "prioSanier": None,
                    },
                    "publizieren": False,
                    "rechtskraft": False,
                },
            )
        },
    )
    assert int(result.data["updateVflzEvaluation"]["vflzId"]) == old_vflz_id


@freeze_time("2020-01-01")
def test_fields_are_updated_after_historization(session, run_query):
    vflz = make_vflz(session, "My Site")
    mass = make_massnahme(session, vflz)
    sani = make_sanierungsziel(session, vflz)
    beurteilung1_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung2_code = make_code(session, code_models.Beurteilung, "beurt2")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=beurteilung1_code)
    vflz.dat_rechtskraft = None
    vflz.rechtskraft = False
    vflz.dat_publizieren = None
    vflz.publizieren = False

    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=beurteilung1_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=False,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=beurteilung2_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#00ff00",
        color_rgb=None,
        belastet=True,
    )
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """
    old_vflz_id = int(vflz.vflz_id)

    result = run_query(
        mutation,
        variable_values={
            "data": prefill_optional_fields(
                UpdateVflzEvaluationInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "beurteilung": {
                        "beurteilung": str(beurteilung2_code),
                        "prioUntersuch": None,
                        "prioSanier": None,
                    },
                    "massnahmen": [
                        {
                            "massId": str(mass.mass_id),
                            "massnahme": "code:10021:test2",
                            "datMassnahme": None,
                            "angMassnahme": None,
                            "bemerkung": {"bem": "Bemerkung Massnahme"},
                        }
                    ],
                    "sanierungsziele": [
                        {
                            "saniId": str(sani.sani_id),
                            "sanierungsziel": "code:10020:test2",
                            "bemerkung": {"bem": "Bemerkung Sanierungsziel"},
                        }
                    ],
                    "rechtskraft": True,
                    "publizieren": True,
                },
            )
        },
    )
    new_vflz_id = int(result.data["updateVflzEvaluation"]["vflzId"])
    assert new_vflz_id > old_vflz_id

    # prehistorized values are unchanged
    old_vflz = session.get_one(vflz_models.Vflz, old_vflz_id)

    assert old_vflz.dat_rechtskraft is None
    assert not old_vflz.rechtskraft
    assert old_vflz.dat_publizieren is None
    assert not old_vflz.publizieren
    assert old_vflz.beurteilung.beurteilung == beurteilung1_code
    assert len(old_vflz.massnahmen) == 1
    assert len(old_vflz.sanierungsziele) == 1
    assert str(old_vflz.massnahmen[0].massnahme) == "code:10021:test"
    assert str(old_vflz.sanierungsziele[0].sanierungsziel) == "code:10020:test"

    new_vflz = session.get_one(vflz_models.Vflz, new_vflz_id)
    assert new_vflz.dat_rechtskraft == datetime.now().date()
    assert new_vflz.rechtskraft
    assert new_vflz.dat_publizieren == datetime.now().date()
    assert new_vflz.publizieren
    assert new_vflz.beurteilung.beurteilung == beurteilung2_code
    assert len(new_vflz.massnahmen) == 1
    assert len(new_vflz.sanierungsziele) == 1
    assert str(new_vflz.massnahmen[0].massnahme) == "code:10021:test2"
    assert str(new_vflz.sanierungsziele[0].sanierungsziel) == "code:10020:test2"


@pytest.mark.parametrize(
    "rechtskraft, belastet, publizieren_allowed",
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
    ],
)
def test_publizieren_only_allowed_if_belastet_and_rechtskraft(
    rechtskraft, belastet, publizieren_allowed, session, run_query
):
    vflz = make_vflz(session, "My Site")
    vflz.rechtskraft = False
    vflz.dat_rechtskraft = None
    vflz.beurteilung = None
    vflz.dat_publizieren = None
    vflz.publizieren = False

    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()

    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    unbelastet_code = make_code(session, code_models.Beurteilung, "beurt2")
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=unbelastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()
    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                publizieren
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
                "beurteilung": {
                    "beurteilung": str(belastet_code)
                    if belastet
                    else str(unbelastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "rechtskraft": rechtskraft,
                "publizieren": True,
            },
        )
    }
    old_vflz_id = vflz.vflz_id
    result = run_query(mutation, variables)

    if publizieren_allowed:
        assert result.data["updateVflzEvaluation"]["publizieren"]
        assert not session.get_one(vflz_models.Vflz, old_vflz_id).publizieren
    else:
        assert (
            result.data["updateVflzEvaluation"]["problems"]
            == [
                {
                    "message": "Rechtskraft darf nur bei belasteten Standorten gesetzt sein."
                }
            ]
        ) or (
            result.data["updateVflzEvaluation"]["problems"]
            == [{"message": "Rechtskraft muss bei Publikation gesetzt sein."}]
        )


@pytest.mark.parametrize(
    "previously_published, unbelastet, delete_allowed",
    [
        (True, True, True),
        (True, False, True),
        (False, True, False),
    ],
)
def test_deleting_from_kbs_only_allowed_if_previously_published_and_belastet(
    previously_published, unbelastet, delete_allowed, session, run_query
):
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    unbelastet_code = make_code(session, code_models.Beurteilung, "beurt2")
    belastet_code_gruppe = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=belastet_code_gruppe,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=unbelastet_code,
        beurteilung_gruppe=belastet_code_gruppe,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )

    vflz = make_vflz(session, "My Site")
    vflz.rechtskraft = True
    vflz.dat_rechtskraft = datetime.now().date()
    vflz.publizieren = previously_published
    vflz.dat_publizieren = datetime.now().date() if previously_published else None
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=belastet_code)
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                publizieren
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
                "beurteilung": {
                    "beurteilung": str(
                        unbelastet_code if unbelastet else belastet_code
                    ),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "rechtskraft": True,
                "publizieren": True,
            },
        )
    }

    old_vflz_id = vflz.vflz_id
    result = run_query(mutation, variables)

    if delete_allowed:
        assert result.data["updateVflzEvaluation"]["publizieren"]
        assert session.get_one(vflz_models.Vflz, old_vflz_id).publizieren
    else:
        assert result.data["updateVflzEvaluation"]["problems"] == [
            {"message": "Kein publizierter Eintrag im KbS."}
        ]


def test_setting_rechtskraft_only_allowed_for_belastete_standorte(session, run_query):
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    unbelastet_code = make_code(session, code_models.Beurteilung, "beurt2")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=unbelastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()

    vflz = make_vflz(session, "My Site")
    vflz.rechtskraft = False
    vflz.dat_rechtskraft = None
    vflz.publizieren = False
    vflz.dat_publizieren = None

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                rechtskraft
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
                "beurteilung": {
                    "beurteilung": str(unbelastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "rechtskraft": True,
                "publizieren": False,
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"]["problems"] == [
        {"message": "Rechtskraft darf nur bei belasteten Standorten gesetzt sein."}
    ]

    variables["data"]["beurteilung"]["beurteilung"] = str(belastet_code)
    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"]["rechtskraft"]


def test_deleting_twice_is_not_allowed(session, run_query):
    vflz = make_vflz(session, "My Site")
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    unbelastet_code = make_code(session, code_models.Beurteilung, "beurt2")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz.dat_rechtskraft = datetime.now().date()
    vflz.rechtskraft = True
    vflz.dat_publizieren = datetime.now().date()
    vflz.publizieren = True
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=belastet_code)
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    unbelastet_kbs_info = code_models.KbsInfo(
        beurteilung=unbelastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )
    session.add(belastet_kbs_info)
    session.add(unbelastet_kbs_info)
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                vflzId
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
                "beurteilung": {
                    "beurteilung": str(unbelastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "vflzId": str(vflz.vflz_id),
                "datPublizieren": datetime.now().date().isoformat(),
                "datRechtskraft": None,
                "rechtskraft": True,
                "publizieren": True,
            },
        )
    }
    result = run_query(mutation, variables)
    assert "problems" not in result.data["updateVflzEvaluation"]
    new_vflz_id = result.data["updateVflzEvaluation"]["vflzId"]

    variables["data"]["vflzId"] = new_vflz_id
    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"]["problems"] == [
        {"message": "Kein publizierter Eintrag im KbS."}
    ]


@freeze_time("2020-03-03")
def test_dat_rechtskraft_automatically_set_to_today(session, run_query):
    vflz = make_vflz(session, "My Site")
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz.dat_rechtskraft = None
    vflz.rechtskraft = False
    vflz.dat_publizieren = None
    vflz.publizieren = False
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=belastet_code)
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    session.add(belastet_kbs_info)
    session.commit()
    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                datRechtskraft
                rechtskraft
                datPublizieren
                publizieren
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
                "beurteilung": {
                    "beurteilung": str(belastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "rechtskraft": True,
                "publizieren": True,
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"] == {
        "datRechtskraft": "2020-03-03",
        "rechtskraft": True,
        "datPublizieren": "2020-03-03",
        "publizieren": True,
    }


@freeze_time("2021-03-03")
def test_dat_publizieren_automatically_set_to_today(session, run_query):
    vflz = make_vflz(session, "My Site")
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz.dat_publizieren = None
    vflz.publizieren = False
    vflz.dat_rechtskraft = None
    vflz.rechtskraft = False
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=belastet_code)
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    session.add(belastet_kbs_info)
    session.commit()
    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                datRechtskraft
                rechtskraft
                datPublizieren
                publizieren
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
                "beurteilung": {
                    "beurteilung": str(belastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "datRechtskraft": "2020-03-03",
                "rechtskraft": True,
                "publizieren": True,
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"] == {
        "datRechtskraft": "2020-03-03",
        "rechtskraft": True,
        "datPublizieren": "2021-03-03",
        "publizieren": True,
    }


def test_setting_rechtskraft_to_false_if_already_set_is_not_allowed(session, run_query):
    vflz = make_vflz(session, "My Site")
    belastet_code = make_code(session, code_models.Beurteilung, "beurt1")
    beurteilung_gruppe_code = session.scalars(
        select(code_models.BeurteilungGruppe).where(
            code_models.BeurteilungGruppe.code == "Test"
        )
    ).one()
    vflz.dat_publizieren = None
    vflz.publizieren = False
    vflz.dat_rechtskraft = datetime.now().date()
    vflz.rechtskraft = True
    vflz.beurteilung = vflz_models.Beurteilung(beurteilung=belastet_code)
    belastet_kbs_info = code_models.KbsInfo(
        beurteilung=belastet_code,
        beurteilung_gruppe=beurteilung_gruppe_code,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    session.add(belastet_kbs_info)
    session.commit()
    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                datRechtskraft
                rechtskraft
                datPublizieren
                publizieren
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
                "beurteilung": {
                    "beurteilung": str(belastet_code),
                    "prioUntersuch": None,
                    "prioSanier": None,
                },
                "datPublizieren": None,
                "datRechtskraft": None,
                "rechtskraft": False,
                "publizieren": False,
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"]["problems"] == [
        {
            "message": "Rechtskraft ist bereits gesetzt und darf nicht mehr geändert werden."
        }
    ]
