"""
Shared FastAPI dependencies
"""

from collections.abc import AsyncIterator, Iterator

from httpx2 import AsyncClient
from preview_generator.manager import (  # pyright: ignore[reportMissingTypeStubs]
    PreviewManager,
)
from sqlalchemy.orm import Session

from alma.settings import settings

from .db import get_session as _get_session


def get_session() -> Iterator[Session]:
    with _get_session() as session:
        yield session


async def get_http_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient() as client:
        yield client


def get_preview_manager() -> Iterator[PreviewManager]:
    yield PreviewManager(settings.documents_path)
