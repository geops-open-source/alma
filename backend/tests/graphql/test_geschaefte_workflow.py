from datetime import date
from io import StringIO
from pathlib import Path

import business_workflow_manager.models as wf_models
import pytest
from pytest import raises as assert_raises
from sqlalchemy import select
from utils import QueryError, make_vflz

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
]


start_prozess_mutation = """
    mutation m($data: StartProzessInput!) {
        startProzess(data: $data) {
            prozess {
                taskId title
                sachbearbeitung { subjekt { user { username } } }
            }
        }
    }
"""
start_folgeschritt_mutation = """
    mutation m($data: StartTaskInput!) {
        startFolgeschritt(data: $data) {
            task {
                taskId title
                sachbearbeitung { subjekt { user { username } } }
            }
        }
    }
"""
folgeschritte_query = """
    query q($taskId: ID!) {
        task(taskId: $taskId) {
            folgeschritte { optionId title type }
        }
    }
"""
update_dokument_mutation = """
    mutation m($data: UpdateDokumentInput!) {
        updateDokument(data: $data) {
            status
            folgeschritte { optionId title type }
        }
    }
"""
update_formular_mutation = """
    mutation m($data: UpdateFormularInput!) {
        updateFormular(data: $data) {
        ... on Formular {
                status
                folgeschritte { optionId title type }
            }
        }
    }
"""
update_aufgabe_mutation = """
    mutation m($data: UpdateAufgabeInput!) {
        updateAufgabe(data: $data) {
        ... on Aufgabe {
                status
                folgeschritte { optionId title type }
            }
        }
    }
"""


@pytest.fixture
def simple_workflow(workflow_manager) -> wf_models.Workflow:
    path = Path(__file__).parent / "workflows" / "simple.yml"
    with path.open() as f:
        workflow, _ = workflow_manager.load_workflow_from_file(f)
    return workflow


def test_query_vflz_prozesse_fails_with_insufficient_permissions(
    session, run_query, simple_workflow: wf_models.Workflow, as_lesen_sachdaten
):
    vflz = make_vflz(session, "Standort 1")
    query = """
        query q($vflzId: ID!) {
            vflz(vflzId: $vflzId) {
                prozesse {
                    optionId
                    title
                    type
                }
            }
        }
    """
    with assert_raises(QueryError, match="not allowed"):
        run_query(query=query, variable_values={"vflzId": str(vflz.vflz_id)})


def test_query_vflz_prozesse(
    session, run_query, simple_workflow: wf_models.Workflow, as_lesen_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    query = """
        query q($vflzId: ID!) {
            vflz(vflzId: $vflzId) {
                prozesse {
                    optionId
                    title
                    type
                }
            }
        }
    """

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data["vflz"] == {
        "prozesse": [
            {
                "optionId": str(simple_workflow.wf_config_id),
                "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:title",
                "type": "PROZESS",
            },
        ],
    }


def test_query_vflz_prozesse_does_not_include_process_if_limit_is_reached(
    session, run_query, simple_workflow: wf_models.Workflow, as_lesen_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    workflow_node = simple_workflow.create_node(str(vflz.vflz_id))
    session.add(workflow_node)
    session.commit()

    query = """
        query q($vflzId: ID!) {
            vflz(vflzId: $vflzId) {
                prozesse {
                    optionId
                    title
                    type
                }
            }
        }
    """

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data["vflz"] == {
        "prozesse": [
            {
                "optionId": str(simple_workflow.wf_config_id),
                "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:title",
                "type": "PROZESS",
            },
        ],
    }

    simple_workflow.max_per_entity = 1

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data == {"vflz": {"prozesse": []}}

    simple_workflow.max_per_entity = 2

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data["vflz"] == {
        "prozesse": [
            {
                "optionId": str(simple_workflow.wf_config_id),
                "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:title",
                "type": "PROZESS",
            },
        ],
    }

    vflz.historize("Kommentar")
    workflow_node = simple_workflow.create_node(str(vflz.vflz_id))
    session.add(workflow_node)
    session.commit()

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data == {"vflz": {"prozesse": []}}


def test_start_prozess_fails_with_insufficient_permission(
    session, run_query, simple_workflow: wf_models.Workflow, as_lesen_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    mutation = """
        mutation m($data: StartProzessInput!) {
            startProzess(data: $data) {
                prozess { taskId title }
            }
        }
    """

    with assert_raises(QueryError, match="not allowed"):
        run_query(
            mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    "optionId": str(simple_workflow.wf_config_id),
                }
            },
        )


def test_start_prozess_creates_workflow_node_with_current_user_as_sachbearbeitung(
    session, run_query, simple_workflow: wf_models.Workflow, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    mutation = """
        mutation m($data: StartProzessInput!) {
            startProzess(data: $data) {
                prozess {
                    taskId title
                    sachbearbeitung { subjekt { user { username } } }
                }
            }
        }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "optionId": str(simple_workflow.wf_config_id),
            }
        },
    )

    node = session.scalars(
        select(wf_models.WorkflowNode).where(
            wf_models.WorkflowNode.entity_id == vflz.vflz_id
        )
    ).one()

    assert result.data["startProzess"] == {
        "prozess": {
            "sachbearbeitung": [{"subjekt": {"user": {"username": "alma-test"}}}],
            "taskId": str(node.wf_node_id),
            "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:title",
        }
    }


def test_start_prozess_fails_if_limit_is_reached(
    session, run_query, simple_workflow: wf_models.Workflow, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    simple_workflow.max_per_entity = 0
    session.commit()

    mutation = """
        mutation m($data: StartProzessInput!) {
            startProzess(data: $data) {
                prozess { taskId title }
            }
        }
    """

    with assert_raises(QueryError, match="Cannot start workflow"):
        run_query(
            mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    "optionId": str(simple_workflow.wf_config_id),
                }
            },
        )


def test_work_through_process(
    session, run_query, simple_workflow: wf_models.Workflow, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    result = run_query(
        start_prozess_mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "optionId": str(simple_workflow.wf_config_id),
            }
        },
    )

    workflow_node = session.scalars(
        select(wf_models.WorkflowNode).where(
            wf_models.WorkflowNode.entity_id == vflz.vflz_id
        )
    ).one()

    assert result.data["startProzess"] == {
        "prozess": {
            "taskId": str(workflow_node.wf_node_id),
            "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:title",
            "sachbearbeitung": [{"subjekt": {"user": {"username": "alma-test"}}}],
        }
    }

    result = run_query(folgeschritte_query, {"taskId": str(workflow_node.wf_node_id)})
    assert result.data["task"]["folgeschritte"] == [
        {
            "optionId": str(simple_workflow.tasks["task_1"].wf_config_id),
            "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:title",
            "type": "AUFGABE",
        }
    ]

    result = run_query(
        start_folgeschritt_mutation,
        {
            "data": {
                "taskId": str(workflow_node.wf_node_id),
                "optionId": str(simple_workflow.tasks["task_1"].wf_config_id),
            }
        },
    )
    assert (
        result.data["startFolgeschritt"]["task"]["title"]
        == "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:title"
    )
    assert result.data["startFolgeschritt"]["task"]["sachbearbeitung"] == [
        {"subjekt": {"user": {"username": "alma-test"}}},
    ]
    task_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    result = run_query(folgeschritte_query, {"taskId": task_node_id})
    assert result.data["task"]["folgeschritte"] == [
        {
            "optionId": str(simple_workflow.tasks["task_1"].steps[0].step.wf_config_id),
            "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:step:1:title",
            "type": "DOKUMENT",
        }
    ]

    result = run_query(
        start_folgeschritt_mutation,
        {
            "data": {
                "taskId": task_node_id,
                "optionId": str(
                    simple_workflow.tasks["task_1"].steps[0].step.wf_config_id
                ),
            }
        },
    )
    assert (
        result.data["startFolgeschritt"]["task"]["title"]
        == "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:step:1:title"
    )
    assert result.data["startFolgeschritt"]["task"]["sachbearbeitung"] == [
        {"subjekt": {"user": {"username": "alma-test"}}},
    ]
    document_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    result = run_query(
        update_dokument_mutation,
        {
            "data": {
                "taskId": document_node_id,
                "title": "Document 1",
                "startDatum": "2025-03-19",
                "notiz": "",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
                "dokument": "",
                "kategorie": None,
                "oeffentlich": False,
            }
        },
    )
    assert result.data["updateDokument"]["status"] == "ABGESCHLOSSEN"
    assert result.data["updateDokument"]["folgeschritte"] == [
        {
            "optionId": str(simple_workflow.tasks["task_1"].steps[1].step.wf_config_id),
            "title": "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:step:2:title",
            "type": "FORMULAR",
        }
    ]

    result = run_query(
        start_folgeschritt_mutation,
        {
            "data": {
                "taskId": document_node_id,
                "optionId": str(
                    simple_workflow.tasks["task_1"].steps[1].step.wf_config_id
                ),
            }
        },
    )
    assert (
        result.data["startFolgeschritt"]["task"]["title"]
        == "wf:b6395856-9556-48b4-828f-6610d153a3bc:task:task_1:step:2:title"
    )
    assert result.data["startFolgeschritt"]["task"]["sachbearbeitung"] == [
        {"subjekt": {"user": {"username": "alma-test"}}},
    ]
    form_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    result = run_query(
        update_formular_mutation,
        {
            "data": {
                "taskId": form_node_id,
                "title": "Form 1",
                "startDatum": "2025-03-19",
                "notiz": "",
                "eingaben": {"field-1": True},
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert result.data["updateFormular"] == {
        "status": "ABGESCHLOSSEN",
        "folgeschritte": [],
    }


def test_can_close_parent_task_if_all_steps_are_closed(
    session, run_query, simple_workflow: wf_models.Workflow, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "Standort 1")

    # at first let's walk through the process and let's close all of the steps
    result = run_query(
        start_prozess_mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "optionId": str(simple_workflow.wf_config_id),
            }
        },
    )
    workflow_node = session.scalars(
        select(wf_models.WorkflowNode).where(
            wf_models.WorkflowNode.entity_id == vflz.vflz_id
        )
    ).one()

    result = run_query(
        start_folgeschritt_mutation,
        variable_values={
            "data": {
                "taskId": str(workflow_node.wf_node_id),
                "optionId": str(simple_workflow.tasks["task_1"].wf_config_id),
            }
        },
    )

    task_node_id = result.data["startFolgeschritt"]["task"]["taskId"]
    result = run_query(
        start_folgeschritt_mutation,
        variable_values={
            "data": {
                "taskId": str(task_node_id),
                "optionId": str(
                    simple_workflow.tasks["task_1"].steps[0].step.wf_config_id
                ),
            }
        },
    )
    document_node_id = result.data["startFolgeschritt"]["task"]["taskId"]
    result = run_query(
        update_dokument_mutation,
        variable_values={
            "data": {
                "taskId": document_node_id,
                "title": "Document 1",
                "startDatum": "2025-03-19",
                "notiz": "",
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
                "dokument": "",
                "kategorie": None,
                "oeffentlich": False,
            }
        },
    )
    assert result.data["updateDokument"]["status"] == "ABGESCHLOSSEN"
    result = run_query(
        start_folgeschritt_mutation,
        {
            "data": {
                "taskId": document_node_id,
                "optionId": str(
                    simple_workflow.tasks["task_1"].steps[1].step.wf_config_id
                ),
            }
        },
    )
    form_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    result = run_query(
        update_formular_mutation,
        {
            "data": {
                "taskId": form_node_id,
                "title": "Form 1",
                "startDatum": "2025-03-19",
                "notiz": "",
                "eingaben": {"field-1": True},
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )

    result = run_query(
        update_aufgabe_mutation,
        {
            "data": {
                "taskId": task_node_id,
                "title": "foo",
                "startDatum": "2025-03-19",
                "faelligkeitsDatum": None,
                "endDatum": None,
                "status": "ABGESCHLOSSEN",
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )
    assert result.data["updateAufgabe"]["status"] == "ABGESCHLOSSEN"


def test_create_new_dokument(session, run_query, as_bearbeiten_geschaefte):
    vflz = make_vflz(session, "Standort 1")
    mutation = """
    mutation m($data: CreateDokumentInput!) {
        createDokument(data: $data) {
            startDatum
            endDatum
            faelligkeitsDatum
            notiz
            title
            vflz {
                vflzId
            }
            status
            dokument
            sachbearbeitung { subjekt { user { username } } }
            kategorie
            oeffentlich
        }
    }
    """

    variables = {
        "data": {
            "title": "Dokument Titel",
            "startDatum": date(2020, 1, 1).isoformat(),
            "vflzId": str(vflz.vflz_id),
            "notiz": "Notiz",
            "dokument": "dummy",
            "kategorie": "code:10022:Kategorie",
            "oeffentlich": True,
        }
    }

    result = run_query(mutation, variables)
    assert result.data["createDokument"] == {
        "startDatum": "2020-01-01",
        "endDatum": "2020-01-01",
        "notiz": "Notiz",
        "title": "Dokument Titel",
        "faelligkeitsDatum": "2020-01-01",
        "vflz": {
            "vflzId": str(vflz.vflz_id),
        },
        "status": "ABGESCHLOSSEN",
        "dokument": "dummy",
        "sachbearbeitung": [{"subjekt": {"user": {"username": "alma-test"}}}],
        "kategorie": "code:10022:Kategorie",
        "oeffentlich": True,
    }


def test_create_new_aufgabe(session, run_query, as_bearbeiten_geschaefte):
    vflz = make_vflz(session, "Standort 1")
    mutation = """
    mutation m($data: CreateAufgabeInput!) {
        createAufgabe(data: $data) {
            startDatum
            endDatum
            faelligkeitsDatum
            notiz
            title
            vflz {
                vflzId
            }
            status
            sachbearbeitung { subjekt { user { username } } }
        }
    }
    """

    variables = {
        "data": {
            "title": "Aufgabe Titel",
            "faelligkeitsDatum": date(2021, 1, 1).isoformat(),
            "vflzId": str(vflz.vflz_id),
            "notiz": "Notiz",
            "startDatum": date(2020, 1, 1).isoformat(),
        }
    }

    result = run_query(mutation, variables)
    assert result.data["createAufgabe"] == {
        "startDatum": "2020-01-01",
        "endDatum": None,
        "notiz": "Notiz",
        "title": "Aufgabe Titel",
        "faelligkeitsDatum": "2021-01-01",
        "vflz": {
            "vflzId": str(vflz.vflz_id),
        },
        "status": "OFFEN",
        "sachbearbeitung": [{"subjekt": {"user": {"username": "alma-test"}}}],
    }


def test_create_new_aufgabe_nested_under_task(
    session, run_query, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "Standort 1")
    mutation = """
    mutation m($data: CreateAufgabeInput!) {
        createAufgabe(data: $data) {
            taskId
            parentId
        }
    }
    """

    parent_variables = {
        "data": {
            "title": "Übergeordnete Aufgabe",
            "faelligkeitsDatum": date(2021, 1, 1).isoformat(),
            "vflzId": str(vflz.vflz_id),
            "notiz": "Notiz",
            "startDatum": date(2020, 1, 1).isoformat(),
        }
    }
    parent_result = run_query(mutation, parent_variables)
    parent_task_id = parent_result.data["createAufgabe"]["taskId"]

    child_variables = {
        "data": {
            "title": "Unteraufgabe",
            "faelligkeitsDatum": date(2021, 1, 1).isoformat(),
            "vflzId": str(vflz.vflz_id),
            "notiz": "Notiz",
            "startDatum": date(2020, 1, 1).isoformat(),
            "taskId": parent_task_id,
        }
    }
    child_result = run_query(mutation, child_variables)

    # The new sub-Aufgabe must be nested directly under the selected parent
    # Aufgabe, not the top-level workflow/process node.
    assert child_result.data["createAufgabe"]["parentId"] == parent_task_id


def test_start_folgeschritt_uses_current_vflz_after_historization(
    session, run_query, as_bearbeiten_geschaefte, workflow_manager
):
    """After a Vflz is historized, startFolgeschritt must attach the new task
    node to the current (post-historization) Vflz, not the old snapshot.

    This exercises AlmaWorkflowManager.set_current_vflz, which is invoked from
    the start_folgeschritt mutation resolver immediately after wm's
    start_next_step returns.
    """
    workflow_yaml = """
    workflow:
      title: Historization test workflow
      version: 1
      min_per_entity: 0
      max_per_entity: null
      start_task_ref: task1
      tasks:
        task1:
          title: Task 1
          steps: []
          links:
            - task_ref: task2
        task2:
          title: Task 2
          steps: []
          links:
            - task_ref: END
        END:
          title: __END__
          steps: []
          links: []
    """
    workflow, _ = workflow_manager.load_workflow_from_file(StringIO(workflow_yaml))
    session.flush()

    vflz = make_vflz(session, "Standort 1")
    original_vflz_id = vflz.vflz_id

    # 1) start the workflow (creates the WorkflowNode on the current vflz)
    result = run_query(
        start_prozess_mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "optionId": str(workflow.wf_config_id),
            }
        },
    )
    workflow_node_id = result.data["startProzess"]["prozess"]["taskId"]

    # 2) start task1
    result = run_query(
        start_folgeschritt_mutation,
        variable_values={
            "data": {
                "taskId": workflow_node_id,
                "optionId": str(workflow.tasks["task1"].wf_config_id),
            }
        },
    )
    task1_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    # 3) close task1 (needed for links to be evaluated)
    run_query(
        update_aufgabe_mutation,
        variable_values={
            "data": {
                "taskId": task1_node_id,
                "title": "Task 1",
                "startDatum": "2025-01-01",
                "faelligkeitsDatum": None,
                "endDatum": "2025-01-02",
                "status": "ABGESCHLOSSEN",
                "notiz": None,
                "sachbearbeitung": [],
                "sonstigeBeteiligte": [],
            }
        },
    )

    # 4) historize vflz — creates a new current vflz_id
    vflz.historize("test historization")
    session.commit()
    new_vflz_id = vflz.vflz_id
    assert new_vflz_id != original_vflz_id

    # 5) start task2 via the GraphQL mutation; set_current_vflz should refresh
    #    the task2 node to point at the current vflz version.
    result = run_query(
        start_folgeschritt_mutation,
        variable_values={
            "data": {
                "taskId": task1_node_id,
                "optionId": str(workflow.tasks["task2"].wf_config_id),
            }
        },
    )
    task2_node_id = result.data["startFolgeschritt"]["task"]["taskId"]

    task2_node = session.get_one(wf_models.TaskNode, int(task2_node_id))
    session.refresh(task2_node)
    assert int(task2_node.entity_id) == new_vflz_id
