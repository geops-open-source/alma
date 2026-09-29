"""
Permission management for Alma

Permissions are linked to users via roles. Each role has a set of permissions
defined in the code below.

From the API perspective, permissions are memebers of the Permission enum.

Permissions should be checked with the has_permission function or the permission
extension of the strawberry.field decorator. For example to check if a user has
both view and edit permissions for VFL data:

    @strawberry.field(
        permission_classes=[
            get_permission_class(
                Permission.VIEW_VFL,
                Permission.EDIT_VFL,
            )
        ]
    )
"""

import typing
from enum import Enum, StrEnum, auto
from functools import cache

from strawberry import Info
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.permission import BasePermission


class RoleName(StrEnum):
    """
    Stored as strings in the database, maped to permissions in PERMISSION_MAP
    """

    LESEN_SACHDATEN = auto()
    LESEN_GESCHAEFTE = auto()
    BEARBEITEN_SACHDATEN = auto()
    BEARBEITEN_GESCHAEFTE = auto()
    ADMINISTRATION = auto()


class Permission(Enum):
    """Permission codes map to actions that can be performed within the API"""

    VIEW_VFL = auto()
    EDIT_VFL = auto()
    VIEW_PROCESS = auto()
    EDIT_PROCESS = auto()
    EDIT_USER = auto()
    EDIT_SETTINGS = auto()


# This is the hardcoded relationship between roles and permissions.
# The implication of editing implies viewing is NOT enforced here, you have to
# list both permissions explicitly.
PERMISSION_MAP: dict[RoleName, frozenset[Permission]] = {
    RoleName.LESEN_SACHDATEN: frozenset([Permission.VIEW_VFL]),
    RoleName.LESEN_GESCHAEFTE: frozenset(
        [Permission.VIEW_VFL, Permission.VIEW_PROCESS]
    ),
    RoleName.BEARBEITEN_SACHDATEN: frozenset(
        [
            Permission.VIEW_VFL,
            Permission.EDIT_VFL,
        ]
    ),
    RoleName.BEARBEITEN_GESCHAEFTE: frozenset(
        [
            Permission.VIEW_VFL,
            Permission.EDIT_VFL,
            Permission.VIEW_PROCESS,
            Permission.EDIT_PROCESS,
        ]
    ),
    RoleName.ADMINISTRATION: frozenset(Permission),
}


@typing.runtime_checkable
class HasAlmaPermission(typing.Protocol):
    alma_permissions: tuple[Permission, ...]


error_class = StrawberryGraphQLError
error_message = "user is not allowed to perform this action"


@cache
def get_permission_class(*required_permissions: Permission) -> type[BasePermission]:
    """Return permission class for the strawberry.field decorator"""

    # Not at top because this imports .models.auth which imports this module:
    from .graphql.context import Context

    class PermissionClass(BasePermission):
        message = error_message
        error_class = error_class
        alma_permissions: tuple[Permission, ...] = required_permissions

        def has_permission(
            self, source: typing.Any, info: Info[Context, None], **kwargs: typing.Any
        ) -> bool:
            return info.context.user.has_permission(*self.alma_permissions)

    return PermissionClass
