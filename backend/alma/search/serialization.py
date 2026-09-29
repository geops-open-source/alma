from datetime import datetime

from alma.search.advanced import ParsedQuery, TranslatedExpression
from alma.search.core import FIELD_CONFIG, FieldType, SearchField
from alma.search.parser import Op, ValueType


class DeserializationError(ValueError):
    pass


def serialize_query(query: ParsedQuery) -> list[dict[str, str]]:
    """
    Serialize a parsed query into a JSON-compatible data structure.
    """
    result: list[dict[str, str]] = []
    for item in query:
        match item:
            case TranslatedExpression(field_name, operator, value):
                result.append(
                    {
                        "__type__": "expression",
                        "name": field_name.value,
                        "operator": operator,
                        "value": serialize_value(value),
                    }
                )
            case Op():
                result.append(
                    {
                        "__type__": "operator",
                        "operator": item.value,
                    }
                )
    return result


def deserialize_query(serialized_query: list[dict[str, str]]) -> ParsedQuery:
    """
    Load a parsed query from its serialized representation.
    """
    result: ParsedQuery = []
    for item in serialized_query:
        match item["__type__"]:
            case "expression":
                field_name = SearchField(item["name"])
                field_type = FIELD_CONFIG[field_name].type
                result.append(
                    TranslatedExpression(
                        name=field_name,
                        operator=item["operator"],
                        value=deserialize_value(item["value"], field_type),
                    )
                )
            case "operator":
                result.append(Op(item["operator"]))
            case _ as item_type:
                raise DeserializationError(
                    f"Unexpected __type__ in serialized query: {item_type!r}"
                )

    return result


def serialize_value(value: ValueType) -> str:
    match value:
        case bool():
            return str(int(value))
        case int():
            return str(value)
        case str():
            return value
        case datetime():
            return value.isoformat()
        case list():
            assert all(isinstance(x, int) for x in value)
            return ",".join(str(el) for el in value)


def deserialize_value(serialized_value: str, field_type: FieldType) -> ValueType:
    match field_type:
        case FieldType.TEXT:
            return serialized_value
        case FieldType.CODE:
            return serialized_value
        case FieldType.NUMBER:
            return int(serialized_value)
        case FieldType.DATE:
            return datetime.fromisoformat(serialized_value)
        case FieldType.BOOL:
            return bool(int(serialized_value))
        case FieldType.BBOX:
            return [int(x) for x in serialized_value.split(",")]
