from typing import TYPE_CHECKING, Annotated, Self

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import Session

from alma import constants
from alma.graphql.types import problems as problems_types
from alma.graphql.types.bem import Bemerkung, BemerkungInput
from alma.graphql.types.codes import Code, CodeInput
from alma.graphql.types.misc import ErfassungMutation
from alma.graphql.utils.schema import to_id, valid_email, valid_phone, valid_url
from alma.models import codes as code_models
from alma.models import subj as subj_models

from ..utils.schema import Info

if TYPE_CHECKING:
    from .auth import User


@strawberry.type
class Kontakt:
    kontakt_id: strawberry.ID
    kontakt_typ: Code
    kontakt: str

    @classmethod
    def from_db(cls, obj: subj_models.Kontakt) -> Self:
        return cls(
            kontakt_id=to_id(obj.kontakt_id),
            kontakt_typ=Code.from_db(obj.kontakt_typ),
            kontakt=obj.kontakt,
        )


@strawberry.input
class KontaktInput:
    kontakt_id: strawberry.ID | None
    kontakt_typ: CodeInput
    kontakt: str

    def validate(self, session: Session) -> problems_types.Problem | None:
        kontakt_type_code = code_models.KontaktTyp.from_db(session, self.kontakt_typ)
        if kontakt_type_code.code in [
            constants.KontaktTyp.EMAIL_PRIVATE,
            constants.KontaktTyp.EMAIL_BUSINESS,
        ] and not valid_email(self.kontakt):
            return problems_types.Problem(
                message="Invalid email",
                problem_code=problems_types.ProblemCode.VALIDATION_EMAIL,
                field="email",
            )
        elif kontakt_type_code.code in [
            constants.KontaktTyp.PHONE_BUSINESS,
            constants.KontaktTyp.PHONE_PRIVATE,
            constants.KontaktTyp.MOBILE,
        ] and not valid_phone(self.kontakt):
            return problems_types.Problem(
                message="Invalid phone",
                problem_code=problems_types.ProblemCode.VALIDATION_PHONE,
                field="phone",
            )
        elif kontakt_type_code.code == constants.KontaktTyp.WEB and not valid_url(
            self.kontakt
        ):
            return problems_types.Problem(
                message="Invalid URL",
                problem_code=problems_types.ProblemCode.VALIDATION_URL,
                field="url",
            )


@strawberry.type
class Subjekt:
    subj_id: strawberry.ID
    anrede: Code | None
    land: Code | None
    name: str
    vorname: str
    taetigkeit: str
    kuerzel: str | None
    ident_nr: str | None
    ort: str
    postleitzahl: str
    strasse: str
    kategorien: list[Code]
    erfassung_mutation: ErfassungMutation | None
    kontakte: list[Kontakt]
    bemerkung: Bemerkung | None

    @strawberry.field
    def user(self, info: Info) -> Annotated["User", strawberry.lazy(".auth")] | None:
        from .auth import User

        session = info.context.db
        subj = session.get_one(subj_models.Subjekt, int(self.subj_id))

        return User.from_db(subj.user) if subj.user else None

    @strawberry.field
    def has_standorte(self, info: Info) -> bool:
        session = info.context.db
        query = select(subj_models.Beteiligter).where(
            subj_models.Beteiligter.subj_id == int(self.subj_id)
        )
        return session.scalars(query).first() is not None

    @classmethod
    def from_db(cls, subjekt: subj_models.Subjekt) -> Self:
        return cls(
            subj_id=to_id(subjekt.subj_id),
            anrede=Code.from_db_or_none(subjekt.anrede),
            land=Code.from_db_or_none(subjekt.land),
            name=subjekt.name,
            vorname=subjekt.vorname,
            taetigkeit=subjekt.taetigkeit,
            kuerzel=subjekt.kuerzel,
            ident_nr=subjekt.ident_nr,
            erfassung_mutation=ErfassungMutation.from_db(subjekt),
            kategorien=[Code.from_db(kategorie) for kategorie in subjekt.kategorien],
            kontakte=[Kontakt.from_db(kontakt) for kontakt in subjekt.kontakte],
            ort=subjekt.ort,
            postleitzahl=subjekt.postleitzahl,
            strasse=subjekt.strasse,
            bemerkung=Bemerkung.from_db(subjekt.bemerkung)
            if subjekt.bemerkung
            else None,
        )


@strawberry.type
class PaginatedSubjektResult:
    num_pages: int
    num_results_total: int
    results: list[Subjekt]
    page: int
    per_page: int


@strawberry.input
class UpdateSubjektInput:
    subj_id: strawberry.ID
    anrede: CodeInput | None
    land: CodeInput | None
    name: str | None
    vorname: str | None
    taetigkeit: str | None
    kuerzel: str | None
    kategorien: list[CodeInput]
    kontakte: list[KontaktInput]
    ort: str | None
    postleitzahl: str | None
    strasse: str | None
    bemerkung: BemerkungInput | None

    def validate(self, session: Session) -> list[problems_types.Problem]:
        problems: list[problems_types.Problem] = []
        for idx, kontakt in enumerate(self.kontakte):
            if problem := kontakt.validate(session):
                problem.field = f"kontakte[{idx}].kontakt"
                problems.append(problem)
        return problems


@strawberry.input
class CreateSubjektInput:
    anrede: CodeInput | None
    land: CodeInput | None
    name: str | None
    vorname: str | None
    taetigkeit: str | None
    kuerzel: str | None
    kategorien: list[CodeInput]
    kontakte: list[KontaktInput]
    ort: str | None
    postleitzahl: str | None
    strasse: str | None
    bemerkung: BemerkungInput | None

    def validate(self, session: Session) -> list[problems_types.Problem]:
        problems: list[problems_types.Problem] = []
        for idx, kontakt in enumerate(self.kontakte):
            if problem := kontakt.validate(session):
                problem.field = f"kontakte[{idx}].kontakt"
                problems.append(problem)
        return problems


@strawberry.type
class UpdateSubjektResult:
    subjekt: Subjekt
    problem_group: problems_types.ProblemGroup
