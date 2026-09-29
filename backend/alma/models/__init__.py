from collections.abc import Callable, Iterable
from typing import cast

from sqlalchemy import Dialect
from sqlalchemy.schema import Table

from . import auth, base

__all__ = ["auth"]


def compile_all() -> Iterable[str]:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    for mapper in base.Base.registry.mappers:
        table = mapper.local_table
        assert isinstance(table, Table)
        compiled = str(
            CreateTable(table).compile(
                dialect=cast(Callable[[], Dialect], postgresql.dialect)(),
                compile_kwargs={"literal_binds": True},
            )
        )[:-2]
        compiled = f"{compiled};"
        model = mapper.class_
        if hasattr(model, "__doc__"):
            compiled = (
                f"{compiled}\n\nCOMMENT ON TABLE {table.fullname} IS '{model.__doc__}';"
            )
        yield compiled


if __name__ == "__main__":
    # print all create table statements for all tables by running this script
    #     python -m alma.models.__init__

    for sql in compile_all():
        print(sql, end="\n\n")
