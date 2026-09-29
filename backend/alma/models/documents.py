from uuid import UUID, uuid4

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Timestamp


class Asset(Base):
    __tablename__ = "asset"
    __table_args__ = {"schema": "documents"}

    # Primary keys
    asset_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Actual fields
    created_at: Mapped[Timestamp] = mapped_column(init=False)
    modified_at: Mapped[Timestamp] = mapped_column(init=False)
    uuid: Mapped[UUID] = mapped_column(default_factory=uuid4)
    file_path: Mapped[str] = mapped_column(init=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, init=False)
    file_type: Mapped[str] = mapped_column(init=False)
    original_file_name: Mapped[str] = mapped_column(init=False)
    preview_path: Mapped[str | None] = mapped_column(init=False)
    title: Mapped[str] = mapped_column(init=False)
