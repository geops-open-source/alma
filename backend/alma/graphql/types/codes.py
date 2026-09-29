from typing import TYPE_CHECKING, NewType, Self, cast

import strawberry
from sqlalchemy import select

from alma.constants import Language
from alma.models import codes as code_models
from alma.models import translations as translation_models

from ..utils.schema import Info, to_id
from .translations import Translation, TranslationInput


class _Code(str):
    __slots__ = ()

    @classmethod
    def from_db(cls, code: code_models.Code) -> Self:
        return cls(code)

    @classmethod
    def from_db_or_none(cls, code: code_models.Code | None) -> Self | None:
        return cls.from_db(code) if code is not None else None


CodeInputType = NewType("CodeInputType", str)


def serialize(v: CodeInputType) -> str:
    return cast(str, v)


def parse(v: str) -> CodeInputType:
    return cast(CodeInputType, v)


if TYPE_CHECKING:
    Code = _Code
    CodeInput = CodeInputType
else:
    Code = strawberry.scalar(_Code, serialize=str)
    CodeInput = strawberry.scalar(CodeInputType, serialize=serialize, parse_value=parse)


# `strawberry.scalar` returns a ScalarWrapper that does not allow access to the
# wrapped objects classmethods.
Code.from_db = _Code.from_db
Code.from_db_or_none = _Code.from_db_or_none


@strawberry.type
class CodeListEntry:
    code: Code
    is_active: bool
    sort_key: int | None

    @strawberry.field
    def bezeichnung(self, info: Info) -> Translation:
        session = info.context.db
        msg_id = str(self.code)

        de_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.DE,
            )
        ).one_or_none()
        fr_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.FR,
            )
        ).one_or_none()
        it_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.IT,
            )
        ).one_or_none()

        return Translation(de=de_translation, fr=fr_translation, it=it_translation)

    @classmethod
    def from_db(cls, obj: code_models.Code) -> Self:
        return cls(
            code=Code.from_db(obj), is_active=obj.is_active, sort_key=obj.sort_key
        )


@strawberry.type
class CodeList:
    _code_liste: strawberry.Private[code_models.CodeListe]
    cli_id: strawberry.ID

    @strawberry.field
    def bezeichnung(self, info: Info) -> Translation:
        session = info.context.db
        msg_id = f"codelist:{self.cli_id}"

        de_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.DE,
            )
        ).one_or_none()
        fr_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.FR,
            )
        ).one_or_none()
        it_translation = session.scalars(
            select(translation_models.Translation.value).where(
                translation_models.Translation.key == msg_id,
                translation_models.Translation.locale == Language.IT,
            )
        ).one_or_none()

        return Translation(de=de_translation, fr=fr_translation, it=it_translation)

    @strawberry.field
    def read_only(self, info: Info) -> bool:
        return self._code_liste.read_only

    @strawberry.field
    def entries(self, info: Info) -> list[CodeListEntry]:
        session = info.context.db
        active_codes = session.scalars(
            select(code_models.Code)
            .where(
                code_models.Code.c_cli_id == int(self.cli_id),
                code_models.Code.is_active,
            )
            .order_by(code_models.Code.sort_key, code_models.Code.code)
        ).all()
        inactive_codes = session.scalars(
            select(code_models.Code)
            .where(
                code_models.Code.c_cli_id == int(self.cli_id),
                ~code_models.Code.is_active,
            )
            .order_by(code_models.Code.code)
        ).all()

        return [CodeListEntry.from_db(code) for code in active_codes] + [
            CodeListEntry.from_db(code) for code in inactive_codes
        ]

    @classmethod
    def from_db(cls, obj: code_models.CodeListe) -> Self:
        return cls(
            _code_liste=obj,
            cli_id=to_id(obj.c_cli_id),
        )


@strawberry.input
class CreateCodeListEntryInput:
    cli_id: strawberry.ID
    code: CodeInput
    bezeichnung: TranslationInput
    sort_key: int | None
    is_active: bool


@strawberry.input
class UpdateCodeListEntryInput:
    code: CodeInput
    bezeichnung: TranslationInput
    sort_key: int | None
    is_active: bool


@strawberry.type
class PaginatedCodeListResult:
    num_pages: int
    num_results_total: int
    results: list[CodeList]
    page: int
    per_page: int


@strawberry.input
class UpdateCodeListInput:
    cli_id: strawberry.ID
    bezeichnung: TranslationInput


@strawberry.type
class KbsInfo:
    beurteilung: Code
    beurteilung_gruppe: Code
    color: str
    color_rgb: str | None
    belastet: bool

    @classmethod
    def from_db(cls, kbs_info: code_models.KbsInfo) -> Self:
        return cls(
            beurteilung=Code.from_db(kbs_info.beurteilung),
            beurteilung_gruppe=Code.from_db(kbs_info.beurteilung_gruppe),
            color=kbs_info.color,
            color_rgb=kbs_info.color_rgb,
            belastet=kbs_info.belastet,
        )
