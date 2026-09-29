from typing import TYPE_CHECKING, Self

import strawberry
from strawberry.scalars import JSON

from alma.models import admin as admin_models

if TYPE_CHECKING:
    SettingCategory = admin_models.SettingCategory
else:
    SettingCategory = strawberry.enum(admin_models.SettingCategory)


@strawberry.type
class InstanceSetting:
    key: str
    value: JSON
    value_schema: JSON
    category: SettingCategory

    @classmethod
    def from_db(cls, db_setting: admin_models.InstanceSetting) -> Self:
        return cls(
            key=db_setting.key,
            value=JSON(db_setting.value),
            value_schema=JSON(db_setting.value_schema),
            category=SettingCategory(db_setting.category),
        )


@strawberry.input
class UpdateInstanceSettingInput:
    key: str
    value: JSON
    category: SettingCategory
