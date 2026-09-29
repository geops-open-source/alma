import business_workflow_manager.models as wf_models
from sqlalchemy import Column, ForeignKey, Integer, Table, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from . import codes
from .auth import User
from .base import Base, CodeForeignKeyConstraint
from .mixins import ErfassungMutationMixin
from .subj import Subjekt

# Association table owned by alma; wm reads it via the relationship
# added in workflow_integration.py.
wf_node_event = Table(
    "wf_node_event",
    Base.metadata,
    Column("wf_node_id", Integer, primary_key=True),
    Column("event_id", Integer, primary_key=True),
)
wf_node_event.schema = "alma"


class BeteiligterGeschaeft(Base, ErfassungMutationMixin):
    __tablename__ = "bet_task"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_bez_art", "c_bez_art"]),
        {"schema": "alma"},
    )

    # Primary key
    bet_task_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    subj_id: Mapped[int] = mapped_column(ForeignKey("alma.subj.subj_id"), init=False)
    wf_node_id: Mapped[int] = mapped_column(init=False)

    # Codewerte
    h_bez_art: Mapped[int] = mapped_column(init=False)
    c_bez_art: Mapped[str] = mapped_column(init=False)

    # Relationships
    subjekt: Mapped[Subjekt] = relationship(Subjekt)
    node: Mapped[wf_models.Node] = relationship(
        wf_models.Node,
        primaryjoin=lambda: (
            BeteiligterGeschaeft.wf_node_id == wf_models.Node.wf_node_id
        ),
        foreign_keys=lambda: [BeteiligterGeschaeft.wf_node_id],
        overlaps="beteiligte",
    )

    beziehungsart: Mapped[codes.BeziehungsartVariante] = relationship(
        codes.BeziehungsartVariante,
        foreign_keys=[h_bez_art, c_bez_art],
        lazy="joined",
    )

    # Fields
    vfl_id: Mapped[int]


class NodeKategorie(Base):
    __tablename__ = "task_category"
    __table_args__ = (
        CodeForeignKeyConstraint(["h_category", "c_category"]),
        {"schema": "alma"},
    )

    # Primary Key
    task_category_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    # Foreign keys
    wf_node_id: Mapped[int] = mapped_column(init=False)

    # Codewerte
    h_category: Mapped[int | None] = mapped_column(init=False)
    c_category: Mapped[str | None] = mapped_column(init=False)

    # Relationships
    kategorie: Mapped[codes.TaskKategorie] = relationship(
        codes.TaskKategorie,
        foreign_keys=[h_category, c_category],
        lazy="joined",
        default=None,
    )


def setup_initial_sachbearbeitung(
    session: Session, node: wf_models.Node, user: User
) -> None:
    # Set user as initial value for sachbearbeitung
    user_subj = session.scalars(
        select(Subjekt).join(User).where(User.id == user.id)
    ).one()

    code_sachbearbeitung = session.scalars(
        select(codes.BeziehungsartSachbearbeitung).where(
            codes.BeziehungsartSachbearbeitung.code == "sachbearbeitung"
        )
    ).one()

    sachbearbeitung = BeteiligterGeschaeft(
        subjekt=user_subj,
        node=node,
        vfl_id=node.entity.vfl_id,  # pyright: ignore
        beziehungsart=code_sachbearbeitung,
    )
    session.add(sachbearbeitung)
