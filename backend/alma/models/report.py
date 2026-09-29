from enum import StrEnum, unique

from sqlalchemy import Column, Enum, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


@unique
class ReportContext(StrEnum):
    STANDORT = "STANDORT"
    DASHBOARD = "DASHBOARD"


@unique
class ReportExportFormat(StrEnum):
    PDF = "PDF"
    XLSX = "XLSX"


@unique
class ParamType(StrEnum):
    INTEGER = "INTEGER"
    BOOL = "BOOL"
    TEXT = "TEXT"
    DATE = "DATE"


report_sql_query_mapping_table = Table(
    "report_report_sql_query",
    Base.metadata,
    Column(
        "report_id",
        Integer,
        ForeignKey("alma_export.report.report_id"),
        primary_key=True,
    ),
    Column(
        "report_sql_query_id",
        Integer,
        ForeignKey("alma_export.report_sql_query.report_sql_query_id"),
        primary_key=True,
    ),
)
report_sql_query_mapping_table.schema = "alma_export"


class ReportQuery(Base):
    __tablename__ = "report_sql_query"
    __table_args__ = {"schema": "alma_export"}
    # Primary Keys
    report_sql_query_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Actual fields
    description: Mapped[str | None] = mapped_column(init=False)
    query: Mapped[str] = mapped_column(init=False)
    name: Mapped[str]
    is_translation_query: Mapped[bool] = mapped_column(init=False)
    worksheet_name: Mapped[str | None] = mapped_column(default=None)


class ReportParam(Base):
    __tablename__ = "report_param"
    __table_args__ = {"schema": "alma_export"}
    # Primary Keys
    param_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign Keys
    report_id: Mapped[int] = mapped_column(
        ForeignKey("alma_export.report.report_id"), init=False
    )

    # Relationships
    type: Mapped[ParamType] = mapped_column(Enum(ParamType, native_enum=False))

    # Actual fields
    sort_key: Mapped[str | None] = mapped_column(init=False)
    name: Mapped[str]


class Report(Base):
    __tablename__ = "report"
    __table_args__ = {"schema": "alma_export"}
    # Primary Keys
    report_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Relationships
    queries: Mapped[list[ReportQuery]] = relationship(
        ReportQuery,
        init=False,
        secondary=report_sql_query_mapping_table,
    )
    parameters: Mapped[list[ReportParam]] = relationship(
        init=False, cascade="all, delete-orphan", order_by=ReportParam.sort_key
    )

    # Actual fields
    title: Mapped[str] = mapped_column(init=False)
    template: Mapped[str] = mapped_column(init=False)
    style: Mapped[str] = mapped_column(init=False)
    context: Mapped[ReportContext] = mapped_column(
        Enum(ReportContext, native_enum=False), init=False
    )
    is_active: Mapped[bool] = mapped_column(init=False)
    export_format: Mapped[ReportExportFormat] = mapped_column(
        Enum(ReportExportFormat, native_enum=False), init=False
    )


class ReportExportOffset(Base):
    __tablename__ = "report_export_offset"
    __table_args__ = {"schema": "alma_external"}

    # Primary key
    report_export_offset_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Actual fields
    report_id: Mapped[int]
    last_vflz_id: Mapped[int]
