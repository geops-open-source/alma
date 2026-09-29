from enum import StrEnum, auto, unique
from typing import Any

DASHBOARD_SAVED_SEARCH_SETTINGS_KEY = "dashboardSavedSearches"


@unique
class MessageCode(StrEnum):
    """
    Message codes for parsing and validation errors.

    These codes reference entries in the UI translations catalog.
    If the translation message has placeholders these are mentioned in the
    comments next to each entry.
    """

    # Override generation for auto() to generate camelCase values (FooBar -> fooBar)
    # in line with our conventions for UI translations.
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> str:
        return name[0].lower() + name[1:]

    ExpectedClosingParenOrLogicalOperator = auto()  # args: context
    ExpectedOpeningParenOrName = auto()  # args: context
    ExpectedOperator = auto()  # args: context
    ExpectedValue = auto()  # args: context
    IncompleteExpression = auto()
    InternalError = auto()
    InvalidOperator = auto()  # args: field, context
    InvalidToken = auto()  # args: context
    InvalidValue = auto()  # args: field, context
    ParenNotClosed = auto()
    UnexpectedClosingParen = auto()  # args: context
    UnknownField = auto()  # args: context
    UnterminatedString = auto()  # args: context
