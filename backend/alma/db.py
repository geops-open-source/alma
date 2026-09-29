import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cache

from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.orm import Session

from .settings import settings


@cache
def get_engine() -> Engine:
    if settings.database.echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    return create_engine(settings.database.url)


@contextmanager
def get_session(
    bind: Engine | Connection | None = None, testing: bool = False
) -> Iterator[Session]:
    if bind is None:
        bind = get_engine()
    if testing:
        with Session(bind=bind, join_transaction_mode="create_savepoint") as session:
            yield session
    else:
        with Session(bind=bind) as session:
            yield session
