from datetime import datetime

import pytest
from sqlalchemy.orm import Session
from utils import (
    make_ablagerung,
    make_beteiligter,
    make_beteiligter_geschaeft,
    make_betrieb,
    make_code,
    make_document_node,
    make_eigentuemer_standort,
    make_einzelereignis,
    make_flugplatz,
    make_gemeinde,
    make_grundwasser,
    make_kbsinfo,
    make_kinderspielplatz_gruenflaeche,
    make_kompartiment_stoffgruppe,
    make_kompartiment_stoffklasse,
    make_ktu,
    make_loeschschaum_einsatz,
    make_massnahme,
    make_nummerierungsbereich,
    make_nutzung_boden,
    make_oberflaechen_gewaesser,
    make_parzelle,
    make_pfas,
    make_pool,
    make_sachbearbeiter_standort,
    make_sanierungsziel,
    make_schiessanlage,
    make_sonstiger_beteiligte_standort,
    make_subj,
    make_translation,
    make_umweltschaden,
    make_umweltstoff,
    make_unfall,
    make_unfallstoff,
    make_vflz,
    make_vflz_beurteilung,
    make_vollzug,
)

from alma.constants import CodeListe, Language
from alma.models import codes
from alma.models.auth import User
from alma.models.bem import (
    BegruendungBewertung,
    BegruendungBewertungBetrieb,
    BegruendungBewertungPFAS,
    BegruendungPrioSanierungsbedarf,
    BegruendungPrioUntersuchungsbedarf,
    BemerkungAblagerung,
    BemerkungBetrieb,
    BemerkungEinzelereignis,
    BemerkungKinderspielplatzGruenflaeche,
    BemerkungMassnahme,
    BemerkungPFAS,
    BemerkungSanierung,
    BemerkungStandort,
    BemerkungSubjekt,
    BemerkungUmwelt,
    BemerkungUmweltschaden,
    BemerkungUnfall,
)
from alma.models.vflz import VflGeo
from alma.models.workflow import NodeKategorie
from alma.search import SearchField, get_search_results
from alma.search.advanced import TranslatedExpression, order_expressions
from alma.search.parser import Op
from alma.search.validation import ValidationError

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
    pytest.mark.usefixtures("as_lesen_geschaefte"),
]


def advanced_search(session: Session, test_user: User, query: str) -> list[int]:
    vflz_ids, direct_match = get_search_results(
        session, user=test_user, search=query, advanced=True
    )
    assert direct_match is False
    return sorted(vflz_ids)


def test_order_expressions():
    # "A and B or C and D" -> [A, B, and, C, D, and, or]
    assert order_expressions(
        [
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "A"),
            Op.AND,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "B"),
            Op.OR,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "C"),
            Op.AND,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "D"),
        ]
    ) == [
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "A"),
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "B"),
        Op.AND,
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "C"),
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "D"),
        Op.AND,
        Op.OR,
    ]

    # "A and (B or C) and D" -> [A, B, C, or, and, D, and]
    assert order_expressions(
        [
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "A"),
            Op.AND,
            Op.LPAREN,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "B"),
            Op.OR,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "C"),
            Op.RPAREN,
            Op.AND,
            TranslatedExpression(SearchField.BEZEICHNUNG, "~", "D"),
        ]
    ) == [
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "A"),
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "B"),
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "C"),
        Op.OR,
        Op.AND,
        TranslatedExpression(SearchField.BEZEICHNUNG, "~", "D"),
        Op.AND,
    ]


def test_advanced_query(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1, combined_id="A-1")
    vflz1.lang = Language.DE

    vflz2 = make_vflz(session, "Standort B", vfl_id=2, combined_id="B-1")
    vflz2.lang = Language.FR

    vflz3 = make_vflz(session, "Firma C", vfl_id=3, combined_id="X-1")
    vflz3.lang = Language.IT

    assert advanced_search(session, test_user, 'Bezeichnung ~ "Standort"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Bezeichnung = "Standort"') == []
    assert advanced_search(session, test_user, 'Bezeichnung = "Standort A"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Bezeichnung = "standort a"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Sprache = "DE"') == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Sprache = "FR"') == [vflz2.vflz_id]


def test_search_by_pool(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    pool1 = make_pool(session, "Pool-1")
    pool2 = make_pool(session, "Pool-2")
    pool1.add_vfl(vflz1.vfl_id)
    pool2.add_vfl(vflz1.vfl_id)

    assert advanced_search(session, test_user, 'Pool ~ "Pool-1"') == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Pool ~ "Pool"') == [vflz1.vflz_id]


def test_search_by_erfassung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz1.objekt.erfassungs_datum = datetime(2025, 1, 1)
    vflz2.objekt.erfassungs_datum = datetime(2025, 1, 2)

    assert advanced_search(session, test_user, "Erfassung < 2025-01-02") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Erfassung <= 2025-01-02") == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, "Erfassung = 2025-01-02") == [
        vflz2.vflz_id
    ]
    assert advanced_search(session, test_user, "Erfassung = 2025-1-2") == [
        vflz2.vflz_id
    ]
    assert advanced_search(session, test_user, "Erfassung > 2025-01-02") == []


def test_search_by_zeitraum_von_bis(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.zeitraum_von = datetime(2025, 1, 1)
    vflz1.zeitraum_bis = None

    assert advanced_search(session, test_user, "Zeitraum-Von >= 01.01.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Zeitraum-Von = 01.01.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Zeitraum-Von = 1.1.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Zeitraum-Von < 01.01.2025") == []
    assert advanced_search(session, test_user, "Zeitraum-Bis >= 01.01.2025") == []


def test_search_by_plz(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.postleitzahl = "12345"
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz2.postleitzahl = "56789"

    assert advanced_search(session, test_user, "PLZ = 12345") == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "PLZ = 56789") == [vflz2.vflz_id]


def test_search_by_flaeche(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    vflz1.vflgeo = VflGeo()
    vflz1.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 1],
                        [1, 1],
                        [1, 0],
                        [0, 0],
                    ],
                ],
            ],
        }
    )

    vflz2.vflgeo = VflGeo()
    vflz2.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 5],
                        [5, 5],
                        [5, 0],
                        [0, 0],
                    ],
                ],
            ],
        }
    )

    assert advanced_search(session, test_user, "Fläche >= 1") == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, "Fläche > 2") == [vflz2.vflz_id]


def test_search_by_flurname(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.flurname = "flurname-1"

    assert advanced_search(session, test_user, 'Flurname ~ "flurname-1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Flurname ~ "flurname-2"') == []


def test_search_by_x_y_koordinate(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    vflz1.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [0, 0, 0],
        }
    )

    vflz2.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [5, 5, 0],
        }
    )

    assert advanced_search(session, test_user, "X-Koordinate >= 0") == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, "Y-Koordinate > 2") == [vflz2.vflz_id]
    assert advanced_search(
        session, test_user, "X-Koordinate >= 0 AND Y-Koordinate < 4"
    ) == [vflz1.vflz_id]


def test_search_by_kanton(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    vflz1.gemeinde = make_gemeinde(
        session, "Aeugst am Albis", bfs_nummer=1, kanton="ZH"
    )
    vflz2.gemeinde = make_gemeinde(session, "Aarberg", bfs_nummer=301, kanton="BE")

    assert advanced_search(session, test_user, 'Kanton = "ZH"') == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Kanton = "BE"') == [vflz2.vflz_id]


def test_search_by_grunddaten_bemerkungen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    vflz1.bemerkung_standort = BemerkungStandort(bem="test-bemerkung-standort")

    assert advanced_search(session, test_user, 'Grunddaten-Bemerkungen ~ "test-"') == [
        vflz1.vflz_id
    ]
    assert (
        advanced_search(
            session, test_user, 'Grunddaten-Bemerkungen ~ "keine-bemerkung"'
        )
        == []
    )


def test_search_by_in_betrieb_nachsorge(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    vflz3 = make_vflz(session, "Standort C", vfl_id=3)

    vflz1.in_betrieb = True
    vflz1.nachsorge = False

    vflz2.in_betrieb = False
    vflz2.nachsorge = True

    vflz3.in_betrieb = None
    vflz3.nachsorge = None

    assert advanced_search(session, test_user, "In-Betrieb = TRUE") == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "In-Betrieb = FALSE") == [vflz2.vflz_id]
    assert advanced_search(session, test_user, "Nachsorge = TRUE") == [vflz2.vflz_id]
    assert advanced_search(session, test_user, "Nachsorge = FALSE") == [vflz1.vflz_id]


def test_search_by_deponietyp(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    typ1 = make_code(session, codes.DeponieTyp, "1")
    typ2 = make_code(session, codes.DeponieTyp, "2")
    vflz1.deponietyp = typ1
    vflz2.deponietyp = typ2

    for lang in Language:
        make_translation(session, lang=lang, key=str(typ1), value="deponie-typ-1")
        make_translation(session, lang=lang, key=str(typ2), value="deponie-typ-2")

    assert advanced_search(session, test_user, 'Deponietyp = "deponie-typ-1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Deponietyp = "deponie-typ-2"') == [
        vflz2.vflz_id
    ]


def test_search_by_kompartiment_von_bis(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    ab1 = make_ablagerung(session, vflz1)
    ab2 = make_ablagerung(session, vflz1)

    ab1.zeitraum_von = datetime(2025, 1, 1)
    ab1.zeitraum_bis = datetime(2025, 6, 1)

    ab2.zeitraum_von = datetime(2025, 2, 1)
    ab2.zeitraum_von = None

    assert advanced_search(session, test_user, "Kompartiment-Von = 01.01.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Kompartiment-Von >= 01.01.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Kompartiment-Bis > 01.01.1999") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Kompartiment-Von < 01.01.1999") == []


def test_search_by_kompartiment_bemerkungen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    ab1 = make_ablagerung(session, vflz1)
    ab1.bemerkung = BemerkungAblagerung("test-bemerkung-ablagerung")
    vflz2.bemerkung_standort = BemerkungStandort(bem="test-bemerkung-standort")

    assert advanced_search(
        session, test_user, 'Kompartiment-Bemerkungen ~ "test-"'
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session, test_user, 'Kompartiment-Bemerkungen ~ "test-bemerkung-standort"'
        )
        == []
    )


def test_search_by_stoffklasse(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    cls1 = make_code(session, codes.Stoffklasse, "klasse-1")
    cls2 = make_code(session, codes.Stoffklasse, "klasse-2")

    ab1 = make_ablagerung(session, vflz1)
    ab2 = make_ablagerung(session, vflz2)

    kksk1 = make_kompartiment_stoffklasse(session, ab1)
    kksk1.stoffklasse = cls1

    kksk2 = make_kompartiment_stoffklasse(session, ab1)
    kksk2.stoffklasse = cls2

    kksk3 = make_kompartiment_stoffklasse(session, ab2)
    kksk3.stoffklasse = cls2

    make_translation(session, lang=Language.DE, key=str(cls1), value="klasse-1")
    make_translation(session, lang=Language.DE, key=str(cls2), value="klasse-2")

    assert advanced_search(
        session, test_user, 'Stoffklasse-Stoffklasse = "klasse-1"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session, test_user, 'Stoffklasse-Stoffklasse = "klasse-2"'
    ) == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]


def test_search_by_stoffklasse_teilvolumen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    ab1 = make_ablagerung(session, vflz1)
    ab2 = make_ablagerung(session, vflz2)

    kksk1 = make_kompartiment_stoffklasse(session, ab1)
    kksk2 = make_kompartiment_stoffklasse(session, ab2)

    kksk1.teilvol = 10
    kksk2.teilvol = 20

    assert advanced_search(session, test_user, "Stoffklasse-Teilvolumen = 10") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Stoffklasse-Teilvolumen >= 10") == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, "Stoffklasse-Teilvolumen > 10") == [
        vflz2.vflz_id
    ]
    assert advanced_search(session, test_user, "Stoffklasse-Teilvolumen > 30") == []

    cls1 = make_code(session, codes.Stoffklasse, "klasse-1")
    make_translation(session, lang=Language.DE, key=str(cls1), value="klasse-1")
    kksk1.stoffklasse = cls1

    assert advanced_search(
        session,
        test_user,
        'Stoffklasse-Teilvolumen = 10 AND Stoffklasse-Stoffklasse = "klasse-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Stoffklasse-Teilvolumen = 10 OR Stoffklasse-Stoffklasse = "klasse-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Stoffklasse-Teilvolumen > 10 OR Stoffklasse-Stoffklasse = "klasse-1"',
    ) == [vflz1.vflz_id, vflz2.vflz_id]

    # No result, because while the filters would individually each apply to vflz1,
    # there is ablagerung that satisfies both criteria at the same time.
    assert (
        advanced_search(
            session,
            test_user,
            'Stoffklasse-Teilvolumen > 10 AND Stoffklasse-Stoffklasse = "klasse-1"',
        )
        == []
    )


def test_search_by_kompartiment_tiefe_volumen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    ab1 = make_ablagerung(session, vflz1)
    ab2 = make_ablagerung(session, vflz2)

    ab1.tiefe = "100 m"
    ab1.vol_kompartiment = 200
    ab2.tiefe = "200 m"
    ab2.vol_kompartiment = None

    assert (
        advanced_search(
            session,
            test_user,
            'Kompartiment-Tiefe ~ "100" AND Kompartiment-Volumen > 200',
        )
        == []
    )

    assert advanced_search(
        session, test_user, 'Kompartiment-Tiefe ~ "100" AND Kompartiment-Volumen <= 200'
    ) == [vflz1.vflz_id]

    assert advanced_search(session, test_user, 'Kompartiment-Tiefe ~ "200"') == [
        vflz2.vflz_id
    ]


def test_search_by_stoffklasse_von_bis(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    ab1 = make_ablagerung(session, vflz1)
    ab2 = make_ablagerung(session, vflz1)

    kksk1 = make_kompartiment_stoffklasse(session, ab1)
    kksk2 = make_kompartiment_stoffklasse(session, ab1)
    kksk3 = make_kompartiment_stoffklasse(session, ab2)

    kksk1.zeitraum_von = datetime(2025, 1, 1)
    kksk1.zeitraum_bis = datetime(2025, 2, 1)
    kksk2.zeitraum_von = datetime(2025, 1, 1)
    kksk2.zeitraum_bis = None
    kksk3.zeitraum_von = datetime(1999, 1, 1)
    kksk3.zeitraum_bis = datetime(2025, 1, 1)

    assert advanced_search(session, test_user, "Stoffklasse-Von = 1.1.2025") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Stoffklasse-Von = 1.1.1999") == [
        vflz1.vflz_id
    ]
    assert (
        advanced_search(
            session,
            test_user,
            "Stoffklasse-Von = 1.1.1999 AND Stoffklasse-Bis = 1.2.2025",
        )
        == []
    )
    assert advanced_search(
        session, test_user, "Stoffklasse-Von = 1.1.2025 AND Stoffklasse-Bis = 1.2.2025"
    ) == [vflz1.vflz_id]


def test_search_by_stoffgruppe_teilvolumen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    ab1 = make_ablagerung(session, vflz1)
    kksk1 = make_kompartiment_stoffklasse(session, ab1)
    kksg1 = make_kompartiment_stoffgruppe(session, kksk1)
    kksg2 = make_kompartiment_stoffgruppe(session, kksk1)

    grp1 = make_code(session, codes.StoffeKlasseI, "sg-I-1")
    grp2 = make_code(session, codes.StoffeKlasseII, "sg-II-1")

    make_translation(session, lang=Language.DE, key=str(grp1), value="Stoffgruppe I: 1")
    make_translation(
        session, lang=Language.DE, key=str(grp2), value="Stoffgruppe II: 1"
    )

    kksg1.teilvol = 100
    kksg1.stoffgruppe = grp1
    kksg2.teilvol = 200
    kksg2.stoffgruppe = grp2

    assert advanced_search(
        session, test_user, 'Stoffgruppe-Stoffgruppe = "Stoffgruppe I: 1"'
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            'Stoffgruppe-Stoffgruppe = "Stoffgruppe I: 1" AND Stoffgruppe-Teilvolumen > 100',
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        'Stoffgruppe-Stoffgruppe = "Stoffgruppe I: 1" OR Stoffgruppe-Teilvolumen > 100',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Stoffgruppe-Stoffgruppe = "Stoffgruppe II: 1" AND Stoffgruppe-Teilvolumen > 100',
    ) == [vflz1.vflz_id]


def test_search_by_eva_nummer(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)
    bet1 = make_betrieb(session, vflz1)
    bet1.eva = "eva-1"
    bet2 = make_betrieb(session, vflz2)
    bet2.eva = "eva-2"

    assert advanced_search(session, test_user, 'EVA-Nummer ~ "eva-1"') == [
        vflz1.vflz_id
    ]


def test_combined_search_for_fields_of_betrieb_and_schiessanlage(
    session: Session, test_user
):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    sa1 = make_schiessanlage(session, vflz1)
    sa2 = make_schiessanlage(session, vflz1)
    sa1.firma_name = "Schiessanlage-1"
    sa1.hat_kugelfang = False
    sa2.firma_name = "Schiessanlage-2"
    sa2.hat_kugelfang = True

    assert advanced_search(
        session, test_user, 'Firma-Name/Schiessanlage-Name ~ "Schiessanlage-1"'
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "Kugelfang-vorhanden = TRUE") == [
        vflz1.vflz_id
    ]

    assert (
        advanced_search(
            session,
            test_user,
            'Firma-Name/Schiessanlage-Name ~ "Schiessanlage-1" AND Kugelfang-vorhanden = TRUE',
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        'Firma-Name/Schiessanlage-Name ~ "Schiessanlage-1" AND Kugelfang-vorhanden = FALSE',
    ) == [vflz1.vflz_id]


def test_search_by_branche_branche_noga(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    branche_asw = make_code(session, codes.BrancheASW, "1")
    branche_noga = make_code(session, codes.BrancheNOGA, "1")
    bet1 = make_betrieb(session, vflz1)
    bet2 = make_betrieb(session, vflz1)
    bet1.branche_asw = branche_asw
    bet2.branche_noga = branche_noga

    make_translation(
        session, lang=Language.DE, key=str(branche_asw), value="Branche ASW 1"
    )
    make_translation(
        session, lang=Language.DE, key=str(branche_noga), value="Branche NOGA 1"
    )

    assert advanced_search(session, test_user, 'Branche = "Branche ASW 1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Branche-NOGA = "Branche NOGA 1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(
        session,
        test_user,
        'Branche = "Branche ASW 1" OR Branche-NOGA = "Branche NOGA 1"',
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            'Branche = "Branche ASW 1" AND Branche-NOGA = "Branche NOGA 1"',
        )
        == []
    )


def test_search_by_firma_name_plz_ort(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    bet1 = make_betrieb(session, vflz1)
    bet2 = make_betrieb(session, vflz1)
    bet1.firma_name = "Firma-1"
    bet1.firma_plz = "12345"
    bet2.firma_ort = "Bern"

    assert advanced_search(
        session, test_user, 'Firma-Name/Schiessanlage-Name ~ "Firma-1"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Name/Schiessanlage-Name ~ "Firma-1" AND Firma-PLZ/Schiessanlage-PLZ = 12345',
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            'Firma-Name/Schiessanlage-Name ~ "Firma-1" AND Firma-Ort/Schiessanlage-Ort ~ "Bern"',
        )
        == []
    )
    assert advanced_search(
        session, test_user, 'Firma-Ort/Schiessanlage-Ort ~ "Bern"'
    ) == [vflz1.vflz_id]


def test_search_by_firma_von_bis(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    bet1 = make_betrieb(session, vflz1)
    bet1.zeitraum_von = datetime(2025, 1, 1)
    bet1.zeitraum_bis = datetime(2025, 2, 1)

    assert advanced_search(
        session, test_user, "Firma-Von/Schiessanlage-Von = 1.1.2025"
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(session, test_user, "Firma-Von/Schiessanlage-Von < 1.1.2025")
        == []
    )
    assert advanced_search(
        session, test_user, "Firma-Bis/Schiessanlage-Bis = 1.2.2025"
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(session, test_user, "Firma-Bis/Schiessanlage-Bis > 1.2.2025")
        == []
    )


def test_search_by_schiessanlage_typ_kugelfang_scheibenzahl_schussanzahl(
    session: Session, test_user
):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    typ1 = make_code(session, codes.SchiessanlageTyp, "1")
    make_translation(session, lang=Language.DE, key=str(typ1), value="Typ-1")

    sa1 = make_schiessanlage(session, vflz1)
    sa1.hat_kugelfang = True
    sa1.schusszahl = 10
    sa1.scheibenzahl = 5
    sa1.typ = typ1

    assert advanced_search(session, test_user, "KugelFang-Vorhanden = TRUE") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Schussanzahl = 10") == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "Schussanzahl > 10") == []
    assert advanced_search(
        session, test_user, "Schussanzahl <= 10 AND Scheibenzahl >= 5"
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Schiessanlage-Typ = "Typ-1"') == [
        vflz1.vflz_id
    ]


def test_search_by_firma_betriebsgroesse_relevant_mobile_stoffe_untersuchungsstand_beurteilung(
    session: Session, test_user
):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    b1 = make_code(session, codes.Beurteilung, "B1")
    b2 = make_code(session, codes.Beurteilung, "B2")
    u1 = make_code(session, codes.UntersuchungsStand, "U1")
    make_translation(session, lang=Language.DE, key=str(b1), value="Beurteilung-1")
    make_translation(session, lang=Language.DE, key=str(b2), value="Beurteilung-2")
    make_translation(
        session, lang=Language.DE, key=str(u1), value="Untersuchungsstand-1"
    )

    bet1 = make_betrieb(session, vflz1)
    bet1.groesse = 10
    bet1.beurteilung = b1
    bet1.untersuchungs_stand = u1
    bet1.relevant = True
    bet1.mobile_stoffe = False

    bet2 = make_betrieb(session, vflz1)
    bet2.beurteilung = b2
    bet2.relevant = False
    bet2.mobile_stoffe = True

    assert advanced_search(session, test_user, "Betriebsgrösse = 10") == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        "Firma-Katasterrelevanz/Schiessanlage-Katasterrelevanz = TRUE",
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        "Firma-Katasterrelevanz/Schiessanlage-Katasterrelevanz = FALSE",
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "mobile-Stoffe = TRUE") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "mobile-Stoffe = FALSE") == [
        vflz1.vflz_id
    ]

    assert advanced_search(
        session,
        test_user,
        'Firma-Beurteilung/Schiessanlage-Beurteilung = "Beurteilung-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Beurteilung/Schiessanlage-Beurteilung = "Beurteilung-2"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Untersuchungsstand/Schiessanlage-Untersuchungsstand = "Untersuchungsstand-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Untersuchungsstand/Schiessanlage-Untersuchungsstand = "Untersuchungsstand-1" AND Firma-Beurteilung/Schiessanlage-Beurteilung = "Beurteilung-1"',
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            'Firma-Untersuchungsstand/Schiessanlage-Untersuchungsstand = "Untersuchungsstand-1" AND Firma-Beurteilung/Schiessanlage-Beurteilung = "Beurteilung-2"',
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        'Firma-Untersuchungsstand/Schiessanlage-Untersuchungsstand = "Untersuchungsstand-1" OR Firma-Beurteilung/Schiessanlage-Beurteilung = "Beurteilung-2"',
    ) == [vflz1.vflz_id]


def test_search_by_firma_bemerkungen_begruendung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    bet1 = make_betrieb(session, vflz1)
    bet1.bemerkung = BemerkungBetrieb(bem="Bemerkung-1")
    bet1.begruendung_bewertung = BegruendungBewertungBetrieb(bem="Begründung-1")

    bet2 = make_betrieb(session, vflz1)
    bet2.bemerkung = BemerkungBetrieb(bem="Bemerkung-2")

    assert advanced_search(
        session, test_user, 'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "Bemerkung"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "Bemerkung-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "Bemerkung-2"',
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session, test_user, 'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "ZZZ"'
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        'Begründung-Bewertung-Betrieb/Begründung-Bewertung-Schiessanlage ~ "Begründung-1"',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "Bemerkung-1" AND Begründung-Bewertung-Betrieb/Begründung-Bewertung-Schiessanlage ~ "Begründung-1"',
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            'Firma-Bemerkungen/Schiessanlage-Bemerkungen ~ "Bemerkung-2" AND Begründung-Bewertung-Betrieb/Begründung-Bewertung-Schiessanlage ~ "Begründung-1"',
        )
        == []
    )


def test_search_by_firma_x_y_koordinate(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    bem1 = make_betrieb(session, vflz1)
    bem1.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [0, 0],
        }
    )

    bem2 = make_betrieb(session, vflz1)
    bem2.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [5, 5],
        }
    )

    assert advanced_search(
        session, test_user, "Firma-X-Koordinate/Schiessanlage-X-Koordinate >= 0"
    ) == [
        vflz1.vflz_id,
    ]
    assert advanced_search(
        session, test_user, "Firma-X-Koordinate/Schiessanlage-X-Koordinate > 0"
    ) == [
        vflz1.vflz_id,
    ]
    assert (
        advanced_search(
            session, test_user, "Firma-X-Koordinate/Schiessanlage-X-Koordinate > 5"
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        "Firma-X-Koordinate/Schiessanlage-X-Koordinate = 5 AND Firma-Y-Koordinate/Schiessanlage-Y-Koordinate = 5",
    ) == [vflz1.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            "Firma-X-Koordinate/Schiessanlage-X-Koordinate = 0 AND Firma-Y-Koordinate/Schiessanlage-Y-Koordinate = 5",
        )
        == []
    )


def test_search_for_unfall_unfallstoff(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    gen1 = make_code(session, codes.Genauigkeit, "gen1")
    stoff1 = make_code(session, codes.Stoff, "stoff1")
    stoff2 = make_code(session, codes.Stoff, "stoff2")

    make_translation(session, lang=Language.DE, key=str(gen1), value="genau")
    make_translation(session, lang=Language.DE, key=str(stoff1), value="Stoff-1")
    make_translation(session, lang=Language.DE, key=str(stoff2), value="Stoff-2")

    u1 = make_unfall(session, vflz1)
    u1.name = "Unfall-1"
    u1.genauigkeit_zeitpunkt = gen1
    u1.bemerkung = BemerkungUnfall(bem="Bemerkung-Unfall-1")
    u1.zeitpunkt = datetime(2025, 1, 1)
    us1 = make_unfallstoff(session, u1)
    us1.stoff = stoff1
    us1.stoffmng = 100
    us1.ausgelaufen = 10
    us1.zurueckgewonnen = 1

    u2 = make_unfall(session, vflz2)
    u2.name = "Unfall-2"
    us2 = make_unfallstoff(session, u2)
    us2.stoff = stoff2
    us2.ausgelaufen = 5

    assert advanced_search(session, test_user, 'Unfall-Name ~ "Unfall-1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(
        session,
        test_user,
        'Unfall-Genauigkeit = "genau" AND Unfall-Bemerkung ~ "Bemerkung-Unfall" AND Unfall-Zeitpunkt = 01.01.2025',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Unfallstoff-Stoffe-und-Stoffgemische = "Stoff-1" AND Unfallstoff-ausgelaufen >= 10 AND Unfallstoff-zurückgewonnen > 0 AND Unfallstoff-Restmenge = 100',
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Unfallstoff-Stoffe-und-Stoffgemische = "Stoff-2" AND Unfallstoff-Ausgelaufen < 10',
    ) == [vflz2.vflz_id]


def test_search_for_natuerliches_umfeld(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    gsb1 = make_code(session, codes.Gewaesserschutzbereich, "gsb1")
    gsz1 = make_code(session, codes.Gewaesserschutzzone, "gsz1")
    dls1 = make_code(session, codes.Durchlaessigkeit, "dls1")
    ja = codes.JaNeinUnbekannt.from_db(session, f"code:{CodeListe.JaNeinUnbekannt}:ja")
    unbek = codes.JaNeinUnbekannt.from_db(
        session, f"code:{CodeListe.JaNeinUnbekannt}:unbek"
    )

    make_translation(session, lang=Language.DE, key=str(gsb1), value="GSB-1")
    make_translation(session, lang=Language.DE, key=str(gsz1), value="GSZ-1")
    make_translation(session, lang=Language.DE, key=str(dls1), value="durchlässig")
    make_translation(session, lang=Language.DE, key=str(ja), value="Ja")
    make_translation(session, lang=Language.DE, key=str(unbek), value="unbekannt")

    vflz1.gws_bereich = gsb1
    vflz1.gws_zone = gsz1
    vflz1.durchlaessigkeit = dls1
    vflz1.karstgeb = ja
    vflz1.bemerkung_umwelt = BemerkungUmwelt(bem="Bemerkung-Umwelt-1")

    vflz2.gws_bereich = gsb1
    vflz2.karstgeb = unbek

    session.flush()

    assert advanced_search(session, test_user, 'Gewässerschutzbereich = "GSB-1"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(
        session, test_user, 'Gewässerschutzbereich = "GSB-1" AND Schutzzone = "GSZ-1"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        'Durchlässigkeit-Untergrund = "durchlässig" AND Karstgebiet = "ja"',
    ) == [
        vflz1.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Karstgebiet = "unbekannt"') == [
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Umwelt-Bemerkungen ~ "Umwelt-1"') == [
        vflz1.vflz_id,
    ]


def test_search_for_grundwasser(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    gwas1 = make_grundwasser(session, vflz1)
    gwas2 = make_grundwasser(session, vflz2)

    rl1 = make_code(session, codes.RelativeLageGrundwasser, "rl1")
    nu1 = make_code(session, codes.NutzungGrundwasserAbstrom, "nu1")
    make_translation(session, lang=Language.DE, key=str(rl1), value="Lage-1")
    make_translation(session, lang=Language.DE, key=str(nu1), value="Nutzung-1")

    gwas1.relative_lage = rl1
    gwas1.flurabstand = 100
    gwas1.nutzung = None
    gwas1.distanz = None

    gwas2.relative_lage = None
    gwas2.flurabstand = None
    gwas2.nutzung = nu1
    gwas2.distanz = 20

    assert advanced_search(
        session, test_user, 'Relative-Lage-zum-Grundwasser = "Lage-1"'
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "Flurabstand = 100") == [vflz1.vflz_id]
    assert advanced_search(
        session, test_user, 'Nutzung-Grundwasser-im-Abstrombereich = "Nutzung-1"'
    ) == [vflz2.vflz_id]
    assert advanced_search(
        session, test_user, "Distanz-zur-GW-Nutzung-im-Abstrombereich <= 20"
    ) == [vflz2.vflz_id]


def test_search_for_oberflaechengewaesser(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    art1 = make_code(session, codes.GewaesserArt, "art1")
    bau1 = make_code(session, codes.GewaesserBau, "bau1")
    lage1 = make_code(session, codes.RelativeLageOberflaechenGewaesser, "lage1")

    make_translation(session, lang=Language.DE, key=str(art1), value="Gewässerart-1")
    make_translation(session, lang=Language.DE, key=str(bau1), value="Gewässerbau-1")
    make_translation(session, lang=Language.DE, key=str(lage1), value="Lage-1")

    ogw1 = make_oberflaechen_gewaesser(session, vflz1)
    ogw1.name = "Oberflächengewässer-1"
    ogw1.distanz = 100
    ogw1.art_gewaesser = art1
    ogw1.bau_gewaesser = bau1
    ogw1.relative_lage = lage1

    assert advanced_search(
        session, test_user, 'Name-Oberflächengewässer ~ "Oberfl"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        """
        Distanz-zum-Oberflächengewässer <= 100
        AND Art-des-Oberflächengewässers = "Gewässerart-1"
        AND Gewässerbau = "Gewässerbau-1"
        AND Relative-Lage-zum-Oberflächengewässer = "Lage-1"
    """,
    ) == [vflz1.vflz_id]


def test_search_for_umweltstoffe(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    usg1 = make_code(session, codes.UmweltStoffgruppe, "usg1")
    s1 = make_code(session, codes.StoffgruppeCKW, "s1")
    gub1 = make_code(session, codes.GefaehrdeteUmweltbereiche, "gub1")
    usb1 = make_code(session, codes.UmweltStoffBeurteilung, "usb1")

    make_translation(session, lang=Language.DE, key=str(usg1), value="Stoffgruppe-1")
    make_translation(session, lang=Language.DE, key=str(s1), value="Stoff-1")
    make_translation(session, lang=Language.DE, key=str(gub1), value="Umweltbereich-1")
    make_translation(session, lang=Language.DE, key=str(usb1), value="Beurteilung-1")

    us1 = make_umweltstoff(session, vflz1)
    us1.stoff_gruppe = usg1
    us1.stoff = s1
    us1.gefaehrdete_bereiche = gub1
    us1.beurteilung = usb1

    assert advanced_search(session, test_user, 'Stoffgruppe = "Stoffgruppe-1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(
        session,
        test_user,
        """
        spezifischer-Stoff = "Stoff-1"
        AND Umwelt = "Umweltbereich-1"
        AND Umweltstoffe-Beurteilung = "Beurteilung-1"
    """,
    ) == [vflz1.vflz_id]


def test_search_for_nutzungeng_gelaende(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    fn1 = make_code(session, codes.Flaechennutzung, "fn1")
    fnw1 = make_code(session, codes.FlaechennutzungWald, "fnw1")

    make_translation(session, lang=Language.DE, key=str(fn1), value="Nutzung-1")
    make_translation(session, lang=Language.DE, key=str(fnw1), value="Nutzung-Wald-1")

    n1 = make_nutzung_boden(session, vflz1)
    n1.nutzungsart = fn1
    n1.aktuelle_nutzung = fnw1

    assert advanced_search(
        session,
        test_user,
        'Nutzungszone = "Nutzung-1" AND Aktuelle-Nutzung = "Nutzung-Wald-1"',
    ) == [vflz1.vflz_id]


def test_search_for_umwelteinwirkungen(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    ub1 = make_code(session, codes.Umweltbereich, "ub1")
    usb1 = make_code(session, codes.UmweltschaedenBoden, "usb1")

    make_translation(session, lang=Language.DE, key=str(ub1), value="Bereich-1")
    make_translation(session, lang=Language.DE, key=str(usb1), value="Schaden-Boden-1")

    us1 = make_umweltschaden(session, vflz1)
    us1.art_schaden = ub1
    us1.schaeden = usb1
    us1.bemerkung = BemerkungUmweltschaden(bem="Bemerkung-Umweltschaden-1")

    assert advanced_search(
        session,
        test_user,
        """
        Gefährdete-Umweltbereiche = "Bereich-1"
        AND Festgestellte-Einwirkungen = "Schaden-Boden-1"
        AND Bemerkung-Umweltschaden ~ "Bemerkung-Umweltschaden"
        """,
    ) == [vflz1.vflz_id]


def test_search_for_vorkommnisse(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    ee1 = make_code(session, codes.Einzelereignis, "ee1")

    make_translation(session, lang=Language.DE, key=str(ee1), value="Ereignis-1")

    e1 = make_einzelereignis(session, vflz1)
    e1.einzelereignis = ee1
    e1.datum = datetime(2025, 1, 1)
    e1.bemerkung = BemerkungEinzelereignis(bem="Bemerkung-Einzelereignis")

    assert advanced_search(
        session,
        test_user,
        """
        Vorkommnis-Datum = 01.01.2025
        AND Vorkommnis = "Ereignis-1"
        AND Bemerkung-Einzelereignis ~ "Bemerkung-Einzelereignis"
        """,
    ) == [vflz1.vflz_id]


def test_search_for_beurteilung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    be1 = make_code(session, codes.Beurteilung, "be1")
    bs1 = make_code(session, codes.Bearbeitungsstand, "bs1")
    us1 = make_code(session, codes.UntersuchungsStand, "us1")

    make_kbsinfo(session, be1, belastet=True, color="#ff0000")

    make_translation(session, lang=Language.DE, key=str(be1), value="Beurteilung-1")
    make_translation(
        session, lang=Language.DE, key=str(bs1), value="Bearbeitungsstand-1"
    )
    make_translation(
        session, lang=Language.DE, key=str(us1), value="Untersuchungsstand-1"
    )

    beu1 = make_vflz_beurteilung(session, vflz1)
    beu1.beurteilung = be1
    vflz1.bearbeitungs_stand = bs1
    vflz1.untersuchungs_stand = us1
    vflz1.begruendung_bewertung = BegruendungBewertung("Begründung-Bewertung-1")
    vflz1.rechtskraft = True
    vflz1.publizieren = True
    vflz1.dat_rechtskraft = datetime(2025, 1, 1)
    vflz1.dat_publizieren = datetime(2025, 2, 1)

    assert advanced_search(
        session,
        test_user,
        """
        Beurteilung = "Beurteilung-1"
        AND Begründung-Beurteilung ~ "Begründung-Bewertung-1"
        AND Bearbeitungsstand = "Bearbeitungsstand-1"
        AND Untersuchungsstand = "Untersuchungsstand-1"
        AND Rechtskräftig = TRUE
        AND Datum-Ersteintrag = 01.01.2025
        AND Datum-Publikation-im-KbS = 01.02.2025
        AND Aktuellste-Publikation-im-KbS = TRUE
        AND Aktuelle-Version-publiziert-oder-gelöscht = TRUE
        """,
    ) == [vflz1.vflz_id]


def test_search_for_massnahme(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    ma1 = make_code(session, codes.Massnahme, "ma1")
    make_translation(session, lang=Language.DE, key=str(ma1), value="Massnahme-1")

    m1 = make_massnahme(session, vflz1)
    m1.massnahme = ma1
    m1.ang_massnahme = datetime(2025, 1, 1)
    m1.dat_massnahme = datetime(2025, 2, 1)
    m1.bemerkung = BemerkungMassnahme(bem="Bemerkung-Massnahme-1")

    assert advanced_search(
        session,
        test_user,
        """
        Massnahme = "Massnahme-1"
        AND Massnahme-Angeordnet-am < 15.01.2025
        AND Massnahme-Erledigt-am > 20.01.2025
        AND Massnahme-Bemerkung ~ "Bemerkung-Massnahme-1"
        """,
    ) == [vflz1.vflz_id]


def test_search_for_beteiligte(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    subj1 = make_subj(session, name="Muster", vorname="Max", taetigkeit="Manager")
    subj2 = make_subj(session, name="Eigentümer", vorname="Egon")

    ba1 = make_code(session, codes.BeziehungsartSonstige, "ba1")
    ba2 = make_code(session, codes.BeziehungsartEigentum, "ba2")

    make_translation(session, lang=Language.DE, key=str(ba1), value="Auskunftsperson")
    make_translation(session, lang=Language.DE, key=str(ba2), value="Mieter")

    bet1 = make_beteiligter(session, vflz1.vflz_id, subj1.subj_id)
    bet2 = make_beteiligter(session, vflz2.vflz_id, subj1.subj_id)
    make_beteiligter(session, vflz1.vflz_id, subj2.subj_id, is_eigentuemer=True)

    grun1 = make_parzelle(session, "1")

    make_sonstiger_beteiligte_standort(session, bet1.bet_id, bez_art_code="ba1")
    make_eigentuemer_standort(session, bet2.bet_id, grun1.grun_id, bez_art_code="ba2")

    assert advanced_search(session, test_user, 'Beteiligte ~ "Muster Max"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(
        session, test_user, 'Beteiligte ~ "Muster Max, Manager"'
    ) == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Beteiligte ~ "Eigentümer"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Vorname ~ "Max"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Vorname ~ "Muster"') == []
    assert advanced_search(session, test_user, 'Nachname ~ "Max"') == []
    assert advanced_search(session, test_user, 'Nachname ~ "Muster"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Tätigkeit ~ "Muster"') == []
    assert advanced_search(session, test_user, 'Tätigkeit ~ "Manager"') == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, 'Standort-Eigentümer ~ "Max"') == []
    assert advanced_search(session, test_user, 'Standort-Eigentümer ~ "Egon"') == [
        vflz1.vflz_id
    ]

    assert advanced_search(
        session, test_user, 'Beteiligte ~ "Max" AND Standort-Eigentümer ~ "Egon"'
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session, test_user, 'Beteiligte ~ "Max" OR Standort-Eigentümer ~ "Egon"'
    ) == [vflz1.vflz_id, vflz2.vflz_id]

    assert advanced_search(
        session,
        test_user,
        'Beteiligte ~ "Max" AND Beziehungsart-Sonstige = "Auskunftsperson"',
    ) == [vflz1.vflz_id]

    assert advanced_search(
        session,
        test_user,
        'Beteiligte ~ "Max" AND Beziehungsart-Eigentum = "Mieter"',
    ) == [vflz2.vflz_id]


def test_search_for_beteiligte_beziehungsart_is_split_by_codelist(
    session: Session, test_user
):
    """
    The Beziehungsart-Eigentum/-Sachbearbeitung/-Sonstige search fields must
    only match codes from their own code list, even though they are all
    stored in the same BeteiligterStandort table.

    (Beziehungsart-Geschaefte is not modeled here, since the "bet_art" table
    has a DB check constraint that disallows this code list for standort
    level Beteiligte; it is only used for Task-Beziehungsart, see below).

    See ALMABASE-652
    """
    vflz_sonstige = make_vflz(session, "Standort Sonstige", vfl_id=1)
    vflz_eigentum = make_vflz(session, "Standort Eigentum", vfl_id=2)
    vflz_sachbearbeitung = make_vflz(session, "Standort Sachbearbeitung", vfl_id=3)

    subj = make_subj(session, name="Muster", vorname="Max")

    sonstige_code = make_code(session, codes.BeziehungsartSonstige, "so1")
    eigentum_code = make_code(session, codes.BeziehungsartEigentum, "ei1")
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "sa1")

    # All three codes share the same translation value, so the only thing
    # that can distinguish them at search time is the join/code list
    # restriction.
    for code in (sonstige_code, eigentum_code, sachbearbeitung_code):
        make_translation(session, lang=Language.DE, key=str(code), value="Beziehung")

    bet_sonstige = make_beteiligter(session, vflz_sonstige.vflz_id, subj.subj_id)
    make_sonstiger_beteiligte_standort(session, bet_sonstige.bet_id, bez_art_code="so1")

    bet_eigentum = make_beteiligter(session, vflz_eigentum.vflz_id, subj.subj_id)
    grun1 = make_parzelle(session, "1")
    make_eigentuemer_standort(
        session, bet_eigentum.bet_id, grun1.grun_id, bez_art_code="ei1"
    )

    bet_sachbearbeitung = make_beteiligter(
        session, vflz_sachbearbeitung.vflz_id, subj.subj_id
    )
    make_sachbearbeiter_standort(
        session, bet_sachbearbeitung.bet_id, bez_art_code="sa1"
    )

    assert advanced_search(
        session, test_user, 'Beziehungsart-Sonstige = "Beziehung"'
    ) == [vflz_sonstige.vflz_id]
    assert advanced_search(
        session, test_user, 'Beziehungsart-Eigentum = "Beziehung"'
    ) == [vflz_eigentum.vflz_id]
    assert advanced_search(
        session, test_user, 'Beziehungsart-Sachbearbeitung = "Beziehung"'
    ) == [vflz_sachbearbeitung.vflz_id]


def test_search_for_tasks_beziehungsart_is_split_by_codelist(
    session: Session, test_user
):
    """
    The Task-Beziehungsart-* search fields must only match codes from their
    own code list, even though they are all stored in the same
    BeteiligterGeschaeft table.

    See ALMABASE-652
    """
    vflz_eigentum = make_vflz(session, "Standort Eigentum", vfl_id=1)
    vflz_sachbearbeitung = make_vflz(session, "Standort Sachbearbeitung", vfl_id=2)
    vflz_sonstige = make_vflz(session, "Standort Sonstige", vfl_id=3)
    vflz_geschaefte = make_vflz(session, "Standort Geschaefte", vfl_id=4)

    subj = make_subj(session, name="Muster", vorname="Max")

    eigentum_code = make_code(session, codes.BeziehungsartEigentum, "ei1")
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "sa1")
    sonstige_code = make_code(session, codes.BeziehungsartSonstige, "so1")
    geschaefte_code = make_code(session, codes.BeziehungsartGeschaefte, "ge1")

    # All four codes share the same translation value, so the only thing
    # that can distinguish them at search time is the join/code list
    # restriction.
    for code in (eigentum_code, sachbearbeitung_code, sonstige_code, geschaefte_code):
        make_translation(session, lang=Language.DE, key=str(code), value="Beziehung")

    doc_eigentum = make_document_node(session, vflz_eigentum, "Document Eigentum")
    bet_eigentum = make_beteiligter_geschaeft(session, subjekt=subj, node=doc_eigentum)
    bet_eigentum.beziehungsart = eigentum_code

    doc_sachbearbeitung = make_document_node(
        session, vflz_sachbearbeitung, "Document Sachbearbeitung"
    )
    bet_sachbearbeitung = make_beteiligter_geschaeft(
        session, subjekt=subj, node=doc_sachbearbeitung
    )
    bet_sachbearbeitung.beziehungsart = sachbearbeitung_code

    doc_sonstige = make_document_node(session, vflz_sonstige, "Document Sonstige")
    bet_sonstige = make_beteiligter_geschaeft(session, subjekt=subj, node=doc_sonstige)
    bet_sonstige.beziehungsart = sonstige_code

    doc_geschaefte = make_document_node(session, vflz_geschaefte, "Document Geschaefte")
    bet_geschaefte = make_beteiligter_geschaeft(
        session, subjekt=subj, node=doc_geschaefte
    )
    bet_geschaefte.beziehungsart = geschaefte_code

    assert advanced_search(
        session, test_user, 'Task-Beziehungsart-Eigentum = "Beziehung"'
    ) == [vflz_eigentum.vflz_id]
    assert advanced_search(
        session, test_user, 'Task-Beziehungsart-Sachbearbeitung = "Beziehung"'
    ) == [vflz_sachbearbeitung.vflz_id]
    assert advanced_search(
        session, test_user, 'Task-Beziehungsart-Sonstige = "Beziehung"'
    ) == [vflz_sonstige.vflz_id]
    assert advanced_search(
        session, test_user, 'Task-Beziehungsart-Geschäfte = "Beziehung"'
    ) == [vflz_geschaefte.vflz_id]


def test_search_for_priorisierung_and_ziele(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    pu1 = make_code(session, codes.PrioUntersuchung, "pu1")
    ps1 = make_code(session, codes.PrioSanierung, "ps1")
    sa1 = make_code(session, codes.Sanierungsziel, "sa1")

    make_translation(
        session, lang=Language.DE, key=str(pu1), value="Prio-Untersuchung-1"
    )
    make_translation(session, lang=Language.DE, key=str(ps1), value="Prio-Sanierung-1")
    make_translation(session, lang=Language.DE, key=str(sa1), value="Sanierungsziel-1")

    beu1 = make_vflz_beurteilung(session, vflz1)
    beu1.prio_untersuch = pu1
    vflz1.begruendung_prio_untersuchungsbedarf = BegruendungPrioUntersuchungsbedarf(
        bem="Begründung-Prio-Untersuchungsbedarf-1"
    )

    beu2 = make_vflz_beurteilung(session, vflz2)
    beu2.prio_sanier = ps1
    vflz2.begruendung_prio_sanierungsbedarf = BegruendungPrioSanierungsbedarf(
        bem="Begründung-Prio-Sanierungsbedarf-1"
    )

    sz1 = make_sanierungsziel(session, vflz2)
    sz1.sanierungsziel = sa1
    sz1.bemerkung = BemerkungSanierung(bem="Bemerkung-Sanierungsziel-1")

    assert advanced_search(
        session,
        test_user,
        """
        Priorisierung-Untersuchungsbedarf = "Prio-Untersuchung-1"
        AND Begründung-Priorisierung-Untersuchungsbedarf ~ "Begründung-Prio-Untersuch"
        """,
    ) == [vflz1.vflz_id]
    assert advanced_search(
        session,
        test_user,
        """
        Priorisierung-Überwachungs-/Sanierungsbedarf = "Prio-Sanierung-1"
        AND Begründung-Priorisierung-Überwachungs-/Sanierungsbedarf ~ "Begründung-Prio-Sanier"
        """,
    ) == [vflz2.vflz_id]
    assert (
        advanced_search(
            session,
            test_user,
            """
        Priorisierung-Untersuchungsbedarf = "Prio-Untersuchung-1"
        AND Priorisierung-Überwachungs-/Sanierungsbedarf = "Prio-Sanierung-1"
        """,
        )
        == []
    )
    assert advanced_search(
        session,
        test_user,
        """
        Priorisierung-Untersuchungsbedarf = "Prio-Untersuchung-1"
        OR Priorisierung-Überwachungs-/Sanierungsbedarf = "Prio-Sanierung-1"
        """,
    ) == [vflz1.vflz_id, vflz2.vflz_id]
    assert advanced_search(
        session,
        test_user,
        """
        Sanierungsziel = "Sanierungsziel-1"
        AND Sanierungsziel-Bemerkungen ~ "Bemerkung-Sanierungsziel-1"
        """,
    ) == [vflz2.vflz_id]
    assert advanced_search(
        session,
        test_user,
        """
        Sanierungsziel = "Sanierungsziel-1"
        AND Sanierungsziel-Bemerkungen ~ "Bemerkung-Sanierungsziel-1"
        AND Begründung-Priorisierung-Überwachungs-/Sanierungsbedarf ~ "Begründung-Prio-Sanier"
        """,
    ) == [vflz2.vflz_id]


def test_search_by_bounding_box(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    vflz1.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [0, 0, 0],
        }
    )

    vflz2.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [5, 5, 0],
        }
    )

    assert advanced_search(session, test_user, "Karten-Ausschnitt = 0,0,5,5") == [
        vflz1.vflz_id,
        vflz2.vflz_id,
    ]
    assert advanced_search(session, test_user, "Karten-Ausschnitt = 4,4,5,5") == [
        vflz2.vflz_id
    ]
    assert advanced_search(session, test_user, "Karten-Ausschnitt = 6,0,7,1") == []


def test_search_for_tasks(session: Session, test_user):
    task_kategorie = make_code(session, codes.TaskKategorie, "kategorie")
    make_translation(session, Language.DE, str(task_kategorie), "kategorie")
    session.commit()

    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    doc1 = make_document_node(session, vflz1, "Document 1")
    doc1.started_at = datetime(2025, 1, 1)
    doc1.finished_at = datetime(2026, 1, 1)
    doc1.deadline = datetime(2027, 1, 1)
    doc1.document_ref = "my-reference"
    doc1.note = "notiz"
    doc1.kategorie = NodeKategorie(kategorie=task_kategorie)  # type: ignore
    code_typ_dokument = make_code(session, codes.TaskTyp, "document")
    code_status_offen = make_code(session, codes.TaskStatus, "started")
    make_translation(
        session, lang=Language.DE, key=str(code_typ_dokument), value="Dokument"
    )
    make_translation(
        session, lang=Language.DE, key=str(code_status_offen), value="offen"
    )

    assert advanced_search(session, test_user, 'Task-Titel ~ "Document 1"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Task-Typ = "Dokument"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, 'Task-Status = "offen"') == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Task-Start < 2025-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Task-Ende < 2026-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Task-Fälligkeit < 2027-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(
        session, test_user, 'Dokument-Referenz ~ "my-reference"'
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, "Task-Start < 2025-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Task-Ende < 2026-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "Task-Fälligkeit < 2027-02-01") == [
        vflz1.vflz_id
    ]
    assert advanced_search(
        session, test_user, 'Dokument-Referenz ~ "my-reference"'
    ) == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Notiz ~ "notiz"') == [vflz1.vflz_id]
    assert advanced_search(session, test_user, 'Task-Kategorie = "kategorie"') == [
        vflz1.vflz_id
    ]


def test_search_for_tasks_searches_accross_vfl_versions(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz_id1 = vflz1.vflz_id
    doc1 = make_document_node(session, vflz1, "Document 1")
    doc1.document_ref = "document-1-reference"

    vflz1.historize("1. Version historisiert")
    vflz_id2 = vflz1.vflz_id
    doc2 = make_document_node(session, vflz1, "Document 2")
    doc2.document_ref = "document-2-reference"

    vflz1.historize("2. Version historisiert")
    vflz_id3 = vflz1.vflz_id
    doc3 = make_document_node(session, vflz1, "Document 3")
    doc3.document_ref = "document-3-reference"

    assert vflz_id1 < vflz_id2 < vflz_id3

    assert advanced_search(session, test_user, 'Task-Titel ~ "Document 1"') == [
        vflz_id3
    ]
    assert advanced_search(session, test_user, 'Task-Titel ~ "Document 2"') == [
        vflz_id3
    ]
    assert advanced_search(session, test_user, 'Task-Titel ~ "Document 3"') == [
        vflz_id3
    ]

    assert advanced_search(
        session, test_user, 'Dokument-Referenz ~ "document-1-reference"'
    ) == [vflz_id3]
    assert advanced_search(
        session, test_user, 'Dokument-Referenz ~ "document-2-reference"'
    ) == [vflz_id3]
    assert advanced_search(
        session, test_user, 'Dokument-Referenz ~ "document-3-reference"'
    ) == [vflz_id3]

    assert advanced_search(
        session,
        test_user,
        """
        Task-Titel ~ "Document 1"
        AND Dokument-Referenz ~ "document-1-reference"
        """,
    ) == [vflz_id3]

    assert (
        advanced_search(
            session,
            test_user,
            """
        Task-Titel ~ "Document 1"
        AND Dokument-Referenz ~ "document-3-reference"
        """,
        )
        == []
    )


def test_search_for_tasks_beteiligte(session: Session, test_user):
    vflz = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    doc1 = make_document_node(session, vflz, "Document 1")
    subj = make_subj(
        session, name="Fleissig", vorname="Frieda", taetigkeit="Productownerin"
    )

    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "bas")
    bet = make_beteiligter_geschaeft(session, subjekt=subj, node=doc1)
    bet.beziehungsart = sachbearbeitung_code

    make_translation(session, Language.DE, str(sachbearbeitung_code), "Sachbearbeitung")

    assert advanced_search(session, test_user, 'Task-Beteiligte ~ "Frieda"') == [
        vflz.vflz_id
    ]
    assert advanced_search(
        session, test_user, 'Task-Beziehungsart-Sachbearbeitung = "Sachbearbeitung"'
    ) == [vflz.vflz_id]
    # Other Task-Beziehungsart-* fields must not accept a value from a
    # different code list, since each field is restricted to its own list.
    with pytest.raises(ValidationError):
        advanced_search(
            session, test_user, 'Task-Beziehungsart-Eigentum = "Sachbearbeitung"'
        )
    with pytest.raises(ValidationError):
        advanced_search(
            session, test_user, 'Task-Beziehungsart-Sonstige = "Sachbearbeitung"'
        )
    with pytest.raises(ValidationError):
        advanced_search(
            session, test_user, 'Task-Beziehungsart-Geschäfte = "Sachbearbeitung"'
        )
    assert advanced_search(
        session, test_user, 'Task-Titel ~ "Document 1" AND Task-Beteiligte ~ "Frieda"'
    ) == [vflz.vflz_id]


def test_search_by_bemerkung_adresse(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)
    subj.bemerkung = BemerkungSubjekt(bem="bar")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_sonstiger_beteiligte_standort(session, bet.bet_id)

    assert advanced_search(
        session,
        test_user,
        """
        Bemerkung-Adresse = "bar"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_name(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.name = "geops"

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Name = "geops"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_strasse(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.strasse = "geops-strasse"

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Strasse = "geops-strasse"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_ort(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.ort = "geops-ort"

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Ort = "geops-ort"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_plz(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.plz = "geops-plz"

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Postleitzahl = "geops-plz"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_eva(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.eva = "geops-eva"

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-EVA-Nummer = "geops-eva"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_bemerkung(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.bemerkung = BemerkungKinderspielplatzGruenflaeche(bem="bemerkung")

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Bemerkung = "bemerkung"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_katasterrelevanz(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.relevant = True

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Katasterrelevanz = TRUE
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_untersuchungsstand(session: Session, test_user):
    u1 = make_code(session, codes.UntersuchungsStand, "U1")
    make_translation(session, lang=Language.DE, key=str(u1), value="Untersuchungsstand")
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.untersuchungs_stand = u1

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Untersuchungsstand = "Untersuchungsstand"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_beurteilung(session: Session, test_user):
    u1 = make_code(session, codes.Beurteilung, "U1")
    make_translation(session, lang=Language.DE, key=str(u1), value="Beurteilung")
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.beurteilung = u1

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Beurteilung = "Beurteilung"
        """,
    ) == [vflz.vflz_id]


def test_search_by_eigentumsform(session: Session, test_user):
    ef = make_code(session, codes.Eigentumsform, "EF")
    make_translation(session, lang=Language.DE, key=str(ef), value="Eigentumsform")
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.eigentumsform = ef

    assert advanced_search(
        session,
        test_user,
        """
        Eigentumsform = "Eigentumsform"
        """,
    ) == [vflz.vflz_id]


def test_search_by_belastung_ueber_sanierungswert(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.belastung_ueber_sanierungswert = True

    assert advanced_search(
        session,
        test_user,
        """
        Belastung-Über-Sanierungswert = TRUE
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_typ(session: Session, test_user):
    typ = make_code(session, codes.KinderspielplatzGruenflaecheTyp, "typ")
    make_translation(session, lang=Language.DE, key=str(typ), value="Typ")
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.kinderspielplatz_gruenflache_typ = typ

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Typ = "Typ"
        """,
    ) == [vflz.vflz_id]


def test_search_by_altersstufe_kinder(session: Session, test_user):
    ak = make_code(session, codes.AltersstufeKinder, "alter")
    make_translation(session, lang=Language.DE, key=str(ak), value="alter")
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.altersstufen_kinder.append(ak)

    assert advanced_search(
        session,
        test_user,
        """
        Altersstufe-Kinder = "alter"
        """,
    ) == [vflz.vflz_id]


def test_search_by_kinderspielplatz_koordinate(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [1, 2],
        }
    )

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-X-Koordinate = 1
        """,
    ) == [vflz.vflz_id]

    assert advanced_search(
        session,
        test_user,
        """
        Kinderspielplatz/Grünfläche-Y-Koordinate = 2
        """,
    ) == [vflz.vflz_id]


def test_search_by_vollzug(session: Session, test_user):
    kuerzel_liste = session.get_one(codes.CodeListe, CodeListe.BehoerdenKuerzel)
    bmi_kuerzel_code = codes.BehoerdenKuerzel(codeliste=kuerzel_liste, code="BMI")

    session.add(bmi_kuerzel_code)
    session.commit()

    vflz = make_vflz(session, "My Site")
    vollzug = make_vollzug(session, vflz, bmi_kuerzel_code)
    vollzug.aktiv = True
    session.flush()

    assert advanced_search(
        session,
        test_user,
        """
        Vollzug = TRUE
        """,
    ) == [vflz.vflz_id]


def test_search_by_behoerde(session: Session, test_user):
    kuerzel_liste = session.get_one(codes.CodeListe, CodeListe.BehoerdenKuerzel)
    bmi_kuerzel_code = codes.BehoerdenKuerzel(codeliste=kuerzel_liste, code="BMI")
    make_translation(session, Language.DE, str(bmi_kuerzel_code), "BMI")

    session.add(bmi_kuerzel_code)
    session.commit()

    vflz = make_vflz(session, "My Site")
    vollzug = make_vollzug(session, vflz, bmi_kuerzel_code)
    vollzug.aktiv = True
    session.flush()

    assert advanced_search(
        session,
        test_user,
        """
        Behörde = "BMI"
        """,
    ) == [vflz.vflz_id]


def test_search_by_alternative_standortnummer(session: Session, test_user):
    kuerzel_liste = session.get_one(codes.CodeListe, CodeListe.BehoerdenKuerzel)
    bmi_kuerzel_code = codes.BehoerdenKuerzel(codeliste=kuerzel_liste, code="BMI")

    session.add(bmi_kuerzel_code)
    session.commit()

    vflz = make_vflz(session, "My Site")
    vollzug = make_vollzug(session, vflz, bmi_kuerzel_code, "alternative")
    vollzug.aktiv = True
    session.flush()

    assert advanced_search(
        session,
        test_user,
        """
        Alternative-Standortnummer = "alternative"
        """,
    ) == [vflz.vflz_id]


def test_search_by_parzelle(session: Session, test_user):
    a_gem = make_gemeinde(session, "A-Gemeinde", 1)
    b_gem = make_gemeinde(session, "B-Gemeinde", 2)

    vflz_geom_ewkt = "SRID=2056;MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)))"
    b_parzelle_geom_ewkt = (
        "SRID=2056;MULTIPOLYGON (((10 10, 10 11, 11 11, 11 10, 10 10)))"
    )

    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = VflGeo()
    vflz.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 1],
                        [1, 1],
                        [1, 0],
                        [0, 0],
                    ],
                ],
            ],
        }
    )
    a_p = make_parzelle(session, "such-gb-nummer", vflz_geom_ewkt, a_gem)
    make_parzelle(session, "such-gb-nummer", b_parzelle_geom_ewkt, b_gem)

    session.flush()

    assert a_p.wkb_geometry
    assert vflz.vflgeo
    assert vflz.vflgeo.wkb_geometry
    assert a_p.wkb_geometry == vflz.vflgeo.wkb_geometry
    assert advanced_search(
        session,
        test_user,
        """
        Parzelle = "such-gb-nummer"
        AND
        Gemeinde = "A-Gemeinde"
        """,
    ) == [vflz.vflz_id]


def test_search_by_nummerierungs_bereich(session: Session, test_user):
    nb1 = make_nummerierungsbereich(session, "NB-1")
    vflz_geom_ewkt = "SRID=2056;MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)))"

    parzelle = make_parzelle(session, "1", vflz_geom_ewkt)
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.vflgeo = VflGeo()
    vflz1.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 1],
                        [1, 1],
                        [1, 0],
                        [0, 0],
                    ],
                ],
            ],
        }
    )
    parzelle.nummerierungsbereich = nb1

    session.flush()

    assert advanced_search(
        session,
        test_user,
        'NBIdent = "NB-1"',
    ) == [vflz1.vflz_id]


def test_search_by_pfas_name(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    pfas1 = make_pfas(session, vflz1)
    pfas1.name = "PFAS-Name-1"
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-Name ~ "PFAS-Name-1"') == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_bemerkung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    pfas1 = make_pfas(session, vflz1)
    pfas1.bemerkung = BemerkungPFAS(bem="PFAS-Bemerkung-1")
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-Bemerkung ~ "PFAS-Bemerkung-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_typ(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    typ1 = make_code(session, codes.PFASTyp, "typ1")
    make_translation(session, lang=Language.DE, key=str(typ1), value="Typ-1")

    pfas1 = make_pfas(session, vflz1)
    pfas1.pfas_typ = typ1
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-Typ = "Typ-1"') == [vflz1.vflz_id]


def test_search_by_pfas_untersuchungsstand(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    us1 = make_code(session, codes.UntersuchungsStand, "us1")
    make_translation(
        session, lang=Language.DE, key=str(us1), value="Untersuchungsstand-1"
    )

    pfas1 = make_pfas(session, vflz1)
    pfas1.untersuchungs_stand = us1
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-Untersuchungsstand = "Untersuchungsstand-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_beurteilung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    be1 = make_code(session, codes.Beurteilung, "be1")
    make_translation(session, lang=Language.DE, key=str(be1), value="Beurteilung-1")

    pfas1 = make_pfas(session, vflz1)
    pfas1.beurteilung = be1
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-Beurteilung = "Beurteilung-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_branche(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    br1 = make_code(session, codes.BranchePFAS, "br1")
    make_translation(session, lang=Language.DE, key=str(br1), value="Branche-1")

    pfas1 = make_pfas(session, vflz1)
    pfas1.branche = br1
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-Branche = "Branche-1"') == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_begruendung_bewertung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    pfas1 = make_pfas(session, vflz1)
    pfas1.begruendung_bewertung = BegruendungBewertungPFAS("Begründung-Bewertung-1")
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'Begründung-Bewertung-PFAS ~ "Begründung-Bewertung-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_haltige_loeschmittel(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    loeschmittel = make_code(session, codes.LoeschmittelPFASHaltig, "lm1")
    make_translation(
        session, lang=Language.DE, key=str(loeschmittel), value="Löschmittel-1"
    )

    pfas1 = make_pfas(session, vflz1)
    pfas1.pfas_haltige_loeschmittel = [loeschmittel]
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-haltige-Löschmittel = "Löschmittel-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_freie_loeschmittel(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    loeschmittel = make_code(session, codes.LoeschmittelPFASFrei, "lm1")
    make_translation(
        session, lang=Language.DE, key=str(loeschmittel), value="Löschmittel-1"
    )

    pfas1 = make_pfas(session, vflz1)
    pfas1.pfas_freie_loeschmittel = [loeschmittel]
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-freie-Löschmittel = "Löschmittel-1"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_loeschschaum_einsatz(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    loeschschaum_einsatz_code = make_code(session, codes.LoeschschaumEinsatz, "le1")
    make_translation(
        session,
        lang=Language.DE,
        key=str(loeschschaum_einsatz_code),
        value="Handfeuerlöscher",
    )
    pfas1 = make_pfas(session, vflz1)
    loeschschaum_einsatz = make_loeschschaum_einsatz(session, pfas1)
    loeschschaum_einsatz.loeschschaum_einsatz = loeschschaum_einsatz_code

    assert advanced_search(
        session, test_user, 'PFAS-Löschschaum-Einsatz = "Handfeuerlöscher"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_haeufigkeit_nutzung(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    make_vflz(session, "Standort B", vfl_id=2)

    haeufigkeit_nutzung_code = make_code(
        session, codes.HaeufigkeitNutzungHandfeuerloescher, "hn1"
    )
    make_translation(
        session, lang=Language.DE, key=str(haeufigkeit_nutzung_code), value="oft"
    )

    pfas1 = make_pfas(session, vflz1)
    loeschschaum_einsatz = make_loeschschaum_einsatz(session, pfas1)
    loeschschaum_einsatz.haeufigkeit_nutzung = haeufigkeit_nutzung_code

    assert advanced_search(
        session, test_user, 'PFAS-Häufigkeit-der-Nutzung = "oft"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_strasse(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.strasse = "Teststrasse 1"
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-Strasse ~ "Teststrasse 1"') == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_plz(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.plz = "54321"
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-PLZ ~ "54321"') == [vflz1.vflz_id]


def test_search_by_pfas_ort(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.ort = "Testort"
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-Ort ~ "Testort"') == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_eva_nummer(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.eva = "EVA-123"
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, 'PFAS-EVA-Nummer ~ "EVA-123"') == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_zeitraum_von(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.zeitraum_von = datetime(2025, 1, 1)
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Zeitraum-Von = 01.01.2025") == [
        vflz1.vflz_id
    ]


def test_search_by_date_not_equal(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.zeitraum_von = datetime(2025, 1, 1)
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Zeitraum-Von != 01.02.2025") == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_zeitraum_bis(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.zeitraum_bis = datetime(2025, 12, 31)
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Zeitraum-Bis = 31.12.2025") == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_loeschmittel(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    loeschmittel = make_code(session, codes.LoeschmittelPFASHaltig, "lm2")
    make_translation(
        session, lang=Language.DE, key=str(loeschmittel), value="Löschmittel-2"
    )
    pfas1 = make_pfas(session, vflz1)
    pfas1.pfas_haltige_loeschmittel = [loeschmittel]
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-haltige-Löschmittel = "Löschmittel-2"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_katasterrelevanz(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.relevant = True
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Katasterrelevanz = TRUE") == [
        vflz1.vflz_id
    ]


def test_search_by_pfast_menge_schaumgemisch(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.menge_schaumgemisch = 123
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Menge-Schaumgemisch = 123") == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_menge_konzentrat(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.menge_konzentrat = 67
    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-Menge-Konzentrat = 67") == [
        vflz1.vflz_id
    ]


def test_search_by_pfas_beschreibungen_detail(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.beschreibungen_detail = "Detailbeschreibung"
    vflz1.pfas = [pfas1]

    assert advanced_search(
        session, test_user, 'PFAS-Beschreibungen-Detail ~ "Detailbeschreibung"'
    ) == [vflz1.vflz_id]


def test_search_by_pfas_x_and_y_koordinate(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    pfas1 = make_pfas(session, vflz1)
    pfas1.set_zentroid(
        {
            "type": "Point",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [1, 2],
        }
    )

    vflz1.pfas = [pfas1]

    assert advanced_search(session, test_user, "PFAS-X-Koordinate = 1") == [
        vflz1.vflz_id
    ]
    assert advanced_search(session, test_user, "PFAS-Y-Koordinate = 2") == [
        vflz1.vflz_id
    ]


def test_search_by_flugplatz(session: Session, test_user):
    bezeichnung_code = make_code(session, codes.FlugplatzBezeichnung, "FP-1")
    make_translation(session, Language.DE, str(bezeichnung_code), "FP-1")
    fp1 = make_flugplatz(session, "FP-1")
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz1.flugplatz = fp1

    assert advanced_search(
        session,
        test_user,
        'Flugplatz = "FP-1"',
    ) == [vflz1.vflz_id]


def test_search_by_ktu(session: Session, test_user):
    ktu_code = make_code(session, codes.KTU, "KTU-1")
    make_translation(session, Language.DE, str(ktu_code), "KTU-1")

    vflz = make_vflz(session, "My Site")
    vflz.ktu = make_ktu(session)
    vflz.ktu.ktu = ktu_code

    assert advanced_search(
        session,
        test_user,
        """
        KTU = "KTU-1"
        """,
    ) == [vflz.vflz_id]


def test_search_by_grundbuch_bezeichnung(session: Session, test_user):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)

    vflz_geom_ewkt = "SRID=2056;MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)))"
    # b_parzelle_geom_ewkt = (
    #     "SRID=2056;MULTIPOLYGON (((10 10, 10 11, 11 11, 11 10, 10 10)))"
    # )

    # vflz = make_vflz(session, "My Site")
    vflz.vflgeo = VflGeo()
    vflz.vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 1],
                        [1, 1],
                        [1, 0],
                        [0, 0],
                    ],
                ],
            ],
        }
    )

    nb = make_nummerierungsbereich(session, "1")
    nb.bezeichnung = "nummerierungsbereich"
    grun = make_parzelle(session, "parcel", vflz_geom_ewkt)
    grun.nummerierungsbereich = nb

    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet.bet_id, grun.grun_id)

    assert advanced_search(
        session,
        test_user,
        """
        Grundbuch = "nummerierungsbereich"
        """,
    ) == [vflz.vflz_id]
