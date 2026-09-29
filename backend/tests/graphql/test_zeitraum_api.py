import pytest
from utils import (
    make_ablagerung,
    make_betrieb,
    make_unfall,
    make_vflz,
    prefill_optional_fields,
)

from alma.graphql.types import vflz as vflz_types

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


def test_bisheute_has_highest_prio(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung2 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    bisheute
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2032-01-01",
                                "vonjahr": True,
                                "bisjahr": True,
                                "bisheute": False,
                            },
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung2.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": True,
                                "bisjahr": True,
                                "bisheute": True,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"]["bisheute"]


def test_vonjahr_overrides_date(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung2 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    von
                    vonjahr
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2032-01-01",
                                "vonjahr": False,
                                "bisjahr": True,
                                "bisheute": True,
                            },
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung2.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": True,
                                "bisjahr": True,
                                "bisheute": True,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "2019-01-01",
        "vonjahr": False,
    }


def test_bisjahr_overrides_date(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung2 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    bis
                    bisjahr
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2032-01-01",
                                "vonjahr": True,
                                "bisjahr": True,
                                "bisheute": False,
                            },
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung2.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": True,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "bis": "2032-01-01",
        "bisjahr": True,
    }


def test_date_override(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung2 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    bis
                    von
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung2.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2032-04-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "2019-01-01",
        "bis": "2032-04-01",
    }


def test_von_date_override_bisheute_override(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung2 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    von
                    bisheute
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung2.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2032-04-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": True,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "2019-01-01",
        "bisheute": True,
    }


def test_one_betrieb_one_ablagerung(session, run_query):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)
    ablagerung = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    von
                    bisheute
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "betriebe": [
                    prefill_optional_fields(
                        vflz_types.BetriebInput,
                        {
                            "intbId": str(betrieb.intb_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": False,
                                "genauigkeitVon": "code:90:test",
                                "genauigkeitBis": "code:90:test",
                            },
                        },
                    )
                ],
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "zeitraum": {
                                "von": "2020-01-01",
                                "bis": "2032-04-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": True,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "2019-01-01",
        "bisheute": True,
    }


def test_ablagerung_initialized_with_kksk_values(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    ablagerung.zeitraum_von = None
    ablagerung.zeitraum_bis = None
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                prefill_optional_fields(
                                    vflz_types.KompartimentStoffklasseInput,
                                    {
                                        "kkskId": None,
                                        "zeitraum": {
                                            "von": "2000-03-04",
                                            "bis": "3000-03-04",
                                            "vonjahr": True,
                                            "bisjahr": False,
                                            "bisheute": False,
                                            "genauigkeitVon": "code:90:test",
                                            "genauigkeitBis": "code:90:test",
                                        },
                                    },
                                )
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["ablagerungen"][0]["zeitraum"] == {  # noqa: E501
        "von": "2000-03-04",
        "bis": "3000-03-04",
        "vonjahr": True,
        "bisjahr": False,
        "bisheute": False,
    }


def test_ablagerung_initialized_only_for_empty_values(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    ablagerung.zeitraum_bis = None
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                prefill_optional_fields(
                                    vflz_types.KompartimentStoffklasseInput,
                                    {
                                        "kkskId": None,
                                        "zeitraum": {
                                            "von": "2000-03-04",
                                            "bis": "3000-03-04",
                                            "vonjahr": True,
                                            "bisjahr": False,
                                            "bisheute": False,
                                            "genauigkeitVon": "code:90:test",
                                            "genauigkeitBis": "code:90:test",
                                        },
                                    },
                                )
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["ablagerungen"][0]["zeitraum"] == {  # noqa: E501
        "von": "2021-01-01",
        "bis": "3000-03-04",
        "vonjahr": True,
        "bisjahr": False,
        "bisheute": False,
    }


def test_one_ablagerung_one_unfall(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    unfall = make_unfall(session, vflz)
    unfall.zeitpunkt_jahr = True

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                zeitraum {
                    von
                    vonjahr
                    bis
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "zeitraum": {
                                "von": "2000-03-04",
                                "bis": "3000-03-04",
                                "vonjahr": True,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    )
                ],
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "zeitpunkt": "1999-03-02",
                            "zeitpunktjahr": False,
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "1999-03-02",
        "vonjahr": False,
        "bis": "3000-03-04",
    }


def test_do_not_take_vflz_dates_into_account(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung1 = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                zeitraum {
                    von
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung1.inta_id),
                            "zeitraum": {
                                "von": "2019-01-01",
                                "bis": "2030-01-01",
                                "vonjahr": False,
                                "bisjahr": False,
                                "bisheute": False,
                            },
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {
        "von": "2019-01-01",
    }

    variables["data"]["ablagerungen"][0]["zeitraum"]["von"] = "2020-01-01"

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["zeitraum"] == {"von": "2020-01-01"}
