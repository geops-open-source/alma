from pathlib import Path

import pytest
from freezegun import freeze_time
from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Session
from utils import make_code, make_translation, make_vflz

from alma.constants import Language
from alma.models import codes
from alma.models.auth import User
from alma.models.search import Search
from alma.search.core import SearchField
from alma.search.export import (
    Command,
    ExportFormat,
    GeoPackageExport,
    SearchExport,
    ShapefileExport,
    get_export_for_saved_search,
    get_result_page_iter,
    make_temp_table,
)
from alma.settings import settings

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
]


def test_make_temp_table(session: Session):
    table, _ = make_temp_table(
        session,
        "export001",
        [SearchField.VFLZ_ID, SearchField.BEZEICHNUNG],
        lang=Language.DE,
    )

    columns = [(c.name, type(c.type)) for c in table.columns]

    assert table.schema == "alma_export"
    assert table.name == "tmp_search_export001"
    assert columns == [
        ("row_id", BigInteger),
        ("vflz_id", String),
        ("Bezeichnung", String),
        ("geom", Geometry),
    ]


def test_get_result_page_iter(session: Session):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    code = make_code(session, codes.StandortTyp, "a-1")
    vflz1.vftyp = code
    vflz2.vftyp = code
    make_translation(session, Language.DE, str(code), "a-1-de")
    make_translation(session, Language.FR, str(code), "a-1-fr")

    page_iter_de = get_result_page_iter(
        session,
        {vflz1.vflz_id, vflz2.vflz_id},
        fields=[SearchField.VFLZ_ID, SearchField.BEZEICHNUNG, SearchField.STANDORTTYP],
        lang=Language.DE,
        translate_codes=True,
        per_page=1,
    )
    page_iter_fr = get_result_page_iter(
        session,
        {vflz1.vflz_id, vflz2.vflz_id},
        fields=[SearchField.VFLZ_ID, SearchField.BEZEICHNUNG, SearchField.STANDORTTYP],
        lang=Language.FR,
        translate_codes=True,
        per_page=1,
    )

    assert list(page_iter_de) == [
        [
            {
                "row_id": 1,
                "vflz_id": vflz1.vflz_id,
                "Bezeichnung": "Standort A",
                "Standorttyp": "a-1-de",
            },
        ],
        [
            {
                "row_id": 2,
                "vflz_id": vflz2.vflz_id,
                "Bezeichnung": "Standort B",
                "Standorttyp": "a-1-de",
            },
        ],
    ]

    assert list(page_iter_fr) == [
        [
            {
                "row_id": 1,
                "vflz_id": vflz1.vflz_id,
                "Désignation": "Standort A",
                "Type-de-site": "a-1-fr",
            },
        ],
        [
            {
                "row_id": 2,
                "vflz_id": vflz2.vflz_id,
                "Désignation": "Standort B",
                "Type-de-site": "a-1-fr",
            },
        ],
    ]


@freeze_time("2020-12-31 02:32:02")
def test_get_export_from_saved_search_geopackage(session: Session, test_user: User):
    search = Search(
        name="export0001",
        is_temporary=True,
        user=test_user,
        query=[
            {
                "__type__": "expression",
                "name": "bezeichnung",
                "operator": "~",
                "value": "test",
            }
        ],
        fields=["bezeichnung"],
        sort_by=[{"field": "bezeichnung", "reverse": False}],
    )
    search_export = SearchExport(
        export_id="export0001",
        format=ExportFormat.GEOPACKAGE,
        lang=Language.DE,
        user=test_user,
        search=search,
    )
    session.add(search_export)
    session.flush()

    export = get_export_for_saved_search(session, search_export)

    assert isinstance(export, GeoPackageExport)
    assert export.table.name == "tmp_search_export0001"
    assert export.output_directory == Path("/app/exports/search/export0001")
    assert export.command == Command(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            # Note: time includes +1h TZ offset
            "/app/exports/search/export0001/alma_search_20201231_0332.gpkg",
            settings.database.url,
            "-sql",
            "select * from alma_export.tmp_search_export0001",
            "-lco",
            "GEOMETRY_NAME=geom",
            "-nln",
            "search_export",
            "-progress",
        ]
    )


@freeze_time("2020-12-31 02:32:02")
def test_get_export_from_saved_search_shapefile(session: Session, test_user: User):
    search = Search(
        name="export0001",
        is_temporary=True,
        user=test_user,
        query=[
            {
                "__type__": "expression",
                "name": "bezeichnung",
                "operator": "~",
                "value": "test",
            }
        ],
        fields=["bezeichnung"],
        sort_by=[{"field": "bezeichnung", "reverse": False}],
    )
    search_export = SearchExport(
        export_id="export0001",
        format=ExportFormat.SHAPEFILE,
        lang=Language.DE,
        user=test_user,
        search=search,
    )
    session.add(search_export)
    session.flush()

    export = get_export_for_saved_search(session, search_export)

    assert isinstance(export, ShapefileExport)
    assert export.table.name == "tmp_search_export0001"
    # Note: time includes +1h TZ offset
    assert export.output_directory == Path(
        "/app/exports/search/export0001/alma_search_20201231_0332"
    )
    assert export.export_points_command == Command(
        [
            "ogr2ogr",
            "-f",
            "ESRI Shapefile",
            # Note: time includes +1h TZ offset
            "/app/exports/search/export0001/alma_search_20201231_0332/points.shp",
            settings.database.url,
            "-sql",
            "select * from alma_export.tmp_search_export0001 where ST_GeometryType(geom) != 'ST_MultiPolygon'",
            "-lco",
            "GEOMETRY_NAME=geom",
            "-nln",
            "search_export",
            "-progress",
        ]
    )
    assert export.export_polygons_command == Command(
        [
            "ogr2ogr",
            "-f",
            "ESRI Shapefile",
            # Note: time includes +1h TZ offset
            "/app/exports/search/export0001/alma_search_20201231_0332/polygons.shp",
            settings.database.url,
            "-sql",
            "select * from alma_export.tmp_search_export0001 where ST_GeometryType(geom) = 'ST_MultiPolygon'",
            "-lco",
            "GEOMETRY_NAME=geom",
            "-nln",
            "search_export",
            "-progress",
        ]
    )

    assert export.create_zip_command == Command(
        ["zip", "-r", "alma_search_20201231_0332.zip", "alma_search_20201231_0332"],
        cwd="/app/exports/search/export0001",
    )
