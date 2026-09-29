from collections.abc import Iterator
from contextlib import contextmanager

from procrastinate.contrib.sqlalchemy import SQLAlchemyPsycopg2Connector

from alma.db import get_engine

from .app import app

# No need to configure this connector, since we'll pass in an existing engine
sync_sqla_connector = SQLAlchemyPsycopg2Connector()


@contextmanager
def open_client() -> Iterator[None]:
    """
    Configure the procrastinate app to use the global sqlalchemy engine.

    This is used to enqueue jobs in the main application, not by the task queue workers.
    """
    engine = get_engine()
    with app.replace_connector(sync_sqla_connector), app.open(engine):
        yield
