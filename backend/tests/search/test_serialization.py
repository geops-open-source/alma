from datetime import datetime

import pytest
from sqlalchemy.orm import Session
from utils import make_code

from alma.models import codes
from alma.search.core import FieldType, SearchField
from alma.search.parser import ValueType
from alma.search.serialization import (
    deserialize_query,
    deserialize_value,
    serialize_query,
    serialize_value,
)
from alma.search.validation import Op, TranslatedExpression


def test_serialize_query_to_dict(session: Session):
    make_code(session, codes.StandortTyp, "A")
    query = [
        TranslatedExpression(
            name=SearchField.BEZEICHNUNG, operator="~", value="test-standort"
        ),
        Op("AND"),
        TranslatedExpression(
            name=SearchField.STANDORTTYP, operator="=", value="code:63:A"
        ),
        Op("OR"),
        TranslatedExpression(name=SearchField.IN_BETRIEB, operator="=", value=True),
    ]

    assert serialize_query(query) == [
        {
            "__type__": "expression",
            "name": SearchField.BEZEICHNUNG.value,
            "operator": "~",
            "value": "test-standort",
        },
        {"__type__": "operator", "operator": "AND"},
        {
            "__type__": "expression",
            "name": SearchField.STANDORTTYP.value,
            "operator": "=",
            "value": "code:63:A",
        },
        {"__type__": "operator", "operator": "OR"},
        {
            "__type__": "expression",
            "name": SearchField.IN_BETRIEB.value,
            "operator": "=",
            "value": "1",
        },
    ]


def test_deserialize_query_from_Dict(session: Session):
    make_code(session, codes.StandortTyp, "A")
    serialized_query = [
        {
            "__type__": "expression",
            "name": SearchField.BEZEICHNUNG.value,
            "operator": "~",
            "value": "test-standort",
        },
        {"__type__": "operator", "operator": "AND"},
        {
            "__type__": "expression",
            "name": SearchField.STANDORTTYP.value,
            "operator": "=",
            "value": "code:63:A",
        },
        {"__type__": "operator", "operator": "OR"},
        {
            "__type__": "expression",
            "name": SearchField.IN_BETRIEB.value,
            "operator": "=",
            "value": "1",
        },
    ]

    assert deserialize_query(serialized_query) == [
        TranslatedExpression(
            name=SearchField.BEZEICHNUNG, operator="~", value="test-standort"
        ),
        Op("AND"),
        TranslatedExpression(
            name=SearchField.STANDORTTYP, operator="=", value="code:63:A"
        ),
        Op("OR"),
        TranslatedExpression(name=SearchField.IN_BETRIEB, operator="=", value=True),
    ]


@pytest.mark.parametrize(
    ("value", "field_type", "serialized"),
    [
        ("foo", FieldType.TEXT, "foo"),
        ("code:63:a", FieldType.CODE, "code:63:a"),
        (True, FieldType.BOOL, "1"),
        (False, FieldType.BOOL, "0"),
        (123, FieldType.NUMBER, "123"),
        (-123, FieldType.NUMBER, "-123"),
        (-123, FieldType.NUMBER, "-123"),
        (datetime(2025, 12, 1), FieldType.DATE, "2025-12-01T00:00:00"),
        ([0, 0, 1, 1], FieldType.BBOX, "0,0,1,1"),
    ],
)
def test_roundtrip_value(value: ValueType, field_type: FieldType, serialized: str):
    assert serialize_value(value) == serialized
    assert deserialize_value(serialized, field_type) == value
