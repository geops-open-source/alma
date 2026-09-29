import re
from typing import TypeAlias
from urllib.parse import urlsplit

import strawberry
from email_validator import EmailNotValidError, validate_email

from ..context import Context

Info: TypeAlias = strawberry.Info[Context, object]


def to_id(id: int) -> strawberry.ID:
    """
    Convert from database id to strawberry.ID
    """
    return strawberry.ID(str(id))


def valid_phone(phone: str) -> bool:
    # Valid formats:
    #   +xx xx xxx xx xx / 0xxx xxx xx xx
    #   0xxx xxx xxx
    #   0xxx xx xx xx
    #   +xxxxxxxxxx (+ and 11 digits)
    #   0xxxxxxxx (0 and 9 digits)
    PHONE_REGEX_PATTERNS = [
        re.compile(r"(\+\d{2} \d{2}|0\d{3}) \d{3} \d{2} \d{2}", re.ASCII),
        re.compile(r"0\d{3} \d{3} \d{3}", re.ASCII),
        re.compile(r"0\d{3} \d{2} \d{2} \d{2}", re.ASCII),
        re.compile(r"\+\d{11}", re.ASCII),
        re.compile(r"0\d{9}", re.ASCII),
    ]
    return any(p.fullmatch(phone.strip()) for p in PHONE_REGEX_PATTERNS)


def valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as _:
        return False
    return True


def valid_url(url: str) -> bool:
    split_result = urlsplit(url)
    return split_result.scheme in ["http", "https"] and split_result.hostname != ""
