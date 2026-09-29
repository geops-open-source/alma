import pytest
from sqlalchemy.orm import Session
from utils import (
    make_beteiligter_geschaeft,
    make_code,
    make_document_node,
    make_oberflaechen_gewaesser,
    make_schiessanlage,
    make_subj,
    make_translation,
    make_vflz,
)

from alma.constants import CodeListe, Language
from alma.models import codes
from alma.models.vflz import EvaluationStatusData, VflGeo
from alma.search import SearchField, get_result_page

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes"),
]


def test_search_can_translate_codes(session: Session):
    """
    Code values are translated with `translate_codes=True`.
    """
    code = make_code(session, codes.StandortTyp, "a-1")
    make_translation(
        session, lang=Language.DE, key=str(code), value="ablagerungsstandort-de"
    )
    make_translation(
        session, lang=Language.FR, key=str(code), value="ablagerungsstandort-fr"
    )
    vflz1 = make_vflz(session, "Standort 1")
    vflz1.vftyp = code

    page_not_translated = get_result_page(
        session,
        [vflz1.vflz_id],
        fields=[SearchField.BEZEICHNUNG, SearchField.STANDORTTYP],
        lang=Language.DE,
    )
    page_translated_de = get_result_page(
        session,
        [vflz1.vflz_id],
        fields=[SearchField.BEZEICHNUNG, SearchField.STANDORTTYP],
        lang=Language.DE,
        translate_codes=True,
    )
    page_translated_fr = get_result_page(
        session,
        [vflz1.vflz_id],
        fields=[SearchField.BEZEICHNUNG, SearchField.STANDORTTYP],
        lang=Language.FR,
        translate_codes=True,
    )

    assert page_not_translated.results == [
        (
            1,
            "Standort 1",
            f"code:{CodeListe.StandortTyp}:a-1",
            EvaluationStatusData().to_dict(),
        ),
    ]
    assert page_translated_de.results == [
        (1, "Standort 1", "ablagerungsstandort-de", EvaluationStatusData().to_dict()),
    ]
    assert page_translated_fr.results == [
        (1, "Standort 1", "ablagerungsstandort-fr", EvaluationStatusData().to_dict()),
    ]


def test_search_can_add_geom(session: Session):
    """
    Vflgeo is included as the last column with `include_geoms=True`,
    """
    vflz1 = make_vflz(session, "Standort 1")
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

    page_without_geoms = get_result_page(
        session,
        [vflz1.vflz_id],
        fields=[SearchField.BEZEICHNUNG],
    )
    page_with_geoms = get_result_page(
        session,
        [vflz1.vflz_id],
        fields=[SearchField.BEZEICHNUNG],
        include_geoms=True,
    )

    assert page_without_geoms.results == [
        (1, "Standort 1", EvaluationStatusData().to_dict()),
    ]
    assert page_with_geoms.results == [
        (
            1,
            "Standort 1",
            "SRID=2056;MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)))",
            EvaluationStatusData().to_dict(),
        ),
    ]


def test_search_for_oberflaechengewaesser(session: Session):
    """
    Bug when asking for fields "Art-des-Oberflächengewässers" and "Gewässerbau".

    See ALMABASE-346
    """
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    art1 = make_code(session, codes.GewaesserArt, "art1")
    bau1 = make_code(session, codes.GewaesserBau, "bau1")

    make_translation(session, lang=Language.DE, key=str(art1), value="Gewässerart-1")
    make_translation(session, lang=Language.DE, key=str(bau1), value="Gewässerbau-1")

    ogw1 = make_oberflaechen_gewaesser(session, vflz1)
    ogw1.name = "Oberflächengewässer-1"
    ogw1.distanz = 100
    ogw1.art_gewaesser = art1
    ogw1.bau_gewaesser = bau1

    page = get_result_page(
        session,
        vflz_ids=[vflz1.vflz_id, vflz2.vflz_id],
        fields=[
            SearchField.VFLZ_ID,
            SearchField.ART_OBERFL_GEWAESSER,
            SearchField.GEWAESSERBAU,
        ],
        sort_by=[(SearchField.VFLZ_ID, False)],
        lang=Language.DE,
        page=1,
        per_page=10,
    )

    assert page.num_results_total == 2
    assert page.results == [
        (
            1,
            vflz1.vflz_id,
            "code:66:art1",
            "code:67:bau1",
            EvaluationStatusData().to_dict(),
        ),
        (2, vflz2.vflz_id, None, None, EvaluationStatusData().to_dict()),
    ]


def test_search_for_schiessanlagen_fields(session: Session):
    """
    Bug where rows where missing when asking for fields of Schiessanlage

    See ALMABASE-346
    """
    vflz1 = make_vflz(session, "Standort A", vfl_id=1)
    vflz2 = make_vflz(session, "Standort B", vfl_id=2)

    sa1 = make_schiessanlage(session, vflz1)
    sa1.firma_name = "Schiessanlage-1"
    sa1.hat_kugelfang = False
    sa1.scheibenzahl = 1
    sa1.schusszahl = 10

    sa2 = make_schiessanlage(session, vflz1)
    sa2.firma_name = "Schiessanlage-2"
    sa2.hat_kugelfang = True
    sa2.scheibenzahl = 2
    sa2.schusszahl = 20

    page = get_result_page(
        session,
        vflz_ids=[vflz1.vflz_id, vflz2.vflz_id],
        fields=[
            SearchField.VFLZ_ID,
            SearchField.FIRMA_NAME,
            SearchField.KUGELFANG_VORHANDEN,
            SearchField.SCHEIBENZAHL,
            SearchField.SCHUSSANZAHL,
        ],
        sort_by=[(SearchField.VFLZ_ID, False), (SearchField.FIRMA_NAME, False)],
        lang=Language.DE,
        page=1,
        per_page=10,
    )

    assert page.num_results_total == 3
    assert page.results == [
        (
            1,
            vflz1.vflz_id,
            "Schiessanlage-1",
            False,
            1,
            10,
            EvaluationStatusData().to_dict(),
        ),
        (
            2,
            vflz1.vflz_id,
            "Schiessanlage-2",
            True,
            2,
            20,
            EvaluationStatusData().to_dict(),
        ),
        (3, vflz2.vflz_id, None, None, None, None, EvaluationStatusData().to_dict()),
    ]


def test_search_for_task_beteiligte(session: Session):
    """
    Bug rows where missing when searching for Task-Beteiligte

    See ALMABASE-357
    """
    vflz = make_vflz(session, "Standort A", vfl_id=1)
    doc1 = make_document_node(session, vflz, "Document 1")
    subj = make_subj(
        session, name="Fleissig", vorname="Frieda", taetigkeit="Productownerin"
    )
    sachbearbeitung_code = make_code(session, codes.BeziehungsartSachbearbeitung, "bas")
    bet = make_beteiligter_geschaeft(session, subjekt=subj, node=doc1)
    bet.beziehungsart = sachbearbeitung_code

    make_translation(session, Language.DE, str(sachbearbeitung_code), "Sachbearbeitung")

    page = get_result_page(
        session,
        vflz_ids=[vflz.vflz_id],
        fields=[
            SearchField.VFLZ_ID,
            SearchField.TASK_BETEILIGTE,
            SearchField.TASK_BEZIEHUNGSART_SACHBEARBEITUNG,
        ],
        sort_by=[(SearchField.VFLZ_ID, False)],
        lang=Language.DE,
        page=1,
        per_page=10,
    )

    assert page.num_results_total == 1
    assert page.results == [
        (
            1,
            vflz.vflz_id,
            "Fleissig Frieda, Productownerin, , ",
            f"code:{CodeListe.BeziehungsartSachbearbeitung}:bas",
            EvaluationStatusData().to_dict(),
        ),
    ]
