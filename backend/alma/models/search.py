from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .auth import User
from .base import Base, Jsonb, Lang


class Search(Base, kw_only=True):
    __tablename__ = "search"
    __table_args__ = {"schema": "alma_admin"}

    # Primary key
    search_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Fields
    name: Mapped[str]
    is_temporary: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("alma_admin.auth_user.id"), init=False
    )
    query: Mapped[Jsonb]
    fields: Mapped[Jsonb]
    sort_by: Mapped[Jsonb]
    is_grouped: Mapped[bool] = mapped_column(default=False)
    is_shared: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped[User] = relationship(User)


class SearchExport(Base, kw_only=True):
    __tablename__ = "search_export"
    __table_args__ = {"schema": "alma_export"}

    # Primary key
    search_export_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Fields
    export_id: Mapped[str]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("alma_admin.auth_user.id"), init=False
    )
    search_id: Mapped[int] = mapped_column(
        ForeignKey("alma_admin.search.search_id"), init=False
    )
    format: Mapped[str]
    lang: Mapped[Lang]
    path: Mapped[str | None] = mapped_column(default=None)
    started_at: Mapped[datetime] = mapped_column(default_factory=datetime.now)
    finished_at: Mapped[datetime | None] = mapped_column(init=False)
    status: Mapped[str] = mapped_column(default="started")

    # Relationships
    user: Mapped[User] = relationship(User)
    search: Mapped[Search] = relationship(Search)
