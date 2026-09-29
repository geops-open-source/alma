import pytest
from sqlalchemy import select
from utils import QueryError, make_code, make_saved_search, make_translation

from alma.constants import Language
from alma.models import codes as code_models
from alma.models import search as search_models
from alma.models.auth import Role, RoleName, User, UserSetting
from alma.search.constants import DASHBOARD_SAVED_SEARCH_SETTINGS_KEY

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("as_lesen_sachdaten"),
]


def test_query_returns_only_saved_searches_that_are_created_by_me_or_shared(
    session, run_query, context
):
    other_user = User(username="other-user", email="other@example.com", sub="sub-foo")
    session.add(other_user)
    session.commit()

    my_saved_search = make_saved_search(
        session, query=[], name="My Search", user=context.user
    )
    my_saved_search.user = context.user
    my_saved_search.is_shared = False

    my_saved_search2 = make_saved_search(
        session, query=[], name="My Search 2", user=context.user
    )
    my_saved_search2.user = context.user
    my_saved_search2.is_shared = True

    other_saved_search_shared = make_saved_search(
        session, query=[], name="Other Saved Search", user=context.user
    )
    other_saved_search_shared.user = other_user
    other_saved_search_shared.is_shared = True

    other_saved_search_not_shared = make_saved_search(
        session, query=[], name="Other Saved Search not shared", user=context.user
    )
    other_saved_search_not_shared.user = other_user
    other_saved_search_not_shared.is_shared = False

    query = """
    {
        savedSearches {
            savedSearchId
        }
    }
    """
    result = run_query(query, {"lang": "DE"})
    assert result.data["savedSearches"] == [
        {
            "savedSearchId": str(my_saved_search.search_id),
        },
        {
            "savedSearchId": str(my_saved_search2.search_id),
        },
        {
            "savedSearchId": str(other_saved_search_shared.search_id),
        },
    ]


@pytest.mark.parametrize(
    "saved_query, translated_query, language",
    [
        ('Task-Titel ~ "foo"', 'Task-Titre ~ "foo"', "FR"),
        ('Task-Titel ~ "foo"', 'Task-Titolo ~ "foo"', "IT"),
        ('Task-Titolo ~ "foo"', 'Task-Titel ~ "foo"', "DE"),
        ("Task-Start > 2020-01-01", "Task-Start > 01.01.2020", "DE"),
        ('Task-Type = "document"', 'Task-Typ = "Dokument"', "DE"),
        ("In-Betrieb = TRUE", "En-service = TRUE", "FR"),
        ("X-Koordinate > 3", "X-Koordinate > 3", "DE"),
        ("Karten-Ausschnitt = 3,4,5,6", "Karten-Ausschnitt = 3,4,5,6", "DE"),
    ],
)
def test_create_saved_search(
    saved_query, translated_query, language, session, run_query
):
    make_code(session, code_models.TaskTyp, "document")
    make_translation(session, Language.FR, "code:30000:document", "document")
    make_translation(session, Language.DE, "code:30000:document", "Dokument")
    mutation = """
    mutation m($data: CreateSavedSearchInput!, $lang: Language!) {
        createSavedSearch(data: $data) {
            ... on SavedSearch {
                name
                isShared
                query(lang: $lang)
                showOnDashboard
                sortBy {
                    field
                    reverse
                }
                fields
                isGrouped
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "name": "My Search",
                "isShared": True,
                "query": saved_query,
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["BEZEICHNUNG"],
                "isGrouped": True,
            },
            "lang": language,
        },
    )

    assert result.data["createSavedSearch"] == {
        "name": "My Search",
        "isShared": True,
        "query": translated_query,
        "showOnDashboard": True,
        "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
        "fields": ["BEZEICHNUNG"],
        "isGrouped": True,
    }


def test_creating_saved_search_with_name_taken_for_user_returns_problem(
    session, run_query, context
):
    make_saved_search(session, [], context.user, "My Saved Search")

    mutation = """
    mutation m($data: CreateSavedSearchInput!) {
        createSavedSearch(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                    message
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={
            "data": {
                "name": "My Saved Search",
                "isShared": True,
                "query": 'Task-Titel ~ "foo"',
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["BEZEICHNUNG"],
                "isGrouped": True,
            },
        },
    )
    assert result.data["createSavedSearch"]["problems"] == [
        {
            "problemCode": "EXISTS",
            "field": "name",
            "message": "Name for saved search must be unique for each user",
        }
    ]


def test_update_saved_search(session, run_query, context):
    saved_search = make_saved_search(session, [], context.user)
    saved_search.name = "bla"
    saved_search.is_shared = True
    mutation = """
    mutation m($data: UpdateSavedSearchInput!) {
        updateSavedSearch(data: $data) {
            ... on SavedSearch {
                name
                isShared
                showOnDashboard
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "savedSearchId": str(saved_search.search_id),
                "name": "foo",
                "isShared": False,
                "showOnDashboard": True,
            }
        },
    )
    assert result.data["updateSavedSearch"] == {
        "name": "foo",
        "isShared": False,
        "showOnDashboard": True,
    }


def test_update_saved_search_with_taken_name_returns_problem(
    session, run_query, context
):
    saved_search = make_saved_search(session, [], context.user, "My Saved Search")
    saved_search.is_shared = True

    saved_search2 = make_saved_search(session, [], context.user, "My Saved Search2")
    saved_search2.is_shared = True
    mutation = """
    mutation m($data: UpdateSavedSearchInput!) {
        updateSavedSearch(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                    message
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "savedSearchId": str(saved_search2.search_id),
                "name": "My Saved Search",
                "isShared": False,
                "showOnDashboard": False,
            }
        },
    )
    assert result.data["updateSavedSearch"]["problems"] == [
        {
            "problemCode": "EXISTS",
            "field": "name",
            "message": "Name for saved search must be unique for each user",
        }
    ]


@pytest.mark.parametrize(
    "role, expected_saved_searches",
    [
        (RoleName.LESEN_SACHDATEN, ["no-geschaefte-field-or-query"]),
        (RoleName.BEARBEITEN_SACHDATEN, ["no-geschaefte-field-or-query"]),
        (
            RoleName.LESEN_GESCHAEFTE,
            [
                "no-geschaefte-field-or-query",
                "geschaefte-fields",
                "geschaefte-query",
                "geschaefte-and-not-geschaefte-in-query",
            ],
        ),
        (
            RoleName.BEARBEITEN_GESCHAEFTE,
            [
                "no-geschaefte-field-or-query",
                "geschaefte-fields",
                "geschaefte-query",
                "geschaefte-and-not-geschaefte-in-query",
            ],
        ),
    ],
)
def test_shared_geschaefte_saved_searches_are_not_returned_if_not_allowed(
    role, expected_saved_searches, session, run_query, context
):
    mutation = """
    mutation m($data: CreateSavedSearchInput!, $lang: Language!) {
        createSavedSearch(data: $data) {
            ... on SavedSearch {
                query(lang: $lang)
            }
        }
    }
    """
    run_query(
        mutation,
        variable_values={
            "data": {
                "name": "geschaefte-query",
                "isShared": True,
                "query": 'Task-Titel ~ "foo"',
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["BEZEICHNUNG"],
                "isGrouped": True,
            },
            "lang": "DE",
        },
    )
    run_query(
        mutation,
        variable_values={
            "data": {
                "name": "geschaefte-fields",
                "isShared": True,
                "query": 'Standort-Nummer ~ "abc"',
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["TASK_STATUS"],
                "isGrouped": True,
            },
            "lang": "DE",
        },
    )

    run_query(
        mutation,
        variable_values={
            "data": {
                "name": "no-geschaefte-field-or-query",
                "isShared": True,
                "query": 'Standort-Nummer ~ "abc"',
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["BEZEICHNUNG"],
                "isGrouped": True,
            },
            "lang": "DE",
        },
    )
    run_query(
        mutation,
        variable_values={
            "data": {
                "name": "geschaefte-and-not-geschaefte-in-query",
                "isShared": True,
                "query": 'Standort-Nummer ~ "abc" AND Task-Titel ~ "abc"',
                "showOnDashboard": True,
                "sortBy": [{"field": "BEZEICHNUNG", "reverse": False}],
                "fields": ["BEZEICHNUNG"],
                "isGrouped": True,
            },
            "lang": "DE",
        },
    )

    context.user.role = session.scalars(select(Role).where(Role.name == role)).one()
    query = """
    {
        savedSearches {
            name
        }
    }
    """

    result = run_query(query)
    assert set(ss["name"] for ss in result.data["savedSearches"]) == set(
        expected_saved_searches
    )


def test_delete_saved_search(session, run_query, context):
    saved_search = make_saved_search(session, [], context.user)

    mutation = """
    mutation m($savedSearchId: ID!) {
        deleteSavedSearch(savedSearchId: $savedSearchId)
    }
    """

    result = run_query(mutation, {"savedSearchId": str(saved_search.search_id)})
    assert result.data["deleteSavedSearch"] == str(saved_search.search_id)
    assert not session.get(search_models.Search, int(saved_search.search_id))


def test_delete_saved_search_of_different_user_raises(session, run_query, context):
    other_user = User(username="other-user", email="other@example.com", sub="sub-foo")
    session.add(other_user)
    session.commit()

    saved_search = make_saved_search(session, [], other_user)

    mutation = """
    mutation m($savedSearchId: ID!) {
        deleteSavedSearch(savedSearchId: $savedSearchId)
    }
    """

    with pytest.raises(
        QueryError,
        match="You are not allowed to delete this search as you did not create it.",
    ):
        run_query(mutation, {"savedSearchId": str(saved_search.search_id)})
    assert session.get(search_models.Search, int(saved_search.search_id))


def test_querying_saved_search_in_different_languages(
    session, run_query, context, as_lesen_geschaefte
):
    document_code = make_code(session, code_models.TaskTyp, "document")
    make_translation(session, Language.DE, str(document_code), "Dokument")
    make_translation(session, Language.FR, str(document_code), "Document")
    make_translation(session, Language.IT, str(document_code), "Documento")
    make_saved_search(
        session,
        [
            {
                "__type__": "expression",
                "name": "task_typ",
                "operator": "=",
                "value": str(document_code),
            }
        ],
        context.user,
    )

    german_saved_searches_query = """{ savedSearches { query(lang: DE) } }"""
    french_saved_searches_query = """{ savedSearches { query(lang: FR) } }"""
    italian_saved_searches_query = """{ savedSearches { query(lang: IT) } }"""

    result = run_query(german_saved_searches_query)
    assert result.data["savedSearches"] == [{"query": 'Task-Typ = "Dokument"'}]

    result = run_query(french_saved_searches_query)
    assert result.data["savedSearches"] == [{"query": 'Task-Type = "Document"'}]

    result = run_query(italian_saved_searches_query)
    assert result.data["savedSearches"] == [{"query": 'Task-Tipo = "Documento"'}]


def test_save_search_without_query(run_query):
    mutation = """
    mutation m($data: CreateSavedSearchInput!) {
        createSavedSearch(data: $data) {
            ... on SavedSearch {
                query(lang: DE)
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "name": "foo",
                "query": "",
                "isGrouped": False,
                "showOnDashboard": False,
                "isShared": False,
                "fields": [],
                "sortBy": [],
            }
        },
    )
    assert result.data["createSavedSearch"]["query"] == ""


def test_updating_show_on_dashboard_for_two_users_with_one_saved_search(
    session, run_query, context
):
    other_user = User(username="other-user", email="other@example.com", sub="sub-foo")
    other_user.role = session.scalars(
        select(Role).where(Role.name == RoleName.ADMINISTRATION)
    ).one()
    session.add(other_user)
    session.commit()

    saved_search = make_saved_search(session, [], context.user)

    mutation = """
    mutation m($data: UpdateSavedSearchInput!) {
        updateSavedSearch(data: $data) {
            ... on SavedSearch {
                showOnDashboard
            }
        }
    }
    """

    variables = {
        "data": {
            "name": "foo",
            "isShared": True,
            "savedSearchId": str(saved_search.search_id),
            "showOnDashboard": True,
        }
    }
    result = run_query(mutation, variable_values=variables)

    query = """{ savedSearches { showOnDashboard } }"""

    result = run_query(query)
    assert result.data["savedSearches"] == [{"showOnDashboard": True}]

    context.user = other_user

    result = run_query(query)
    assert result.data["savedSearches"] == [{"showOnDashboard": False}]

    result = run_query(mutation, variables)
    assert result.data["updateSavedSearch"]["showOnDashboard"]

    variables["data"]["showOnDashboard"] = False
    result = run_query(mutation, variables)
    assert not result.data["updateSavedSearch"]["showOnDashboard"]


def test_updating_saved_search_multiple_times_does_not_create_duplicates_in_user_setting(
    session, run_query, context
):
    saved_search = make_saved_search(
        session,
        [],
        context.user,
        name="Old Name",
        is_temporary=False,
        show_on_dashboard=True,
    )
    session.commit()

    mutation = """
    mutation m($data: UpdateSavedSearchInput!) {
        updateSavedSearch(data: $data) {
            ... on SavedSearch {
                showOnDashboard
            }
        }
    }
    """
    variable_values = {
        "data": {
            "savedSearchId": str(saved_search.search_id),
            "name": "New Name",
            "showOnDashboard": True,
            "isShared": False,
        }
    }

    user_setting = session.scalars(
        select(UserSetting).where(
            UserSetting.key == DASHBOARD_SAVED_SEARCH_SETTINGS_KEY,
            UserSetting.user_id == context.user.id,
        )
    ).one()
    assert user_setting.value == [saved_search.search_id]

    result = run_query(mutation, variable_values)
    assert result.data["updateSavedSearch"]["showOnDashboard"]
    session.refresh(user_setting)
    assert user_setting.value == [saved_search.search_id]

    result = run_query(mutation, variable_values)
    assert result.data["updateSavedSearch"]["showOnDashboard"]
    session.refresh(user_setting)
    assert user_setting.value == [saved_search.search_id]


def test_removing_saved_search_from_dashboard_twice_does_not_throw_error(
    session, run_query, context
):
    saved_search = make_saved_search(
        session,
        [],
        context.user,
        name="Old Name",
        is_temporary=False,
        show_on_dashboard=True,
    )
    session.commit()

    mutation = """
    mutation m($data: UpdateSavedSearchInput!) {
        updateSavedSearch(data: $data) {
            ... on SavedSearch {
                showOnDashboard
            }
        }
    }
    """
    variable_values = {
        "data": {
            "savedSearchId": str(saved_search.search_id),
            "name": "New Name",
            "showOnDashboard": False,
            "isShared": False,
        }
    }

    user_setting = session.scalars(
        select(UserSetting).where(
            UserSetting.key == DASHBOARD_SAVED_SEARCH_SETTINGS_KEY,
            UserSetting.user_id == context.user.id,
        )
    ).one()
    assert user_setting.value == [saved_search.search_id]

    result = run_query(mutation, variable_values)
    assert not result.data["updateSavedSearch"]["showOnDashboard"]
    session.refresh(user_setting)
    assert user_setting.value == []

    result = run_query(mutation, variable_values)
    assert not result.data["updateSavedSearch"]["showOnDashboard"]
    session.refresh(user_setting)
    assert user_setting.value == []
