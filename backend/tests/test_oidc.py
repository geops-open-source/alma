import logging
from datetime import UTC, datetime, timedelta
from json import dumps
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from authlib.integrations.starlette_client import OAuthError
from authlib.oidc.core import UserInfo
from fastapi import HTTPException
from pytest import fixture
from sqlalchemy import select

from alma.models import admin as admin_models
from alma.models import auth as auth_models
from alma.oidc import (
    SessionToken,
    _append_query_prams,
    get_current_user,
    get_valid_session,
    update_or_create_user_session,
)


@fixture
def oidc_user(session):
    user = auth_models.User(email="test@example.com", username="test", sub="sub")

    session.add(user)
    session.commit()
    user = session.get_one(auth_models.User, user.id)
    yield user


@fixture
def oidc_user_session(session, oidc_user):
    oidc_session = auth_models.OIDCSession(
        user=oidc_user,
        token=dumps(
            {
                "access_token": "access token",
                "refresh_token": "refresh token",
                "id_token": "id token",
                "expires_at": int(1e12),
                "userinfo": {"sub": oidc_user.sub},
            }
        ),
        expires_at=datetime.max.replace(tzinfo=UTC),
    )
    session.add(oidc_session)
    session.commit()
    session.refresh(oidc_session)
    yield oidc_session


@pytest.mark.parametrize(
    "url, params, result",
    [
        ("http://example.com", {"a": 1, "b": 2}, "http://example.com?a=1&b=2"),
        (
            "http://example.com?c=3",
            {"a": 1, "b": 2},
            "http://example.com?c=3&a=1&b=2",
        ),
    ],
)
def test_append_query_params(url, params, result):
    assert _append_query_prams(url, **params) == result


def test_get_user(oidc_user, oidc_user_session, session):
    request = Mock(session={"key": oidc_user_session.session_key})

    with pytest.raises(HTTPException) as e_403:
        get_current_user(session, request, oidc_user_session)

    assert e_403.value.status_code == 403, "User without role should raise 403"

    oidc_user.role = auth_models.Role.get_by_name(
        session, auth_models.RoleName.ADMINISTRATION
    )
    assert get_current_user(session, request, oidc_user_session).id == oidc_user.id

    with pytest.raises(HTTPException) as e_401:
        request = Mock(session={})
        get_current_user(session, request, None)

    assert e_401.value.status_code == 401, "Missing token should raise 401"


def test_update_or_create_user(session, caplog):
    session.add(
        admin_models.InstanceSetting(
            key="mapLayerTree.editor",
            value={"collapsed": True},
            category=admin_models.SettingCategory.USER_INITIAL,
            value_schema={"type": "object"},
        )
    )
    session.commit()

    userinfo = UserInfo(
        {
            "sub": "sub",
            "email": "test1@example.com",
            "preferred_username": "test",
            "given_name": "foo",
            "family_name": "bar",
        }
    )

    token: SessionToken = {
        "expires_at": int((datetime.now(tz=UTC) + timedelta(minutes=10)).timestamp()),
        "refresh_token": "refresh token",
        "id_token": "id token",
        "userinfo": {
            "sub": "sub",
        },
    }

    with caplog.at_level(logging.INFO, logger="alma.oidc"):
        oidc_user_session = update_or_create_user_session(session, token, userinfo)

    with pytest.raises(HTTPException) as e_403:
        get_current_user(
            session,
            Mock(session={"key": oidc_user_session.session_key}),
            oidc_user_session,
        )

    assert e_403.value.status_code == 403, "User without role should raise 403"

    user = (
        session.execute(select(auth_models.User).where(auth_models.User.sub == "sub"))
        .scalars()
        .one()
    )
    user.role = auth_models.Role.get_by_name(
        session, auth_models.RoleName.ADMINISTRATION
    )
    session.commit()

    user = get_current_user(
        session, Mock(session={"key": oidc_user_session.session_key}), oidc_user_session
    )

    oidc_records = [r for r in caplog.records if r.name == "alma.oidc"]
    assert oidc_records[-1].message == "Creating user 'test' with sub 'sub'"
    assert user.email == "test1@example.com"
    assert user.first_name == "foo"
    assert user.last_name == "bar"

    user_setting = session.scalars(
        select(auth_models.UserSetting).where(
            auth_models.UserSetting.user_id == user.id,
            auth_models.UserSetting.key == "mapLayerTree.editor",
        )
    ).one()
    assert user_setting.value == {"collapsed": True}

    user_setting.value = {"collapsed": False}
    session.commit()

    userinfo = UserInfo(
        {
            "sub": "sub",
            "email": "test2@example.com",
            "preferred_username": "test",
        }
    )

    with caplog.at_level(logging.INFO, logger="alma.oidc"):
        update_or_create_user_session(session, token, userinfo)

    oidc_records = [r for r in caplog.records if r.name == "alma.oidc"]
    assert oidc_records[-1].message == "Updating user with sub 'sub'"
    user = get_current_user(
        session, Mock(session={"key": oidc_user_session.session_key}), oidc_user_session
    )
    assert user.email == "test2@example.com"
    user_settings = session.scalars(
        select(auth_models.UserSetting).where(
            auth_models.UserSetting.user_id == user.id,
            auth_models.UserSetting.key == "mapLayerTree.editor",
        )
    ).all()
    assert len(user_settings) == 1
    assert user_settings[0].value == {"collapsed": False}


def test_assign_initial_settings_does_not_duplicate_pending_settings(session):
    session.add(
        admin_models.InstanceSetting(
            key="mapLayerTree.editor",
            value={"collapsed": True},
            category=admin_models.SettingCategory.USER_INITIAL,
            value_schema={"type": "object"},
        )
    )
    session.commit()

    user = auth_models.User(
        email="test@example.com",
        username="test",
        sub="sub",
    )
    session.add(user)

    user.assign_initial_settings()
    user.assign_initial_settings()
    session.commit()

    user_settings = session.scalars(
        select(auth_models.UserSetting).where(
            auth_models.UserSetting.user_id == user.id,
            auth_models.UserSetting.key == "mapLayerTree.editor",
        )
    ).all()

    assert len(user_settings) == 1
    assert user_settings[0].value == {"collapsed": True}


class FakeOAuthClient:
    def __init__(self, token: dict[str, Any]) -> None:
        self.token = token

    async def refresh_token(self, url: str):
        return {
            "access_token": "access token",
            "refresh_token": "refresh token",
            "expires_at": int(
                (datetime.now(tz=UTC) + timedelta(minutes=10)).timestamp()
            ),
        }


class FakeOAuthClientWithError:
    def __init__(self, token: dict[str, Any]) -> None:
        self.token = token

    async def refresh_token(self, url: str):
        raise OAuthError("Nope")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token, sso, result, assumption",
    [
        (
            None,
            Mock(server_metadata={}),
            False,
            "should return False if no token is present",
        ),
        (
            {"expires_at": 0, "userinfo": {"sub": "sub"}},
            Mock(server_metadata={}),
            False,
            "should return False if token is expired and refreshing is not possible",
        ),
        (
            {
                "expires_at": (
                    datetime.now(tz=UTC) + timedelta(minutes=10)
                ).timestamp(),
                "userinfo": {"iss": "iss", "sub": "sub"},
                "refresh_token": None,
            },
            Mock(server_metadata={}),
            True,
            "should return True if token is not expired",
        ),
        (
            {
                "expires_at": 0,
                "userinfo": {"iss": "iss", "sub": "sub"},
            },
            Mock(server_metadata={"token_endpoint": "http://example.test"}),
            False,
            "should return False if refresh_token is missing",
        ),
        (
            {
                "expires_at": 0,
                "userinfo": {"sub": "sub"},
                "refresh_token": "something",
            },
            Mock(
                server_metadata={"token_endpoint": "http://example.test"},
                _get_oauth_client=FakeOAuthClient,
                userinfo=AsyncMock(
                    return_value={
                        "sub": "sub",
                        "email": "test@expample.test",
                        "preferred_username": "test",
                    }
                ),
            ),
            True,
            "should return True if refresh_token is successful",
        ),
        (
            {"expires_at": 0, "userinfo": {"sub": "sub"}},
            Mock(
                server_metadata={"token_endpoint": "http://example.test"},
                _get_oauth_client=FakeOAuthClientWithError,
            ),
            False,
            "should return False if refresh_token raises an OAuthError",
        ),
    ],
)
async def test_is_authenticated(token, sso, session, result, assumption, oidc_user):
    if token:
        oidc_session = auth_models.OIDCSession(
            user=oidc_user,
            token=dumps(token),
            expires_at=datetime.fromtimestamp(token["expires_at"], tz=UTC),
        )
        session.add(oidc_session)
        session.commit()
        request = Mock(session={"key": oidc_session.session_key})
    else:
        oidc_session = None
        request = Mock(session={})
    assert (
        await get_valid_session(
            request=request,
            sso=sso,
            db=session,
        )
    ) == (oidc_session if result else None), assumption
