import pytest
from pytest import raises as assert_raises
from sqlalchemy.orm import Session
from utils import make_code, make_translation

from alma.constants import CodeListe, Language
from alma.models import codes
from alma.search import SearchField
from alma.search.advanced import TranslatedExpression
from alma.search.validation import ValidationError, validate

pytestmark = [
    pytest.mark.usefixtures("as_lesen_geschaefte"),
]


def test_validate_invalid_syntax(session: Session):
    with assert_raises(ValidationError, match="Syntax error: Incomplete expression"):
        validate(session, "")

    with assert_raises(ValidationError, match="Syntax error: Incomplete expression"):
        validate(session, " ")

    with assert_raises(ValidationError, match="Syntax error: Incomplete expression"):
        validate(session, "A")

    with assert_raises(ValidationError, match="Syntax error: Incomplete expression"):
        validate(session, "A =")

    with assert_raises(
        ValidationError, match="Syntax error: Expected field value, got LPAREN"
    ):
        validate(session, "A = (")

    with assert_raises(ValidationError, match="Invalid token: '%'"):
        validate(session, "A = %")

    with assert_raises(ValidationError, match="Invalid token: '% 1'"):
        validate(session, "A % 1")

    with assert_raises(
        ValidationError, match="Syntax error: Missing closing parenthesis"
    ):
        validate(session, "(A = 1")

    with assert_raises(
        ValidationError, match="Syntax error: Missing opening parenthesis"
    ):
        validate(session, "A = 1)")

    with assert_raises(
        ValidationError, match="Syntax error: Missing opening parenthesis"
    ):
        validate(session, "A = 1 OR (B= 2))")


def tests_validates_field_names(session: Session):
    with assert_raises(ValidationError, match="Unknown field name: ZZZ"):
        validate(session, "ZZZ = 1")


def tests_validates_operators(session: Session):
    with assert_raises(
        ValidationError, match='Unsupported operator for field "Bezeichnung": ">="'
    ):
        validate(session, "Bezeichnung >= 1")


def tests_validates_value_type(session: Session):
    with assert_raises(
        ValidationError, match='Unsupported value for field "Bezeichnung": 1'
    ):
        validate(session, "Bezeichnung ~ 1")

    with assert_raises(
        ValidationError, match='Unsupported value for field "Standorttyp": 1'
    ):
        validate(session, "Standorttyp = 1")

    with assert_raises(
        ValidationError, match='Unsupported value for field "vflz_id": "test"'
    ):
        validate(session, 'vflz_id = "test"')

    with assert_raises(
        ValidationError,
        match='Unsupported value for field "Aktuelle-Version-publiziert-oder-gelöscht": "test"',
    ):
        validate(session, 'Aktuelle-Version-publiziert-oder-gelöscht = "test"')

    with assert_raises(
        ValidationError, match='Unsupported value for field "Zeitraum-Von": "test"'
    ):
        validate(session, 'Zeitraum-Von = "test"')


def test_validates_code_values(session: Session):
    make_code(session, codes.StandortTyp, "A")
    make_code(session, codes.StandortTyp, "B")
    make_code(session, codes.StandortTyp, "U")
    make_code(session, codes.Beurteilung, "ZZZ")

    make_translation(
        session, Language.DE, f"code:{CodeListe.StandortTyp}:A", "Ablagerungsstandort"
    )
    make_translation(
        session, Language.DE, f"code:{CodeListe.StandortTyp}:B", "Betriebsstandort"
    )
    make_translation(
        session, Language.DE, f"code:{CodeListe.StandortTyp}:U", "Unfallstandort"
    )
    make_translation(
        session, Language.DE, f"code:{CodeListe.StandortTyp}:Z", "Ungültig"
    )
    make_translation(
        session,
        Language.DE,
        f"code:{CodeListe.Beurteilung}:ZZZ",
        "Andere Codeliste",
    )

    make_translation(
        session, Language.FR, f"code:{CodeListe.StandortTyp}:A", "site de stockage"
    )
    make_translation(
        session, Language.FR, f"code:{CodeListe.StandortTyp}:B", "aire d'entreprise"
    )
    make_translation(
        session, Language.FR, f"code:{CodeListe.StandortTyp}:U", "lieu d'accident"
    )

    with assert_raises(
        ValidationError,
        match='Not a valid value for field "Standorttyp": "XXX"',
    ):
        validate(session, 'Standorttyp = "XXX"')

    with assert_raises(
        ValidationError,
        match='Not a valid value for field "Standorttyp": "ZZZ"',
    ):
        validate(session, 'Standorttyp = "ZZZ"')

    with assert_raises(
        ValidationError,
        match='Not a valid value for field "Standorttyp": "Ungültig"',
    ):
        validate(session, 'Standorttyp = "Ungültig"')

    validate(session, 'Standorttyp = "Ablagerungsstandort"')
    validate(session, 'standorttyp = "ablagerungsstandort"')
    validate(session, 'type-de-site = "site de stockage"')
    validate(session, 'TYPE-DE-SITE = "SITE DE STOCKAGE"')
    validate(session, "Erfassung = 2025-01-01")


def test_validate_translates_field_names_to_enum(session: Session):
    assert validate(session, 'Bezeichnung ~ "test"') == [
        TranslatedExpression(name=SearchField.BEZEICHNUNG, operator="~", value="test"),
    ]


def test_validate_translates_code_values(session: Session):
    make_code(session, codes.StandortTyp, "A")
    make_translation(
        session, Language.DE, f"code:{CodeListe.StandortTyp}:A", "Ablagerungsstandort"
    )
    make_translation(
        session, Language.FR, f"code:{CodeListe.StandortTyp}:A", "site de stockage"
    )

    assert validate(session, 'Standorttyp = "Ablagerungsstandort"') == [
        TranslatedExpression(
            name=SearchField.STANDORTTYP, operator="=", value="code:63:A"
        ),
    ]

    assert validate(session, 'type-de-site = "site de stockage"') == [
        TranslatedExpression(
            name=SearchField.STANDORTTYP, operator="=", value="code:63:A"
        ),
    ]
