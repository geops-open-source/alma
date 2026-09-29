from datetime import date
from typing import Any
from unittest.mock import ANY

import business_workflow_manager.models as wf_models
import pytest
from business_workflow_manager.types import NodeStatus
from sqlalchemy.orm import Session
from utils import (
    make_task_config,
    make_vflz,
    make_workflow_config,
)

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
]


def prepare_test_workflow_config(
    session: Session, workflow_manager, triggers: list[dict[str, Any]]
):
    vflz = make_vflz(session, "Standort 1")
    workflow_config = make_workflow_config(session, title="Workflow 1")
    task_config = make_task_config(
        session, workflow_config, name="my_task", title="Task 1"
    )
    workflow_config.start_task_id = task_config.wf_config_id
    task_config.triggers = triggers

    wf_node = workflow_config.create_node(str(vflz.vflz_id))
    session.add(wf_node)
    session.flush()

    node_info = workflow_manager.start_next_step(
        wf_node.wf_node_id, task_config.wf_config_id
    )
    task_node = session.get_one(wf_models.Node, node_info.wf_node_id)
    session.flush()

    assert task_node.title == "Task 1"
    return vflz, task_node


def test_closing_task_with_event_triggers_can_historize(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    vflz, task_node = prepare_test_workflow_config(
        session,
        workflow_manager,
        triggers=[{"type": "StandortHistorisieren", "value": "my message"}],
    )

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    original_vflz_id = vflz.vflz_id

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on StandortHistorisieren { value }
                    }
                    events {
                        ... on StandortHistorisiert { timestamp vflzId newVflzId }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "StandortHistorisiert"
    assert event.event_data == {"message": "my message", "new_vflz_id": vflz.vflz_id}
    assert event.vflz_id == original_vflz_id
    assert vflz.vflz_id > original_vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "newVflzId": str(vflz.vflz_id),
                "vflzId": str(original_vflz_id),
            }
        ],
    }


def test_closing_task_with_event_triggers_can_start_new_process(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    other_workflow_config = make_workflow_config(session, title="Workflow 2")
    assert other_workflow_config.key
    vflz, task_node = prepare_test_workflow_config(
        session,
        workflow_manager,
        [{"type": "ProzessStarten", "value": str(other_workflow_config.key)}],
    )

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on ProzessStarten { title }
                    }
                    events {
                        ... on ProzessGestartet { timestamp title vflzId }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "ProzessGestartet"
    assert event.event_data == {
        "key": str(other_workflow_config.key),
        "wf_config_id": other_workflow_config.wf_config_id,
        "title": "Workflow 2",
        "wf_node_id": ANY,
    }
    assert event.vflz_id == vflz.vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "title": "Workflow 2",
                "vflzId": str(vflz.vflz_id),
            }
        ],
    }


def test_closing_task_with_event_triggers_can_set_untersuchungsstand(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    other_workflow_config = make_workflow_config(session, title="Workflow 2")
    assert other_workflow_config.key
    vflz, task_node = prepare_test_workflow_config(
        session,
        workflow_manager,
        [{"type": "UntersuchungsStandSetzen", "value": "code:10023:test2"}],
    )

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on UntersuchungsStandSetzen { code }
                    }
                    events {
                        ... on UntersuchungsStandGesetzt { timestamp vflzId code }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "UntersuchungsStandGesetzt"
    assert event.event_data == {"code": "code:10023:test2"}
    assert event.vflz_id == vflz.vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "code": "code:10023:test2",
                "vflzId": str(vflz.vflz_id),
            }
        ],
    }


def test_closing_task_with_event_triggers_can_set_bearbeitungsstand(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    other_workflow_config = make_workflow_config(session, title="Workflow 2")
    assert other_workflow_config.key
    vflz, task_node = prepare_test_workflow_config(
        session,
        workflow_manager,
        [{"type": "BearbeitungsstandSetzen", "value": "code:55:test2"}],
    )

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on BearbeitungsstandSetzen { code }
                    }
                    events {
                        ... on BearbeitungsstandGesetzt { timestamp vflzId code }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "BearbeitungsstandGesetzt"
    assert event.event_data == {"code": "code:55:test2"}
    assert event.vflz_id == vflz.vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "vflzId": str(vflz.vflz_id),
                "code": "code:55:test2",
            }
        ],
    }


def test_closing_task_with_event_triggers_can_put_into_kbs(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    other_workflow_config = make_workflow_config(session, title="Workflow 2")
    assert other_workflow_config.key
    vflz, task_node = prepare_test_workflow_config(
        session, workflow_manager, [{"type": "Publizieren", "value": None}]
    )
    vflz.publizieren = False

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on Publizieren { value }
                    }
                    events {
                        ... on InKbsEingetragen { timestamp vflzId }
                        ... on AusKbsGeloescht { timestamp vflzId }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "InKbsEingetragen"
    assert event.event_data == {}
    assert event.vflz_id == vflz.vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "vflzId": str(vflz.vflz_id),
            }
        ],
    }


def test_closing_task_with_event_triggers_can_delete_from_kbs(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    other_workflow_config = make_workflow_config(session, title="Workflow 2")
    assert other_workflow_config.key
    vflz, task_node = prepare_test_workflow_config(
        session, workflow_manager, [{"type": "Publizieren", "value": None}]
    )
    vflz.rechtskraft = True
    vflz.dat_rechtskraft = date(2020, 1, 1)
    vflz.publizieren = True

    assert task_node.status is NodeStatus.STARTED
    assert not task_node.events_triggered
    assert not task_node.events  # type: ignore

    mutation = """
        mutation m($data: UpdateAufgabeInput!) {
            updateAufgabe(data: $data) {
                ... on Aufgabe {
                    title
                    status
                    triggers {
                        ... on Publizieren { value }
                    }
                    events {
                        ... on InKbsEingetragen { timestamp vflzId }
                        ... on AusKbsGeloescht { timestamp vflzId }
                    }
                }
            }
        }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "taskId": task_node.wf_node_id,
                "title": task_node.title,
                "startDatum": task_node.started_at.date().isoformat(),
                "endDatum": task_node.started_at.date().isoformat(),
                "faelligkeitsDatum": None,
                "notiz": None,
                "status": "ABGESCHLOSSEN",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert task_node.status is NodeStatus.FINISHED
    assert task_node.events_triggered

    [event] = task_node.events  # type: ignore
    assert event.event_type == "AusKbsGeloescht"
    assert event.event_data == {}
    assert event.vflz_id == vflz.vflz_id

    assert result.data["updateAufgabe"] == {
        "title": "Task 1",
        "status": "ABGESCHLOSSEN",
        "triggers": [],
        "events": [
            {
                "timestamp": event.event_timestamp.isoformat(),
                "vflzId": str(vflz.vflz_id),
            }
        ],
    }


update_prozess_mutation = """
    mutation m($data: UpdateProzessInput!, $updateChildTasks: Boolean!) {
        updateProzess(data: $data, updateChildTasks: $updateChildTasks) {
            ... on WorkflowProblemGroup {
                openEventsProblemTasks { taskId title }
                statusProblemTasks { taskId }
                faelligkeitsDatumProblemTasks { taskId }
            }
            ... on Prozess {
                status
            }
        }
    }
"""


def prepare_parent_child_with_open_events(
    session: Session, workflow_manager, triggers: list[dict[str, Any]]
):
    """Set up a WorkflowNode (parent) with a child TaskNode that has pending triggers."""
    vflz = make_vflz(session, "Standort 1")
    workflow_config = make_workflow_config(session, title="Parent Workflow")
    task_config = make_task_config(
        session, workflow_config, name="child_task", title="Child Task 1"
    )
    workflow_config.start_task_id = task_config.wf_config_id
    task_config.triggers = triggers

    wf_node = workflow_config.create_node(str(vflz.vflz_id))
    session.add(wf_node)
    session.flush()

    node_info = workflow_manager.start_next_step(
        wf_node.wf_node_id, task_config.wf_config_id
    )
    child_task_node = session.get_one(wf_models.Node, node_info.wf_node_id)
    session.flush()

    return vflz, wf_node, child_task_node


def test_closing_parent_prozess_blocked_when_child_has_open_events(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    """Closing a parent Prozess must be blocked when a child TaskNode has pending
    event triggers that have not yet been executed."""
    vflz, wf_node, child_task_node = prepare_parent_child_with_open_events(
        session,
        workflow_manager,
        triggers=[{"type": "StandortHistorisieren", "value": "test message"}],
    )

    assert child_task_node.status is NodeStatus.STARTED
    assert child_task_node.config is not None
    assert child_task_node.config.triggers
    assert not child_task_node.events_triggered

    result = run_query(
        update_prozess_mutation,
        {
            "data": {
                "taskId": str(wf_node.wf_node_id),
                "title": "Prozess",
                "status": "ABGESCHLOSSEN",
                "startDatum": "2025-03-19",
                "endDatum": "2025-03-20",
                "faelligkeitsDatum": None,
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            },
            "updateChildTasks": True,
        },
    )

    assert result.data["updateProzess"]["openEventsProblemTasks"] == [
        {"taskId": str(child_task_node.wf_node_id), "title": "Child Task 1"}
    ]
    assert result.data["updateProzess"]["statusProblemTasks"] == []
    assert result.data["updateProzess"]["faelligkeitsDatumProblemTasks"] == []

    # Parent and child must remain open
    assert wf_node.status is NodeStatus.FINISHED  # parent status was set before check
    session.refresh(child_task_node)
    assert child_task_node.status is NodeStatus.STARTED
    assert not child_task_node.events_triggered


def test_closing_parent_prozess_blocked_even_with_update_child_tasks_false(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    """The open-events block must fire before the update_child_tasks check."""
    _vflz, wf_node, child_task_node = prepare_parent_child_with_open_events(
        session,
        workflow_manager,
        triggers=[{"type": "StandortHistorisieren", "value": "test message"}],
    )

    result = run_query(
        update_prozess_mutation,
        {
            "data": {
                "taskId": str(wf_node.wf_node_id),
                "title": "Prozess",
                "status": "ABGESCHLOSSEN",
                "startDatum": "2025-03-19",
                "endDatum": "2025-03-20",
                "faelligkeitsDatum": None,
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            },
            "updateChildTasks": False,
        },
    )

    assert len(result.data["updateProzess"]["openEventsProblemTasks"]) == 1
    assert not child_task_node.events_triggered


def test_closing_parent_prozess_succeeds_when_child_events_already_triggered(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    """If the child's events have already been triggered, closing the parent
    must succeed and must not trigger events on the child a second time."""
    vflz, wf_node, child_task_node = prepare_parent_child_with_open_events(
        session,
        workflow_manager,
        triggers=[{"type": "StandortHistorisieren", "value": "test message"}],
    )
    # Mark child events as already executed
    child_task_node.events_triggered = True
    session.flush()

    result = run_query(
        update_prozess_mutation,
        {
            "data": {
                "taskId": str(wf_node.wf_node_id),
                "title": "Prozess",
                "status": "ABGESCHLOSSEN",
                "startDatum": "2025-03-19",
                "endDatum": "2025-03-20",
                "faelligkeitsDatum": None,
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            },
            "updateChildTasks": True,
        },
    )

    assert result.data["updateProzess"]["status"] == "ABGESCHLOSSEN"


def test_closing_parent_prozess_succeeds_when_child_has_no_triggers(
    session: Session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    """Closing a parent Prozess with update_child_tasks=True must succeed when
    child tasks have no configured event triggers."""
    _vflz, wf_node, child_task_node = prepare_parent_child_with_open_events(
        session,
        workflow_manager,
        triggers=[],  # no triggers configured
    )

    result = run_query(
        update_prozess_mutation,
        {
            "data": {
                "taskId": str(wf_node.wf_node_id),
                "title": "Prozess",
                "status": "ABGESCHLOSSEN",
                "startDatum": "2025-03-19",
                "endDatum": "2025-03-20",
                "faelligkeitsDatum": None,
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            },
            "updateChildTasks": True,
        },
    )

    assert result.data["updateProzess"]["status"] == "ABGESCHLOSSEN"
    assert child_task_node.status is NodeStatus.FINISHED
