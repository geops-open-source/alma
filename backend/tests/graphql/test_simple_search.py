import pytest
from utils import (
    make_ablagerung,
    make_beteiligter,
    make_betrieb,
    make_einzelereignis,
    make_gemeinde,
    make_kinderspielplatz_gruenflaeche,
    make_massnahme,
    make_note_node,
    make_pfas,
    make_sanierungsziel,
    make_sonstiger_beteiligte_standort,
    make_subj,
    make_umweltschaden,
    make_unfall,
    make_vflz,
    make_vflz_beurteilung,
)

from alma.models import bem as bem_models
from alma.models.vflz import EvaluationStatusData

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_can_get_search_fields(session, run_query):
    query = "{ searchFields { field name type } }"
    result = run_query(query)
    search_fields = result.data["searchFields"]

    assert {
        "field": "VFLZ_ID",
        "name": "vflz_id",
        "type": "NUMBER",
    } in search_fields
    assert {
        "field": "FIRMA_NAME",
        "name": "firma_name",
        "type": "TEXT",
    } in search_fields


@pytest.mark.parametrize(
    "filters, fields, search_result",
    [
        (
            [{"field": "FIRMA_NAME", "value": "foo"}],
            ["FIRMA_NAME"],
            (1, "foo", EvaluationStatusData().to_dict()),
        ),
        (
            [{"field": "FIRMA_NAME", "value": "foo"}],
            ["FIRMA_NAME", "STANDORTTYP"],
            (1, "foo", "code:63:02", EvaluationStatusData().to_dict()),
        ),
        (
            [{"field": "FIRMA_NAME", "value": "foo"}],
            [
                "STANDORTNUMMER",
                "STANDORTTYP",
                "GEMEINDE",
                "BEURTEILUNG",
                "FIRMA_NAME",
                "FIRMA_STRASSE",
            ],
            (
                1,
                "34asfadsf",
                "code:63:02",
                "Freiburg",
                "code:103:test",
                "foo",
                "bar",
                EvaluationStatusData().to_dict(),
            ),
        ),
    ],
)
def test_fields_and_items(session, run_query, filters, fields, search_result):
    vflz = make_vflz(session, "My Vflz Site", 1, "34asfadsf")
    vflz.publizieren = False
    vflz.gemeinde = make_gemeinde(session, bfs_nummer=99)
    vflz.gemeinde.gemeinde = "Freiburg"
    vflz.beurteilung = make_vflz_beurteilung(session, vflz)
    betrieb = make_betrieb(session, vflz)
    betrieb.firma_name = "foo"
    betrieb.firma_strasse = "bar"
    session.commit()

    query = """
    query q($filters: [SearchFilter!]!, $fields: [SearchField!]!) {
        search(query: "", filters: $filters, fields: $fields) {
            tabular { results }
        }
    }
    """

    variables = {"filters": filters, "fields": fields}

    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] == [search_result]


@pytest.mark.parametrize(
    "sort_by, expected_result",
    [
        (
            [],
            [
                (1, "y standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (2, "z standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (3, "z standortnummer", "c foo", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            [{"field": "STANDORTNUMMER"}],
            [
                (1, "y standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (2, "z standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (3, "z standortnummer", "c foo", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            [{"field": "STANDORTNUMMER", "reverse": True}],
            [
                (1, "z standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (2, "z standortnummer", "c foo", EvaluationStatusData().to_dict()),
                (3, "y standortnummer", "b foo", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            [{"field": "FIRMA_NAME"}],
            [
                (1, "y standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (2, "z standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (3, "z standortnummer", "c foo", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            [{"field": "FIRMA_NAME"}, {"field": "STANDORTNUMMER"}],
            [
                (1, "y standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (2, "z standortnummer", "b foo", EvaluationStatusData().to_dict()),
                (3, "z standortnummer", "c foo", EvaluationStatusData().to_dict()),
            ],
        ),
    ],
)
def test_sorting_of_search_results(session, run_query, sort_by, expected_result):
    vflz1 = make_vflz(session, "My Vflz Site", 1, "z standortnummer")
    vflz2 = make_vflz(session, "My Vflz site 2", 2, "y standortnummer")
    betrieb = make_betrieb(session, vflz1)
    betrieb2 = make_betrieb(session, vflz1)
    betrieb3 = make_betrieb(session, vflz2)

    betrieb.firma_name = "b foo"
    betrieb2.firma_name = "c foo"
    betrieb3.firma_name = "b foo"

    session.commit()

    query = """
    query q($query: String!, $fields: [SearchField!]!, $sortBy: [SortItemInput!]) {
        search(query: $query, filters: [], fields: $fields, sortBy: $sortBy) {
            tabular { results }
        }
    }
    """
    variables = {
        "query": "Vflz",
        "filters": [],
        "fields": ["STANDORTNUMMER", "FIRMA_NAME"],
        "sortBy": sort_by,
    }
    response = run_query(query, variables)
    result = response.data["search"]["tabular"]["results"]

    assert result == expected_result


def test_pagination(session, run_query):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    make_betrieb(session, vflz1, firma_name="Firma 1")
    make_betrieb(session, vflz1, firma_name="Firma 2")
    make_betrieb(session, vflz2, firma_name="Firma 3")

    query = """
    query q($query: String!, $fields: [SearchField!]!, $sortBy: [SortItemInput!], $page: Int!, $perPage: Int!) {
        search(query: $query, filters: [], fields: $fields, sortBy: $sortBy, page: $page, perPage: $perPage) {
            tabular {
                numPages
                numResultsTotal
                results
            }
        }
    }
    """

    variables = {
        "query": "Standort",
        "fields": ["VFLZ_ID", "FIRMA_NAME"],
        "sortBy": [{"field": "VFLZ_ID"}, {"field": "FIRMA_NAME"}],
    }

    response = run_query(query, variables | {"page": 1, "perPage": 2})
    result = response.data["search"]["tabular"]
    assert result["results"] == [
        (1, vflz1.vflz_id, "Firma 1", EvaluationStatusData().to_dict()),
        (2, vflz1.vflz_id, "Firma 2", EvaluationStatusData().to_dict()),
    ]
    assert result["numPages"] == 2
    assert result["numResultsTotal"] == 3

    response = run_query(query, variables | {"page": 2, "perPage": 2})
    result = response.data["search"]["tabular"]
    assert result["results"] == [
        (3, vflz2.vflz_id, "Firma 3", EvaluationStatusData().to_dict()),
    ]
    assert result["numPages"] == 2
    assert result["numResultsTotal"] == 3


def test_standortnummer_match_sets_flag_in_response(session, run_query):
    make_vflz(session, "My TEST Site", 1, "TEST-001")

    session.commit()

    query = """
    query q($query: String!, $fields: [SearchField!]!) {
        search(query: $query, fields: $fields, filters: []) {
            directMatch
            tabular { results }
        }
    }
    """
    response = run_query(query, {"fields": ["STANDORTNUMMER"], "query": "TEST"})
    result = response.data["search"]

    assert result["directMatch"] is False
    assert result["tabular"]["results"] == [
        (1, "TEST-001", EvaluationStatusData().to_dict())
    ]

    response = run_query(query, {"fields": ["STANDORTNUMMER"], "query": "TEST-001"})
    result = response.data["search"]

    assert result["directMatch"] is True
    assert result["tabular"]["results"] == [
        (1, "TEST-001", EvaluationStatusData().to_dict())
    ]


def test_bezeichnung_match_sets_flag_in_response(session, run_query):
    make_vflz(session, "My TEST Site", 1, "TEST-001")

    session.commit()

    query = """
    query q($query: String!, $fields: [SearchField!]!) {
        search(query: $query, fields: $fields, filters: []) {
            directMatch
            tabular { results }
        }
    }
    """
    response = run_query(query, {"fields": ["BEZEICHNUNG"], "query": "TEST"})
    result = response.data["search"]

    assert result["directMatch"] is False
    assert result["tabular"]["results"] == [
        (1, "My TEST Site", EvaluationStatusData().to_dict())
    ]

    response = run_query(query, {"fields": ["BEZEICHNUNG"], "query": "My TEST Site"})
    result = response.data["search"]

    assert result["directMatch"] is True
    assert result["tabular"]["results"] == [
        (1, "My TEST Site", EvaluationStatusData().to_dict())
    ]


def test_empty_search_string_matches_all_results(session, run_query):
    make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    query = """
    query q($query: String!, $fields: [SearchField!]!) {
        search(query: $query, fields: $fields, filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query, {"fields": ["BEZEICHNUNG"], "query": ""})

    assert response.data["search"]["tabular"]["results"] == [
        (1, "Standort A", EvaluationStatusData().to_dict()),
        (2, "Standort B", EvaluationStatusData().to_dict()),
    ]


def test_search_by_firma_name(session, run_query):
    vflz = make_vflz(session, "My Site", vfl_id=1)
    make_betrieb(session, vflz, "Betrieb")

    query = """
    {
        search(query: "Betrieb", fields: [FIRMA_NAME], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "Betrieb", EvaluationStatusData().to_dict())
    ]


def test_search_by_beteiligte(session, run_query):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session, name="Froehlich", vorname="Frieda")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_sonstiger_beteiligte_standort(session, bet.bet_id)

    query = """
    {
        search(query: "Froehlich", fields: [VORNAME], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "Frieda", EvaluationStatusData().to_dict())
    ]


def test_search_by_notiz(session, run_query, as_lesen_geschaefte):
    vflz = make_vflz(session, "My Site")
    note_node = make_note_node(session, vflz, "Mein Titel")
    note_node.note = "Notiz"

    query = """
    {
        search(query: "Notiz", fields: [TASK_TITEL], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "Mein Titel", EvaluationStatusData().to_dict())
    ]


def test_search_by_unfall_name(session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    unfall.name = "unfall"

    query = """
    {
        search(query: "unfall", fields: [UNFALL_NAME], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "unfall", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_standort(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz.bemerkung_standort = bem_models.BemerkungStandort(bem="standort")

    query = """
    {
        search(query: "standort", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_umwelt(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz.bemerkung_umwelt = bem_models.BemerkungUmwelt(bem="umwelt")

    query = """
    {
        search(query: "umwelt", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_begruendung_bewertung(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz.begruendung_bewertung = bem_models.BegruendungBewertung(bem="bewertung")

    query = """
    {
        search(query: "bewertung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_begruendung_prio_untersuchung(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz.begruendung_prio_untersuchungsbedarf = (
        bem_models.BegruendungPrioUntersuchungsbedarf(bem="untersuchung")
    )

    query = """
    {
        search(query: "untersuchung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_begruendung_prio_sanierung(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz.begruendung_prio_sanierungsbedarf = bem_models.BegruendungPrioSanierungsbedarf(
        bem="sanierung"
    )

    query = """
    {
        search(query: "sanierung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_betrieb(session, run_query):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)
    betrieb.bemerkung = bem_models.BemerkungBetrieb(bem="bemerkung")

    query = """
    {
        search(query: "bemerkung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_ablagerung(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    ablagerung.bemerkung = bem_models.BemerkungAblagerung(bem="ablagerung")

    query = """
    {
        search(query: "ablagerung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_unfall(session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    unfall.bemerkung = bem_models.BemerkungUnfall(bem="unfall")

    query = """
    {
        search(query: "unfall", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_massnahme(session, run_query):
    vflz = make_vflz(session, "My Site")
    massnahme = make_massnahme(session, vflz)
    massnahme.bemerkung = bem_models.BemerkungMassnahme(bem="massnahme")

    query = """
    {
        search(query: "massnahme", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_sanierung(session, run_query):
    vflz = make_vflz(session, "My Site")
    sanierung = make_sanierungsziel(session, vflz)
    sanierung.bemerkung = bem_models.BemerkungSanierung(bem="sanierung")

    query = """
    {
        search(query: "sanierung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_umweltschaden(session, run_query):
    vflz = make_vflz(session, "My Site")
    umweltschaden = make_umweltschaden(session, vflz)
    umweltschaden.bemerkung = bem_models.BemerkungUmweltschaden(bem="umweltschaden")

    query = """
    {
        search(query: "umweltschaden", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_einzelereignis(session, run_query):
    vflz = make_vflz(session, "My Site")
    einzelereignis = make_einzelereignis(session, vflz)
    einzelereignis.bemerkung = bem_models.BemerkungEinzelereignis(bem="einzelereignis")

    query = """
    {
        search(query: "einzelereignis", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_begruendung_bew_betrieb(session, run_query):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)
    betrieb.begruendung_bewertung = bem_models.BegruendungBewertungBetrieb(
        bem="bew_betrieb"
    )

    query = """
    {
        search(query: "bew_betrieb", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bemerkung_subjekt(session, run_query):
    vflz = make_vflz(session, "My Site")
    subjekt = make_subj(session)
    bet = make_beteiligter(session, vflz.vflz_id, subjekt.subj_id)
    make_sonstiger_beteiligte_standort(session, bet.bet_id)
    subjekt.bemerkung = bem_models.BemerkungSubjekt(bem="subjekt")

    query = """
    {
        search(query: "subjekt", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_pfas_name(session, run_query):
    vflz = make_vflz(session, "My Site")
    pfas = make_pfas(session, vflz)
    pfas.name = "pfas_name"
    vflz.pfas = [pfas]

    query = """
    {
        search(query: "pfas_name", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_pfas_bemerkung(session, run_query):
    vflz = make_vflz(session, "My Site")
    pfas = make_pfas(session, vflz)
    pfas.bemerkung = bem_models.BemerkungPFAS(bem="pfas_bemerkung")
    vflz.pfas = [pfas]

    query = """
    {
        search(query: "pfas_bemerkung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_kinderspielplatz_name(session, run_query):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.name = "geops-name"
    query = """
    {
        search(query: "geops-name", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_kinderspielplatz_bemerkung(session, run_query):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.bemerkung = bem_models.BemerkungKinderspielplatzGruenflaeche(
        bem="geops-bemerkung"
    )
    query = """
    {
        search(query: "geops-bemerkung", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_pfas_beschreibungen_detail(session, run_query):
    vflz = make_vflz(session, "My Site")
    intp = make_pfas(session, vflz)
    intp.beschreibungen_detail = "detail"
    query = """
    {
        search(query: "detail", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_begruendung_bew_pfas(session, run_query):
    vflz = make_vflz(session, "My Site")
    intp = make_pfas(session, vflz)
    intp.begruendung_bewertung = bem_models.BegruendungBewertungPFAS(bem="bew_pfas")
    query = """
    {
        search(query: "bew_pfas", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_standortnummer_inplace(session, run_query):
    make_vflz(session, "My Site", 1, "Standortnummer")
    query = """
    {
        search(query: "num", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]


def test_search_by_bezeichnung_inplace(session, run_query):
    make_vflz(session, "My Site")
    query = """
    {
        search(query: "Si", fields: [BEZEICHNUNG], filters: []) {
            tabular { results }
        }
    }
    """
    response = run_query(query)
    assert response.data["search"]["tabular"]["results"] == [
        (1, "My Site", EvaluationStatusData().to_dict())
    ]
