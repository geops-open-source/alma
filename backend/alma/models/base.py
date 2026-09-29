"""Shared base class and utilities for ORM models"""

from datetime import datetime
from enum import StrEnum
from functools import partial
from typing import Annotated, Any

from sqlalchemy import BigInteger, Enum, ForeignKeyConstraint, MetaData
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    mapped_column,
)
from sqlalchemy.sql import func

from ..constants import Language

CODE_REF_COLUMNS = ["alma.cod.c_cli_id", "alma.cod.code"]
CodeForeignKeyConstraint = partial(ForeignKeyConstraint, refcolumns=CODE_REF_COLUMNS)


def get_enum_values(cls: type[StrEnum]) -> list[str]:
    """
    Helper to store Enum members in sqlalchemy by value instead of by name.
    """
    return [e.value for e in cls]


BigInt = Annotated[int, mapped_column(BigInteger)]
Timestamp = Annotated[
    datetime,
    mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
]
Lang = Annotated[
    Language,
    mapped_column(Enum(Language, native_enum=False, values_callable=get_enum_values)),
]
Jsonb = Annotated[Any, mapped_column(JSONB)]


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all ORM models, sub-classes are dataclasses"""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "chk_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(referred_table_name)s_%(table_name)s_%(column_0_name)s",
            "pk": "pk_%(table_name)s_%(column_0_name)s",
        }
    )
