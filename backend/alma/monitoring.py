import ssl
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from logging import getLogger

import httpx2
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alma.models.task_status import TaskCategory, TaskStatus, TaskStatusEnum
from alma.settings import settings

logger = getLogger(__name__)


@contextmanager
def monitor_task_status(
    session: Session, unique_task_status_name: str, category: TaskCategory
) -> Iterator[None]:
    task_status = session.scalars(
        select(TaskStatus).where(TaskStatus.name == unique_task_status_name)
    ).one_or_none()
    if not task_status:
        task_status = TaskStatus(
            name=unique_task_status_name,
            category=category,
            last_update=datetime.now(tz=UTC),
            status=TaskStatusEnum.OK,
            detail="",
        )
    try:
        yield
        task_status.detail = ""
        task_status.status = TaskStatusEnum.OK
    except DBAPIError as e:
        # Rollback the failed transaction before updating task status
        session.rollback()
        task_status.detail = str(e)
        task_status.status = TaskStatusEnum.ERROR
        raise
    except Exception as e:
        task_status.detail = str(e)
        task_status.status = TaskStatusEnum.ERROR
        raise
    finally:
        session.add(task_status)
        task_status.last_update = datetime.now(tz=UTC)
        session.commit()


@dataclass
class GatheredTaskStatus:
    code: int
    message: str


def send_icinga_state(code: int, message: str, task_category: TaskCategory):
    url = settings.icinga_settings.url
    password = settings.icinga_settings.password
    ca_cert = settings.icinga_settings.ca_cert
    ignore_certs = settings.icinga_settings.ignore_certs
    additional_info = settings.icinga_settings.additional_info or ""
    proxy_url = settings.icinga_settings.proxy_url

    assert url and password

    username = f"alma-{settings.customer}-{task_category}"
    url = f"{url}{username}"
    payload = {
        "exit_status": code,
        "plugin_output": message.replace('"', r"\"")
        + f", {task_category}, {additional_info}",
    }
    client_kwargs = {}

    if not ignore_certs:
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(ca_cert)
        client_kwargs["verify"] = ctx
    if proxy_url:
        client_kwargs["proxy"] = proxy_url

    client = httpx2.Client(**client_kwargs)  # type: ignore
    response = client.post(
        url=url,
        headers={"Accept": "application/json"},
        auth=(username, password),
        json=payload,
    )
    response.raise_for_status()
    logger.info(
        "Sent code %s with message %s for task_category: %s",
        code,
        message,
        task_category,
    )


def gather_task_statuses(
    task_statuses: Sequence[TaskStatus],
) -> GatheredTaskStatus:
    update_cutoff = datetime.now(tz=UTC) - timedelta(
        days=settings.monitoring_settings.min_update_interval_in_days
    )
    task_statuses = [
        t
        for t in task_statuses
        if (
            t.last_update
            if t.last_update.tzinfo is not None
            else t.last_update.replace(tzinfo=UTC)
        )
        >= update_cutoff
    ]

    error_tasks = [t for t in task_statuses if t.status == TaskStatusEnum.ERROR]
    warning_tasks = [t for t in task_statuses if t.status == TaskStatusEnum.WARNING]
    ok_tasks = [t for t in task_statuses if t.status == TaskStatusEnum.OK]

    if error_tasks:
        gathered_status = GatheredTaskStatus(
            code=2,
            message=",".join(
                f"{t.name}: {t.detail}" or "" for t in error_tasks if t.detail
            ),
        )
    elif warning_tasks:
        gathered_status = GatheredTaskStatus(
            code=1,
            message=",".join(
                f"{t.name}: {t.detail}" or "" for t in warning_tasks if t.detail
            ),
        )
    elif ok_tasks:
        gathered_status = GatheredTaskStatus(code=0, message="ok")

    else:
        gathered_status = GatheredTaskStatus(
            code=2,
            message=f"No status could be found or no recent updates for {settings.monitoring_settings.min_update_interval_in_days} days are available.",
        )

    return gathered_status


def send_task_status(session: Session):
    import_task_statuses = session.scalars(
        select(TaskStatus).where(TaskStatus.category == TaskCategory.IMPORT)
    ).all()
    export_task_statuses = session.scalars(
        select(TaskStatus).where(TaskStatus.category == TaskCategory.EXPORT)
    ).all()
    application_task_statuses = session.scalars(
        select(TaskStatus).where(TaskStatus.category == TaskCategory.APPLICATION)
    ).all()

    gathered_import_task_status = gather_task_statuses(import_task_statuses)
    gathered_export_task_status = gather_task_statuses(export_task_statuses)
    gathered_application_task_status = gather_task_statuses(application_task_statuses)

    send_icinga_state(
        code=gathered_import_task_status.code,
        message=gathered_import_task_status.message,
        task_category=TaskCategory.IMPORT,
    )
    send_icinga_state(
        code=gathered_export_task_status.code,
        message=gathered_export_task_status.message,
        task_category=TaskCategory.EXPORT,
    )
    send_icinga_state(
        code=gathered_application_task_status.code,
        message=gathered_application_task_status.message,
        task_category=TaskCategory.APPLICATION,
    )
