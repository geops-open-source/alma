import pytest
from sqlalchemy.orm import Session
from utils import make_code, make_gemeinde, make_nummerierungsbereich, make_translation

from alma.constants import CodeListe, Language
from alma.models import codes
from alma.search.autosuggest import AutoSuggestItem, AutoSuggestType, autosuggest
from alma.search.core import FieldCategory, FieldType


@pytest.mark.parametrize(
    ("s", "result"),
    [
        (
            "Bet",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Betriebsgrösse",
                    FieldCategory.BETRIEBE,
                ),
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME, "Beteiligte", FieldCategory.BETEILIGTE
                ),
            ],
        ),
        (
            "Beteil",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME, "Beteiligte", FieldCategory.BETEILIGTE
                ),
            ],
        ),
        (
            "Beteiligte",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME, "Beteiligte", FieldCategory.BETEILIGTE
                ),
            ],
        ),
        (
            "Stoffgruppe-",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Stoffgruppe-Stoffgruppe",
                    FieldCategory.ABLAGERUNGEN,
                ),
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Stoffgruppe-Teilvolumen",
                    FieldCategory.ABLAGERUNGEN,
                ),
            ],
        ),
        (
            "vflz_",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME, "vflz_id", FieldCategory.STANDORT
                ),
            ],
        ),
    ],
)
def test_autosuggest_fields(session: Session, s: str, result: list[AutoSuggestItem]):
    assert autosuggest(session, s) == result


@pytest.mark.parametrize(
    ("s", "lang", "result"),
    [
        (
            "num",
            "fr",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Numéro-du-site",
                    FieldCategory.STANDORT,
                ),
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Numéro-postal",
                    FieldCategory.GRUNDDATEN,
                ),
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Numéro-EVA",
                    FieldCategory.BETRIEBE,
                ),
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Numéro-de-site-alternatif",
                    FieldCategory.VOLLZUG,
                ),
            ],
        ),
        (
            "pers",
            "fr",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Personnes-concernées",
                    FieldCategory.BETEILIGTE,
                ),
            ],
        ),
        (
            "Personnes-concernées",
            "fr",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME,
                    "Personnes-concernées",
                    FieldCategory.BETEILIGTE,
                ),
            ],
        ),
    ],
)
def test_autosuggest_fields_translated(
    session: Session, s: str, lang: str, result: list[AutoSuggestItem]
):
    assert autosuggest(session, s, lang=Language(lang)) == result


@pytest.mark.parametrize(
    ("s", "result"),
    [
        (
            "Beteiligte ",
            [
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "~", field_type=FieldType.TEXT
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "=", field_type=FieldType.TEXT
                ),
            ],
        ),
        (
            "Standorttyp ",
            [
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "=", field_type=FieldType.CODE
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "!=", field_type=FieldType.CODE
                ),
            ],
        ),
    ],
)
def test_autosuggest_operator_with_quote_after_text_or_code_field(
    session: Session, s: str, result: list[AutoSuggestItem]
):
    assert autosuggest(session, s) == result


@pytest.mark.parametrize(
    ("s", "result"),
    [
        (
            "Aktuelle-Version-publiziert-oder-gelöscht ",
            [AutoSuggestItem(AutoSuggestType.OPERATOR, "=", field_type=FieldType.BOOL)],
        ),
        (
            "BFS-Gemeinde-Nr ",
            [
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, ">", field_type=FieldType.NUMBER
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "<", field_type=FieldType.NUMBER
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, ">=", field_type=FieldType.NUMBER
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "<=", field_type=FieldType.NUMBER
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "=", field_type=FieldType.NUMBER
                ),
            ],
        ),
    ],
)
def test_autosuggest_operator_without_quote_after_bool_or_number_field(
    session: Session, s: str, result: list[AutoSuggestItem]
):
    assert autosuggest(session, s) == result


def test_autosuggest_grouping_operator(session: Session):
    assert autosuggest(session, 'Bezeichnung ~ "test"') == []

    assert autosuggest(session, 'Bezeichnung ~ "test" ') == [
        AutoSuggestItem(AutoSuggestType.OPERATOR, "AND"),
        AutoSuggestItem(AutoSuggestType.OPERATOR, "OR"),
    ]


def test_autosuggest_field_after_grouping_operator(session: Session):
    assert autosuggest(session, 'Bezeichnung ~ "test" AND') == []

    result = autosuggest(session, 'Bezeichnung ~ "test" AND ')
    assert result and all(item.type == AutoSuggestType.FIELD_NAME for item in result)


def test_autosuggest_grouping_operator_after_paren(session: Session):
    assert autosuggest(session, '(Bezeichnung ~ "test")') == []

    assert autosuggest(session, '(Bezeichnung ~ "test") ') == [
        AutoSuggestItem(AutoSuggestType.OPERATOR, "AND"),
        AutoSuggestItem(AutoSuggestType.OPERATOR, "OR"),
    ]


@pytest.mark.parametrize(
    ("s", "result"),
    [
        (
            "beteil",
            [
                AutoSuggestItem(
                    AutoSuggestType.FIELD_NAME, "Beteiligte", FieldCategory.BETEILIGTE
                )
            ],
        ),
        (
            "standorttyp ",
            [
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "=", field_type=FieldType.CODE
                ),
                AutoSuggestItem(
                    AutoSuggestType.OPERATOR, "!=", field_type=FieldType.CODE
                ),
            ],
        ),
    ],
)
def test_autosuggest_is_case_insensitive(
    session: Session, s: str, result: list[AutoSuggestItem]
):
    assert autosuggest(session, s) == result


def test_autosuggest_field_after_opening_paren(session: Session):
    result = autosuggest(session, "( ")
    assert result and all(item.type == AutoSuggestType.FIELD_NAME for item in result)

    result = autosuggest(session, "(")
    assert result and all(item.type == AutoSuggestType.FIELD_NAME for item in result)


def test_autosuggest_bool_values(session: Session):
    result = autosuggest(session, "Aktuelle-Version-publiziert-oder-gelöscht = ")
    assert result == [
        AutoSuggestItem(AutoSuggestType.VALUE, "TRUE"),
        AutoSuggestItem(AutoSuggestType.VALUE, "FALSE"),
    ]


def test_autosuggest_translated_code_values(session: Session):
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

    assert autosuggest(session, "Standorttyp =") == []
    assert autosuggest(session, "Standorttyp = ") == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Ablagerungsstandort"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Betriebsstandort"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Unfallstandort"'),
    ]
    assert autosuggest(session, 'Standorttyp = "Abl') == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Ablagerungsstandort"'),
    ]

    assert autosuggest(session, 'Standorttyp = "Ablagerungsstandort"') == []

    # TODO - requires change in parser
    # assert autosuggest(session, "Standorttyp = Abl") == [
    #    AutoSuggestItem(AutoSuggestType.VALUE, '"Ablagerungsstandort"'),
    # ]

    assert autosuggest(session, 'Standorttyp = "site', lang=Language.DE) == []
    assert autosuggest(session, 'Standorttyp = "site', lang=Language.FR) == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"site de stockage"'),
    ]
    assert autosuggest(session, 'Standorttyp = "site de', lang=Language.FR) == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"site de stockage"'),
    ]

    assert autosuggest(session, "Standorttyp = \"d'", lang=Language.FR) == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"aire d\'entreprise"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"lieu d\'accident"'),
    ]


def test_custom_autosuggest_function_gemeinde(session: Session, generate_codes):
    make_gemeinde(session, "Aeugst am Albis", bfs_nummer=1, kanton="ZH")
    make_gemeinde(session, "Affoltern am Albis", bfs_nummer=2, kanton="ZH")
    make_gemeinde(session, "Bonstetten", bfs_nummer=3, kanton="ZH")
    make_gemeinde(session, "Obfelden", bfs_nummer=10, kanton="ZH")

    assert autosuggest(session, "Gemeinde = ") == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Aeugst am Albis"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Affoltern am Albis"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Bonstetten"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Obfelden"'),
    ]

    assert autosuggest(session, 'Gemeinde = "Alb') == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Aeugst am Albis"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Affoltern am Albis"'),
    ]
    assert autosuggest(session, 'Gemeinde = "Bonstetten"') == []

    assert autosuggest(session, "BFS-Gemeinde-Nr = ") == [
        AutoSuggestItem(AutoSuggestType.VALUE, "1"),
        AutoSuggestItem(AutoSuggestType.VALUE, "2"),
        AutoSuggestItem(AutoSuggestType.VALUE, "3"),
        AutoSuggestItem(AutoSuggestType.VALUE, "10"),
    ]

    assert autosuggest(session, "BFS-Gemeinde-Nr = 1") == [
        AutoSuggestItem(AutoSuggestType.VALUE, "1"),
        AutoSuggestItem(AutoSuggestType.VALUE, "10"),
    ]


def test_custom_autosuggest_function_sprache(session: Session):
    assert autosuggest(session, "Sprache = ") == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"DE"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"FR"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"IT"'),
    ]


def test_custom_autosuggest_function_grundbuch_bezeichnung(session: Session):
    make_nummerierungsbereich(session, "nb-1", bezeichnung="Aeugst")
    make_nummerierungsbereich(session, "nb-2", bezeichnung="Bonstetten")
    make_nummerierungsbereich(session, "nb-3", bezeichnung="Obfelden")
    # Duplicate bezeichnung to verify DISTINCT
    make_nummerierungsbereich(session, "nb-4", bezeichnung="Aeugst")

    assert autosuggest(session, "Grundbuch = ") == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Aeugst"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Bonstetten"'),
        AutoSuggestItem(AutoSuggestType.VALUE, '"Obfelden"'),
    ]

    assert autosuggest(session, 'Grundbuch = "Ae') == [
        AutoSuggestItem(AutoSuggestType.VALUE, '"Aeugst"'),
    ]

    assert autosuggest(session, 'Grundbuch = "xyz') == []


def test_autosuggest_does_not_fail_on_parse_errors(session: Session):
    assert autosuggest(session, ".12.202") == []  # invalid token
    assert autosuggest(session, "))) ") == []  # missing opening parens
    assert autosuggest(session, "AND AND ") == []  # invalid syntax
