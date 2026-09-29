from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import make_saved_search

from alma.models import admin as admin_models
from alma.models import auth as auth_models
from alma.models import search as search_models
from alma.models import subj as subj_models
from alma.settings import settings


def make_user(
    session: Session,
    username: str = "test",
    email: str = "test@example.com",
    sub: str = "sub",
):
    user = auth_models.User(email=email, username=username, sub=sub)
    subj = subj_models.Subjekt()
    user.subjekt = subj
    session.add(user)
    session.commit()
    user = session.get_one(auth_models.User, user.id)
    return user


def make_setting(session: Session, key: str, value: dict[str, Any], user_id: int):
    db_setting = auth_models.UserSetting(key=key, value=value, user_id=user_id)
    session.add(db_setting)
    session.commit()

    return db_setting


def make_instance_setting(
    session: Session,
    key: str,
    value: Any,
    category: admin_models.SettingCategory,
):
    db_setting = admin_models.InstanceSetting(
        key=key,
        value=value,
        category=category,
        value_schema={"type": "object"},
    )
    session.add(db_setting)
    session.commit()

    return db_setting


def test_query_settings_for_user(session, run_query, context):
    user = make_user(session)
    context.user = user
    make_setting(session, "setting1", {"vfl_id": "1"}, context.user.id)
    make_setting(session, "setting2", {"vfl_id": "2"}, context.user.id)

    query = """{
        currentUser {
            settings {
                key
                value
            }
        }
    }
    """
    result = run_query(query)
    assert result.data["currentUser"] == {
        "settings": [
            {"key": "setting1", "value": {"vfl_id": "1"}},
            {"key": "setting2", "value": {"vfl_id": "2"}},
        ],
    }


def test_update_user_setting_update_existing_key(session, run_query, context):
    user = make_user(session)
    user.role = session.scalars(
        select(auth_models.Role).where(
            auth_models.Role.name == auth_models.RoleName.LESEN_SACHDATEN
        )
    ).one()
    context.user = user
    setting1 = make_setting(session, "setting1", {"vfl_id": "1"}, context.user.id)
    make_setting(session, "setting2", {"vfl_id": "2"}, context.user.id)

    mutation = """
    mutation m($data: UpdateUserSettingInput!) {
        updateUserSetting(data: $data) {
            key
            value
        }
    }
    """

    run_query(
        query=mutation,
        variable_values={"data": {"key": "setting1", "value": "new_value"}},
    )

    session.refresh(setting1)
    assert setting1.value == "new_value"


def test_update_user_setting_update_key_that_does_not_exist(
    session, run_query, context
):
    user = make_user(session)
    user.role = session.scalars(
        select(auth_models.Role).where(
            auth_models.Role.name == auth_models.RoleName.LESEN_SACHDATEN
        )
    ).one()
    context.user = user
    assert not user.settings
    mutation = """
    mutation m($data: UpdateUserSettingInput!) {
        updateUserSetting(data: $data) {
            key
            value
        }
    }
    """

    run_query(
        query=mutation,
        variable_values={"data": {"key": "new key", "value": "new_value"}},
    )

    session.refresh(user)
    assert [(s.key, s.value) for s in user.settings] == [("new key", "new_value")]


def test_user_does_have_edit_permissions(session):
    user = make_user(session)
    user.role = session.scalars(
        select(auth_models.Role).where(
            auth_models.Role.name == auth_models.RoleName.BEARBEITEN_GESCHAEFTE
        )
    ).one()
    assert user.has_edit_permission()


def test_user_does_not_have_edit_permissions(session):
    user = make_user(session)
    user.role = session.scalars(
        select(auth_models.Role).where(
            auth_models.Role.name == auth_models.RoleName.LESEN_GESCHAEFTE
        )
    ).one()
    assert not user.has_edit_permission()


def test_users_query_is_ordered_by_email(session, run_query, as_admin):
    make_user(session, username="foo", email="test@example.com", sub="user1")
    make_user(session, username="bar", email="another_test@example.com", sub="user2")

    query = """
    {
        users {
            email
        }
    }
    """

    result = run_query(query)
    assert result.data["users"] == [
        {"email": "alma-test@example.com"},
        {"email": "another_test@example.com"},
        {"email": "test@example.com"},
    ]


def test_update_user_with_sachbearbeitung(session, run_query, as_admin, httpx2_mock):
    httpx2_mock.add_response(
        is_reusable=True, method="POST", json={"access_token": "dummy-token"}
    )
    httpx2_mock.add_response(method="PUT")
    user = make_user(session, username="foo", email="test@example.com", sub="user1")
    mutation = """
    mutation m($data: UpdateUserInput!) {
        updateUser(data: $data) {
            ... on User {
                id
                isSachbearbeitung
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "id": str(user.id),
                "isSachbearbeitung": True,
                "firstName": "",
                "lastName": "",
                "email": user.email,
            }
        },
    )

    assert result.data["updateUser"]["isSachbearbeitung"]


def test_create_user(run_query, as_admin, httpx2_mock):
    httpx2_mock.add_response(
        is_reusable=True, method="POST", json={"access_token": "dummy-token"}
    )
    httpx2_mock.add_response(method="GET", json=[{"id": "sub"}])

    mutation = """
    mutation m($data: CreateUserInput!) {
        createUser(data: $data) {
            ... on User {
                username
                email
                roleName
                firstName
                lastName
                isSachbearbeitung
                subjekt {
                    vorname
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "email": "unit@test.com",
                "firstName": "unit",
                "lastName": "last",
                "roleName": None,
                "password": "foo",
                "isSachbearbeitung": True,
            }
        },
    )
    assert result.data["createUser"] == {
        "username": "unit@test.com",
        "email": "unit@test.com",
        "roleName": None,
        "firstName": "unit",
        "lastName": "last",
        "isSachbearbeitung": True,
        "subjekt": {"vorname": "unit"},
    }


def test_create_user_applies_initial_settings(
    session, run_query, as_admin, httpx2_mock
):
    httpx2_mock.add_response(
        is_reusable=True, method="POST", json={"access_token": "dummy-token"}
    )
    httpx2_mock.add_response(method="GET", json=[{"id": "sub"}])

    old_system_user_sub = settings.system_user_sub
    settings.system_user_sub = None
    try:
        make_instance_setting(
            session,
            "mapLayerTree.editor",
            {"collapsed": False},
            admin_models.SettingCategory.USER_INITIAL,
        )
        make_instance_setting(
            session,
            "search.filters",
            {"onlyOpen": True},
            admin_models.SettingCategory.USER_INITIAL,
        )

        mutation = """
        mutation m($data: CreateUserInput!) {
            createUser(data: $data) {
                ... on User {
                    settings {
                        key
                        value
                    }
                }
            }
        }
        """

        result = run_query(
            mutation,
            variable_values={
                "data": {
                    "email": "initial@test.com",
                    "firstName": "unit",
                    "lastName": "last",
                    "roleName": None,
                    "password": "foo",
                    "isSachbearbeitung": True,
                }
            },
        )
    finally:
        settings.system_user_sub = old_system_user_sub

    settings_by_key = {
        setting["key"]: setting["value"]
        for setting in result.data["createUser"]["settings"]
    }
    assert settings_by_key == {
        "mapLayerTree.editor": {"collapsed": False},
        "search.filters": {"onlyOpen": True},
    }


def test_create_user_ignores_missing_system_user_for_default_saved_searches(
    run_query, as_admin, httpx2_mock
):
    httpx2_mock.add_response(
        is_reusable=True, method="POST", json={"access_token": "dummy-token"}
    )
    httpx2_mock.add_response(method="GET", json=[{"id": "sub"}])

    settings.system_user_sub = "missing-system-user-sub"
    mutation = """
    mutation m($data: CreateUserInput!) {
        createUser(data: $data) {
            ... on User {
                username
                settings {
                    key
                    value
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "email": "missing-system@test.com",
                "firstName": "unit",
                "lastName": "last",
                "roleName": None,
                "password": "foo",
                "isSachbearbeitung": True,
            }
        },
    )

    assert result.data["createUser"]["username"] == "missing-system@test.com"
    assert result.data["createUser"]["settings"] == []


def test_create_user_with_email_that_exists_returns_problem(
    session, run_query, as_admin
):
    make_user(session, email="test@example.com")
    mutation = """
    mutation m($data: CreateUserInput!) {
        createUser(data: $data) {
            ... on ProblemGroup {
                problems {
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
                "email": "test@example.com",
                "firstName": "unit",
                "lastName": "last",
                "roleName": None,
                "password": "foo",
                "isSachbearbeitung": True,
            }
        },
    )
    assert result.data["createUser"]["problems"] == [
        {"message": "User with email already exists."}
    ]


def test_update_user_with_email_that_exists_returns_problem(
    session, run_query, as_admin
):
    user1 = make_user(
        session, username="user1", email="user1@example.com", sub="sub_user1"
    )
    user2 = make_user(
        session, username="user2", email="user2@example.com", sub="sub_user2"
    )

    mutation = """
    mutation m($data: UpdateUserInput!) {
        updateUser(data: $data) {
            ... on ProblemGroup {
                problems {
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
                "id": str(user1.id),
                "isSachbearbeitung": True,
                "firstName": "",
                "lastName": "",
                "email": user2.email,
            }
        },
    )

    assert result.data["updateUser"]["problems"] == [
        {"message": "User with email already exists."}
    ]


def test_system_users_are_not_returned(session, run_query, as_admin):
    system_user = make_user(
        session, username="foo", email="test@example.com", sub="user1"
    )
    system_user.is_system_user = True

    query = """
    {
        users {
            email
        }
    }
    """

    result = run_query(query)
    assert "test@example.com" not in [user["email"] for user in result.data["users"]]


def test_create_user_creates_saved_searches_from_saved_searches_of_system_user(
    session, run_query, httpx2_mock, as_admin
):
    httpx2_mock.add_response(
        is_reusable=True, method="POST", json={"access_token": "dummy-token"}
    )
    httpx2_mock.add_response(method="GET", json=[{"id": "sub"}])

    settings.system_user_sub = "system-user-sub"
    system_user = make_user(
        session, username="system", email="system@example.com", sub="system-user-sub"
    )
    s1 = make_saved_search(
        session,
        [
            {
                "name": "bearbeitungsstand",
                "value": "code:55:BAV_105",
                "__type__": "expression",
                "operator": "=",
            }
        ],
        system_user,
        "Bearbeitungsstand",
    )
    s1.is_shared = True

    s2 = make_saved_search(
        session,
        [
            {
                "name": "publiziert",
                "value": "1",
                "__type__": "expression",
                "operator": "=",
            }
        ],
        system_user,
        "Publizierte Standorte",
    )
    s2.is_shared = True

    mutation = """
    mutation m($data: CreateUserInput!) {
        createUser(data: $data) {
            ... on User {
                settings {
                    key
                    value
                }
                id
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "email": "test@example.com",
                "firstName": "unit",
                "lastName": "last",
                "roleName": None,
                "password": "foo",
                "isSachbearbeitung": True,
            }
        },
    )

    dashboard_saved_searches = result.data["createUser"]["settings"][0]
    created_user = session.get_one(
        auth_models.User, int(result.data["createUser"]["id"])
    )
    assert dashboard_saved_searches["key"] == "dashboardSavedSearches"
    ids = dashboard_saved_searches["value"]

    saved_user_searches = session.scalars(
        select(search_models.Search)
        .where(search_models.Search.search_id.in_(ids))
        .order_by(search_models.Search.name)
    ).all()

    assert saved_user_searches[0].name == s1.name
    assert saved_user_searches[0].query == s1.query
    assert saved_user_searches[0].fields == s1.fields
    assert saved_user_searches[0].sort_by == s1.sort_by
    assert saved_user_searches[0].user == created_user
    assert not saved_user_searches[0].is_shared

    assert saved_user_searches[1].name == s2.name
    assert saved_user_searches[1].query == s2.query
    assert saved_user_searches[1].fields == s2.fields
    assert saved_user_searches[1].sort_by == s2.sort_by
    assert saved_user_searches[1].user == created_user
    assert not saved_user_searches[1].is_shared
