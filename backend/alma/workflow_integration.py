"""
Alma integration layer for business-workflow-manager.

This module must be imported before any SQLAlchemy mapper use to ensure
alma-specific augmentations are applied to wm's Node model.
It is imported by alma.graphql.context (and transitively by all app
entry-points and tests), so the import order is guaranteed.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import business_workflow_manager.models as wf_models
from business_workflow_manager.events import Event
from business_workflow_manager.manager import (
    WorkflowManager,
    WorkflowManagerConfig,
)
from sqlalchemy import Integer, cast, select
from sqlalchemy.orm import Session, configure_mappers, foreign, relationship

from alma.models import codes as code_models
from alma.models.vflz import Vflz
from alma.models.workflow import setup_initial_sachbearbeitung

logger = logging.getLogger(__name__)


from alma.models.events import Event as AlmaEvent  # noqa: E402
from alma.models.workflow import (  # noqa: E402
    BeteiligterGeschaeft,
    NodeKategorie,
    wf_node_event,
)

# Force wm's FK string refs ("wf_config.wf_config_id", etc.) to resolve to
# concrete Column objects *before* we move tables to a new schema. Once
# resolved, ForeignKey holds a direct reference to the target Column and no
# longer needs to re-look-up the table by name in the metadata dict.
configure_mappers()


tbl = wf_models.Base.metadata.tables["translations"]
tbl.c.created_at.name = "erfassungs_datum"
tbl.c.created_by.name = "erfasser"
tbl.c.updated_at.name = "mutations_datum"
tbl.c.updated_by.name = "mutierer"

wf_models.Base.metadata.schema = "alma"

WF_TABLES = ["wf_config", "wf_link", "wf_step", "wf_node", "translations"]

for tbl_name in WF_TABLES:
    tbl = wf_models.Base.metadata.tables[tbl_name]
    wf_models.Base.metadata._remove_table(tbl_name, None)  # pyright: ignore[reportPrivateUsage]
    tbl.schema = "alma"
    tbl.fullname = f"alma.{tbl_name}"
    wf_models.Base.metadata._add_table(tbl_name, "alma", tbl)  # pyright: ignore[reportPrivateUsage]


def _add_node_relationships() -> None:
    """
    Add alma-specific ORM relationships onto wf_models.Node.

    The function is idempotent: subsequent calls are no-ops.
    """
    # entity: Node.entity_id (str in wm) → Vflz.vflz_id (int in alma).
    # Cast entity_id to Integer for the join so Postgres can use the index.
    if "entity" not in wf_models.Node.__mapper__.relationships:
        wf_models.Node.__mapper__.add_property(
            "entity",
            relationship(
                Vflz,
                primaryjoin=cast(foreign(wf_models.Node.entity_id), Integer)
                == Vflz.vflz_id,
                viewonly=True,
                uselist=False,
                repr=False,
            ),
        )

    # beteiligte: Node.wf_node_id ← BeteiligterGeschaeft.wf_node_id
    if "beteiligte" not in wf_models.Node.__mapper__.relationships:
        wf_models.Node.__mapper__.add_property(
            "beteiligte",
            relationship(
                BeteiligterGeschaeft,
                primaryjoin=(
                    wf_models.Node.wf_node_id
                    == foreign(BeteiligterGeschaeft.wf_node_id)
                ),
                viewonly=True,
                repr=False,
            ),
        )

    # kategorie: Node.wf_node_id ← NodeKategorie.wf_node_id (one-to-one)
    if "kategorie" not in wf_models.Node.__mapper__.relationships:
        wf_models.Node.__mapper__.add_property(
            "kategorie",
            relationship(
                NodeKategorie,
                primaryjoin=(
                    wf_models.Node.wf_node_id == foreign(NodeKategorie.wf_node_id)
                ),
                cascade="all, delete-orphan",
                single_parent=True,
                uselist=False,
                repr=False,
            ),
        )

    # events: many-to-many via alma.wf_node_event join table
    if "events" not in wf_models.Node.__mapper__.relationships:
        wf_models.Node.__mapper__.add_property(
            "events",
            relationship(
                AlmaEvent,
                secondary=wf_node_event,
                primaryjoin=wf_models.Node.wf_node_id == wf_node_event.c.wf_node_id,
                secondaryjoin=wf_node_event.c.event_id == AlmaEvent.event_id,
                repr=False,
            ),
        )


_add_node_relationships()


@dataclass
class StandortHistorisieren(Event):
    message: str


@dataclass
class UntersuchungsStandSetzen(Event):
    code: str


@dataclass
class BearbeitungsstandSetzen(Event):
    code: str


@dataclass
class ProzessStarten(Event):
    key: UUID


@dataclass
class Publizieren(Event):
    message: str | None = None


def _get_current_vflz(session: Session, node: wf_models.Node) -> Vflz:
    """Resolve the ``Vflz`` associated with *node* via a database lookup. Must be current.

    ``Node.entity_id`` is a ``str`` in wm; alma stores an ``int`` vflz_id there.
    """
    return session.get_one(Vflz, int(node.entity_id)).get_current(session)


def handle_standort_historisieren(
    session: Session, event: StandortHistorisieren, node: wf_models.Node, context: Any
) -> None:
    vflz = _get_current_vflz(session, node)
    original_vflz_id = vflz.vflz_id
    vflz.historize(event.message)

    alma_event = AlmaEvent(
        event_type="StandortHistorisiert",
        event_data={"message": event.message, "new_vflz_id": vflz.vflz_id},
        vflz_id=original_vflz_id,
    )
    session.add(alma_event)
    node.events.append(alma_event)  # type: ignore


def handle_untersuchungsstand_setzen(
    session: Session,
    event: UntersuchungsStandSetzen,
    node: wf_models.Node,
    context: Any,
) -> None:
    vflz = _get_current_vflz(session, node)
    code = code_models.UntersuchungsStand.from_db(session, event.code)
    vflz.untersuchungs_stand = code

    alma_event = AlmaEvent(
        event_type="UntersuchungsStandGesetzt",
        event_data={"code": str(code)},
        vflz_id=vflz.vflz_id,
    )
    session.add(alma_event)
    node.events.append(alma_event)  # type: ignore


def handle_bearbeitungsstand_setzen(
    session: Session,
    event: BearbeitungsstandSetzen,
    node: wf_models.Node,
    context: Any,
) -> None:
    vflz = _get_current_vflz(session, node)
    code = code_models.Bearbeitungsstand.from_db(session, event.code)
    vflz.bearbeitungs_stand = code

    alma_event = AlmaEvent(
        event_type="BearbeitungsstandGesetzt",
        event_data={"code": str(code)},
        vflz_id=vflz.vflz_id,
    )
    session.add(alma_event)
    node.events.append(alma_event)  # type: ignore


def handle_prozess_starten(
    session: Session, event: ProzessStarten, node: wf_models.Node, context: Any
) -> None:
    vflz = _get_current_vflz(session, node)
    wm_workflow = session.scalars(
        select(wf_models.Workflow).where(wf_models.Workflow.key == event.key)
    ).one()

    if not is_applicable(session, wm_workflow, str(node.entity_id)):
        raise ValueError(
            f"Cannot start workflow {wm_workflow.title} at vfl_id = {vflz.vfl_id}: limit reached"
        )

    workflow_node = wm_workflow.create_node(str(vflz.get_current(session).vflz_id))
    session.add(workflow_node)

    setup_initial_sachbearbeitung(session, workflow_node, context["user"])
    session.flush()

    assert workflow_node.wf_node_id

    alma_event = AlmaEvent(
        event_type="ProzessGestartet",
        event_data={
            "key": str(wm_workflow.key),
            "wf_config_id": wm_workflow.wf_config_id,
            "title": wm_workflow.title,
            "wf_node_id": workflow_node.wf_node_id,
        },
        vflz_id=vflz.vflz_id,
    )
    session.add(alma_event)
    node.events.append(alma_event)  # type: ignore


def handle_publizieren(
    session: Session,
    event: Publizieren,
    node: wf_models.Node,
    context: Any,
) -> None:
    vflz = _get_current_vflz(session, node)

    if vflz.publizieren:
        vflz.publizieren = False
    elif vflz.rechtskraft:
        vflz.publizieren = not vflz.publizieren
    else:
        vflz.rechtskraft = True
        vflz.publizieren = True
        vflz.dat_rechtskraft = datetime.now().date()
    vflz.dat_publizieren = datetime.now().date()

    alma_event = AlmaEvent(
        event_type="InKbsEingetragen" if vflz.publizieren else "AusKbsGeloescht",
        event_data={},
        vflz_id=vflz.vflz_id,
    )
    session.add(alma_event)
    node.events.append(alma_event)  # type: ignore


def get_entity_data(session: Session, entity_id: str) -> dict[str, Any]:
    """Return vflz facts dict for jmespath condition evaluation."""
    vflz = session.get(Vflz, int(entity_id))
    if vflz is None:
        return {}
    if vflz.beurteilung and vflz.beurteilung.beurteilung:
        beurteilung_code = vflz.beurteilung.beurteilung.code
    else:
        beurteilung_code = None
    return {
        "beurteilung": beurteilung_code,
        "rechtskraft": vflz.rechtskraft,
        "belastet": (
            vflz.beurteilung.kbs_info.belastet
            if (vflz.beurteilung and vflz.beurteilung.kbs_info)
            else False
        ),
    }


def is_applicable(
    session: Session, workflow: wf_models.Workflow, entity_id: str
) -> bool:
    """
    Check if a new workflow instance can be started.

    Unlike wm's default check (which only looks at the supplied entity_id),
    alma counts *all* vflz versions of the same physical site (vfl_id).
    """
    vflz_id = int(entity_id)
    vflz = session.get_one(Vflz, vflz_id)

    all_vflz_ids = session.scalars(
        select(Vflz.vflz_id).where(Vflz.vfl_id == vflz.vfl_id)
    ).all()

    workflow_nodes = session.scalars(
        select(wf_models.WorkflowNode).where(
            wf_models.WorkflowNode.entity_id.in_([str(id) for id in all_vflz_ids]),
            wf_models.WorkflowNode.wf_config_id == workflow.wf_config_id,
        )
    ).all()

    if workflow.max_per_entity is not None:
        return len(workflow_nodes) < workflow.max_per_entity
    return True


def add_event_handlers(workflow_manager: WorkflowManager) -> None:
    workflow_manager.register_event_handler(
        StandortHistorisieren, handle_standort_historisieren
    )
    workflow_manager.register_event_handler(
        UntersuchungsStandSetzen, handle_untersuchungsstand_setzen
    )
    workflow_manager.register_event_handler(
        BearbeitungsstandSetzen, handle_bearbeitungsstand_setzen
    )
    workflow_manager.register_event_handler(ProzessStarten, handle_prozess_starten)
    workflow_manager.register_event_handler(Publizieren, handle_publizieren)


wf_manager_config = WorkflowManagerConfig(
    get_entity_data=get_entity_data,
    is_applicable=is_applicable,
    entity_data_key="vflz",
)


def set_current_vflz(session: Session, wf_node_id: int) -> None:
    """Refresh the node's entity_id to point at the current vflz version.

    Call this after ``start_next_step`` / ``start_workflow`` when the node
    should reflect the latest vflz state rather than the (possibly
    historized) snapshot inherited from the parent.
    """
    node = session.get(wf_models.Node, wf_node_id)
    if node is None:
        return
    vflz = session.get_one(Vflz, int(node.entity_id))
    current = vflz.get_current(session)
    if current.vflz_id != int(node.entity_id):
        node.entity_id = str(current.vflz_id)
        session.flush()
