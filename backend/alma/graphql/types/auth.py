from typing import TYPE_CHECKING, Annotated, Self

import strawberry
from strawberry.scalars import JSON
from strawberry.types.base import WithStrawberryObjectDefinition, get_object_definition
from strawberry.utils.str_converters import to_camel_case

from alma import permissions
from alma.models import auth as auth_models
from alma.models import subj as subj_models

from ..utils.schema import Info, to_id

RoleName = Annotated[permissions.RoleName, strawberry.enum(permissions.RoleName)]
Permission = Annotated[permissions.Permission, strawberry.enum(permissions.Permission)]


if TYPE_CHECKING:
    from .subj import Subjekt


@strawberry.input
class UpdateUserSettingInput:
    key: str
    value: JSON


@strawberry.type
class UserSetting:
    key: str
    value: JSON

    @classmethod
    def from_db(cls, db_setting: auth_models.UserSetting) -> Self:
        return cls(key=db_setting.key, value=db_setting.value)


@strawberry.type
class User:
    _user: strawberry.Private[auth_models.User]
    id: strawberry.ID
    username: str
    email: str
    role_name: RoleName | None
    permissions: list[Permission]
    first_name: str
    last_name: str
    is_sachbearbeitung: bool

    @strawberry.field
    def subjekt(
        self, info: Info
    ) -> Annotated["Subjekt", strawberry.lazy(".subj")] | None:
        from .subj import Subjekt

        session = info.context.db
        user = session.get_one(auth_models.User, int(self.id))
        return (
            Subjekt.from_db(session.get_one(subj_models.Subjekt, user.subj_id))
            if user.subj_id
            else None
        )

    @strawberry.field
    def settings(self, info: Info) -> list[UserSetting]:
        return [UserSetting.from_db(db_setting) for db_setting in self._user.settings]

    @classmethod
    def from_db(cls, db_user: auth_models.User) -> Self:
        return cls(
            _user=db_user,
            id=to_id(db_user.id),
            username=db_user.username,
            email=db_user.email,
            role_name=db_user.role.name if db_user.role else None,
            permissions=sorted(db_user.get_permission_set(), key=lambda p: p.value),
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            is_sachbearbeitung=db_user.is_sachbearbeitung,
        )


@strawberry.input
class UpdateUserInput:
    id: strawberry.ID
    role_name: RoleName | None = strawberry.UNSET
    email: str
    first_name: str
    last_name: str
    is_sachbearbeitung: bool


@strawberry.input
class UpdateCurrentUserPasswordInput:
    password: str = strawberry.UNSET


@strawberry.input
class UpdateCurrentUserInput:
    first_name: str
    last_name: str


@strawberry.type
class RequiredPermissions:
    field: str
    has_permission: bool
    permissions: list[Permission]

    @classmethod
    def get_for_type(
        cls, obj: type[WithStrawberryObjectDefinition], user: auth_models.User
    ) -> list[Self]:
        result: list[Self] = []

        for field in get_object_definition(obj, strict=True).fields:
            permissions_: list[Permission] = []
            for permission_class in field.permission_classes:
                assert isinstance(permission_class, permissions.HasAlmaPermission)
                permissions_.extend(permission_class.alma_permissions)
            result.append(
                cls(
                    field=to_camel_case(field.name),
                    has_permission=user.has_permission(*permissions_),
                    permissions=permissions_,
                )
            )

        return result


@strawberry.input
class CreateUserInput:
    first_name: str
    last_name: str
    email: str
    role_name: RoleName | None
    password: str
    is_sachbearbeitung: bool
