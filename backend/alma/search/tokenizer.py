import re
from dataclasses import dataclass
from enum import Enum, auto, unique


class InvalidToken(Exception):
    def __init__(self, token: str):
        super().__init__(f"Invalid token: {token!r}")
        self.token = token


@unique
class TokenType(Enum):
    """
    Types of tokens that make up a search string.
    """

    WS = auto()
    NAME = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_MATCH = auto()
    OP_GT = auto()
    OP_GTE = auto()
    OP_LT = auto()
    OP_LTE = auto()
    STR = auto()
    BOOL_TRUE = auto()
    BOOL_FALSE = auto()
    STR_PREFIX = auto()
    INT = auto()
    DATE_DMY = auto()
    DATE_YMD = auto()
    AND = auto()
    OR = auto()
    LPAREN = auto()
    RPAREN = auto()
    LIST_INT = auto()


T = TokenType

# Defines the patterns for each token. Patterns are matched incrementally
# against the current position in the search string.
# Order matters here: More specialized patterns need to appear before more general ones,
# or they will never match.
TOKENS = [
    (re.compile(r"\s+"), T.WS),
    (re.compile(r"AND\b", re.I), T.AND),
    (re.compile(r"OR\b", re.I), T.OR),
    (re.compile(r"TRUE\b", re.I), T.BOOL_TRUE),
    (re.compile(r"FALSE\b", re.I), T.BOOL_FALSE),
    (re.compile(r"="), T.OP_EQ),
    (re.compile(r"!="), T.OP_NE),
    (re.compile(r"~"), T.OP_MATCH),
    (re.compile(r">="), T.OP_GTE),
    (re.compile(r"<="), T.OP_LTE),
    (re.compile(r">"), T.OP_GT),
    (re.compile(r"<"), T.OP_LT),
    (re.compile(r"\d{4}-\d{1,2}-\d{1,2}"), T.DATE_YMD),
    (re.compile(r"\d{1,2}\.\d{1,2}\.\d{4}"), T.DATE_DMY),
    (re.compile(r"(?:\d+,\s*)+\d+"), T.LIST_INT),
    (re.compile(r"\d+"), T.INT),
    (re.compile(r'"[^"]+"'), T.STR),
    (re.compile(r'"[^"]*'), T.STR_PREFIX),
    (re.compile(r"\("), T.LPAREN),
    (re.compile(r"\)"), T.RPAREN),
    (re.compile(r"\w[\w'/\.-]*"), T.NAME),
]


@dataclass
class Token:
    type: TokenType
    value: str

    def __str__(self) -> str:
        return f"{self.type.name} ({self.value!r})"


class Tokenizer:
    """
    Generate tokens from the input text.
    """

    def __init__(self, input: str):
        self.input = input
        self.pos = 0

    def get_next_token(self) -> Token | None:
        """
        Request the next token.
        """
        if self.pos >= len(self.input):
            return None

        for regexp, token_type in TOKENS:
            if m := regexp.match(self.input, pos=self.pos):
                value = m.group()
                self.pos += len(value)
                return Token(token_type, value)

        raise InvalidToken(self.input[self.pos :])
