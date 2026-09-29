import shutil
import subprocess
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from itertools import count
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from geoalchemy2 import Geometry
from openpyxl import Workbook
from sqlalchemy import BigInteger, Column, MetaData, String, Table, text
from sqlalchemy.orm import Session

from alma.constants import LV_95_SRID, Language
from alma.models.search import SearchExport
from alma.search.core import FIELD_CONFIG, FieldType, SearchField
from alma.search.execution import (
    execute_advanced_search,
    execute_simple_search,
    get_result_page,
)
from alma.search.serialization import deserialize_query
from alma.search.translation import translate_search_field
from alma.settings import settings


class ExportFormat(StrEnum):
    EXCEL = auto()
    GEOPACKAGE = auto()
    SHAPEFILE = auto()


class ExportStatus(StrEnum):
    STARTED = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()


def _get_column(session: Session, field: SearchField, lang: Language) -> Column[Any]:
    translated_name = translate_search_field(session, field, lang=lang)
    match FIELD_CONFIG[field].type:
        case FieldType.TEXT | FieldType.CODE | FieldType.DATE | FieldType.BBOX:
            return Column(translated_name, String)
        case FieldType.NUMBER:
            return Column(translated_name, String)
        case FieldType.BOOL:
            return Column(translated_name, String)


def make_temp_table(
    session: Session, name: str, fields: list[SearchField], lang: Language
) -> tuple[Table, MetaData]:
    metadata = MetaData(schema="alma_export")
    columns = [Column("row_id", BigInteger)]
    for field_name in fields:
        columns.append(_get_column(session, field_name, lang=lang))
    columns.append(Column("geom", Geometry("Geometry", srid=LV_95_SRID)))
    table = Table(f"tmp_search_{name}", metadata, *columns)

    return (table, metadata)


def get_result_page_iter(
    session: Session,
    vflz_ids: Iterable[int],
    fields: Sequence[SearchField],
    sort_by: Sequence[tuple[SearchField, bool]] | None = None,
    lang: Language = Language.DE,
    translate_codes: bool = False,
    include_geoms: bool = False,
    per_page: int = 100,
) -> Iterator[list[dict[str, Any]]]:
    field_names: list[str] = ["row_id"]
    for field in fields:
        field_names.append(translate_search_field(session, field, lang=lang))
    if include_geoms:
        field_names.append("geom")
    for page_no in count(start=1):
        page = get_result_page(
            session,
            vflz_ids,
            fields=fields,
            sort_by=sort_by,
            lang=lang,
            translate_codes=translate_codes,
            include_geoms=include_geoms,
            page=page_no,
            per_page=per_page,
        )
        if not page.results:
            break
        yield [dict(zip(field_names, row)) for row in page.results]


@dataclass
class Command:
    command: list[str]
    cwd: str | None = None

    def run(self) -> int:
        return subprocess.check_call(self.command, cwd=self.cwd)


@dataclass
class GeoPackageExport:
    paged_results: Iterator[list[dict[str, Any]]]
    table: Table
    metadata: MetaData
    output_directory: Path
    output_file_path: str
    command: Command


@dataclass
class ShapefileExport:
    paged_results: Iterator[list[dict[str, Any]]]
    table: Table
    metadata: MetaData
    output_directory: Path
    output_file_path: str
    export_points_command: Command
    export_polygons_command: Command
    create_zip_command: Command


@dataclass
class ExcelExport:
    paged_results: Iterator[list[dict[str, Any]]]
    output_directory: Path
    output_file_path: str
    column_names: list[str]


Export = GeoPackageExport | ShapefileExport | ExcelExport


def delete_search_export(session: Session, search_export: SearchExport) -> None:
    output_directory = Path(settings.search_export_path) / search_export.export_id
    shutil.rmtree(output_directory, ignore_errors=True)

    session.delete(search_export.search)
    session.delete(search_export)


def get_export_for_saved_search(
    session: Session, search_export: SearchExport
) -> Export:
    search = search_export.search
    export_id = search_export.export_id
    export_format = ExportFormat(search_export.format)
    if not search.query:
        vflz_ids = execute_simple_search(session, search.query)
    else:
        parsed_query = deserialize_query(search.query)
        vflz_ids = execute_advanced_search(session, parsed_query)
    fields = [SearchField(f) for f in search.fields]
    results_iter = get_result_page_iter(
        session,
        vflz_ids,
        fields=fields,
        sort_by=[(SearchField(sb["field"]), sb["reverse"]) for sb in search.sort_by],
        lang=search_export.lang,
        translate_codes=True,
        include_geoms=True,
    )
    table, metadata = make_temp_table(
        session, name=export_id, fields=fields, lang=search_export.lang
    )

    export_root = Path(settings.search_export_path)
    output_directory = export_root / export_id
    dt = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    export_base_name = f"alma_search_{dt.strftime('%Y%m%d_%H%M')}"

    match export_format:
        case ExportFormat.EXCEL:
            return ExcelExport(
                paged_results=results_iter,
                output_directory=output_directory,
                output_file_path=str(output_directory / f"{export_base_name}.xlsx"),
                column_names=[
                    translate_search_field(session, field, lang=search_export.lang)
                    for field in fields
                ],
            )

        case ExportFormat.GEOPACKAGE:
            output_path = output_directory / f"{export_base_name}.gpkg"

            write_geopkg_command = Command(
                [
                    "ogr2ogr",
                    "-f",
                    "GPKG",
                    str(output_path),
                    settings.database.url,
                    "-sql",
                    f"select * from {table.schema}.{table.name}",
                    "-lco",
                    "GEOMETRY_NAME=geom",
                    "-nln",
                    "search_export",
                    "-progress",
                ]
            )

            return GeoPackageExport(
                paged_results=results_iter,
                output_directory=output_directory,
                output_file_path=str(output_path),
                table=table,
                metadata=metadata,
                command=write_geopkg_command,
            )

        case ExportFormat.SHAPEFILE:
            shapefile_directory = output_directory / export_base_name
            points_shapefile_path = shapefile_directory / "points.shp"
            polygon_shapefile_path = shapefile_directory / "polygons.shp"
            output_filename = f"{export_base_name}.zip"

            write_points_shapefile_command = Command(
                [
                    "ogr2ogr",
                    "-f",
                    "ESRI Shapefile",
                    str(points_shapefile_path),
                    settings.database.url,
                    "-sql",
                    f"select * from {table.schema}.{table.name} where ST_GeometryType(geom) != 'ST_MultiPolygon'",
                    "-lco",
                    "GEOMETRY_NAME=geom",
                    "-nln",
                    "search_export",
                    "-progress",
                ]
            )

            write_polygons_shapefile_command = Command(
                [
                    "ogr2ogr",
                    "-f",
                    "ESRI Shapefile",
                    str(polygon_shapefile_path),
                    settings.database.url,
                    "-sql",
                    f"select * from {table.schema}.{table.name} where ST_GeometryType(geom) = 'ST_MultiPolygon'",
                    "-lco",
                    "GEOMETRY_NAME=geom",
                    "-nln",
                    "search_export",
                    "-progress",
                ]
            )

            create_zip_command = Command(
                [
                    "zip",
                    "-r",
                    output_filename,
                    shapefile_directory.stem,
                ],
                cwd=str(output_directory),
            )

            return ShapefileExport(
                paged_results=results_iter,
                output_directory=shapefile_directory,
                output_file_path=str(output_directory / output_filename),
                table=table,
                metadata=metadata,
                export_points_command=write_points_shapefile_command,
                export_polygons_command=write_polygons_shapefile_command,
                create_zip_command=create_zip_command,
            )


def export_search_to_file(session: Session, export: Export) -> str:
    match export:
        case GeoPackageExport():
            export.output_directory.mkdir(parents=True)
            export.metadata.create_all(session.connection())
            try:
                for rows in export.paged_results:
                    session.execute(export.table.insert(), rows)
                session.commit()
                export.command.run()
            finally:
                export.metadata.drop_all(session.connection())
                session.commit()
        case ShapefileExport():
            export.output_directory.mkdir(parents=True)
            export.metadata.create_all(session.connection())
            try:
                for rows in export.paged_results:
                    session.execute(export.table.insert(), rows)
                session.commit()
                table = export.table
                points_count = session.execute(
                    text(
                        f"select count(*) from {table.schema}.{table.name} where ST_GeometryType(geom) != 'ST_MultiPolygon'"
                    )
                ).scalar_one()
                if points_count:
                    export.export_points_command.run()

                polygons_count = session.execute(
                    text(
                        f"select count(*) from {table.schema}.{table.name} where ST_GeometryType(geom) = 'ST_MultiPolygon'"
                    )
                ).scalar_one()
                if polygons_count:
                    export.export_polygons_command.run()

                export.create_zip_command.run()
            finally:
                export.metadata.drop_all(session.connection())
                session.commit()
        case ExcelExport():
            export.output_directory.mkdir(parents=True)
            workbook = Workbook()
            worksheet = workbook.active
            assert worksheet
            worksheet.append(export.column_names)
            for page in export.paged_results:
                for row in page:
                    row.pop("row_id")
                    row.pop("geom")
                    worksheet.append([v for _, v in row.items()])
            workbook.save(export.output_file_path)
    return export.output_file_path
