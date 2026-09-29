from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import (
    make_beteiligter,
    make_code,
    make_eigentuemer_standort,
    make_nummerierungsbereich,
    make_parzelle,
    make_subj,
    make_vflz,
)

from alma import constants
from alma.constants import CodeListe
from alma.models import codes
from alma.models.grun import Nummerierungsbereich, Parzelle
from alma.models.subj import BeteiligterStandort, Subjekt
from alma.models.vflz import VflGeo, Vflz

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_vflz_eigentum_includes_parzellen_as_fehlend(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [1, 1],
                        [1, 5],
                        [5, 5],
                        [5, 1],
                        [1, 1],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo
    session.commit()

    p1 = make_parzelle(
        session, "1", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p2 = make_parzelle(
        session, "2", geom_ewkt="SRID=2056;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
    )

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
    ]


def test_vflz_eigentum_includes_associated_parzellen_as_zugeordnet(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    p1 = make_parzelle(session, "1")
    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
    ]


def test_vflz_eigentum_zugeordnet_is_grouped(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    p1 = make_parzelle(session, "1")
    p2 = make_parzelle(session, "2")
    p3 = make_parzelle(session, "3")

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1
    p3.nummerierungsbereich = nb1

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p2.grun_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p3.grun_id)

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "2", "3"],
        },
    ]


def test_vflz_eigentum_fehlend_is_ungrouped(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [2, 2],
                        [2, 4],
                        [4, 4],
                        [4, 2],
                        [2, 2],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo
    session.commit()

    p1 = make_parzelle(
        session, "1", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p2 = make_parzelle(
        session, "2", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
    ]


def test_vflz_eigentum_includes_parzellen_as_fehlend_unless_they_are_associated(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [2, 2],
                        [2, 4],
                        [4, 4],
                        [4, 2],
                        [2, 2],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo
    session.commit()

    p1 = make_parzelle(
        session, "1", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p2 = make_parzelle(
        session, "2", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
    ]


def test_vflz_eigentum_includes_parzellen_as_ueberzaehlig_unless_associated_with_a_current_parcel(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [2, 2],
                        [2, 4],
                        [4, 4],
                        [4, 2],
                        [2, 2],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo
    session.commit()

    status_parzelle_aktuell = session.scalars(
        select(codes.StatusParzelle).where(
            codes.StatusParzelle.code == constants.StatusParzelle.AKTUELL
        )
    ).one()

    status_parzelle_nicht_aktuell = session.scalars(
        select(codes.StatusParzelle).where(
            codes.StatusParzelle.code == constants.StatusParzelle.NICHT_AKTUELL
        )
    ).one()

    p1 = make_parzelle(
        session, "1", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p2 = make_parzelle(
        session, "2", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )

    p1.status = status_parzelle_aktuell
    p2.status = status_parzelle_nicht_aktuell

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p2.grun_id)

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
    ]


@pytest.fixture
def setup_eigentum(session: Session) -> tuple[Vflz, Subjekt, Nummerierungsbereich]:
    """
    Setup eigentum for vflz so that each status is represented, including two
    (grouped) entries with status ZUGEORDNET.
    """
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [2, 2],
                        [2, 4],
                        [4, 4],
                        [4, 2],
                        [2, 2],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo
    session.commit()

    status_parzelle_aktuell = session.scalars(
        select(codes.StatusParzelle).where(
            codes.StatusParzelle.code == constants.StatusParzelle.AKTUELL
        )
    ).one()

    status_parzelle_nicht_aktuell = session.scalars(
        select(codes.StatusParzelle).where(
            codes.StatusParzelle.code == constants.StatusParzelle.NICHT_AKTUELL
        )
    ).one()

    p1 = make_parzelle(
        session, "1", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p2 = make_parzelle(
        session, "2", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p3 = make_parzelle(
        session, "3", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )
    p4 = make_parzelle(
        session, "4", geom_ewkt="SRID=2056;POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    )

    p1.status = status_parzelle_aktuell
    p2.status = status_parzelle_nicht_aktuell
    p3.status = status_parzelle_aktuell
    p4.status = status_parzelle_aktuell

    nb1 = make_nummerierungsbereich(session, "1", bezeichnung="nb-1")
    p1.nummerierungsbereich = nb1
    p2.nummerierungsbereich = nb1
    p3.nummerierungsbereich = nb1
    p4.nummerierungsbereich = nb1

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p2.grun_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p4.grun_id)

    return vflz, subj, nb1


def get_update_beteiligte_input(vflz: Vflz, run_query) -> dict[str, Any]:
    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { subjId name }
                beziehungsart
                gemeinde { hGemId }
                nummerierungsbereich { hNbId bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    original_eigentum = result.data["vflz"]["eigentum"]

    update_beteiligte_input = {
        "vflzId": str(vflz.vflz_id),
        "eigentum": [
            {
                "status": obj["status"],
                "subjId": obj["subjekt"]["subjId"]
                if obj["subjekt"] is not None
                else None,
                "beziehungsart": obj["beziehungsart"],
                "hGemId": obj["gemeinde"]["hGemId"] if obj["gemeinde"] else None,
                "hNbId": obj["nummerierungsbereich"]["hNbId"]
                if obj["nummerierungsbereich"] is not None
                else None,
                "parzellen": obj["parzellen"],
            }
            for obj in original_eigentum
        ],
        "sachbearbeitung": [],
        "sonstigeBeteiligte": [],
    }

    return update_beteiligte_input


def test_vflz_eigentum_roundtrip(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, _ = setup_eigentum

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { subjId name }
                beziehungsart
                gemeinde { gemeinde }
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})
    original_eigentum = result.data["vflz"]["eigentum"]

    assert original_eigentum == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"gemeinde": "Aeugst am Albis"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    gemeinde { gemeinde }
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )
    new_eigentum = result.data["updateVflzBeteiligte"]["eigentum"]

    assert new_eigentum == original_eigentum


def test_update_vflz_eigentum_import_fehlend(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, _ = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    fehlend = update_beteiligte_input["eigentum"][-1]

    assert fehlend["status"] == "FEHLEND"

    fehlend["status"] = "ZUGEORDNET"
    fehlend["subjId"] = str(subj.subj_id)
    fehlend["beziehungsart"] = f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer"

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "3", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
    ]


def test_update_vflz_eigentum_add_new_zugeordnet_entries(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    p = make_parzelle(
        session, "5", geom_ewkt="SRID=2056;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
    )
    p.nummerierungsbereich = nb

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    update_beteiligte_input["eigentum"].append(
        {
            "status": "ZUGEORDNET",
            "subjId": str(subj.subj_id),
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "hGemId": str(vflz.h_gem_id),
            "hNbId": str(nb.h_nb_id),
            "parzellen": ["5"],
        }
    )

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4", "5"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_parzelle_removed_from_zugeordnet_entry_appears_as_fehlend(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    zugeordnet = update_beteiligte_input["eigentum"][0]
    assert zugeordnet["status"] == "ZUGEORDNET"

    zugeordnet["parzellen"].pop()  # Remove one parzelle

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["4"],
        },
    ]


def test_update_vflz_eigentum_parzelle_removing_parzellen_removes_bet_art_entries(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, _ = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    zugeordnet = update_beteiligte_input["eigentum"][0]
    assert zugeordnet["status"] == "ZUGEORDNET"

    zugeordnet["parzellen"] = []  # Clear all parzellen

    beteiligte_parzellen = session.scalars(
        select(BeteiligterStandort).where(BeteiligterStandort.grun_id.is_not(None))
    ).all()
    assert sorted(
        [b.parzelle.gb_nummer for b in beteiligte_parzellen if b.parzelle is not None]
    ) == ["1", "2", "4"]

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["4"],
        },
    ]

    beteiligte_parzellen = session.scalars(
        select(BeteiligterStandort).where(BeteiligterStandort.grun_id.is_not(None))
    ).all()

    assert sorted(
        [b.parzelle.gb_nummer for b in beteiligte_parzellen if b.parzelle is not None]
    ) == ["2"]


def test_update_vflz_eigentum_removing_rejects_empty_parzelle(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    zugeordnet = update_beteiligte_input["eigentum"][0]
    assert zugeordnet["status"] == "ZUGEORDNET"

    zugeordnet["parzellen"] = [" "]  # Invalid input

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on ProblemGroup {
                problems {
                    message
                    field
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["problems"] == [
        {
            "field": "eigentum[0].parzellen[0]",
            "message": "Parzelle value can not be empty",
        },
    ]


def test_update_vflz_eigentum_add_parzelle_to_zugeordnet_appears_as_ueberzaehlig_if_it_didnt_exist(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    zugeordnet = update_beteiligte_input["eigentum"][0]
    assert zugeordnet["status"] == "ZUGEORDNET"

    zugeordnet["parzellen"].append("99")  # Add one parzelle

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2", "99"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_add_parzelle_to_ueberzaehlig(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    ueberzaehlig = update_beteiligte_input["eigentum"][1]
    assert ueberzaehlig["status"] == "UEBERZAEHLIG"

    ueberzaehlig["parzellen"].append("99")  # Add one parzelle

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2", "99"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_add_parzelle_to_ueberzaehlig_that_already_exists_appears_as_zugeordnet(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    ueberzaehlig = update_beteiligte_input["eigentum"][1]
    assert ueberzaehlig["status"] == "UEBERZAEHLIG"

    p = make_parzelle(
        session, "5", geom_ewkt="SRID=2056;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
    )
    p.nummerierungsbereich = nb

    ueberzaehlig["parzellen"].append("5")  # Add one parzelle

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4", "5"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_remove_parzelle_from_ueberzaehlig_removes_the_entry(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    ueberzaehlig = update_beteiligte_input["eigentum"][1]
    assert ueberzaehlig["status"] == "UEBERZAEHLIG"

    update_beteiligte_input["eigentum"].remove(ueberzaehlig)

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_can_add_same_parzelle_to_multiple_owners(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum

    subj2 = make_subj(session, "name-2")

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    update_beteiligte_input["eigentum"].append(
        {
            "status": "ZUGEORDNET",
            "subjId": str(subj2.subj_id),
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "hGemId": str(vflz.h_gem_id),
            "hNbId": str(nb.h_nb_id),
            "parzellen": ["1"],
        }
    )

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj2.subj_id), "name": "name-2"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_can_update_beziehungsart(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    vflz, subj, nb = setup_eigentum
    new_beziehungsart = make_code(
        session, codes.BeziehungsartEigentum, "teileigentuemer"
    )

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    zugeordnet = update_beteiligte_input["eigentum"][0]
    assert zugeordnet["status"] == "ZUGEORDNET"
    assert (
        zugeordnet["beziehungsart"]
        == f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer"
    )
    zugeordnet["beziehungsart"] = str(new_beziehungsart)

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                }
            }
        }
    }
    """
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:teileigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]


def test_update_vflz_eigentum_with_nummerierungsbereich_and_no_gemeinde(
    session: Session, run_query, as_bearbeiten_sachdaten, setup_eigentum
):
    from copy import deepcopy

    vflz, subj, nb = setup_eigentum

    update_beteiligte_input = get_update_beteiligte_input(vflz, run_query)
    ueberzaehlig = update_beteiligte_input["eigentum"][1]
    assert ueberzaehlig["status"] == "UEBERZAEHLIG"
    new_ueberzaehlig = deepcopy(ueberzaehlig)
    new_ueberzaehlig["parzellen"] = ["5", "6"]
    new_ueberzaehlig["hNbId"] = nb.h_nb_id
    new_ueberzaehlig["hGemId"] = None

    update_beteiligte_input["eigentum"].append(new_ueberzaehlig)

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                eigentum {
                    status
                    subjekt { subjId name }
                    beziehungsart
                    nummerierungsbereich { bezeichnung }
                    parzellen
                    gemeinde { hGemId }
                }
            }
        }
    }
    """
    assert not session.scalars(
        select(Parzelle).where(Parzelle.h_gem_id.is_(None))
    ).all()
    result = run_query(
        mutation,
        variable_values={"vflzId": vflz.vflz_id, "data": update_beteiligte_input},
    )

    assert result.data["updateVflzBeteiligte"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"hGemId": "1"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1", "4"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["5", "6"],
        },
        {
            "status": "UEBERZAEHLIG",
            "subjekt": {"subjId": str(subj.subj_id), "name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "gemeinde": {"hGemId": "1"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["2"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "gemeinde": {"hGemId": "1"},
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]

    parzellen_without_gem = list(
        session.scalars(
            select(Parzelle)
            .where(Parzelle.h_gem_id.is_(None))
            .order_by(Parzelle.gb_nummer)
        ).all()
    )
    assert parzellen_without_gem[0].gb_nummer == "5"
    assert parzellen_without_gem[0].nummerierungsbereich
    assert parzellen_without_gem[0].nummerierungsbereich.bezeichnung == "nb-1"

    assert parzellen_without_gem[1].gb_nummer == "6"
    assert parzellen_without_gem[1].nummerierungsbereich
    assert parzellen_without_gem[1].nummerierungsbereich.bezeichnung == "nb-1"


def test_eigentum_does_not_return_parzelle_that_overlaps_less_than_1m(
    session: Session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    vflgeo = VflGeo()
    vflgeo.set_geometry(
        {
            "type": "MultiPolygon",
            "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
            "coordinates": [
                [
                    [
                        [0, 0],
                        [0, 10],
                        [10, 10],
                        [10, 0],
                        [0, 0],
                    ]
                ],
            ],
        }
    )
    vflz.vflgeo = vflgeo

    nb = make_nummerierungsbereich(session, "10", bezeichnung="nb-1")

    # Assigned parcel, clearly inside vflz.
    p1 = make_parzelle(
        session,
        "1",
        geom_ewkt="SRID=2056;POLYGON((2 2, 4 2, 4 4, 2 4, 2 2))",
    )
    p1.nummerierungsbereich = nb

    # This parcel overlaps the vflz only in the outer 1m edge band and must be excluded.
    p2 = make_parzelle(
        session,
        "2",
        geom_ewkt="SRID=2056;POLYGON((9.2 2, 10.2 2, 10.2 4, 9.2 4, 9.2 2))",
    )
    p2.nummerierungsbereich = nb

    # This parcel overlaps deeper than 1m and must be included as FEHLEND.
    p3 = make_parzelle(
        session,
        "3",
        geom_ewkt="SRID=2056;POLYGON((8.8 5, 10.2 5, 10.2 7, 8.8 7, 8.8 5))",
    )
    p3.nummerierungsbereich = nb

    subj = make_subj(session, "name-1")
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    make_eigentuemer_standort(session, bet_id=bet.bet_id, grun_id=p1.grun_id)

    session.commit()

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            eigentum {
                status
                subjekt { name }
                beziehungsart
                nummerierungsbereich { bezeichnung }
                parzellen
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": vflz.vflz_id})

    assert result.data["vflz"]["eigentum"] == [
        {
            "status": "ZUGEORDNET",
            "subjekt": {"name": "name-1"},
            "beziehungsart": f"code:{CodeListe.BeziehungsartEigentum}:eigentuemer",
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["1"],
        },
        {
            "status": "FEHLEND",
            "subjekt": None,
            "beziehungsart": None,
            "nummerierungsbereich": {"bezeichnung": "nb-1"},
            "parzellen": ["3"],
        },
    ]
