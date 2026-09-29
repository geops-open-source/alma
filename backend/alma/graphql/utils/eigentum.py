from sqlalchemy import func, not_, select
from sqlalchemy.orm import Session

from alma import constants
from alma.models import grun as grun_models
from alma.models import subj as subj_models
from alma.models import vflz as vflz_models

from ..types.codes import Code
from ..types.grun import Eigentum, EigentumStatus, Gemeinde, Nummerierungsbereich
from ..types.misc import ErfassungMutation
from ..types.subj import Subjekt


def get_eigentum(session: Session, vflz_id: int) -> list[Eigentum]:
    eigentum: list[Eigentum] = []

    vflz = session.get_one(vflz_models.Vflz, vflz_id)

    eigentuemer = session.scalars(
        select(subj_models.BeteiligterStandort)
        .join(subj_models.Beteiligter)
        .where(
            subj_models.Beteiligter.vflz_id == vflz.vflz_id,
            subj_models.BeteiligterStandort.grun_id.is_not(None),
        )
    ).all()
    for et in eigentuemer:
        assert et.parzelle
        match et.parzelle.status.code:
            case constants.StatusParzelle.AKTUELL:
                status_eigentum = EigentumStatus.ZUGEORDNET
            case constants.StatusParzelle.NICHT_AKTUELL:
                status_eigentum = EigentumStatus.UEBERZAEHLIG
            case _:
                raise ValueError(
                    f"Unknown value for grun.c_grun_status: {et.parzelle.status.code}"
                    f" (grun_id: {et.parzelle.grun_id})."
                    f" Expected one of {list(constants.StatusParzelle)}"
                )
        eigentum.append(
            Eigentum(
                status=status_eigentum,
                subjekt=Subjekt.from_db(et.beteiligter.subjekt),
                beziehungsart=Code.from_db(et.beziehungsart),
                gemeinde=Gemeinde.from_db(et.parzelle.gemeinde)
                if et.parzelle.gemeinde
                else None,
                nummerierungsbereich=Nummerierungsbereich.from_db(
                    et.parzelle.nummerierungsbereich
                )
                if et.parzelle.nummerierungsbereich is not None
                else None,
                parzellen=[et.parzelle.gb_nummer],
                erfassung_mutation=ErfassungMutation.from_db(et.beteiligter),
            )
        )

    if vflz.vflgeo:
        grun_query = (
            select(grun_models.Parzelle)
            .where(
                func.ST_Intersects(
                    vflz.vflgeo.buffered_wkb_geometry,
                    grun_models.Parzelle.wkb_geometry,
                ),
                # Only include parcels from official source
                grun_models.Parzelle.c_grun_status == constants.StatusParzelle.AKTUELL,
                not_(
                    select(subj_models.BeteiligterStandort)
                    .join(subj_models.Beteiligter)
                    .where(
                        subj_models.BeteiligterStandort.grun_id
                        == grun_models.Parzelle.grun_id,
                        subj_models.Beteiligter.vflz_id == vflz.vflz_id,
                    )
                    .exists()
                ),
            )
            .order_by(grun_models.Parzelle.grun_id)
        )
        for parzelle in session.scalars(grun_query).all():
            eigentum.append(
                Eigentum(
                    status=EigentumStatus.FEHLEND,
                    subjekt=None,
                    beziehungsart=None,
                    gemeinde=Gemeinde.from_db(parzelle.gemeinde)
                    if parzelle.gemeinde
                    else None,
                    nummerierungsbereich=Nummerierungsbereich.from_db(
                        parzelle.nummerierungsbereich
                    )
                    if parzelle.nummerierungsbereich is not None
                    else None,
                    parzellen=[parzelle.gb_nummer],
                    erfassung_mutation=None,
                )
            )

    return eigentum
