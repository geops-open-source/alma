import strawberry

from ..scalars import JSONTranslation


@strawberry.type
class TranslationTable:
    de: JSONTranslation
    fr: JSONTranslation
    it: JSONTranslation


@strawberry.input
class TranslationInput:
    de: str
    fr: str
    it: str


@strawberry.input
class UpdateTranslationInput:
    key: str
    translation: TranslationInput


@strawberry.type
class Translation:
    de: str | None
    fr: str | None
    it: str | None
