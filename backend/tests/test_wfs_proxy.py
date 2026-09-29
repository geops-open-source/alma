from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import alma.oidc
from alma.api import app
from alma.models.auth import User
from alma.settings import AuthSettings, BasicCredentials, settings


@contextmanager
def override_dependency(
    key: Callable[..., Any], value: Callable[..., Any]
) -> Iterator[None]:
    old_value = app.dependency_overrides.get(key)
    try:
        app.dependency_overrides[key] = value
        yield
    finally:
        if old_value is not None:
            app.dependency_overrides[key] = old_value


@pytest.fixture
def has_current_user() -> Iterator[None]:
    def _fake_get_user() -> User:
        return User(
            username="test",
            email="test@localhost",
            sub="test-sub",
        )

    with override_dependency(alma.oidc.get_current_user, _fake_get_user):
        yield


@pytest.fixture
def no_current_user() -> Iterator[None]:
    def _fake_get_user() -> User:
        raise HTTPException(status_code=401, detail="Authentication required")

    with override_dependency(alma.oidc.get_current_user, _fake_get_user):
        yield


def test_proxy_requires_authentication(
    client: TestClient, wfs_test_settings, no_current_user
):
    response = client.get("/api/wfs_proxy/gemeinde")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_proxy_returns_404_for_unknown_service(
    client: TestClient, wfs_test_settings, has_current_user
):
    response = client.get("/api/wfs_proxy/unknown-service")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service not configured"}


def test_proxy_forwards_get_request(
    client: TestClient, wfs_test_settings, has_current_user
):
    response = client.get(
        "/api/wfs_proxy/gemeinde",
        params={
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "getCapabilities",
        },
    )

    assert response.status_code == 200
    assert "WFS_Capabilities" in response.text


def test_proxy_applies_headers(
    client: TestClient, wfs_test_settings, has_current_user, httpx2_mock
):
    httpx2_mock.add_response(
        match_headers={"Authorization": "Basic Zm9vOmJhcg==", "X-Other": "foo"}
    )
    settings.wfs_proxy["gemeinde"].auth = AuthSettings(
        basic=BasicCredentials(user="foo", password="bar"), headers={"X-Other": "foo"}
    )
    response = client.get(
        "/api/wfs_proxy/gemeinde",
        params={
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "getCapabilities",
        },
    )
    assert response.status_code == 200


def test_proxy_not_configured_raises(
    client: TestClient, wfs_test_settings, has_current_user
):
    response = client.get(
        "/api/wfs_proxy/ort_plz",
        params={
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "getCapabilities",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Service not configured"}
