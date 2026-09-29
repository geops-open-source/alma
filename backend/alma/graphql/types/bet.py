from typing import Self

import strawberry

from alma.graphql.types.misc import ErfassungMutation
from alma.graphql.utils.schema import to_id
from alma.models import subj as subj_models

from .codes import Code, CodeInput
from .grun import EigentumInput
from .subj import Subjekt


@strawberry.type
class Beteiligter:
    bet_id: strawberry.ID
    is_eigentuemer: bool
    is_sachbearbeiter: bool
    erfassung_mutation: ErfassungMutation | None
    subjekt: Subjekt

    @classmethod
    def from_db(cls, beteiligter: subj_models.Beteiligter) -> Self:
        return cls(
            bet_id=to_id(beteiligter.bet_id),
            is_eigentuemer=beteiligter.is_eigentuemer,
            is_sachbearbeiter=beteiligter.is_sachbearbeiter,
            erfassung_mutation=ErfassungMutation.from_db(beteiligter),
            subjekt=Subjekt.from_db(beteiligter.subjekt),
        )


@strawberry.type
class BeteiligterStandort:
    bet_art_id: strawberry.ID
    beziehungsart: Code
    erfassung_mutation: ErfassungMutation | None
    beteiligter: Beteiligter

    @classmethod
    def from_db(cls, beteiligter_standort: subj_models.BeteiligterStandort) -> Self:
        return cls(
            bet_art_id=to_id(beteiligter_standort.bet_art_id),
            beziehungsart=Code.from_db(beteiligter_standort.beziehungsart),
            erfassung_mutation=ErfassungMutation.from_db(beteiligter_standort),
            beteiligter=Beteiligter.from_db(beteiligter_standort.beteiligter),
        )


@strawberry.type
class SachbearbeiterStandort(BeteiligterStandort):
    pass


@strawberry.input
class CreateBeteiligterInput:
    subj_id: strawberry.ID
    vflz_id: strawberry.ID
    grun_id: strawberry.ID | None = None
    beziehungsart: CodeInput


@strawberry.input
class BeteiligterStandortInput:
    bet_art_id: strawberry.ID | None
    subj_id: strawberry.ID
    beziehungsart: CodeInput


@strawberry.input
class SachbearbeitungInput:
    bet_art_id: strawberry.ID | None
    subj_id: strawberry.ID


@strawberry.input
class UpdateVflzBeteiligteInput:
    vflz_id: strawberry.ID
    sachbearbeitung: list[SachbearbeitungInput]
    sonstige_beteiligte: list[BeteiligterStandortInput]
    eigentum: list[EigentumInput]
