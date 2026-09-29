import pytest
from sqlalchemy import select
from utils import (
    QueryError,
    make_beteiligter,
    make_eigentuemer_standort,
    make_email_kontakt,
    make_parzelle,
    make_phone_private_kontakt,
    make_sonstiger_beteiligte_standort,
    make_subj,
    make_vflz,
    prefill_optional_fields,
)

from alma.graphql.types import subj as subj_types
from alma.models import auth, codes
from alma.models import bem as bem_models
from alma.models import subj as subj_models
from alma.models import vflz as vflz_models

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_get_all_subj_with_filter_sachbearbeiter(session, run_query):
    subj1 = make_subj(session)
    subj2 = make_subj(session)

    subj1.name = "name1"
    subj2.name = "name2-sachbearbeiter"

    user = auth.User(sub="sub", username="username", email="user@geops.com")
    user.is_sachbearbeitung = True
    user.subjekt = subj2
    session.add(user)
    session.commit()

    query = """
    query q($isSachbearbeiter: Boolean!) {
        subjekte(isSachbearbeiter: $isSachbearbeiter) {
            numResultsTotal
            results {
                name
                user { username }
            }
        }
    }
    """
    results = run_query(query, variable_values={"isSachbearbeiter": False})
    assert results.data["subjekte"]["numResultsTotal"] == 3
    assert results.data["subjekte"]["results"] == [
        {
            # The user that runs the queries (set up by fixture)
            "name": "alma test user",
            "user": {"username": "alma-test"},
        },
        {
            "name": "name1",
            "user": None,
        },
        {
            "name": "name2-sachbearbeiter",
            "user": {"username": "username"},
        },
    ]

    results = run_query(query, variable_values={"isSachbearbeiter": True})
    assert results.data["subjekte"]["numResultsTotal"] == 1
    assert results.data["subjekte"]["results"] == [
        {
            "name": "name2-sachbearbeiter",
            "user": {"username": "username"},
        },
    ]


def test_get_all_subj_query(session, run_query, test_user):
    sachbearbeiter_kategorie = session.scalars(
        select(codes.SubjektKategorie).where(
            codes.SubjektKategorie.code == "Sachbearbeiter"
        )
    ).one()

    subj = make_subj(session)
    parent_subj = make_subj(session)
    make_email_kontakt(session, subj)
    make_phone_private_kontakt(session, subj)
    subj.name = "name"
    subj.vorname = "vorname"
    subj.taetigkeit = "taetigkeit"
    subj.kuerzel = "kuerzel"
    subj.ident_nr = "ident_nr"
    subj.kategorien.append(sachbearbeiter_kategorie)
    subj.ort = "Foo Ort"
    subj.postleitzahl = "4321"
    subj.strasse = "Foo Strasse"
    subj.anrede = session.scalars(
        select(codes.Anrede).where(codes.Anrede.code == "Herr")
    ).one()
    subj.land = session.scalars(
        select(codes.Land).where(codes.Land.code == "Schweiz")
    ).one()
    subj.bemerkung = bem_models.BemerkungSubjekt(bem="subjekt bemerkung")
    query = """{
        subjekte {
            numResultsTotal
            results {
                subjId
                name
                vorname
                taetigkeit
                kuerzel
                identNr
                kategorien
                ort
                postleitzahl
                strasse
                anrede
                bemerkung {
                    bem
                }
                land
            }
        }
    }

    """
    results = run_query(query)
    assert results.data["subjekte"]["numResultsTotal"] == 3
    # Result includes the user that runs the queries (set up by fixture)
    assert results.data["subjekte"]["results"] == [
        {
            "subjId": str(parent_subj.subj_id),
            "name": "",
            "vorname": "",
            "kuerzel": None,
            "taetigkeit": "",
            "identNr": None,
            "kategorien": [],
            "ort": "",
            "postleitzahl": "",
            "strasse": "",
            "anrede": None,
            "bemerkung": None,
            "land": None,
        },
        {
            "subjId": str(test_user.subj_id),
            "name": "alma test user",
            "vorname": "",
            "kuerzel": None,
            "taetigkeit": "",
            "identNr": None,
            "kategorien": [],
            "ort": "",
            "postleitzahl": "",
            "strasse": "",
            "anrede": None,
            "bemerkung": None,
            "land": None,
        },
        {
            "subjId": str(subj.subj_id),
            "name": "name",
            "vorname": "vorname",
            "kuerzel": "kuerzel",
            "taetigkeit": "taetigkeit",
            "identNr": "ident_nr",
            "kategorien": ["code:10019:Sachbearbeiter"],
            "ort": "Foo Ort",
            "postleitzahl": "4321",
            "strasse": "Foo Strasse",
            "anrede": "code:31:Herr",
            "bemerkung": {"bem": "subjekt bemerkung"},
            "land": "code:14:Schweiz",
        },
    ]


@pytest.mark.parametrize(
    "filter, expected_results",
    [
        ("nam", [("geops", "vorname"), ("name", "geops")]),
        ("geo", [("geops", "vorname"), ("name", "geops")]),
        # Includes user created by fixture to run the queries
        (None, [("alma test user", ""), ("geops", "vorname"), ("name", "geops")]),
        ("ab", []),
        ("ort", [("name", "geops")]),
        ("allee", [("geops", "vorname"), ("name", "geops")]),
        ("geops vorname", [("geops", "vorname")]),
        ("vorname geops", [("geops", "vorname")]),
    ],
)
def test_filter_subjekte(session, run_query, filter, expected_results):
    subj = make_subj(session)
    subj.name = "name"
    subj.vorname = "geops"
    subj.taetigkeit = "job"
    subj.ort = "ort"
    subj.strasse = "allee"

    subj2 = make_subj(session)
    subj2.name = "geops"
    subj2.vorname = "vorname"
    subj2.taetigkeit = "taetigkeit"
    subj2.ort = "stadt"
    subj2.strasse = "mallee"

    query = """
    query q($filter: String) {
        subjekte(filter: $filter) {
            results { name vorname }
        }
    }
    """

    result = run_query(query, {"filter": filter})
    assert [
        (r["name"], r["vorname"]) for r in result.data["subjekte"]["results"]
    ] == expected_results


def test_get_beteiligte_pool(session, run_query):
    subj = make_subj(session)
    subj2 = make_subj(session)
    vflz = make_vflz(session, "My Site")
    beteiligter = make_beteiligter(
        session, vflz.vflz_id, subj.subj_id, is_eigentuemer=True
    )
    beteiligter2 = make_beteiligter(
        session, vflz.vflz_id, subj2.subj_id, is_sachbearbeiter=True
    )

    query = """
    query q($id: ID!){
        vflz(vflzId: $id) {
            beteiligte {
                betId
                subjekt {
                    subjId
                }
                isEigentuemer
                isSachbearbeiter
            }
        }
    }
    """

    result = run_query(query, {"id": vflz.vflz_id})
    assert result.data["vflz"]["beteiligte"] == [
        {
            "betId": str(beteiligter.bet_id),
            "subjekt": {
                "subjId": str(subj.subj_id),
            },
            "isEigentuemer": True,
            "isSachbearbeiter": False,
        },
        {
            "betId": str(beteiligter2.bet_id),
            "subjekt": {
                "subjId": str(subj2.subj_id),
            },
            "isEigentuemer": False,
            "isSachbearbeiter": True,
        },
    ]


def test_get_beteiligte_standort(session, run_query):
    subj = make_subj(session)
    subj2 = make_subj(session)
    vflz = make_vflz(session, "My Site")
    beteiligter = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    _ = make_beteiligter(session, vflz.vflz_id, subj2.subj_id)

    beteiligter_standort = make_sonstiger_beteiligte_standort(
        session, beteiligter.bet_id
    )
    beteiligter_standort.beziehungsart = session.scalars(
        select(codes.BeziehungsartSonstige).where(
            codes.BeziehungsartSonstige.code == "test2"
        )
    ).one()
    query = """
    query q($id: ID!) {
        vflz(vflzId: $id) {
            beteiligteStandort {
                betArtId
                beziehungsart
                beteiligter {
                    betId
                    subjekt {
                        subjId
                    }
                }
            }
        }
    }
    """

    result = run_query(query, {"id": str(vflz.vflz_id)})
    assert result.data["vflz"]["beteiligteStandort"] == [
        {
            "betArtId": str(beteiligter_standort.bet_art_id),
            "beziehungsart": "code:2201:test2",
            "beteiligter": {
                "betId": str(beteiligter.bet_id),
                "subjekt": {"subjId": str(subj.subj_id)},
            },
        }
    ]


def test_get_beteiligte_parzelle(session, run_query):
    subj = make_subj(session)
    subj2 = make_subj(session)

    # create vflz with geometry and its corresponding parzelle, use same geometry
    vflz = make_vflz(session, "My Site")
    vflgeo_ewkt = "SRID=2056;MULTIPOLYGON (((2600010 1200000, 2600010 1200100, 260040 1200100, 260040 1200000, 2600010 1200000)))"
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.wkb_geometry = vflgeo_ewkt  # type: ignore[assignment]
    vflz_parzelle = make_parzelle(session, "1", geom_ewkt=vflgeo_ewkt)

    beteiligter = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    _ = make_beteiligter(session, vflz.vflz_id, subj2.subj_id)

    beteiligter_parzelle = make_eigentuemer_standort(
        session, beteiligter.bet_id, vflz_parzelle.grun_id
    )
    beteiligter_parzelle.beziehungsart = session.scalars(
        select(codes.BeziehungsartSonstige).where(
            codes.BeziehungsartSonstige.code == "test2"
        )
    ).one()
    query = """
    query q($id: ID!) {
        vflz(vflzId: $id) {
            beteiligteParzellen {
                betArtId
                beziehungsart
                beteiligter {
                    betId
                    subjekt {
                        subjId
                    }
                }
            }
        }
    }
    """

    result = run_query(query, {"id": str(vflz.vflz_id)})
    assert result.data["vflz"]["beteiligteParzellen"] == [
        {
            "betArtId": str(beteiligter_parzelle.bet_art_id),
            "beziehungsart": "code:2201:test2",
            "beteiligter": {
                "betId": str(beteiligter.bet_id),
                "subjekt": {"subjId": str(subj.subj_id)},
            },
        }
    ]


def test_create_beteiligter_not_allowed_for_reading_sachdaten_role(session, run_query):
    subj = make_subj(session)
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: CreateBeteiligterInput!) {
        createBeteiligter(data: $data) {
            ... on BeteiligterStandort {
                beteiligter {
                    betId
                }
            }
        }
    }
    """
    with pytest.raises(QueryError):
        run_query(
            mutation,
            {
                "data": {
                    "subjId": str(subj.subj_id),
                    "vflzId": str(vflz.vflz_id),
                    "beziehungsart": "code:2201:test",
                }
            },
        )


def test_get_subj_by_id(session, run_query):
    sachbearbeiter_kategorie = session.scalars(
        select(codes.SubjektKategorie).where(
            codes.SubjektKategorie.code == "Sachbearbeiter"
        )
    ).one()
    land = session.scalars(select(codes.Land).where(codes.Land.code == "Schweiz")).one()
    subj = make_subj(session)
    subj.name = "my name"
    subj.vorname = "my vorname"
    subj.taetigkeit = "my taetigkeit"
    subj.kuerzel = "my kuerzel"
    subj.ident_nr = "my ident nr"
    subj.kategorien.append(sachbearbeiter_kategorie)
    subj.land = land
    email_kontakt = make_email_kontakt(session, subj)
    email_kontakt.kontakt = "unit@geops.com"
    telefon_kontakt = make_phone_private_kontakt(session, subj)
    telefon_kontakt.kontakt = "01234"

    query = """
    query q($subjId: ID!) {
        subjekt(subjId: $subjId) {
            subjId
            name
            vorname
            taetigkeit
            kuerzel
            identNr
            kategorien
            kontakte {
                kontaktId
                kontaktTyp
                kontakt
            }
            anrede
            bemerkung {
                bem
            }
            land
        }
    }
    """
    result = run_query(query, {"subjId": str(subj.subj_id)})
    assert result.data["subjekt"] == {
        "subjId": str(subj.subj_id),
        "name": "my name",
        "vorname": "my vorname",
        "taetigkeit": "my taetigkeit",
        "kuerzel": "my kuerzel",
        "identNr": "my ident nr",
        "kategorien": ["code:10019:Sachbearbeiter"],
        "kontakte": [
            {
                "kontaktId": str(email_kontakt.kontakt_id),
                "kontaktTyp": "code:33:EMAIL",
                "kontakt": "unit@geops.com",
            },
            {
                "kontaktId": str(telefon_kontakt.kontakt_id),
                "kontaktTyp": "code:33:2",
                "kontakt": "01234",
            },
        ],
        "anrede": None,
        "bemerkung": None,
        "land": "code:14:Schweiz",
    }


def test_updating_subjekt_with_valid_data(session, run_query, as_bearbeiten_sachdaten):
    sachbearbeiter_kategorie = session.scalars(
        select(codes.SubjektKategorie).where(
            codes.SubjektKategorie.code == "Sachbearbeiter"
        )
    ).one()
    subj = make_subj(session)
    subj.kategorien = []
    email_kontakt = make_email_kontakt(session, subj)
    email_kontakt.kontakt = "unit@geops.com"

    mutation = """
    mutation m($data: UpdateSubjektInput!) {
        updateSubjekt(data: $data) {
            subjekt {
                subjId
                name
                vorname
                taetigkeit
                kuerzel
                kategorien
                kontakte {
                    kontaktId
                    kontaktTyp
                    kontakt
                }
                ort
                postleitzahl
                strasse
                anrede
                bemerkung {
                    bem
                }
                land
            }
            problemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "subjId": str(subj.subj_id),
                "name": "foo name",
                "vorname": "foo vorname",
                "taetigkeit": "foo taetigkeit",
                "kuerzel": "KU",
                "kategorien": [str(sachbearbeiter_kategorie)],
                "kontakte": [
                    {
                        "kontaktId": str(email_kontakt.kontakt_id),
                        "kontaktTyp": "code:33:EMAIL",
                        "kontakt": "geops@geops.com",
                    }
                ],
                "ort": "neuer Ort",
                "postleitzahl": "1111",
                "strasse": "neue Strasse",
                "anrede": "code:31:Herr",
                "bemerkung": {"bem": "neue subjekt bemerkung"},
                "land": "code:14:Schweiz",
            }
        },
    )

    assert result.data["updateSubjekt"]["subjekt"] == {
        "subjId": str(subj.subj_id),
        "name": "foo name",
        "vorname": "foo vorname",
        "taetigkeit": "foo taetigkeit",
        "kuerzel": "KU",
        "kategorien": [str(sachbearbeiter_kategorie)],
        "kontakte": [
            {
                "kontaktId": str(email_kontakt.kontakt_id),
                "kontaktTyp": "code:33:EMAIL",
                "kontakt": "geops@geops.com",
            }
        ],
        "ort": "neuer Ort",
        "postleitzahl": "1111",
        "strasse": "neue Strasse",
        "anrede": "code:31:Herr",
        "bemerkung": {"bem": "neue subjekt bemerkung"},
        "land": "code:14:Schweiz",
    }
    assert not result.data["updateSubjekt"]["problemGroup"]["problems"]


def test_updating_subjekt_with_invalid_data_saves_and_returns_problems(
    session, run_query, as_bearbeiten_sachdaten
):
    sachbearbeiter_kategorie = session.scalars(
        select(codes.SubjektKategorie).where(
            codes.SubjektKategorie.code == "Sachbearbeiter"
        )
    ).one()
    subj = make_subj(session)
    subj.kategorien = []
    email_kontakt = make_email_kontakt(session, subj)
    email_kontakt.kontakt = "unit@geops.com"

    mutation = """
    mutation m($data: UpdateSubjektInput!) {
        updateSubjekt(data: $data) {
            subjekt {
                subjId
                name
                vorname
                taetigkeit
                kuerzel
                kategorien
                kontakte {
                    kontaktId
                    kontaktTyp
                    kontakt
                }
                ort
                postleitzahl
                strasse
                anrede
                bemerkung {
                    bem
                }
                land
            }
            problemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "subjId": str(subj.subj_id),
                "name": "foo name",
                "vorname": "foo vorname",
                "taetigkeit": "foo taetigkeit",
                "kuerzel": "KU",
                "kategorien": [str(sachbearbeiter_kategorie)],
                "kontakte": [
                    {
                        "kontaktId": str(email_kontakt.kontakt_id),
                        "kontaktTyp": "code:33:EMAIL",
                        "kontakt": "this email is not supported",
                    }
                ],
                "ort": "neuer Ort",
                "postleitzahl": "1111",
                "strasse": "neue Strasse",
                "anrede": "code:31:Herr",
                "bemerkung": {"bem": "neue subjekt bemerkung"},
                "land": "code:14:Schweiz",
            }
        },
    )

    assert result.data["updateSubjekt"]["subjekt"] == {
        "subjId": str(subj.subj_id),
        "name": "foo name",
        "vorname": "foo vorname",
        "taetigkeit": "foo taetigkeit",
        "kuerzel": "KU",
        "kategorien": [str(sachbearbeiter_kategorie)],
        "kontakte": [
            {
                "kontaktId": str(email_kontakt.kontakt_id),
                "kontaktTyp": "code:33:EMAIL",
                "kontakt": "this email is not supported",
            }
        ],
        "ort": "neuer Ort",
        "postleitzahl": "1111",
        "strasse": "neue Strasse",
        "anrede": "code:31:Herr",
        "bemerkung": {"bem": "neue subjekt bemerkung"},
        "land": "code:14:Schweiz",
    }
    assert result.data["updateSubjekt"]["problemGroup"]["problems"]


def test_has_standorte(session, run_query):
    vflz = make_vflz(session, "my site")
    subj1 = make_subj(session, "hans")
    subj2 = make_subj(session, "lisa")
    bet1 = make_beteiligter(session, vflz.vflz_id, subj1.subj_id)
    bet2 = make_beteiligter(session, vflz.vflz_id, subj2.subj_id)
    grun = make_parzelle(session, "1")
    make_sonstiger_beteiligte_standort(session, bet1.bet_id)
    make_eigentuemer_standort(session, bet2.bet_id, grun.grun_id)

    query = """
    query q($subjId: ID!) {
        subjekt(subjId: $subjId) {
            hasStandorte
        }
    }
    """

    result = run_query(query, {"subjId": subj1.subj_id})
    assert result.data["subjekt"]["hasStandorte"]

    result = run_query(query, {"subjId": subj2.subj_id})
    assert result.data["subjekt"]["hasStandorte"]

    session.delete(bet1)
    session.delete(bet2)

    result = run_query(query, {"subjId": subj1.subj_id})
    assert not result.data["subjekt"]["hasStandorte"]

    result = run_query(query, {"subjId": subj2.subj_id})
    assert not result.data["subjekt"]["hasStandorte"]


def test_create_subjekt(run_query, as_bearbeiten_sachdaten):
    mutation = """
    mutation m($data: CreateSubjektInput!) {
        createSubjekt(data: $data) {
            subjekt {
                name
                vorname
                taetigkeit
                kuerzel
                kategorien
                kontakte {
                    kontaktTyp
                    kontakt
                }
                ort
                postleitzahl
                strasse
                anrede
                bemerkung {
                    bem
                }
                land
            }
            problemGroup {
                problems {
                    message
                }
            }
        }
    }

    """

    variables = {
        "data": {
            "name": "my name",
            "vorname": "my vorname",
            "taetigkeit": "my taetigkeit",
            "kuerzel": "my kuerzel",
            "kategorien": ["code:10019:Sachbearbeiter"],
            "kontakte": [
                {
                    "kontaktId": None,
                    "kontaktTyp": "code:33:EMAIL",
                    "kontakt": "this email is not supported",
                }
            ],
            "ort": "neuer Ort",
            "postleitzahl": "1111",
            "strasse": "neue Strasse",
            "anrede": "code:31:Frau",
            "bemerkung": {"bem": "neue subjekt bemerkung"},
            "land": "code:14:Schweiz",
        }
    }

    result = run_query(mutation, variables)
    assert result.data["createSubjekt"]["subjekt"] == {
        "name": "my name",
        "vorname": "my vorname",
        "taetigkeit": "my taetigkeit",
        "kuerzel": "my kuerzel",
        "kategorien": ["code:10019:Sachbearbeiter"],
        "kontakte": [
            {
                "kontaktTyp": "code:33:EMAIL",
                "kontakt": "this email is not supported",
            }
        ],
        "ort": "neuer Ort",
        "postleitzahl": "1111",
        "strasse": "neue Strasse",
        "anrede": "code:31:Frau",
        "bemerkung": {"bem": "neue subjekt bemerkung"},
        "land": "code:14:Schweiz",
    }
    assert result.data["createSubjekt"]["problemGroup"]["problems"]


def test_delete_subjekt(session, run_query, as_bearbeiten_sachdaten):
    mutation = """
    mutation m($subjId: ID!) {
        deleteSubjekt(subjId: $subjId)
    }
    """

    vflz = make_vflz(session, "my site")
    subj = make_subj(session)
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id)
    bet_standort = make_sonstiger_beteiligte_standort(session, bet.bet_id)
    subj_id = subj.subj_id
    bet_id = bet.bet_id
    bet_art_id = bet_standort.bet_art_id

    result = run_query(mutation, {"subjId": subj_id})

    assert result.data["deleteSubjekt"] == str(subj_id)

    assert session.get(subj_models.Subjekt, subj_id) is None
    assert session.get(subj_models.Beteiligter, bet_id) is None
    assert session.get(subj_models.BeteiligterStandort, bet_art_id) is None


def test_get_assigned_user_of_subjekt(session, run_query):
    dummy_user = auth.User(
        username="dummy user", email="dummy-user@example.com", sub="sub"
    )
    session.add(dummy_user)

    subj = make_subj(session)
    subj.user = dummy_user
    query = """
    query q($subjId: ID!) {
        subjekt(subjId: $subjId) {
            user {
                username
            }
        }
    }
    """

    result = run_query(query, {"subjId": str(subj.subj_id)})
    assert result.data["subjekt"] == {"user": {"username": "dummy user"}}


def test_kontakt_validation(session, run_query, as_bearbeiten_sachdaten):
    subj = make_subj(session)
    assert subj.kontakte == []
    mutation = """
    mutation q($data: UpdateSubjektInput!) {
        updateSubjekt(data: $data) {
            subjekt {
                subjId
                kontakte {
                    kontakt
                }
            }
            problemGroup {
                problems {
                    field
                    problemCode
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": prefill_optional_fields(
                subj_types.UpdateSubjektInput,
                {
                    "subjId": str(subj.subj_id),
                    "kontakte": [
                        {
                            "kontaktId": None,
                            "kontaktTyp": "code:33:EMAIL",
                            "kontakt": "unsupported email adress",
                        }
                    ],
                },
            )
        },
    )
    assert result.data["updateSubjekt"]["problemGroup"]["problems"] == [
        {"field": "kontakte[0].kontakt", "problemCode": "VALIDATION_EMAIL"}
    ]
    assert result.data["updateSubjekt"]["subjekt"] == {
        "subjId": str(subj.subj_id),
        "kontakte": [{"kontakt": "unsupported email adress"}],
    }
