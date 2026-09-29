from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import make_saved_search

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
