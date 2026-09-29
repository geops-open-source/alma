from enum import StrEnum, unique
from typing import Annotated

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Enum

from .base import Base, Timestamp, get_enum_values


@unique
class TaskCategory(StrEnum):
    IMPORT = "import"
    EXPORT = "export"
    APPLICATION = "application"


@unique
class TaskStatusEnum(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


_TaskStatus = Annotated[
    TaskStatusEnum,
    mapped_column(
        Enum(TaskStatusEnum, native_enum=False, values_callable=get_enum_values)
    ),
]

_TaskCategory = Annotated[
    TaskCategory,
    mapped_column(
        Enum(TaskCategory, native_enum=False, values_callable=get_enum_values)
    ),
]


class TaskStatus(Base, kw_only=True):
    __tablename__ = "task_status"
    __table_args__ = {"schema": "alma_admin"}

    # Primary Key
    task_status_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Fields
    name: Mapped[str]
    category: Mapped[_TaskCategory]
    last_update: Mapped[Timestamp]
    status: Mapped[_TaskStatus]
    detail: Mapped[str | None]
