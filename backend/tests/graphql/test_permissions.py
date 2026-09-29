import pytest
import strawberry
from business_workflow_manager.manager import WorkflowManager
from strawberry.types import has_object_definition

from alma import permissions
from alma.graphql.context import Context
from alma.graphql.schema import schema
from alma.graphql.types.auth import RequiredPermissions
from alma.models import auth as auth_models
from alma.models import subj as subj_models
from alma.permissions import Permission, RoleName
from alma.settings import settings

PERMISSION_CLASS_MESSAGE = "user is not allowed to perform this action"


@pytest.fixture
def user(session):
    user = auth_models.User(email="test@example.com", username="test", sub="sub")
    subjekt = subj_models.Subjekt()
    user.subjekt = subjekt
    session.add(user)
    session.commit()
    yield user


def test_leser_geschaefte_allowed_to_query_vflz(session, user):
    user.set_role(session, RoleName.LESEN_GESCHAEFTE)

    query = """
    {
        latestVflz {
            vflzId
        }
    }
    """
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )
    assert not result.errors
    assert result.data


def test_leser_standortdaten_allowed_to_query_vflz(session, user):
    user.set_role(session, RoleName.LESEN_SACHDATEN)

    query = """
    {
        latestVflz {
            vflzId
        }
    }
    """
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )

    assert not result.errors
    assert result.data


def test_user_without_role_not_allowed_to_query_vflz(session, user):
    query = """
    {
        latestVflz {
            vflzId
        }
    }
    """
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )
    assert result.errors
    assert result.errors[0].message == PERMISSION_CLASS_MESSAGE
    assert not result.data


def test_get_user_role_and_permissions_from_user(session, user):
    role_name = RoleName.ADMINISTRATION
    user.set_role(session, role_name)
    query = """
    {
        currentUser {
            roleName
            permissions
        }
    }
    """
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )
    assert result.data == {
        "currentUser": {
            "roleName": "ADMINISTRATION",
            # should contain all permission names:
            "permissions": [p.name for p in Permission],
        }
    }


def test_set_user_role(session, user, httpx2_mock):
    user.set_role(session, RoleName.ADMINISTRATION)
    query = """
    mutation M($userId: ID!) {
        updateUser(
            data: {
                id: $userId,
                roleName: LESEN_GESCHAEFTE,
                isSachbearbeitung: false,
                firstName: "",
                lastName: "",
                email: "test@example.com"
            }
        ) {
            ... on User {
                roleName
            }
        }
    }
    """
    httpx2_mock.add_response(
        url=settings.oidc.keycloak_url("realms/master/protocol/openid-connect/token"),
        method="POST",
        json={"access_token": "dummy token"},
        status_code=200,
    )
    httpx2_mock.add_response(
        url=settings.oidc.keycloak_url("admin/realms/alma/users/sub"),
        method="PUT",
        match_json={
            "emailVerified": True,
            "attributes": {"alma_role": "lesen_geschaefte"},
            "firstName": "",
            "lastName": "",
            "email": "test@example.com",
        },
    )
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
        variable_values={"userId": user.id},
    )
    assert not result.errors
    assert result.data == {"updateUser": {"roleName": "LESEN_GESCHAEFTE"}}

    user.set_role(session, RoleName.ADMINISTRATION)
    query = """
    mutation M($userId: ID!) {
        updateUser(data: {id: $userId, roleName: null, isSachbearbeitung: false, firstName: "", lastName: "", email: "test@example.com"}) {
            ... on User {
                roleName
                permissions
            }
        }
    }
    """
    httpx2_mock.add_response(
        url=settings.oidc.keycloak_url("realms/master/protocol/openid-connect/token"),
        method="POST",
        json={"access_token": "dummy token"},
        status_code=200,
    )
    httpx2_mock.add_response(
        url=settings.oidc.keycloak_url("admin/realms/alma/users/sub"),
        method="PUT",
        match_json={
            "emailVerified": True,
            "attributes": {"alma_role": ""},
            "firstName": "",
            "lastName": "",
            "email": "test@example.com",
        },
    )
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
        variable_values={"userId": user.id},
    )
    assert not result.errors
    assert result.data == {"updateUser": {"roleName": None, "permissions": []}}


def test_get_type_permisssions(session, user):
    @strawberry.type
    class TestType:
        @strawberry.field(
            permission_classes=[permissions.get_permission_class(Permission.EDIT_USER)]
        )
        def test_query(
            self, info: strawberry.Info[Context, None], id: strawberry.ID
        ) -> str:
            return ""

    assert has_object_definition(TestType)
    assert RequiredPermissions.get_for_type(TestType, user) == [
        RequiredPermissions(
            field="testQuery", has_permission=False, permissions=[Permission.EDIT_USER]
        )
    ]

    user.set_role(session, RoleName.ADMINISTRATION)
    assert RequiredPermissions.get_for_type(TestType, user) == [
        RequiredPermissions(
            field="testQuery", has_permission=True, permissions=[Permission.EDIT_USER]
        )
    ]


def test_permission_query(session, user):
    user.set_role(session, RoleName.ADMINISTRATION)
    query = """
    {
        queryPermissions {
            field
            hasPermission
            permissions
        }
        mutationPermissions {
            field
            hasPermission
            permissions
        }
    }
    """
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )
    assert not result.errors
    assert result.data
    assert "queryPermissions" in result.data
    assert "mutationPermissions" in result.data

    for req_perm in result.data["queryPermissions"]:
        assert req_perm["hasPermission"] is True

    for req_perm in result.data["mutationPermissions"]:
        assert req_perm["hasPermission"] is True

    for role_name in [RoleName.LESEN_GESCHAEFTE, RoleName.LESEN_SACHDATEN]:
        user.set_role(session, role_name)
        result = schema.execute_sync(
            query=query,
            context_value=Context(
                db=session, user=user, workflow_manager=WorkflowManager(session, None)
            ),
        )
        assert not result.errors
        assert result.data
        assert "mutationPermissions" in result.data

        expected = [
            "updateCurrentUser",
            "updateCurrentUserPassword",
            "updateInstanceSetting",
            "updateUserSetting",
            "createSavedSearch",
            "exportSearch",
            "updateSavedSearch",
            "deleteSavedSearch",
        ]
        assert [
            req_perm["field"]
            for req_perm in result.data["mutationPermissions"]
            if req_perm["hasPermission"]
        ] == expected, (
            f"User with role {role_name} should only be permitted to use mutations {', '.join(expected)}"
        )

    user.set_role(session, None)
    result = schema.execute_sync(
        query=query,
        context_value=Context(
            db=session, user=user, workflow_manager=WorkflowManager(session, None)
        ),
    )
    assert not result.errors
    assert result.data
    assert "mutationPermissions" in result.data

    expected = [
        "updateCurrentUser",
        "updateCurrentUserPassword",
        "updateInstanceSetting",
        "updateUserSetting",
    ]
    assert [
        req_perm["field"]
        for req_perm in result.data["mutationPermissions"]
        if req_perm["hasPermission"]
    ] == expected, (
        f"User with no role assigned should only be permitted to use mutations {', '.join(expected)}"
    )
