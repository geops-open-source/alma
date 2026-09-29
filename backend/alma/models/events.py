from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import ErfassungMutationMixin


class Event(Base, ErfassungMutationMixin):
    """Event"""

    __tablename__ = "event"
    __table_args__ = {"schema": "alma"}

    event_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    vflz_id: Mapped[int]
    event_type: Mapped[str]
    event_data: Mapped[Any] = mapped_column(JSONB)
    event_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=func.now()
    )
