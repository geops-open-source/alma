from collections.abc import Sequence

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Lang
from .mixins import ErfassungMutationMixin


class Translation(Base, ErfassungMutationMixin):
    __tablename__ = "translations"
    __table_args__ = {
        "schema": "alma",
    }

    key: Mapped[str] = mapped_column("msgid", primary_key=True)
    value: Mapped[str] = mapped_column("msgstr")
    locale: Mapped[Lang] = mapped_column(primary_key=True)


def to_formatted_dict(translations: Sequence[Translation]) -> dict[str, str]:
    """Convert sequence of translations in dict with (formatted) keys and values."""
    return {t.key: t.value for t in translations}
