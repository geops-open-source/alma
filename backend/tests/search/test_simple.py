from datetime import date, timedelta
from typing import Any

import pytest
from sqlalchemy.orm import Session
from utils import make_code, make_gemeinde, make_kbsinfo, make_vflz

from alma import constants
from alma.constants import Language
from alma.models import codes
from alma.models.subj import Beteiligter, Subjekt
from alma.models.translations import Translation
from alma.models.vflz import Beurteilung, EvaluationStatusData
from alma.search import SearchField, get_result_page, get_search_results

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
    pytest.mark.usefixtures("as_lesen_geschaefte"),
]


def test_simple_query(session: Session, test_user):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1, combined_id="A-1")
    vflz2 = make_vflz(session, "Standort B", vfl_id=2, combined_id="B-1")
    vflz3 = make_vflz(session, "Firma C", vfl_id=3, combined_id="X-1")
    session.commit()

    # direct match in Vflz.combined_id
    assert get_search_results(session, test_user, search="A-1") == (
        {vflz1.vflz_id},
        True,
    )

    # direct match in Vflz.combined_id, case insensitive
    assert get_search_results(session, test_user, search="a-1") == (
        {vflz1.vflz_id},
        True,
    )

    # substring match in Vflz.bezeichnung
    assert get_search_results(session, test_user, search="Standort") == (
        {
            vflz1.vflz_id,
            vflz2.vflz_id,
        },
        False,
    )

    # prefix match in standortnummer
    assert get_search_results(session, test_user, search="X") == (
        {vflz3.vflz_id},
        False,
    )

    # no match
    assert get_search_results(session, test_user, search="Y") == (set(), False)


def test_direct_match_for_standortnummer_returns_latest_version(
    session: Session, test_user
):
    vflz = make_vflz(session, "Standort A", vfl_id=1, combined_id="A-1")
    old_vflz_id = vflz.vflz_id
    vflz.historize("Historized")
    new_vflz_id = vflz.vflz_id
    session.commit()

    assert new_vflz_id > old_vflz_id

    assert get_search_results(session, test_user, search="A-1") == ({new_vflz_id}, True)


# ALMABASE-348
def test_no_direct_match_if_search_string_matches_more_than_one_standortnummer(
    session: Session, test_user
):
    vflz1 = make_vflz(session, "Standort A", vfl_id=1, combined_id="A01")
    vflz2 = make_vflz(
        session, "Standort A Teilstandort 1", vfl_id=2, combined_id="A01.01"
    )

    assert get_search_results(session, test_user, search="A01") == (
        {vflz1.vflz_id, vflz2.vflz_id},
        False,
    )
    assert get_search_results(session, test_user, search="A01.01") == (
        {vflz2.vflz_id},
        True,
    )


def test_simple_query_filter_by_bewertung_multiple(session: Session, test_user):
    codeliste_beurteilung = session.get_one(
        codes.CodeListe, constants.CodeListe.Beurteilung
    )
    beurteilung_test = session.get_one(
        codes.Beurteilung, (codeliste_beurteilung.c_cli_id, "test")
    )
    beurteilung_test2 = session.get_one(
        codes.Beurteilung, (codeliste_beurteilung.c_cli_id, "test2")
    )

    beurteilung_test3 = codes.Beurteilung(codeliste=codeliste_beurteilung, code="test3")
    session.add(beurteilung_test3)

    standort_a = make_vflz(session, "Standort A", vfl_id=1)
    standort_b = make_vflz(session, "Standort B", vfl_id=2)
    standort_c = make_vflz(session, "Standort C", vfl_id=3)

    standort_a.beurteilung = Beurteilung(beurteilung=beurteilung_test)
    standort_b.beurteilung = Beurteilung(beurteilung=beurteilung_test2)
    standort_c.beurteilung = Beurteilung(beurteilung=beurteilung_test3)

    session.commit()

    vflz_ids, _ = get_search_results(
        session,
        test_user,
        search="",
        filters=[
            (SearchField.BEURTEILUNG, [str(beurteilung_test2), str(beurteilung_test3)])
        ],
    )

    assert sorted(vflz_ids) == [standort_b.vflz_id, standort_c.vflz_id]


def test_filter_by_gemeinde_multiple(session: Session, test_user):
    gemeinde_301 = make_gemeinde(session, "Aarberg", bfs_nummer=301, kanton="BE")
    gemeinde_302 = make_gemeinde(session, "Bargen (BE)", bfs_nummer=302, kanton="BE")
    gemeinde_303 = make_gemeinde(session, "Grossaffoltern", bfs_nummer=303, kanton="BE")

    standort_a = make_vflz(session, "Standort A", vfl_id=1)
    standort_b = make_vflz(session, "Standort B", vfl_id=2)
    standort_c = make_vflz(session, "Standort C", vfl_id=3)

    standort_a.gemeinde = gemeinde_301
    standort_b.gemeinde = gemeinde_302
    standort_c.gemeinde = gemeinde_303

    session.commit()

    vflz_ids, _ = get_search_results(
        session,
        test_user,
        search="",
        filters=[
            (SearchField.BFS_NR, [301, 302]),
        ],
    )

    assert sorted(vflz_ids) == [standort_a.vflz_id, standort_b.vflz_id]


def test_filter_publiziert(session: Session, test_user):
    standort_a = make_vflz(session, "Standort A", vfl_id=1)
    standort_b = make_vflz(session, "Standort B", vfl_id=2)
    standort_c = make_vflz(session, "Standort C", vfl_id=3)
    standort_d = make_vflz(session, "Standort D", vfl_id=4)
    standort_e = make_vflz(session, "Standort E", vfl_id=5)

    belastet = make_code(session, codes.Beurteilung, "B")
    unbelastet = make_code(session, codes.Beurteilung, "U")
    make_kbsinfo(session, belastet, belastet=True, color="#ff0000")
    make_kbsinfo(session, unbelastet, belastet=False, color="#00ff00")

    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)

    # publiziert, belastet
    standort_a.dat_publizieren = yesterday
    standort_a.beurteilung = Beurteilung(beurteilung=belastet)

    # publiziert, unbelastet
    standort_b.dat_publizieren = yesterday
    standort_b.beurteilung = Beurteilung(beurteilung=unbelastet)

    # nicht publiziert
    standort_c.dat_publizieren = None
    standort_c.beurteilung = None

    # publiziert unbelastet, ehemals belastet
    standort_d.dat_publizieren = yesterday
    standort_d.beurteilung = Beurteilung(beurteilung=belastet)
    standort_d.historize("Belastete version historisiert")

    standort_d.dat_publizieren = yesterday
    standort_d.beurteilung = Beurteilung(beurteilung=unbelastet)

    # wie standort_d, aber zweite Publikation liegt in der Zukunft
    standort_e.dat_publizieren = yesterday
    standort_e.beurteilung = Beurteilung(beurteilung=belastet)
    standort_e.historize("Belastete version historisiert")

    standort_e.dat_publizieren = tomorrow
    standort_e.beurteilung = Beurteilung(beurteilung=unbelastet)

    session.commit()

    vflz_ids, _ = get_search_results(
        session,
        test_user,
        search="",
        filters=[],
    )
    assert sorted(vflz_ids) == [
        standort_a.vflz_id,
        standort_b.vflz_id,
        standort_c.vflz_id,
        standort_d.vflz_id,
        standort_e.vflz_id,
    ]

    vflz_ids, _ = get_search_results(
        session,
        test_user,
        search="",
        filters=[(SearchField.AKTUELLSTE_PUBLIKATION, True)],
    )
    assert sorted(vflz_ids) == [
        standort_a.vflz_id,
        standort_e.vflz_id,
    ]


@pytest.mark.parametrize(
    ("lang", "expected_results"),
    [
        (
            Language.DE,
            [
                (1, "Standort A", "code:103:test", EvaluationStatusData().to_dict()),
                (2, "Standort B", "code:103:test2", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            Language.FR,
            [
                (1, "Standort B", "code:103:test2", EvaluationStatusData().to_dict()),
                (2, "Standort A", "code:103:test", EvaluationStatusData().to_dict()),
            ],
        ),
        (
            Language.IT,
            [
                (1, "Standort B", "code:103:test2", EvaluationStatusData().to_dict()),
                (2, "Standort A", "code:103:test", EvaluationStatusData().to_dict()),
            ],
        ),
    ],
)
def test_order_by_code_value_uses_translation(
    session: Session, lang: Language, expected_results: list[tuple[Any, ...]], test_user
):
    beurteilung_test = session.get_one(
        codes.Beurteilung, (constants.CodeListe.Beurteilung, "test")
    )
    beurteilung_test2 = session.get_one(
        codes.Beurteilung, (constants.CodeListe.Beurteilung, "test2")
    )

    standort_a = make_vflz(session, "Standort A", vfl_id=1)
    standort_b = make_vflz(session, "Standort B", vfl_id=2)

    standort_a.beurteilung = Beurteilung(beurteilung=beurteilung_test)
    standort_b.beurteilung = Beurteilung(beurteilung=beurteilung_test2)

    session.add_all(
        [
            Translation(
                key=str(beurteilung_test), value="AA de-test", locale=Language.DE
            ),
            Translation(
                key=str(beurteilung_test2), value="ZZ de-test2", locale=Language.DE
            ),
            Translation(
                key=str(beurteilung_test), value="ZZ fr-test", locale=Language.FR
            ),
            Translation(
                key=str(beurteilung_test2), value="AA fr-test2", locale=Language.FR
            ),
            Translation(
                key=str(beurteilung_test2), value="AA it-test2", locale=Language.IT
            ),
        ]
    )

    result_page = get_result_page(
        session,
        [standort_a.vflz_id, standort_b.vflz_id],
        fields=[SearchField.BEZEICHNUNG, SearchField.BEURTEILUNG],
        sort_by=[(SearchField.BEURTEILUNG, False)],
        lang=lang,
    )

    assert result_page.results == expected_results


def test_search_stopwords_and_stemming(session: Session, test_user):
    standort_a = make_vflz(session, "Standort A", vfl_id=1)
    standort_b = make_vflz(session, "Site B", vfl_id=2)
    subjekt_a = Subjekt(name="Meier und Söhne")
    subjekt_b = Subjekt(name="Dupont et fils")
    session.add_all([subjekt_a, subjekt_b])
    session.flush()
    # TODO improve API to add beteiligte
    beteiligter_a = Beteiligter()
    beteiligter_a.vflz_id = standort_a.vflz_id
    beteiligter_a.subj_id = subjekt_a.subj_id
    beteiligter_b = Beteiligter()
    beteiligter_b.vflz_id = standort_b.vflz_id
    beteiligter_b.subj_id = subjekt_b.subj_id
    session.add_all([beteiligter_a, beteiligter_b])
    session.commit()

    assert get_search_results(session, test_user, search="meier", lang=Language.DE) == (
        {standort_a.vflz_id},
        False,
    )
    assert get_search_results(session, test_user, search="sohn", lang=Language.DE) == (
        {standort_a.vflz_id},
        False,
    )
    assert get_search_results(session, test_user, search="und", lang=Language.DE) == (
        {standort_a.vflz_id},
        False,
    )

    assert get_search_results(
        session, test_user, search="dupont", lang=Language.FR
    ) == (
        {standort_b.vflz_id},
        False,
    )
    assert get_search_results(session, test_user, search="fil", lang=Language.FR) == (
        {standort_b.vflz_id},
        False,
    )
    assert get_search_results(session, test_user, search="et", lang=Language.FR) == (
        {standort_b.vflz_id},
        False,
    )
