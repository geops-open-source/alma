import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx2
from sqlalchemy import select, sql
from sqlalchemy.orm import Session

from alma.db import get_session
from alma.models import report as report_models
from alma.models import task_status as task_status_models
from alma.models import vflz as vflz_models
from alma.monitoring import monitor_task_status
from alma.reports import render_report
from alma.search.export import (
    ExportStatus,
    SearchExport,
    export_search_to_file,
    get_export_for_saved_search,
)
from alma.settings import ReportExportType, settings

from .app import app

logger = logging.getLogger(__name__)


@app.task(name="export_search")
def export_search(search_export_id: int) -> None:
    with get_session() as session:
        search_export = session.get_one(SearchExport, search_export_id)
        search_export.status = ExportStatus.RUNNING
        session.commit()
        try:
            export = get_export_for_saved_search(session, search_export)
            file_path = export_search_to_file(session, export)
            search_export.path = file_path
            search_export.status = ExportStatus.SUCCESS
        except Exception as e:
            logger.exception(
                "Export for export_id %s failed: %s", search_export.export_id, e
            )
            search_export.status = ExportStatus.ERROR
        finally:
            search_export.finished_at = datetime.now()
            session.commit()


def create_report(
    report: report_models.Report,
    session: Session,
    vflz_id: int,
    export_path: str,
    report_type: ReportExportType,
) -> None:
    vflz = session.get_one(vflz_models.Vflz, vflz_id)
    filename = session.execute(
        sql.text(
            "select filename from alma_export.vflz_filename_v where vflz_id=:vflz_id"
        ),
        params={"vflz_id": vflz.vflz_id},
    ).scalar_one()
    export_file = Path(export_path) / filename
    match report_type:
        case ReportExportType.PUBLISHED:
            params = {
                "vflz_id": vflz.vflz_id,
                "date": datetime.today().date(),
                "language": vflz.lang,
            }
    pdf_bytes = render_report(session, report, language=vflz.lang, params=params)
    export_file.write_bytes(pdf_bytes or b"")


@app.task(name="update_report")
def update_report(vflz_id: int) -> None:
    with get_session() as session:
        if not settings.report_export_settings.report_id:
            logger.warning(
                "Requested to update report of vflz with id %s, but no report id provided. Doing nothing.",
                vflz_id,
            )
            return
        report = session.get_one(
            report_models.Report, settings.report_export_settings.report_id
        )
        create_report(
            report,
            session,
            vflz_id,
            settings.report_export_settings.export_path,
            settings.report_export_settings.type,
        )


@app.task(name="update_all_reports", queueing_lock="update_all_reports")
def update_all_reports(timestamp: int):
    with (
        get_session() as session,
        monitor_task_status(
            session, "update_all_reports", task_status_models.TaskCategory.EXPORT
        ),
    ):
        if not settings.report_export_settings.report_id:
            logger.warning(
                "Requested to update all reports, but no settings provided. Doing nothing."
            )
            return
        report = session.get_one(
            report_models.Report, settings.report_export_settings.report_id
        )
        batch_size = settings.report_export_settings.batch_size
        report_export_offset = session.scalars(
            select(report_models.ReportExportOffset).where(
                report_models.ReportExportOffset.report_id == report.report_id
            )
        ).one_or_none()

        if not report_export_offset:
            report_export_offset = report_models.ReportExportOffset(
                report_id=report.report_id, last_vflz_id=0
            )
            session.add(report_export_offset)

        vflz_ids = session.scalars(
            sql.text(
                "select vflz_id asc from alma.vflz_is_published_v where is_latest_published=true and vflz_id >= :last_vflz_id limit :limit;"
            ),
            params={
                "last_vflz_id": report_export_offset.last_vflz_id,
                "limit": batch_size,
            },
        ).all()

        highest_vflz_id = session.scalars(
            sql.text(
                "select max(vflz_id) from alma.vflz_is_published_v where is_latest_published=true;"
            )
        ).one()

        for vflz_id in vflz_ids:
            create_report(
                report,
                session,
                vflz_id,
                settings.report_export_settings.export_path,
                settings.report_export_settings.type,
            )

        # we reached the end of the vflz ids -> start from the beginning
        if vflz_ids and vflz_ids[-1] == highest_vflz_id:
            report_export_offset.last_vflz_id = 0
        else:
            report_export_offset.last_vflz_id = vflz_ids[-1]
        response = httpx2.post(
            url=urljoin(
                str(settings.monitoring_settings.screenshot_service_url),
                "restart_browser",
            )
        )
        response.raise_for_status()
        session.commit()
