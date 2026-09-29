import pytest
from utils import (
    make_ablagerung,
    make_report,
    make_report_query,
    make_translation,
    make_vflz,
)

from alma.constants import Language
from alma.models import report as report_models
from alma.reports import format_thousands, get_data

pytestmark = [pytest.mark.usefixtures("generate_codes")]


def test_get_one_to_one_relation_from_database_with_one_query(session):
    vflz = make_vflz(session, "My Site")
    report = make_report(session, report_models.ReportContext.STANDORT)
    make_report_query(
        session,
        "grunddata",
        "select vflz_postleitzahl, vflz_ort from alma.vflz where vflz_id=:vflz_id;",
        report,
    )
    vflz.ort = "Basel"
    vflz.postleitzahl = "1234"

    data = get_data(session, report, {"vflz_id": vflz.vflz_id})
    assert data["grunddata"] == [{"vflz_postleitzahl": "1234", "vflz_ort": "Basel"}]


def test_get_one_to_many_relation_from_database_with_one_query(session):
    vflz = make_vflz(session, "My Site")
    report = make_report(session, report_models.ReportContext.STANDORT)
    make_report_query(
        session,
        "ablagerung",
        "select inta_tiefe, vflz_ort from alma.vflz vz join alma.inta inta on vz.vflz_id = inta.vflz_id where vz.vflz_id=:vflz_id;",
        report,
    )
    vflz.ort = "Basel"
    session.add(vflz)

    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung1.tiefe = "3.0"
    session.add(ablagerung1)

    ablagerung2 = make_ablagerung(session, vflz)
    ablagerung2.tiefe = "5.0"
    session.add(ablagerung2)
    session.commit()

    data = get_data(session, report, {"vflz_id": vflz.vflz_id})
    assert data["ablagerung"] == [
        {"inta_tiefe": "3.0", "vflz_ort": "Basel"},
        {"inta_tiefe": "5.0", "vflz_ort": "Basel"},
    ]


def test_multiple_queries(session):
    vflz = make_vflz(session, "My Site")
    report = make_report(session, report_models.ReportContext.STANDORT)
    make_report_query(
        session,
        "ablagerung",
        "select inta_tiefe from alma.vflz vz join alma.inta inta on vz.vflz_id = inta.vflz_id where vz.vflz_id=:vflz_id;",
        report,
    )
    make_report_query(
        session,
        "grunddata",
        "select vflz_ort from alma.vflz where vflz_id=:vflz_id;",
        report,
    )
    vflz.ort = "Basel"
    session.add(vflz)

    ablagerung1 = make_ablagerung(session, vflz)
    ablagerung1.tiefe = "3.0"
    session.add(ablagerung1)

    ablagerung2 = make_ablagerung(session, vflz)
    ablagerung2.tiefe = "5.0"
    session.add(ablagerung2)
    session.commit()

    data = get_data(session, report, {"vflz_id": vflz.vflz_id})
    assert data["ablagerung"] == [{"inta_tiefe": "3.0"}, {"inta_tiefe": "5.0"}]
    assert data["grunddata"] == [{"vflz_ort": "Basel"}]


def test_get_translations(session):
    vflz = make_vflz(session, "My Site")
    report = make_report(session, report_models.ReportContext.STANDORT)
    make_translation(session, Language.DE, "report.test.greeting", "Hallo")
    make_translation(session, Language.FR, "report.test.greeting", "Salut")
    translation_query = make_report_query(
        session,
        "translations",
        "select msgid, msgstr from alma.translations where msgid like 'report.test.%' and locale=:lang;",
        report,
    )
    translation_query.is_translation_query = True

    data = get_data(session, report, {"vflz_id": vflz.vflz_id, "lang": "de"})
    assert data["translations"] == {"report.test.greeting": "Hallo"}


def test_format_thousands():
    assert format_thousands(2600000) == "2'600'000"
