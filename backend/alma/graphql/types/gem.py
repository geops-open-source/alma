from typing import Self

import strawberry

from alma.models import gem as gem_models

from ..utils.schema import to_id
from .codes import Code


@strawberry.type
class Gemeinde:
    h_gem_id: strawberry.ID
    bfs_nummer: int | None
    gemeinde: str
    kanton: Code | None

    @strawberry.field
    def display_value(self) -> str:
        return (
            f"{self.gemeinde} ({self.bfs_nummer:0>4})"
            if self.bfs_nummer
            else self.gemeinde
        )

    @classmethod
    def from_db(cls, gemeinde: gem_models.Gemeinde) -> Self:
        return cls(
            h_gem_id=to_id(gemeinde.h_gem_id),
            bfs_nummer=gemeinde.bfs_nummer,
            gemeinde=gemeinde.gemeinde,
            kanton=Code.from_db_or_none(gemeinde.kanton),
        )


@strawberry.input
class GemeindeInput:
    h_gem_id: strawberry.ID
