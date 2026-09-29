from logging import getLogger
from secrets import token_urlsafe
from typing import TYPE_CHECKING, Any

import httpx2
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import (
    Mapped,
    Session,
    mapped_column,
    relationship,
)

from ..permissions import PERMISSION_MAP, Permission, RoleName
from ..settings import settings
from .admin import InstanceSetting, SettingCategory
from .base import Base, BigInt, Jsonb, Timestamp
from .mixins import CreateUpdateMixin, IDMixin

logger = getLogger(__name__)

if TYPE_CHECKING:
    from .subj import Subjekt


class AuthBase(IDMixin, CreateUpdateMixin, Base):
    __abstract__ = True


class Role(AuthBase):
    """Store role information"""

    __tablename__ = "auth_role"
    __table_args__ = {"schema": "alma_admin"}

    name: Mapped[RoleName] = mapped_column(unique=True)
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="role", default_factory=list, repr=False
    )

    @classmethod
    def get_by_name(cls, db: Session, name: RoleName) -> "Role":
        return db.execute(select(cls).filter(cls.name == name)).scalar_one()


class UserSetting(Base):
    __tablename__ = "user_settings"
    __table_args__ = {"schema": "alma_admin"}

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column()
    value: Mapped[Jsonb]
    user_id: Mapped[BigInt] = mapped_column(
        ForeignKey("alma_admin.auth_user.id"), default=None, nullable=False
    )


class User(AuthBase):
    """Store user information"""

    __tablename__ = "auth_user"
    __table_args__ = {"schema": "alma_admin"}

    sub: Mapped[str] = mapped_column(unique=True, repr=False)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True, repr=False)
    first_name: Mapped[str] = mapped_column(default="")
    last_name: Mapped[str] = mapped_column(default="")
    is_sachbearbeitung: Mapped[bool] = mapped_column(default=False)

    role_id: Mapped[BigInt | None] = mapped_column(
        ForeignKey("alma_admin.auth_role.id", ondelete="SET NULL"), default=None
    )
    role: Mapped[Role | None] = relationship(
        "Role", back_populates="users", default=None, repr=False, lazy="joined"
    )
    oidc_sessions: Mapped[list["OIDCSession"]] = relationship(
        "OIDCSession", back_populates="user", default_factory=list, repr=False
    )
    settings: Mapped[list[UserSetting]] = relationship(
        "UserSetting", init=False, cascade="all, delete-orphan", repr=False
    )
    subj_id: Mapped[int | None] = mapped_column(
        ForeignKey("alma.subj.subj_id"), default=None
    )
    subjekt: Mapped["Subjekt | None"] = relationship(
        "Subjekt", default=None, back_populates="user"
    )
    is_system_user: Mapped[bool] = mapped_column(default=False)

    def get_permission_set(self) -> frozenset[Permission]:
        return PERMISSION_MAP[self.role.name] if self.role else frozenset()

    def has_permission(self, *permissions: Permission) -> bool:
        return self.get_permission_set().issuperset(permissions)

    def has_edit_permission(self) -> bool:
        return any(p for p in self.get_permission_set() if p.name.startswith("EDIT"))

    def set_role(self, db: Session, name: RoleName | None) -> None:
        self.role = Role.get_by_name(db, name) if name else None
        db.commit()

    def assign_initial_settings(self) -> None:
        session = Session.object_session(self)
        assert session is not None

        initial_settings = session.scalars(
            select(InstanceSetting).where(
                InstanceSetting.category == SettingCategory.USER_INITIAL,
                InstanceSetting.key.not_in([s.key for s in self.settings]),
            )
        ).all()

        for setting in initial_settings:
            self.settings.append(UserSetting(key=setting.key, value=setting.value))

    @classmethod
    def create(
        cls,
        db: Session,
        keycloak_client: httpx2.Client,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        role_name: RoleName | None,
        password: str | None = None,
    ) -> "User":
        """Create a new user in the database and in Keycloak"""
        role = Role.get_by_name(db, role_name) if role_name else None
        params: dict[str, Any] = {
            "username": username,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": True,
            "attributes": {
                "alma_role": role.name.value if role else "",
            },
        }

        if password:
            params["credentials"] = [
                {"type": "password", "value": password, "temporary": True}
            ]
        resp = keycloak_client.post(
            settings.oidc.keycloak_url("admin/realms/alma/users"), json=params
        )
        if resp.status_code >= 400:
            raise ValueError(resp.json())
        resp.raise_for_status()
        keycloak_user_response = keycloak_client.get(
            settings.oidc.keycloak_url("admin/realms/alma/users/"),
            params={"email": email, "exact": True},
        )
        keycloak_user_response.raise_for_status()
        sub = keycloak_user_response.json()[0]["id"]
        try:
            user = cls(
                username=username,
                email=email,
                role=role,
                sub=sub,
                first_name=first_name,
                last_name=last_name,
            )
            db.add(user)
            db.commit()
            return user
        except Exception:
            keycloak_client.delete(
                settings.oidc.keycloak_url(f"admin/realms/alma/users/{sub}")
            ).raise_for_status()
            raise

    def send_password_reset_email(
        self, keycloak_client: httpx2.Client, redirect_uri: str | None = None
    ) -> "User":
        params = (
            {"client_id": settings.oidc.client_id, "redirect_uri": redirect_uri}
            if redirect_uri
            else {}
        )
        resp = keycloak_client.put(
            settings.oidc.keycloak_url(
                f"admin/realms/alma/users/{self.sub}/execute-actions-email"
            ),
            json=["UPDATE_PASSWORD"],
            params=params,
        )
        resp.raise_for_status()
        return self

    def update(
        self,
        db: Session,
        keycloak_client: httpx2.Client,
        email: str,
        first_name: str,
        last_name: str,
        role_name: RoleName | None,
    ) -> None:
        """Update the user's role and/or email address in the database and in Keycloak"""
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = Role.get_by_name(db, role_name) if role_name else None
        keycloak_client.put(
            settings.oidc.keycloak_url(f"admin/realms/alma/users/{self.sub}"),
            json={
                "emailVerified": True,
                "attributes": {
                    "alma_role": self.role.name.value if self.role else "",
                },
                "firstName": self.first_name,
                "lastName": self.last_name,
                "email": self.email,
            },
        ).raise_for_status()
        db.commit()

    @classmethod
    def sync_from_keycloak(
        cls,
        db: Session,
        keycloak_client: httpx2.Client,
    ) -> None:
        """Sync users from Keycloak

        This method is intended for one-time use to populate the database with
        users from Keycloak. It will add new users and update the email address
        of existing users. It will not remove users from the database.
        """
        keycloak_users = keycloak_client.get(
            settings.oidc.keycloak_url("admin/realms/alma/users")
        ).json()
        existing_users = {
            user.username: user for user in db.execute(select(cls)).scalars()
        }
        new_users: list[User] = []
        for keycloak_user in keycloak_users:
            if user := existing_users.pop(keycloak_user["username"], None):
                if user.email != keycloak_user["email"]:
                    user.email = keycloak_user["email"]
                    logger.info(
                        "Updated email for user %s from %s to %s",
                        user.username,
                        user.email,
                        keycloak_user["email"],
                    )
            else:
                user = cls(
                    username=keycloak_user["username"],
                    email=keycloak_user["email"],
                    sub=keycloak_user["id"],
                )
                new_users.append(user)
                db.add(user)
        for user in existing_users.values():
            # From a data perspective we would need te recreate the user in Keycloak
            # but at this point the intention of removing a user is not clear:
            logger.error("User %s not found in Keycloak", user.username)
        logger.info(
            "Added %d new users: %s",
            len(new_users),
            [user.username for user in new_users],
        )


class OIDCSession(AuthBase):
    __tablename__ = "oidc_session"
    __table_args__ = {"schema": "alma_admin"}

    expires_at: Mapped[Timestamp]
    token: Mapped[str] = mapped_column(repr=False)
    user_id: Mapped[BigInt] = mapped_column(
        ForeignKey("alma_admin.auth_user.id", ondelete="CASCADE"), init=False
    )
    user: Mapped[User] = relationship(
        User, back_populates="oidc_sessions", lazy="joined"
    )
    session_key: Mapped[str] = mapped_column(
        unique=True,
        default_factory=token_urlsafe,
        init=False,
    )
