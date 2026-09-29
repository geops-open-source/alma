from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete, select, sql
from sqlalchemy.exc import IntegrityError
from utils import make_task_status, make_vflz

from alma.models.task_status import TaskCategory, TaskStatus, TaskStatusEnum
from alma.monitoring import (
    GatheredTaskStatus,
    gather_task_statuses,
    monitor_task_status,
    send_icinga_state,
)
from alma.settings import settings
from alma.task_queue.schedules import send_task_status

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes"),
]


def test_sending_task_status_to_icinga(httpx2_mock, test_settings):
    settings.icinga_settings.url = "https://example.com?service=external!"
    settings.icinga_settings.password = "password"
    settings.customer = "test_customer"
    settings.icinga_settings.additional_info = "additional_info"

    code = 2
    message = "Something went wrong"
    task_category = TaskCategory.IMPORT

    httpx2_mock.add_response(
        method="POST",
        url="https://example.com?service=external!alma-test_customer-import",
        match_content=b'{"exit_status":2,"plugin_output":"Something went wrong, import, additional_info"}',
    )
    send_icinga_state(code, message, task_category)


@pytest.mark.parametrize(
    "task_statuses, gathered_task_status",
    [
        (
            [
                TaskStatus(
                    category=TaskCategory.IMPORT,
                    last_update=datetime.now(),
                    status=TaskStatusEnum.ERROR,
                    detail="error1",
                    name="import1",
                ),
                TaskStatus(
                    category=TaskCategory.IMPORT,
                    last_update=datetime.now(),
                    status=TaskStatusEnum.ERROR,
                    detail="error2",
                    name="import2",
                ),
            ],
            GatheredTaskStatus(code=2, message="import1: error1,import2: error2"),
        ),
        (
            [
                TaskStatus(
                    category=TaskCategory.EXPORT,
                    last_update=datetime.now(),
                    status=TaskStatusEnum.ERROR,
                    detail="error",
                    name="export1",
                ),
                TaskStatus(
                    category=TaskCategory.EXPORT,
                    last_update=datetime.now(),
                    status=TaskStatusEnum.WARNING,
                    detail="warning",
                    name="export2",
                ),
            ],
            GatheredTaskStatus(code=2, message="export1: error"),
        ),
        (
            [],
            GatheredTaskStatus(
                code=2,
                message="No status could be found or no recent updates for 7 days are available.",
            ),
        ),
    ],
)
def test_gathering_status(task_statuses, gathered_task_status):
    assert gather_task_statuses(task_statuses) == gathered_task_status


def test_gathering_status_excludes_status_older_than_update_interval(monkeypatch):
    monkeypatch.setattr(settings.monitoring_settings, "min_update_interval_in_days", 7)
    task_status = TaskStatus(
        category=TaskCategory.IMPORT,
        last_update=datetime.now() - timedelta(days=9),
        status=TaskStatusEnum.ERROR,
        detail="error",
        name="import1",
    )

    assert gather_task_statuses([task_status]) == GatheredTaskStatus(
        code=2,
        message="No status could be found or no recent updates for 7 days are available.",
    )


def test_gathering_status_includes_status_within_update_interval(monkeypatch):
    monkeypatch.setattr(settings.monitoring_settings, "min_update_interval_in_days", 7)
    task_status = TaskStatus(
        category=TaskCategory.IMPORT,
        last_update=datetime.now() - timedelta(days=6),
        status=TaskStatusEnum.ERROR,
        detail="error",
        name="import1",
    )

    assert gather_task_statuses([task_status]) == GatheredTaskStatus(
        code=2, message="import1: error"
    )


def test_sending_task_status(session, test_settings, httpx2_mock):
    session.execute(delete(TaskStatus))
    settings.icinga_settings.url = "https://example.com?service=external!"
    settings.icinga_settings.password = "password"
    settings.icinga_settings.additional_info = "additional_info"
    settings.customer = "test_customer"

    httpx2_mock.add_response(
        method="POST",
        url="https://example.com?service=external!alma-test_customer-import",
        match_content=b'{"exit_status":0,"plugin_output":"ok, import, additional_info"}',
    )
    httpx2_mock.add_response(
        method="POST",
        url="https://example.com?service=external!alma-test_customer-export",
        match_content=b'{"exit_status":2,"plugin_output":"export_task1: Something went wrong on export, export, additional_info"}',
    )
    httpx2_mock.add_response(
        method="POST",
        url="https://example.com?service=external!alma-test_customer-application",
        match_content=b'{"exit_status":2,"plugin_output":"application_task1: Something went wrong in the application, application, additional_info"}',
    )

    import_task = make_task_status(
        session, TaskStatusEnum.OK, TaskCategory.IMPORT, "import_task1"
    )
    import_task.detail = ""
    export_task = make_task_status(
        session, TaskStatusEnum.ERROR, TaskCategory.EXPORT, "export_task1"
    )
    export_task.detail = "Something went wrong on export"

    application_task = make_task_status(
        session, TaskStatusEnum.ERROR, TaskCategory.APPLICATION, "application_task1"
    )
    application_task.detail = "Something went wrong in the application"

    session.commit()
    send_task_status(session)


def test_monitor_task_status_with_db_error_rollbacks_session(session):
    task_name = "test_task_with_error"
    vflz = make_vflz(session, "My Site")
    assert not session.scalars(
        select(TaskStatus).where(TaskStatus.name == task_name)
    ).one_or_none()
    vflz.bezeichnung = "My new Site"  # update to make session dirty

    with (
        pytest.raises(IntegrityError),
        monitor_task_status(session, task_name, TaskCategory.APPLICATION),
    ):
        session.execute(sql.text("insert into alma.vflz (vflz_id) values (3);"))
        session.execute(
            sql.text("insert into alma.vflz (vflz_id) values (4);")
        )  # This will raise an InFailedSqlTransaction by psycopg2 (if session not rolled back), since the previous insert failed3
        session.commit()
    # Verify that the task status was written to the database despite the error
    task_status = session.scalars(
        select(TaskStatus).where(TaskStatus.name == task_name)
    ).one()

    assert vflz.bezeichnung == "My Site"
    assert task_status.status == TaskStatusEnum.ERROR
    assert task_status.category == TaskCategory.APPLICATION
    assert task_status.name == task_name


def test_monitor_task_status_without_db_error_does_not_rollback_session(session):
    task_name = "test_task_with_error"
    vflz = make_vflz(session, "My Site")
    vflz.bezeichnung = "My new Site"  # update to make session dirty

    assert session.dirty
    assert not session.scalars(
        select(TaskStatus).where(TaskStatus.name == task_name)
    ).one_or_none()

    with (
        pytest.raises(ValueError),
        monitor_task_status(session, task_name, TaskCategory.APPLICATION),
    ):
        raise ValueError("Foo")
    assert vflz.bezeichnung == "My new Site"

    # Verify that the task status was written to the database despite the error
    task_status = session.scalars(
        select(TaskStatus).where(TaskStatus.name == task_name)
    ).one()

    assert task_status.status == TaskStatusEnum.ERROR
    assert task_status.category == TaskCategory.APPLICATION
    assert task_status.name == task_name


def test_monitor_task_status_success(session):
    task_name = "test_task_success"
    vflz = make_vflz(session, "My Site")
    vflz.bezeichnung = "My new Site"
    with monitor_task_status(session, task_name, TaskCategory.APPLICATION):
        # Simulate successful execution
        pass

    # Verify that the task status was written with OK status
    task_status = session.scalars(
        select(TaskStatus).where(TaskStatus.name == task_name)
    ).one()

    assert vflz.bezeichnung == "My new Site"

    assert task_status.status == TaskStatusEnum.OK
    assert task_status.detail == ""
    assert task_status.category == TaskCategory.APPLICATION


def test_exception_is_reraised_by_monitoring(session):
    task_name = "test_task_reraise"
    with (
        pytest.raises(ValueError, match="Test exception"),
        monitor_task_status(session, task_name, TaskCategory.APPLICATION),
    ):
        raise ValueError("Test exception")
