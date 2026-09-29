import json
from typing import Any, NewType

from strawberry import scalar

GeoJSONPoint = NewType("GeoJSONPoint", dict[str, Any])
GeoJSONMultiPolygon = NewType("GeoJSONMultiPolygon", dict[str, Any])
GeoJSONPointOrMultiPolygon = NewType("GeoJSONPointOrMultiPolygon", dict[str, Any])
GeoJSONFeatureCollection = NewType("GeoJSONFeatureCollection", dict[str, Any])
GeoJSONLineString = NewType("GeoJSONLineString", dict[str, Any])
JSONTranslation = NewType("JSONTranslation", dict[str, str])
FormularFelder = NewType("FormularFelder", dict[str, Any])
FormularEingaben = NewType("FormularEingaben", dict[str, Any])

GeoJSONPointScalar = scalar(
    name="GeoJSONPoint", serialize=lambda v: json.loads(v), parse_value=lambda v: v
)
GeoJSONMultiPolygonScalar = scalar(
    name="GeoJSONMultiPolygon",
    serialize=lambda v: json.loads(v),
    parse_value=lambda v: v,
)
GeoJSONPointOrMultiPolygonScalar = scalar(
    name="GeoJSONPointOrMultiPolygon",
    serialize=lambda v: json.loads(v),
    parse_value=lambda v: v,
)
GeoJSONFeatureCollectionScalar = scalar(
    name="GeoJSONFeatureCollection",
    serialize=lambda v: json.loads(v),
    parse_value=lambda v: v,
)
GeoJSONLineStringScalar = scalar(
    name="GeoJSONLineString",
    serialize=lambda v: json.loads(v),
    parse_value=lambda v: v,
)
JSONTranslationScalar = scalar(
    name="JSONTranslation",
    serialize=lambda v: v,
    parse_value=lambda v: json.loads(v),
)
FormularFelderScalar = scalar(
    name="FormularFelder", serialize=lambda v: v, parse_value=lambda v: v
)
FormularEingabenScalar = scalar(
    name="FormularEingaben", serialize=lambda v: v, parse_value=lambda v: v
)
