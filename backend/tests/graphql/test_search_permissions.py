from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from utils import (
    Language,
    QueryError,
    make_beteiligter_geschaeft,
    make_code,
    make_document_node,
    make_subj,
    make_translation,
    make_vflz,
)

from alma.models import codes
from alma.models.auth import Role, RoleName

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("as_lesen_geschaefte", "generate_codes"),
]


@pytest.mark.parametrize(
    "role, expected_result",
    [
        (RoleName.LESEN_SACHDATEN, []),
        (RoleName.BEARBEITEN_SACHDATEN, []),
        (
            RoleName.LESEN_GESCHAEFTE,
            [
                {
                    "type": "FIELD_NAME",
                    "value": "Task-Titel",
                    "category": "GESCHAEFT",
                    "fieldType": None,
                }
            ],
        ),
        (
            RoleName.BEARBEITEN_GESCHAEFTE,
            [
                {
                    "type": "FIELD_NAME",
                    "value": "Task-Titel",
                    "category": "GESCHAEFT",
                    "fieldType": None,
                }
            ],
        ),
        (
            RoleName.ADMINISTRATION,
            [
                {
                    "type": "FIELD_NAME",
                    "value": "Task-Titel",
                    "category": "GESCHAEFT",
                    "fieldType": None,
                }
            ],
        ),
    ],
)
def test_search_autosuggest_permissions(role, expected_result, run_query, context):
    query = """
    query q($input: String!, $pos: Int!, $lang: Language!) {
        autosuggestSearchQuery(input: $input, pos: $pos, lang: $lang) {
            type value category, fieldType
        }
    }
    """
    context.user.role = context.db.scalars(select(Role).where(Role.name == role)).one()
    response = run_query(query, {"input": "Task-Titel", "pos": 10, "lang": "DE"})
    assert response.data["autosuggestSearchQuery"] == expected_result


@pytest.mark.parametrize(
    "search_query",
    [
        'Task-Titel ~ "Dokument"',
        "Task-Start > 2020-01-01",
        "Task-Ende > 2020-01-01",
        "Task-Fälligkeit > 2020-01-01",
        'Dokument-Referenz ~ "document_ref"',
        'Notiz ~ "Notiz"',
        'Task-Beteiligte ~ "Frieda"',
        'Task-Beziehungsart-Sachbearbeitung = "Sachbearbeitung"',
        'Task-Typ = "Dokument"',
        'Task-Status = "offen"',
    ],
)
def test_geschaefte_fields_in_advanced_query_raises_if_not_allowed(
    run_query,
    session,
    context,
    search_query,
):
    vflz = make_vflz(session, "Standort A", 1)
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "bas")
    make_translation(session, Language.DE, str(sachbearbeitung_code), "Sachbearbeitung")

    code_typ_dokument = make_code(session, codes.TaskTyp, "document")
    code_status_offen = make_code(session, codes.TaskStatus, "started")
    doc = make_document_node(session, vflz, "Dokument")
    doc.started_at = datetime.now()
    doc.finished_at = datetime.now() + timedelta(hours=3)
    doc.deadline = datetime.now() + timedelta(hours=1)
    doc.note = "Notiz"
    doc.document_ref = "document_ref"

    make_translation(
        session, lang=Language.DE, key=str(code_typ_dokument), value="Dokument"
    )
    make_translation(
        session, lang=Language.DE, key=str(code_status_offen), value="offen"
    )
    subj = make_subj(
        session, name="Fleissig", vorname="Frieda", taetigkeit="Productownerin"
    )
    bet = make_beteiligter_geschaeft(session, subjekt=subj, node=doc)
    bet.beziehungsart = sachbearbeitung_code
    query = """
    query q($search: String!, $fields: [SearchField!]!) {
        search(query: $search, advanced: true, fields: $fields) {
            tabular { results }
        }
    }
    """
    variables = {"search": search_query, "fields": ["VFLZ_ID"]}

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.LESEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.BEARBEITEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.LESEN_GESCHAEFTE)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.BEARBEITEN_GESCHAEFTE)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.ADMINISTRATION)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []


@pytest.mark.parametrize(
    "search_filter",
    [
        ("TASK_TITEL", "Dokument"),
        ("TASK_START_DATUM", "2020-01-01"),
        ("TASK_END_DATUM", "2020-01-01"),
        ("TASK_FAELLIGKEIT", "2020-01-01"),
        ("DOKUMENT_REFERENZ", "document_ref"),
        ("NOTIZ", "Notiz"),
        ("TASK_BETEILIGTE", "Frieda"),
        ("TASK_BEZIEHUNGSART_SACHBEARBEITUNG", "code:2202:bas"),
        ("TASK_TYP", "code:30000:document"),
        ("TASK_STATUS", "code:30001:started"),
    ],
)
def test_geschaefte_fields_in_simple_search_filters_raises_if_not_allowed(
    run_query,
    session,
    context,
    search_filter,
):
    vflz = make_vflz(session, "Standort A", 1)
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "bas")
    make_translation(session, Language.DE, str(sachbearbeitung_code), "Sachbearbeitung")

    code_typ_dokument = make_code(session, codes.TaskTyp, "document")
    code_status_offen = make_code(session, codes.TaskStatus, "started")
    doc = make_document_node(session, vflz, "Dokument")
    doc.started_at = datetime(2020, 1, 1)
    doc.finished_at = datetime(2020, 1, 1)
    doc.deadline = datetime(2020, 1, 1)
    doc.note = "Notiz"
    doc.document_ref = "document_ref"

    make_translation(
        session, lang=Language.DE, key=str(code_typ_dokument), value="Dokument"
    )
    make_translation(
        session, lang=Language.DE, key=str(code_status_offen), value="offen"
    )
    subj = make_subj(
        session, name="Fleissig", vorname="Frieda", taetigkeit="Productownerin"
    )
    bet = make_beteiligter_geschaeft(session, subjekt=subj, node=doc)
    bet.beziehungsart = sachbearbeitung_code
    query = """
    query q($fields: [SearchField!]!, $filters: [SearchFilter!]!) {
        search(query: "Standort A", advanced: false, filters: $filters, fields: $fields) {
            tabular { results }
        }
    }
    """
    field, value = search_filter
    variables = {"filters": [{"field": field, "value": value}], "fields": ["VFLZ_ID"]}

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.LESEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.BEARBEITEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    print(search_filter)
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.LESEN_GESCHAEFTE)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.BEARBEITEN_GESCHAEFTE)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.ADMINISTRATION)
    ).one()
    result = run_query(query, variables)
    assert result.data["search"]["tabular"]["results"] != []


@pytest.mark.parametrize(
    "field_name",
    [
        "TASK_TITEL",
        "TASK_START_DATUM",
        "TASK_END_DATUM",
        "TASK_FAELLIGKEIT",
        "DOKUMENT_REFERENZ",
        "NOTIZ",
        "TASK_BETEILIGTE",
        "TASK_BEZIEHUNGSART_SACHBEARBEITUNG",
        "TASK_STATUS",
        "TASK_TYP",
    ],
)
def test_geschaefte_fields_in_requested_result_raises_if_not_allowed(
    run_query,
    session,
    context,
    field_name,
):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    doc1 = make_document_node(session, vflz1, "Document 1")
    doc1.started_at = datetime(2025, 1, 1)
    doc1.finished_at = datetime(2026, 1, 1)
    doc1.deadline = datetime(2027, 1, 1)
    doc1.document_ref = "my-reference"
    doc1.note = "notiz"

    code_typ_dokument = make_code(session, codes.TaskTyp, "document")
    code_status_offen = make_code(session, codes.TaskStatus, "started")
    make_translation(
        session, lang=Language.DE, key=str(code_typ_dokument), value="Dokument"
    )
    make_translation(
        session, lang=Language.DE, key=str(code_status_offen), value="offen"
    )
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "bas")
    make_translation(session, Language.DE, str(sachbearbeitung_code), "Sachbearbeitung")

    query = """
    query q($search: String!, $fields: [SearchField!]!) {
        search(query: $search, advanced: true, fields: $fields) {
            tabular { results }
        }
    }
    """
    variables = {
        "search": 'Bezeichnung ~ "Standort A"',
        "fields": ["VFLZ_ID", field_name],
    }

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.LESEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    with pytest.raises(QueryError, match="error.Permissions.SearchQuery"):
        context.user.role = context.db.scalars(
            select(Role).where(Role.name == RoleName.BEARBEITEN_SACHDATEN)
        ).one()
        run_query(query, variables)

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.LESEN_GESCHAEFTE)
    ).one()
    run_query(query, variables)

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.BEARBEITEN_GESCHAEFTE)
    ).one()
    run_query(query, variables)

    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.ADMINISTRATION)
    ).one()
    run_query(query, variables)


@pytest.mark.parametrize(
    ("user_role", "can_see_geschaefte"),
    [
        (RoleName.LESEN_SACHDATEN, False),
        (RoleName.BEARBEITEN_SACHDATEN, False),
        (RoleName.LESEN_GESCHAEFTE, True),
        (RoleName.BEARBEITEN_GESCHAEFTE, True),
    ],
)
def test_search_field_names_are_filtered_by_user_role(
    context, run_query, user_role: RoleName, can_see_geschaefte: bool
):
    query = "{ searchFieldNames (lang: DE) { category } }"
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == user_role)
    ).one()
    result = run_query(query)
    assert can_see_geschaefte == (
        "GESCHAEFT"
        in [field_name["category"] for field_name in result.data["searchFieldNames"]]
    )


@pytest.mark.parametrize(
    ("user_role", "can_see_geschaefte"),
    [
        (RoleName.LESEN_SACHDATEN, False),
        (RoleName.BEARBEITEN_SACHDATEN, False),
        (RoleName.LESEN_GESCHAEFTE, True),
        (RoleName.BEARBEITEN_GESCHAEFTE, True),
    ],
)
def test_search_fields_are_filterd_by_user_role(
    context, run_query, user_role: RoleName, can_see_geschaefte: bool
):
    query = "{ searchFields { field } }"
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == user_role)
    ).one()
    result = run_query(query)
    assert can_see_geschaefte == (
        "TASK_TYP"
        in [field_info["field"] for field_info in result.data["searchFields"]]
    )
