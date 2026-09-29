from typing import Any

import pytest
from pytest import raises as assert_raises
from sqlalchemy.orm import Session
from utils import QueryError

from alma.models import admin as admin_models

# Run all tests in this module using the admin role unless otherwise specified
pytestmark = [
    pytest.mark.usefixtures("as_bearbeiten_sachdaten"),
]


def make_instance_setting(
    session: Session,
    key: str,
    value: dict[str, Any],
    category: admin_models.SettingCategory = admin_models.SettingCategory.GENERAL,
):
    db_setting = admin_models.InstanceSetting(
        key=key, value=value, category=category, value_schema={"type": "string"}
    )
    session.add(db_setting)
    session.commit()

    return db_setting


def test_reading_instance_settings(session, run_query):
    make_instance_setting(session=session, key="foo key", value={"val": "foo value"})
    query = """{
        instanceSettings {
            key
            value
            category
        }
    }
    """

    result = run_query(query)
    assert result.data == {
        "instanceSettings": [
            {"key": "foo key", "value": {"val": "foo value"}, "category": "GENERAL"}
        ]
    }


def test_update_existing_setting(session, run_query):
    make_instance_setting(session=session, key="foo", value={})
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: GENERAL}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    result = run_query(mutation)

    assert result.data == {"updateInstanceSetting": {"key": "foo", "value": "foo val"}}


def test_update_existing_admin_setting(session, run_query, as_admin):
    make_instance_setting(
        session=session,
        key="foo",
        value={},
        category=admin_models.SettingCategory.ADMIN,
    )
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: ADMIN}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    result = run_query(mutation)

    assert result.data == {"updateInstanceSetting": {"key": "foo", "value": "foo val"}}


def test_reading_user_initial_instance_settings(session, run_query):
    make_instance_setting(
        session=session,
        key="foo key",
        value={"val": "foo value"},
        category=admin_models.SettingCategory.USER_INITIAL,
    )
    query = """{
        instanceSettings {
            key
            value
            category
        }
    }
    """

    result = run_query(query)
    assert result.data == {
        "instanceSettings": [
            {
                "key": "foo key",
                "value": {"val": "foo value"},
                "category": "USER_INITIAL",
            }
        ]
    }


def test_update_existing_user_initial_setting(session, run_query, as_admin):
    make_instance_setting(
        session=session,
        key="foo",
        value={},
        category=admin_models.SettingCategory.USER_INITIAL,
    )
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: USER_INITIAL}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    result = run_query(mutation)

    assert result.data == {"updateInstanceSetting": {"key": "foo", "value": "foo val"}}


def test_update_setting_that_does_not_exist_returns_error(run_query):
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: GENERAL}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    with assert_raises(QueryError, match="No row was found"):
        run_query(mutation)


def test_update_setting_with_only_view_permissions_not_allowed(
    run_query, session, as_lesen_sachdaten
):
    make_instance_setting(session=session, key="foo", value={})
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:{val: "foo val"}, category: GENERAL}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    with assert_raises(QueryError, match="user is not allowed"):
        run_query(mutation)


def test_update_admin_setting_not_allowed_with_bearbeiten_sachdaten(
    run_query, session, as_bearbeiten_sachdaten
):
    make_instance_setting(session=session, key="foo", value={})
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: ADMIN}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    with assert_raises(QueryError, match="user is not allowed"):
        run_query(mutation)


def test_update_user_initial_setting_not_allowed_with_bearbeiten_sachdaten(
    run_query, session, as_bearbeiten_sachdaten
):
    make_instance_setting(
        session=session,
        key="foo",
        value={},
        category=admin_models.SettingCategory.USER_INITIAL,
    )
    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value:"foo val", category: USER_INITIAL}) {
            ... on InstanceSetting {
                key
                value
            }
        }
    }
    """
    with assert_raises(QueryError, match="user is not allowed"):
        run_query(mutation)


def test_invalid_value_returns_problem_group(run_query, session, as_admin):
    instance_setting = make_instance_setting(session=session, key="foo", value={})
    instance_setting.value_schema = {"type": "integer"}

    mutation = """
    mutation {
        updateInstanceSetting(data: {key:"foo", value: "foo", category: GENERAL}) {
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """
    result = run_query(mutation)
    assert result.data["updateInstanceSetting"]["problems"] == [
        {"message": "Invalid type"}
    ]
