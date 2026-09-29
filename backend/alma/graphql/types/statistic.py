from dataclasses import field
from datetime import date, datetime
from typing import Self

import business_workflow_manager.models as wf_models
import strawberry
from business_workflow_manager.types import NodeStatus, NodeType
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from alma import constants
from alma.models import codes as code_models
from alma.models import vflz as vflz_models

from .codes import Code
from .vflz import StandortTyp
from .workflow import FaelligkeitStatus


@strawberry.type
class StandortTypenStatistic:
    typ: StandortTyp
    count: int

    @classmethod
    def from_db(cls, session: Session, stichtag: date) -> list[Self]:
        timestamp = datetime(stichtag.year, stichtag.month, stichtag.day, 23, 59, 59)
        result: dict[StandortTyp, int] = {key: 0 for key in StandortTyp}

        latest_vflz_id = (
            select(func.max(vflz_models.Vflz.vflz_id).label("vflz_id"))
            .join(
                vflz_models.VflzCurrent,
                vflz_models.VflzCurrent.vfl_id == vflz_models.Vflz.vfl_id,
            )
            .where(vflz_models.Vflz.vflz_created_date <= timestamp)
            .group_by(vflz_models.Vflz.vfl_id, vflz_models.Vflz.obje_id)
        ).cte("latest_vflz_id")

        vftyp_stats = session.execute(
            select(
                vflz_models.Vflz.c_vflz_vftyp,
                func.count(vflz_models.Vflz.vfl_id.distinct()).label("count"),
            )
            .join(latest_vflz_id, latest_vflz_id.c.vflz_id == vflz_models.Vflz.vflz_id)
            .group_by(vflz_models.Vflz.c_vflz_vftyp)
            .order_by(vflz_models.Vflz.c_vflz_vftyp)
        )

        for vftyp, count in vftyp_stats:
            result[StandortTyp(vftyp)] = count

        return [cls(typ=typ, count=count) for typ, count in result.items()]


@strawberry.type
class BeurteilungStatistic:
    beurteilung_gruppe: Code
    count: int

    @classmethod
    def from_db(cls, session: Session, stichtag: date) -> list[Self]:
        timestamp = datetime(stichtag.year, stichtag.month, stichtag.day, 23, 59, 59)
        beurteilung_gruppe_codes = session.scalars(
            select(code_models.BeurteilungGruppe)
        ).all()
        result: dict[str, int] = {code.code: 0 for code in beurteilung_gruppe_codes}

        latest_vflz_id = (
            select(func.max(vflz_models.Vflz.vflz_id).label("vflz_id"))
            .where(vflz_models.Vflz.vflz_created_date <= timestamp)
            .group_by(vflz_models.Vflz.vfl_id, vflz_models.Vflz.obje_id)
        ).cte("latest_vflz_id")

        beurteilung_gruppe_stats = session.execute(
            select(
                code_models.KbsInfo.c_bewe_gruppe.label("beurteilung_gruppe"),
                func.count(code_models.KbsInfo.c_bewe_gruppe).label("count"),
            )
            .join(
                vflz_models.Beurteilung,
                vflz_models.Beurteilung.c_bere_res_abwbewe
                == code_models.KbsInfo.c_bere_res_abwbewe,
            )
            .join(
                latest_vflz_id,
                vflz_models.Beurteilung.vflz_id == latest_vflz_id.c.vflz_id,
            )
            .group_by(code_models.KbsInfo.c_bewe_gruppe)
            .order_by(code_models.KbsInfo.c_bewe_gruppe)
        ).all()

        for beurteilung_gruppe_code, count in beurteilung_gruppe_stats:
            result[beurteilung_gruppe_code] = count

        return [
            cls(
                beurteilung_gruppe=Code(
                    f"code:{constants.CodeListe.BeurteilungGruppe}:{code}"
                ),
                count=count,
            )
            for code, count in result.items()
        ]


@strawberry.type
class GeschaefteStatistic:
    faelligkeit: FaelligkeitStatus
    count: int

    @classmethod
    def from_db(cls, session: Session, stichtag: date) -> list[Self]:
        timestamp = datetime(stichtag.year, stichtag.month, stichtag.day, 23, 59)
        result: dict[FaelligkeitStatus, int] = {
            status: 0 for status in FaelligkeitStatus
        }

        geschaefte_deadlines = session.execute(
            select(wf_models.Node.deadline, wf_models.Node.type).where(
                wf_models.Node.status.in_([NodeStatus.STARTED, NodeStatus.INACTIVE]),
                wf_models.Node.started_at <= timestamp,
                wf_models.Node.finished_at.is_(None),
            )
        ).all()

        for deadline, node_type in geschaefte_deadlines:
            match node_type:
                # The deadline of forms, notes, and documents cannot be changed by the user.
                # Therefore, for the statistic, we consider them to be "ruhend".
                case NodeType.FORM:
                    result[FaelligkeitStatus.RUHEND] += 1
                case NodeType.NOTE:
                    result[FaelligkeitStatus.RUHEND] += 1
                case NodeType.DOCUMENT:
                    result[FaelligkeitStatus.RUHEND] += 1
                case _:
                    result[FaelligkeitStatus.from_datetime(deadline)] += 1

        return [
            cls(faelligkeit=faelligkeit_status, count=count)
            for faelligkeit_status, count in result.items()
        ]


@strawberry.type
class DashboardStatistic:
    standort_typen: list[StandortTypenStatistic] = field(default_factory=list)
    beurteilungen: list[BeurteilungStatistic] = field(default_factory=list)
    geschaefte: list[GeschaefteStatistic] = field(default_factory=list)
