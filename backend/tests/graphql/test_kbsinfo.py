import pytest
from sqlalchemy import select

from alma.models import codes

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_get_list_of_kbsinfo(session, run_query):
    beurteilung1 = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == "test")
    ).one()
    beurteilung2 = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == "test2")
    ).one()
    beurteilung_gruppe = session.scalars(
        select(codes.BeurteilungGruppe).where(codes.BeurteilungGruppe.code == "Test")
    ).one()
    kbsinfo1 = codes.KbsInfo(
        beurteilung=beurteilung1,
        beurteilung_gruppe=beurteilung_gruppe,
        color="#ff0000",
        color_rgb=None,
        belastet=True,
    )
    kbsinfo2 = codes.KbsInfo(
        beurteilung=beurteilung2,
        beurteilung_gruppe=beurteilung_gruppe,
        color="#00ff00",
        color_rgb=None,
        belastet=False,
    )
    session.add_all([kbsinfo1, kbsinfo2])
    session.commit()

    query = """
        { kbsInfos { beurteilung, color, belastet, beurteilungGruppe} }
    """
    result = run_query(query)

    assert result.data == {
        "kbsInfos": [
            {
                "beurteilung": "code:103:test",
                "color": "#ff0000",
                "belastet": True,
                "beurteilungGruppe": "code:1031:Test",
            },
            {
                "beurteilung": "code:103:test2",
                "color": "#00ff00",
                "belastet": False,
                "beurteilungGruppe": "code:1031:Test",
            },
        ],
    }
