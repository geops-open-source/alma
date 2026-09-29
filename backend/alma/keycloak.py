from collections.abc import Iterator
from contextlib import contextmanager

import httpx2

from alma.settings import settings


@contextmanager
def get_keycloak_client(
    transport: httpx2.HTTPTransport | None = None,
) -> Iterator[httpx2.Client]:
    with httpx2.Client(transport=transport) as client:
        token_response = client.post(
            settings.oidc.keycloak_url("realms/master/protocol/openid-connect/token"),
            data={
                "username": settings.oidc.keycloak_admin_user,
                "password": settings.oidc.keycloak_admin_password,
                "client_id": "admin-cli",
                "grant_type": "password",
            },
        )
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
