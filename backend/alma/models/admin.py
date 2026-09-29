from enum import StrEnum, unique

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Enum

from .base import Base, Jsonb, get_enum_values


@unique
class SettingCategory(StrEnum):
    GENERAL = "GENERAL"
    ADMIN = "ADMIN"
    USER_INITIAL = "USER_INITIAL"


class InstanceSetting(Base):
    """Stores settings."""

    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("key", "category"), {"schema": "alma_admin"})

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str]
    value: Mapped[Jsonb]
    value_schema: Mapped[Jsonb]
    category: Mapped[SettingCategory] = mapped_column(
        Enum(SettingCategory, native_enum=False, values_callable=get_enum_values)
    )
