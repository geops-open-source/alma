import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import QueryError, make_translation

from alma import constants
from alma.models.codes import Code, CodeListe
from alma.models.translations import Translation


def make_codeliste_and_codes(
    session: Session, cli_id: int, *values: str
) -> tuple[CodeListe, list[Code], Translation]:
    codeliste = CodeListe(cli_id)
    codelist_bezeichnung = make_translation(
        session, constants.Language.DE, f"codelist:{cli_id}", f"Code list {cli_id}"
    )

    codes = []
    for v in values:
        code = Code(codeliste=codeliste, code=v)
        codes.append(code)

    session.add(codeliste)
    session.add_all(codes)
    session.commit()
    return codeliste, codes, codelist_bezeichnung


def test_can_get_codes_by_cli_id(session, run_query):
    _, codes, _ = make_codeliste_and_codes(
        session, constants.CodeListe.Genauigkeit, "A", "B", "C", "D"
    )
    a, b, c, _ = codes
    a.is_active = False
    a.sort_key = 2
    b.sort_key = 99
    c.sort_key = 1
    session.commit()

    query = """
    query q($cliIds: [ID!]!) {
        codeLists(cliIds: $cliIds) { results { entries { code isActive sortKey} } }
    }
    """

    result = run_query(
        query, variable_values={"cliIds": [constants.CodeListe.Genauigkeit]}
    )

    # Codes are sorted by sort_key
    assert result.data["codeLists"]["results"] == [
        {
            "entries": [
                {"code": "code:90:C", "isActive": True, "sortKey": 1},
                {"code": "code:90:B", "isActive": True, "sortKey": 99},
                {"code": "code:90:D", "isActive": True, "sortKey": None},
                {"code": "code:90:A", "isActive": False, "sortKey": 2},
            ]
        }
    ]


def test_can_get_codes_by_cli_id_multiple(session, run_query):
    make_codeliste_and_codes(session, constants.CodeListe.StoffeKlasseI, "A1", "B1")
    _, codes, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseII, "A2", "B2"
    )

    a2, b2 = codes
    a2.sort_key = 99
    b2.sort_key = 1
    session.commit()

    query = """
    query q($cliIds: [ID!]!) {
        codeLists(cliIds: $cliIds) { results { cliId entries { code } } }
    }
    """

    result = run_query(
        query,
        variable_values={
            "cliIds": [
                constants.CodeListe.StoffeKlasseI,
                constants.CodeListe.StoffeKlasseII,
            ]
        },
    )

    # Codes are sorted by code list, then by sort_key
    assert result.data["codeLists"]["results"] == [
        {
            "cliId": "111",
            "entries": [
                {"code": "code:111:A1"},
                {"code": "code:111:B1"},
            ],
        },
        {
            "cliId": "112",
            "entries": [
                {"code": "code:112:B2"},
                {"code": "code:112:A2"},
            ],
        },
    ]


def test_can_get_mapping_codelisten(session, run_query):
    query = "{ mappingCodelisten }"
    result = run_query(query)
    mapping = result.data["mappingCodelisten"]

    # Field w/ single code list
    assert mapping["Vflz"]["vftyp"] == [constants.CodeListe.StandortTyp]
    assert mapping["Gemeinde"]["kanton"] == [constants.CodeListe.Kanton]
    assert mapping["KompartimentStoffklasse"]["stoffklasse"] == [
        constants.CodeListe.Stoffklasse
    ]

    # Field w/ multiple code lists
    assert mapping["KompartimentStoffgruppe"]["stoffgruppe"] == [
        constants.CodeListe.Stoffgruppen,
        constants.CodeListe.StoffeKlasseI,
        constants.CodeListe.StoffeKlasseII,
        constants.CodeListe.StoffeKlasseIII,
        constants.CodeListe.StoffeKlasseIV,
    ]

    # Field w/ code liste depending on another field
    assert mapping["NutzungBoden"]["nutzungsart"] == [
        constants.CodeListe.Flaechennutzung
    ]
    assert mapping["NutzungBoden"]["aktuelleNutzung"] == [
        "nutzungsart",
        {
            "code:87:01": constants.CodeListe.FlaechennutzungWald,
            "code:87:02": constants.CodeListe.FlaechennutzungLandwirtschaft,
            "code:87:03": constants.CodeListe.FlaechennutzungUngenutz,
            "code:87:04": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:05": None,
            "code:87:06": None,
            "code:87:07": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:08": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:09": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:10": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:11": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:12": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:13": constants.CodeListe.FlaechennutzungSiedlungsgebiet,
            "code:87:14": constants.CodeListe.FlaechennutzungLandwirtschaft,
        },
    ]
    assert mapping["UmweltStoff"]["stoffGruppe"] == [
        constants.CodeListe.UmweltStoffgruppe
    ]
    assert mapping["UmweltStoff"]["stoff"] == [
        "stoffGruppe",
        {
            "code:300:01": constants.CodeListe.StoffgruppeCKW,
            "code:300:02": constants.CodeListe.StoffgruppeSchwermetalle,
            "code:300:03": constants.CodeListe.StoffgruppeMKW,
            "code:300:04": constants.CodeListe.StoffgruppeBTEX,
            "code:300:05": constants.CodeListe.StoffgruppePAK,
            "code:300:06": constants.CodeListe.StoffgruppeDioxine,
            "code:300:07": constants.CodeListe.StoffgruppePCB,
            "code:300:08": constants.CodeListe.StoffgruppePFAS,
            "code:300:09": constants.CodeListe.StoffgruppeBenzinartige,
            "code:300:10": constants.CodeListe.StoffgruppeNichtmetalle,
            "code:300:11": constants.CodeListe.StoffgruppeHalogenierteKW,
            "code:300:12": constants.CodeListe.StoffgruppeFreone,
            "code:300:13": constants.CodeListe.StoffgruppeSonstige,
            "code:300:14": constants.CodeListe.StoffgruppePhenole,
        },
    ]
    assert mapping["Umweltschaden"]["schaeden"] == [
        "artSchaden",
        {
            "code:101:01": None,
            "code:101:02": constants.CodeListe.UmweltschaedenWasser,
            "code:101:03": constants.CodeListe.UmweltschaedenWasser,
            "code:101:04": constants.CodeListe.UmweltschaedenLuft,
            "code:101:05": constants.CodeListe.UmweltschaedenBoden,
            "code:101:06": None,
        },
    ]

    # Objects that exist only at the GraphQL level
    assert mapping["ZeitraumMitGenauigkeit"]["genauigkeitVon"] == [
        constants.CodeListe.Genauigkeit
    ]
    assert mapping["ZeitraumMitGenauigkeit"]["genauigkeitBis"] == [
        constants.CodeListe.Genauigkeit
    ]
    assert mapping["Beurteilung"]["rechtlicherBezug"] == [
        constants.CodeListe.RechtlicherBezug
    ]
    assert mapping["Beurteilung"]["handlungsbedarf"] == [
        constants.CodeListe.Handlungsbedarf
    ]

    # Beteiligte
    assert mapping["BeteiligterStandort"]["beziehungsart"] == [
        constants.CodeListe.BeziehungsartSonstige
    ]
    assert mapping["EigentuemerStandort"]["beziehungsart"] == [
        constants.CodeListe.BeziehungsartEigentum
    ]
    assert mapping["SachbearbeiterStandort"]["beziehungsart"] == [
        constants.CodeListe.BeziehungsartSachbearbeitung
    ]


@pytest.mark.parametrize(
    "filter_value, results",
    [
        (
            "My",
            [
                {"bezeichnung": {"de": "My First Code"}},
                {"bezeichnung": {"de": "My Second Code"}},
            ],
        ),
        ("First", [{"bezeichnung": {"de": "My First Code"}}]),
        ("Foo", []),
    ],
)
def test_filtering_codelists_by_bezeichnung(filter_value, results, session, run_query):
    _, _, sk1_codelist_bezeichnung = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A1", "B1"
    )
    _, _, branch_codelist_bezeichnung = make_codeliste_and_codes(
        session, constants.CodeListe.BrancheNOGA, "NOGA1", "AGON1"
    )

    sk1_codelist_bezeichnung.value = "My First Code"
    branch_codelist_bezeichnung.value = "My Second Code"

    query = """
    query q($filter: String!) {
        codeLists(filter: $filter, cliIds: []) {
            results {
                bezeichnung {
                    de
                }
            }

        }
    }
    """

    result = run_query(query, variable_values={"filter": filter_value})
    assert result.data["codeLists"]["results"] == results


def test_filtering_codelists_by_cli_id(session, run_query):
    sk1_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A1", "B1"
    )
    branch_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.BrancheNOGA, "NOGA1", "AGON1"
    )

    query = """
    query q($filter: String!) {
        codeLists(filter: $filter, cliIds: []) {
            results {
                cliId
            }
        }
    }
    """

    result = run_query(query, variable_values={"filter": str(sk1_code_list.c_cli_id)})
    assert result.data["codeLists"]["results"] == [
        {"cliId": str(sk1_code_list.c_cli_id)}
    ]

    result = run_query(
        query, variable_values={"filter": str(branch_code_list.c_cli_id)}
    )
    assert result.data["codeLists"]["results"] == [
        {"cliId": str(branch_code_list.c_cli_id)}
    ]


def test_filtering_codelists_by_cli_ids(session, run_query):
    sk1_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A1", "B1"
    )
    branch_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.BrancheNOGA, "NOGA1", "AGON1"
    )

    query = """
    query q($cliIds: [ID!]!) {
        codeLists(cliIds: $cliIds) {
            results {
                cliId
            }

        }
    }
    """

    result = run_query(query, variable_values={"cliIds": [sk1_code_list.c_cli_id]})
    assert result.data["codeLists"]["results"] == [
        {"cliId": str(sk1_code_list.c_cli_id)}
    ]

    result = run_query(
        query,
        variable_values={"cliIds": [sk1_code_list.c_cli_id, branch_code_list.c_cli_id]},
    )
    assert result.data["codeLists"]["results"] == [
        {"cliId": str(sk1_code_list.c_cli_id)},
        {"cliId": str(branch_code_list.c_cli_id)},
    ]

    result = run_query(query, variable_values={"cliIds": [branch_code_list.c_cli_id]})
    assert result.data["codeLists"]["results"] == [
        {"cliId": str(branch_code_list.c_cli_id)}
    ]


def test_code_lists_are_sorted_by_bezeichnung(session, run_query):
    _, _, sk1_codelist_bezeichnung = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A1", "B1"
    )
    _, _, branch_codelist_bezeichnung = make_codeliste_and_codes(
        session, constants.CodeListe.BrancheNOGA, "NOGA1", "AGON1"
    )

    sk1_codelist_bezeichnung.value = "B"
    branch_codelist_bezeichnung.value = "A"

    query = """
    {
        codeLists(cliIds: []) {
            results {
                bezeichnung {
                    de
                }
            }

        }
    }
    """

    result = run_query(query)
    assert result.data["codeLists"]["results"] == [
        {"bezeichnung": {"de": "A"}},
        {"bezeichnung": {"de": "B"}},
    ]


def test_code_lists_do_not_return_duplicates_for_multiple_locales(session, run_query):
    code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A1", "B1"
    )
    key = f"codelist:{code_list.c_cli_id}"
    make_translation(session, constants.Language.FR, key, "Liste FR")
    make_translation(session, constants.Language.IT, key, "Lista IT")

    query = """
    query q($cliIds: [ID!]!, $lang: Language!) {
        codeLists(cliIds: $cliIds, lang: $lang) {
            numResultsTotal
            results {
                cliId
            }
        }
    }
    """

    result = run_query(
        query,
        variable_values={"cliIds": [code_list.c_cli_id], "lang": "FR"},
    )

    assert result.data["codeLists"]["numResultsTotal"] == 1
    assert result.data["codeLists"]["results"] == [{"cliId": str(code_list.c_cli_id)}]


def test_sorting_codes(session, run_query):
    _, codes, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StoffeKlasseI, "A", "B", "F", "E", "D"
    )
    codes[0].sort_key = 4
    codes[1].sort_key = 3
    codes[2].sort_key = 2
    codes[3].sort_key = 1
    codes[4].sort_key = 0

    codes[2].is_active = False
    codes[3].is_active = False

    query = """
    {
        codeLists(cliIds: []) {
            results {
                entries {
                    code
                }
            }
        }
    }
    """
    result = run_query(query)
    assert result.data["codeLists"]["results"] == [
        {
            "entries": [
                {"code": str(codes[4])},
                {"code": str(codes[1])},
                {"code": str(codes[0])},
                {"code": str(codes[3])},
                {"code": str(codes[2])},
            ]
        }
    ]


def test_read_only_flag_set(session, run_query):
    read_only_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.StandortTyp, "foo"
    )
    mutable_code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.Bearbeitungsstand, "bar"
    )

    query = """
    {
        codeLists(cliIds: []) {
            results {
                cliId
                readOnly
            }
        }
    }
    """
    result = run_query(query)

    assert result.data["codeLists"]["results"] == [
        {"cliId": str(mutable_code_list.c_cli_id), "readOnly": False},
        {"cliId": str(read_only_code_list.c_cli_id), "readOnly": True},
    ]


def test_create_code_list_entry_not_allowed_for_read_only_code_lists(
    session, run_query, as_admin
):
    mutation = """
    mutation m($data: CreateCodeListEntryInput!) {
        createCodeListEntry(data: $data) {
            ... on CodeListEntry {
                code
                isActive
                sortKey
            }
        }
    }
    """

    for c_cli_id in constants.READ_ONLY_CODE_LISTS:
        make_codeliste_and_codes(session, c_cli_id.value, "foo")
        variables = {
            "data": {
                "cliId": str(c_cli_id.value),
                "code": "A",
                "bezeichnung": {"de": "", "fr": "", "it": ""},
                "sortKey": None,
                "isActive": False,
            }
        }
        with pytest.raises(QueryError, match="Code list is read only."):
            run_query(mutation, variables)


def test_create_code_list_entry(session, run_query, as_admin):
    mutation = """
    mutation m($data: CreateCodeListEntryInput!) {
        createCodeListEntry(data: $data) {
            ... on CodeListEntry {
                code
                isActive
                sortKey
                bezeichnung {
                    de
                    fr
                    it
                }
            }
        }
    }
    """

    assert not session.scalars(
        select(Translation).where(Translation.key == "code:2201:A")
    ).all()
    make_codeliste_and_codes(session, constants.CodeListe.BeziehungsartSonstige, "foo")
    variables = {
        "data": {
            "cliId": str(constants.CodeListe.BeziehungsartSonstige.value),
            "code": "A",
            "bezeichnung": {"de": "foo de", "fr": "foo fr", "it": "foo it"},
            "sortKey": 3,
            "isActive": True,
        }
    }
    result = run_query(mutation, variables)
    assert result.data["createCodeListEntry"] == {
        "code": "code:2201:A",
        "isActive": True,
        "sortKey": 3,
        "bezeichnung": {"de": "foo de", "fr": "foo fr", "it": "foo it"},
    }

    assert session.scalars(
        select(Translation.value).where(Translation.key == "code:2201:A")
    ).all() == ["foo de", "foo fr", "foo it"]


def test_return_problem_if_code_already_exists(session, run_query, as_admin):
    mutation = """
    mutation m($data: CreateCodeListEntryInput!) {
        createCodeListEntry(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    message
                    field
                }
            }
        }
    }
    """

    make_codeliste_and_codes(session, constants.CodeListe.BeziehungsartSonstige, "foo")
    variables = {
        "data": {
            "cliId": str(constants.CodeListe.BeziehungsartSonstige.value),
            "code": "foo",
            "bezeichnung": {"de": "foo de", "fr": "foo fr", "it": "foo it"},
            "sortKey": 3,
            "isActive": True,
        }
    }
    result = run_query(mutation, variables)
    assert result.data["createCodeListEntry"]["problems"] == [
        {"problemCode": "EXISTS", "message": "Code exists already.", "field": "code"}
    ]


def test_setting_code_to_inactive_not_allowed_for_read_only_codelists(
    session, run_query, as_admin
):
    mutation = """
    mutation m($data: UpdateCodeListEntryInput!) {
        updateCodeListEntry(data: $data) {
            ... on CodeListEntry {
                isActive
            }
        }
    }
    """

    for c_cli_id in constants.READ_ONLY_CODE_LISTS:
        make_codeliste_and_codes(session, c_cli_id.value, "foo")
        variables = {
            "data": {
                "code": f"code:{c_cli_id.value}:foo",
                "bezeichnung": {"de": "", "fr": "", "it": ""},
                "sortKey": None,
                "isActive": False,
            }
        }
        with pytest.raises(QueryError, match="Code list is read only."):
            run_query(mutation, variables)


def test_updating_codelist_entry(session, run_query, as_admin):
    make_codeliste_and_codes(session, constants.CodeListe.Bearbeitungsstand, "foo")

    make_translation(session, constants.Language.DE, "code:55:foo", "a de")
    make_translation(session, constants.Language.FR, "code:55:foo", "a fr")
    make_translation(session, constants.Language.IT, "code:55:foo", "a it")
    mutation = """
    mutation m($data: UpdateCodeListEntryInput!) {
        updateCodeListEntry(data: $data) {
            ... on CodeListEntry {
                code
                isActive
                sortKey
            }
        }
    }
    """

    variables = {
        "data": {
            "code": "code:55:foo",
            "bezeichnung": {"de": "b de", "fr": "b fr", "it": "b it"},
            "sortKey": 3,
            "isActive": True,
        }
    }
    assert session.scalars(
        select(Translation.value).where(Translation.key == "code:55:foo")
    ).all() == ["a de", "a fr", "a it"]

    result = run_query(mutation, variables)
    assert result.data["updateCodeListEntry"] == {
        "code": "code:55:foo",
        "isActive": True,
        "sortKey": 3,
    }
    assert session.scalars(
        select(Translation.value).where(Translation.key == "code:55:foo")
    ).all() == ["b de", "b fr", "b it"]


def test_updating_code_list_bezeichnung(session, run_query, as_admin):
    code_list, _, _ = make_codeliste_and_codes(
        session, constants.CodeListe.Bearbeitungsstand, "foo"
    )
    mutation = """
    mutation m($data: UpdateCodeListInput!) {
        updateCodeList(data: $data) {
            bezeichnung {
                de
                fr
                it
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "cliId": str(code_list.c_cli_id),
                "bezeichnung": {"de": "bla de", "fr": "bla fr", "it": "bla it"},
            }
        },
    )
    assert result.data["updateCodeList"]["bezeichnung"] == {
        "de": "bla de",
        "fr": "bla fr",
        "it": "bla it",
    }


def test_updating_code_list_entry_with_existing_translation_returns_problem_group(
    session, run_query, as_admin
):
    _, codes, _ = make_codeliste_and_codes(
        session, constants.CodeListe.Bearbeitungsstand, "foo", "foo2"
    )
    make_translation(
        session, constants.Language.DE, str(codes[0]), "translation already exists"
    )
    mutation = """
    mutation m($data: UpdateCodeListEntryInput!) {
        updateCodeListEntry(data: $data) {
            ... on CodeListEntry {
                code
            }
            ... on ProblemGroup {
                problems {
                    message
                    field
                }
            }
        }
    }
    """
    variables = {
        "data": {
            "code": str(codes[1]),
            "bezeichnung": {
                "de": "translation already exists",
                "fr": "bla",
                "it": "blub",
            },
            "isActive": False,
            "sortKey": None,
        }
    }
    result = run_query(mutation, variables)
    assert result.data["updateCodeListEntry"]["problems"] == [
        {
            "message": "Error occurred updating translation",
            "field": "bezeichnung.de",
        }
    ]


def test_create_code_list_entry_with_existing_translation_returns_problem_group(
    session, run_query, as_admin
):
    codelist, codes, _ = make_codeliste_and_codes(
        session, constants.CodeListe.Bearbeitungsstand, "foo"
    )
    make_translation(
        session, constants.Language.DE, str(codes[0]), "translation already exists"
    )
    mutation = """
    mutation m($data: CreateCodeListEntryInput!) {
        createCodeListEntry(data: $data) {
            ... on ProblemGroup {
                problems {
                    message
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
                "cliId": str(codelist.c_cli_id),
                "code": f"code:{codelist.c_cli_id}:foo2",
                "bezeichnung": {
                    "de": "translation already exists",
                    "fr": "fr",
                    "it": "it",
                },
                "sortKey": None,
                "isActive": True,
            }
        },
    )
    assert result.data["createCodeListEntry"]["problems"] == [
        {
            "message": "Error occurred updating translation",
            "field": "bezeichnung.de",
        },
        {
            "message": "Error occurred updating translation",
            "field": "bezeichnung.fr",
        },
        {
            "message": "Error occurred updating translation",
            "field": "bezeichnung.it",
        },
    ]
