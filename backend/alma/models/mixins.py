"""Commom mixins for models

Mixins should only add colums with init=False or default values.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

from .base import BigInt, Timestamp


class IDMixin(MappedAsDataclass):
    """Mixin to add an id column"""

    id: Mapped[BigInt] = mapped_column(init=False, primary_key=True)
    """Primary key column, uninitialized before insert"""


class CreateUpdateMixin(MappedAsDataclass):
    """Mixin to add created_at and updated_at columns"""

    created_at: Mapped[Timestamp] = mapped_column(init=False, repr=False)
    """Timestamp of row creation, uninitialized before insert"""
    updated_at: Mapped[Timestamp] = mapped_column(
        init=False, repr=False, onupdate=func.now()
    )
    """Timestamp of row update, uninitialized before insert"""


class ErfassungMutationMixin(MappedAsDataclass):
    erfassungs_datum: Mapped[datetime | None] = mapped_column(init=False)
    erfasser: Mapped[str | None] = mapped_column(init=False)
    mutations_datum: Mapped[datetime | None] = mapped_column(init=False)
    mutierer: Mapped[str | None] = mapped_column(init=False)
