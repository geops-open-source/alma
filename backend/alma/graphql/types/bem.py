from typing import Self

import strawberry

from alma.models import bem as bem_models

from .misc import ErfassungMutation


@strawberry.type
class Bemerkung:
    bem: str
    public: bool
    sort: int | None
    erfassung_mutation: ErfassungMutation

    @classmethod
    def from_db(cls, bemerkung: bem_models.BasisBemerkung) -> Self:
        return cls(
            bem=bemerkung.bem,
            public=bemerkung.public,
            sort=bemerkung.sort,
            erfassung_mutation=ErfassungMutation.from_db(bemerkung),
        )


@strawberry.input
class BemerkungInput:
    bem: str
