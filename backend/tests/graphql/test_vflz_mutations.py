from datetime import date, datetime

import pytest
from freezegun import freeze_time
from pytest import raises as assert_raises
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import (
    QueryError,
    make_ablagerung,
    make_beteiligter,
    make_betrieb,
    make_einzelereignis,
    make_flugplatz,
    make_gemeinde,
    make_grundwasser,
    make_kinderspielplatz_gruenflaeche,
    make_kompartiment_stoffgruppe,
    make_kompartiment_stoffklasse,
    make_ktu,
    make_massnahme,
    make_nutzung_boden,
    make_oberflaechen_gewaesser,
    make_pfas,
    make_pool,
    make_sanierungsziel,
    make_schiessanlage,
    make_sonstiger_beteiligte_standort,
    make_subj,
    make_umweltschaden,
    make_umweltstoff,
    make_unfall,
    make_unfallstoff,
    make_vfl_pool,
    make_vflz,
    make_vflz_beurteilung,
    prefill_optional_fields,
)

from alma import constants
from alma.graphql.types import vflz as vflz_types
from alma.models import bem as bem_models
from alma.models.auth import User
from alma.models.cache import WfsUpdate
from alma.models.codes import BeziehungsartSachbearbeitung
from alma.models.subj import Beteiligter, BeteiligterStandort
from alma.models.umwelt import (
    Einzelereignis,
    Grundwasser,
    NutzungBoden,
    OberflaechenGewaesser,
    Umweltschaden,
    UmweltStoff,
)
from alma.models.vflz import (
    Ablagerung,
    Betrieb,
    Beurteilung,
    KompartimentStoffgruppe,
    KompartimentStoffklasse,
    Massnahme,
    Pool,
    Sanierungsziel,
    Schiessanlage,
    Unfall,
    Unfallstoff,
    VflGeo,
    VflPool,
)
from alma.settings import CombinedIdFactoryName, settings

pytestmark = [
    # Fixture required by all tests in this module
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


def test_update_vflz_without_relation_and_without_code_input(
    session: Session, run_query
):
    make_flugplatz(session)
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                bezeichnung
                flurname
                strasse
                postleitzahl
                ort
                lang
                flugplatz
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "bezeichnung": "foo",
                "flurname": "neu flurname",
                "strasse": "neu strasse",
                "postleitzahl": "12345",
                "ort": "foo city",
                "lang": "IT",
                "deponietyp": None,
                "gwsBereich": None,
                "gwsZone": None,
                "durchlaessigkeit": None,
                "karstgeb": None,
                "inBetrieb": None,
                "nachsorge": None,
                "ablagerungen": [],
                "betriebe": [],
                "schiessanlagen": [],
                "unfaelle": [],
                "pfas": [],
                "kinderspielplaetzeGruenflaechen": [],
                "grundwasser": [],
                "oberflaechenGewaesser": [],
                "nutzungenBoden": [],
                "umweltStoffe": [],
                "einzelereignisse": [],
                "umweltschaeden": [],
                "gemeinde": None,
                "bemerkungStandort": None,
                "bemerkungUmwelt": None,
                "bemerkungDatenimport": None,
                "flugplatz": "code:600:Test",
                "ktu": None,
            }
        },
    )
    assert result.data == {
        "updateVflzData": {
            "vflzId": str(vflz.vflz_id),
            "bezeichnung": "foo",
            "flurname": "neu flurname",
            "strasse": "neu strasse",
            "postleitzahl": "12345",
            "ort": "foo city",
            "lang": "IT",
            "flugplatz": "code:600:Test",
        }
    }


def test_update_not_allowed_with_lesen_sachdaten(
    session: Session, run_query, as_lesen_sachdaten
):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    with assert_raises(QueryError, match="not allowed"):
        run_query(
            query=mutation,
            variable_values={
                "data": prefill_optional_fields(
                    vflz_types.UpdateVflzDataInput,
                    {"vflzId": vflz.vflz_id},
                )
            },
        )


def test_update_not_allowed_with_lesen_geschaefte(
    session: Session, run_query, as_lesen_geschaefte
):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    with assert_raises(QueryError, match="not allowed"):
        run_query(
            query=mutation,
            variable_values={
                "data": prefill_optional_fields(
                    vflz_types.UpdateVflzDataInput,
                    {"vflzId": vflz.vflz_id},
                )
            },
        )


def test_update_allowed_with_bearbeiten_geschaefte(
    session: Session, run_query, as_bearbeiten_geschaefte
):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {"vflzId": vflz.vflz_id, "bezeichnung": "bla"},
            )
        },
    )
    assert result.data == {"updateVflzData": {"vflzId": str(vflz.vflz_id)}}


def test_update_allowed_with_bearbeiten_sachdaten(
    session: Session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {"vflzId": vflz.vflz_id, "bezeichnung": "bla"},
            )
        },
    )
    assert result.data == {"updateVflzData": {"vflzId": str(vflz.vflz_id)}}


def test_update_vflz_bemerkungen(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                bemerkungStandort { bem }
                bemerkungUmwelt { bem }
                bemerkungDatenimport { bem }
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "bemerkungStandort": {"bem": "Bemerkung Standort"},
                    "bemerkungUmwelt": {"bem": "Bemerkung Umwelt"},
                    "bemerkungDatenimport": {"bem": "Bemerkung Datenimport"},
                },
            )
        },
    )

    assert (
        vflz.bemerkung_standort and vflz.bemerkung_standort.bem == "Bemerkung Standort"
    )
    assert vflz.bemerkung_umwelt and vflz.bemerkung_umwelt.bem == "Bemerkung Umwelt"

    assert result.data["updateVflzData"] == {
        "bemerkungStandort": {"bem": "Bemerkung Standort"},
        "bemerkungUmwelt": {"bem": "Bemerkung Umwelt"},
        "bemerkungDatenimport": {"bem": "Bemerkung Datenimport"},
    }

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {"vflzId": str(vflz.vflz_id), "bezeichnung": "bla"},
            )
        },
    )

    assert vflz.bemerkung_standort is None
    assert vflz.bemerkung_umwelt is None
    assert vflz.bemerkung_datenimport is None

    assert result.data["updateVflzData"] == {
        "bemerkungStandort": None,
        "bemerkungUmwelt": None,
        "bemerkungDatenimport": None,
    }


def test_update_bemerkung_datenimport_schiessanlage(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    schiessanlage = make_schiessanlage(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                schiessanlagen {
                    intbId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "schiessanlagen": [
                    prefill_optional_fields(
                        vflz_types.SchiessanlageInput,
                        {
                            "intbId": str(schiessanlage.intb_id),
                            "bemerkungDatenimport": {
                                "bem": "Neue Bemerkung Schiessanlage"
                            },
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "schiessanlagen": [
                {
                    "intbId": str(schiessanlage.intb_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung Schiessanlage"},
                }
            ],
        },
    }


def test_update_bemerkung_datenimport_ablagerung(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    intaId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "bemerkungDatenimport": {
                                "bem": "Neue Bemerkung Ablagerung"
                            },
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "ablagerungen": [
                {
                    "intaId": str(ablagerung.inta_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung Ablagerung"},
                }
            ],
        },
    }


def test_update_bemerkung_datenimport_betrieb(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                betriebe {
                    intbId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "betriebe": [
                    prefill_optional_fields(
                        vflz_types.BetriebInput,
                        {
                            "intbId": str(betrieb.intb_id),
                            "bemerkungDatenimport": {"bem": "Neue Bemerkung Betrieb"},
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "betriebe": [
                {
                    "intbId": str(betrieb.intb_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung Betrieb"},
                }
            ],
        },
    }


def test_update_bemerkung_datenimport_pfas(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    pfas = make_pfas(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                pfas {
                    intpId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "pfas": [
                    prefill_optional_fields(
                        vflz_types.PFASInput,
                        {
                            "intpId": str(pfas.intp_id),
                            "bemerkungDatenimport": {"bem": "Neue Bemerkung PFAS"},
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "pfas": [
                {
                    "intpId": str(pfas.intp_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung PFAS"},
                }
            ],
        },
    }


def test_update_bemerkung_datenimport_kinderspielplatz_gruenflaeche(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    ksgf = make_kinderspielplatz_gruenflaeche(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                kinderspielplaetzeGruenflaechen {
                    intkId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "kinderspielplaetzeGruenflaechen": [
                    prefill_optional_fields(
                        vflz_types.KinderspielplatzGruenflaecheInput,
                        {
                            "intkId": str(ksgf.intk_id),
                            "bemerkungDatenimport": {"bem": "Neue Bemerkung KSGF"},
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "kinderspielplaetzeGruenflaechen": [
                {
                    "intkId": str(ksgf.intk_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung KSGF"},
                }
            ],
        },
    }


def test_update_bemerkung_datenimport_unfall(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    intuId
                    bemerkungDatenimport {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "bemerkungDatenimport": {"bem": "Neue Bemerkung Unfall"},
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "unfaelle": [
                {
                    "intuId": str(unfall.intu_id),
                    "bemerkungDatenimport": {"bem": "Neue Bemerkung Unfall"},
                }
            ],
        },
    }


def test_update_vflz_codes(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    make_ktu(session, "bls")
    assert not vflz.ktu
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                deponietyp
                inBetrieb
                nachsorge
                gwsBereich
                gwsZone
                durchlaessigkeit
                karstgeb
                ktu
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "deponietyp": "code:12001:test2",
                    "inBetrieb": False,
                    "nachsorge": True,
                    "gwsBereich": "code:10017:test",
                    "gwsZone": "code:10018:test",
                    "durchlaessigkeit": "code:58:test",
                    "karstgeb": "code:80:nein",
                    "ktu": "code:210:bls",
                },
            )
        },
    )

    assert result.data == {
        "updateVflzData": {
            "vflzId": str(vflz.vflz_id),
            "deponietyp": "code:12001:test2",
            "inBetrieb": False,
            "nachsorge": True,
            "gwsBereich": "code:10017:test",
            "gwsZone": "code:10018:test",
            "durchlaessigkeit": "code:58:test",
            "karstgeb": "code:80:nein",
            "ktu": "code:210:bls",
        }
    }
    assert vflz.ktu
    assert str(vflz.ktu.ktu) == "code:210:bls"


def test_update_ablagerung_of_vflz(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                ablagerungen {
                    intaId
                    volKompartiment
                    tiefe
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                    }
                    bemerkung { bem }
                    bemerkungDatenimport { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    {
                        "intaId": str(ablagerung.inta_id),
                        "volKompartiment": 3.0,
                        "tiefe": "3m",
                        "zeitraum": {
                            "von": "2023-01-01",
                            "bis": "2024-02-02",
                            "vonjahr": False,
                            "bisjahr": True,
                            "bisheute": True,
                        },
                        "kompartimentStoffklassen": [],
                        "bemerkung": {"bem": "Bemerkung Ablagerung"},
                        "bemerkungDatenimport": {
                            "bem": "Bemerkung Datenimport Ablagerung"
                        },
                    }
                ],
            },
        )
    }
    result = run_query(mutation, variables)

    assert result.data == {
        "updateVflzData": {
            "vflzId": str(vflz.vflz_id),
            "ablagerungen": [
                {
                    "intaId": str(ablagerung.inta_id),
                    "volKompartiment": 3.0,
                    "tiefe": "3m",
                    "zeitraum": {
                        "von": "2023-01-01",
                        "bis": "2024-02-02",
                        "vonjahr": False,
                        "bisjahr": True,
                        "bisheute": True,
                    },
                    "bemerkung": {"bem": "Bemerkung Ablagerung"},
                    "bemerkungDatenimport": {"bem": "Bemerkung Datenimport Ablagerung"},
                }
            ],
        }
    }


def test_create_ablagerung_for_existing_vflz(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    assert not session.scalars(select(Ablagerung)).one_or_none()

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                ablagerungen {
                    intaId
                    volKompartiment
                    tiefe
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    {
                        "intaId": None,
                        "volKompartiment": 3.0,
                        "tiefe": "3m",
                        "zeitraum": {
                            "von": "2023-01-01",
                            "bis": "2024-02-02",
                            "vonjahr": False,
                            "bisjahr": True,
                            "bisheute": True,
                        },
                        "kompartimentStoffklassen": [],
                        "bemerkung": None,
                        "bemerkungDatenimport": None,
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    db_ablagerung = session.scalars(select(Ablagerung)).one()

    assert result.data == {
        "updateVflzData": {
            "vflzId": str(vflz.vflz_id),
            "ablagerungen": [
                {
                    "intaId": str(db_ablagerung.inta_id),
                    "volKompartiment": 3.0,
                    "tiefe": "3m",
                    "zeitraum": {
                        "von": "2023-01-01",
                        "bis": "2024-02-02",
                        "vonjahr": False,
                        "bisjahr": True,
                        "bisheute": True,
                    },
                }
            ],
        },
    }


def test_update_vflz_delete_one_ablagerung_update_one_and_create_one(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    make_ablagerung(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    intaId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "tiefe": "10m",
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "tiefe": "5m",
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    inta_ids = [
        int(ablagerung["intaId"])
        for ablagerung in result.data["updateVflzData"]["ablagerungen"]
    ]
    db_ablagerungen_ids = list(
        session.scalars(
            select(Ablagerung.inta_id).where(Ablagerung.vflz_id == vflz.vflz_id)
        ).all()
    )

    assert inta_ids == db_ablagerungen_ids

    # test if new object was created
    db_ablagerungen_ids.remove(ablagerung.inta_id)
    assert len(db_ablagerungen_ids) == 1
    assert db_ablagerungen_ids[0] != ablagerung.inta_id


def test_update_vflz_betrieb(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                betriebe {
                    intbId
                    brancheAsw
                    brancheNoga
                    untersuchungsStand
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                        genauigkeitVon
                        genauigkeitBis
                    }
                    firmaName
                    firmaStrasse
                    firmaPlz
                    firmaOrt
                    groesse
                    eva
                    relevant
                    mobileStoffe
                    beurteilung
                    zentroid
                    bemerkung { bem }
                    bemerkungDatenimport { bem }
                    begruendungBewertung { bem }
                }
            }
        }
    }
    """

    geojson = {
        "type": "Point",
        "coordinates": [40, 20],
    }

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": vflz.vflz_id,
                "betriebe": [
                    {
                        "intbId": str(betrieb.intb_id),
                        "brancheAsw": "code:25:test2",
                        "brancheNoga": "code:25001:test2",
                        "untersuchungsStand": "code:10023:test2",
                        "zeitraum": {
                            "von": date(2027, 1, 1).isoformat(),
                            "bis": date(2028, 2, 2).isoformat(),
                            "vonjahr": False,
                            "bisjahr": True,
                            "bisheute": False,
                            "genauigkeitVon": "code:90:test2",
                            "genauigkeitBis": None,
                        },
                        "firmaName": "Foo Firma Name",
                        "firmaStrasse": "Foo Firma Strasse",
                        "firmaPlz": "1234",
                        "firmaOrt": "Foo Firma Ort",
                        "groesse": 10,
                        "eva": "Foo EVA",
                        "relevant": False,
                        "mobileStoffe": True,
                        "beurteilung": "code:103:test2",
                        "zentroid": geojson,
                        "bemerkung": {"bem": "Bemerkung Betrieb"},
                        "bemerkungDatenimport": {
                            "bem": "Bemerkung Datenimport Betrieb"
                        },
                        "begruendungBewertung": {"bem": "Begründung Bewertung Betrieb"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["betriebe"] == [
        {
            "intbId": str(betrieb.intb_id),
            "brancheAsw": "code:25:test2",
            "brancheNoga": "code:25001:test2",
            "untersuchungsStand": "code:10023:test2",
            "zeitraum": {
                "von": date(2027, 1, 1).isoformat(),
                "bis": date(2028, 2, 2).isoformat(),
                "vonjahr": False,
                "bisjahr": True,
                "bisheute": False,
                "genauigkeitVon": "code:90:test2",
                "genauigkeitBis": None,
            },
            "firmaName": "Foo Firma Name",
            "firmaStrasse": "Foo Firma Strasse",
            "firmaPlz": "1234",
            "firmaOrt": "Foo Firma Ort",
            "groesse": 10,
            "eva": "Foo EVA",
            "relevant": False,
            "mobileStoffe": True,
            "beurteilung": "code:103:test2",
            "zentroid": {
                "type": "Point",
                "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                "coordinates": [40, 20],
            },
            "bemerkung": {"bem": "Bemerkung Betrieb"},
            "bemerkungDatenimport": {"bem": "Bemerkung Datenimport Betrieb"},
            "begruendungBewertung": {"bem": "Begründung Bewertung Betrieb"},
        }
    ]


def test_update_vflz_delete_one_betrieb_update_one_and_create_one(
    session: Session, run_query
):
    vflz = make_vflz(session, "My Site")
    betrieb = make_betrieb(session, vflz)
    other_betrieb = make_betrieb(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                betriebe {
                    intbId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "betriebe": [
                    prefill_optional_fields(
                        vflz_types.BetriebInput,
                        {
                            "intbId": str(betrieb.intb_id),
                            "groesse": 20,
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.BetriebInput,
                        {
                            "groesse": 30,
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    betrieb_ids = [
        intb_id
        for intb_id in session.scalars(
            select(Betrieb.intb_id)
            .where(Betrieb.vflz_id == vflz.vflz_id)
            .order_by(Betrieb.zeitraum_von, Betrieb.vflz_id)
        ).all()
    ]
    assert other_betrieb.intb_id not in betrieb_ids
    assert [
        int(betrieb["intbId"]) for betrieb in result.data["updateVflzData"]["betriebe"]
    ] == betrieb_ids

    # test if new object was created
    betrieb_ids.remove(betrieb.intb_id)
    assert len(betrieb_ids) == 1
    assert betrieb_ids[0] != betrieb.intb_id


def test_update_vflz_schiessanlage(session: Session, run_query):
    zentroid = {
        "type": "Point",
        "coordinates": [40, 20],
    }

    vflz = make_vflz(session, "My Site")
    schiessanlage = make_schiessanlage(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                schiessanlagen {
                    intbId
                    brancheAsw
                    brancheNoga
                    untersuchungsStand
                    beurteilung
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                        genauigkeitVon
                        genauigkeitBis
                    }
                    firmaName
                    firmaStrasse
                    firmaPlz
                    firmaOrt
                    groesse
                    eva
                    relevant
                    mobileStoffe
                    typ
                    schusszahl
                    scheibenzahl
                    hatKugelfang
                    zentroid
                    bemerkung {
                        bem
                    }
                    bemerkungDatenimport {
                        bem
                    }
                    begruendungBewertung {
                        bem
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": vflz.vflz_id,
                "schiessanlagen": [
                    {
                        "intbId": str(schiessanlage.intb_id),
                        "brancheAsw": "code:25:test2",
                        "brancheNoga": "code:25001:test2",
                        "untersuchungsStand": "code:10023:test2",
                        "zeitraum": {
                            "von": date(2027, 1, 1).isoformat(),
                            "bis": date(2028, 2, 2).isoformat(),
                            "vonjahr": False,
                            "bisjahr": True,
                            "bisheute": False,
                            "genauigkeitVon": None,
                            "genauigkeitBis": "code:90:test2",
                        },
                        "firmaName": "Foo Firma Name",
                        "firmaStrasse": "Foo Firma Strasse",
                        "firmaPlz": "1234",
                        "firmaOrt": "Foo Firma Ort",
                        "groesse": 10,
                        "eva": "Foo EVA",
                        "relevant": False,
                        "mobileStoffe": True,
                        "typ": "code:11410:test2",
                        "schusszahl": 3,
                        "scheibenzahl": 23,
                        "hatKugelfang": False,
                        "beurteilung": "code:103:test2",
                        "zentroid": zentroid,
                        "bemerkung": {"bem": "foo bem"},
                        "bemerkungDatenimport": {"bem": "bar bem"},
                        "begruendungBewertung": {"bem": "bar"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["schiessanlagen"] == [
        {
            "intbId": str(schiessanlage.intb_id),
            "brancheAsw": "code:25:test2",
            "brancheNoga": "code:25001:test2",
            "untersuchungsStand": "code:10023:test2",
            "beurteilung": "code:103:test2",
            "zeitraum": {
                "von": date(2027, 1, 1).isoformat(),
                "bis": date(2028, 2, 2).isoformat(),
                "vonjahr": False,
                "bisjahr": True,
                "bisheute": False,
                "genauigkeitVon": None,
                "genauigkeitBis": "code:90:test2",
            },
            "firmaName": "Foo Firma Name",
            "firmaStrasse": "Foo Firma Strasse",
            "firmaPlz": "1234",
            "firmaOrt": "Foo Firma Ort",
            "groesse": 10,
            "eva": "Foo EVA",
            "relevant": False,
            "mobileStoffe": True,
            "typ": "code:11410:test2",
            "schusszahl": 3,
            "scheibenzahl": 23,
            "hatKugelfang": False,
            "zentroid": {
                "type": "Point",
                "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
                "coordinates": [40, 20],
            },
            "bemerkung": {"bem": "foo bem"},
            "bemerkungDatenimport": {"bem": "bar bem"},
            "begruendungBewertung": {"bem": "bar"},
        }
    ]


def test_update_vflz_delete_one_schiessanlage_update_one_and_create_one(
    session, run_query
):
    vflz = make_vflz(session, "My Site")
    schiessanlage = make_schiessanlage(session, vflz)
    other_schiessanlage = make_schiessanlage(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                schiessanlagen {
                    intbId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "schiessanlagen": [
                    prefill_optional_fields(
                        vflz_types.SchiessanlageInput,
                        {
                            "intbId": str(schiessanlage.intb_id),
                            "groesse": 20,
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.SchiessanlageInput,
                        {
                            "groesse": 30,
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    schiessanlagen_ids = list(
        session.scalars(
            select(Schiessanlage.intb_id).where(Schiessanlage.vflz_id == vflz.vflz_id)
        ).all()
    )
    assert other_schiessanlage.intb_id not in schiessanlagen_ids
    assert sorted(
        [
            int(schiessanlage["intbId"])
            for schiessanlage in result.data["updateVflzData"]["schiessanlagen"]
        ]
    ) == sorted(schiessanlagen_ids)

    # test if new object was created
    schiessanlagen_ids.remove(schiessanlage.intb_id)
    assert len(schiessanlagen_ids) == 1
    assert schiessanlagen_ids[0] != schiessanlage.intb_id


def test_update_vflz_unfall(session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    intuId
                    genauigkeitZeitpunkt
                    zeitpunkt
                    zeitpunktjahr
                    bemerkung { bem }
                    bemerkungDatenimport { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    {
                        "intuId": str(unfall.intu_id),
                        "genauigkeitZeitpunkt": "code:90:test2",
                        "zeitpunkt": "2020-01-01",
                        "zeitpunktjahr": False,
                        "name": None,
                        "unfallstoffe": [],
                        "bemerkung": {"bem": "Bemerkung Unfall"},
                        "bemerkungDatenimport": {"bem": "Bemerkung Datenimport Unfall"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    assert result.data["updateVflzData"] == {
        "unfaelle": [
            {
                "intuId": str(unfall.intu_id),
                "genauigkeitZeitpunkt": "code:90:test2",
                "zeitpunkt": "2020-01-01",
                "zeitpunktjahr": False,
                "bemerkung": {"bem": "Bemerkung Unfall"},
                "bemerkungDatenimport": {"bem": "Bemerkung Datenimport Unfall"},
            }
        ]
    }


def test_update_vflz_delete_one_unfall_update_one_and_create_one(session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    other_unfall = make_unfall(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    intuId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "zeitpunktjahr": True,
                        },
                    ),
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "zeitpunktjahr": False,
                        },
                    ),
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    unfaelle_ids = [unfall.intu_id for unfall in vflz.unfaelle]
    assert other_unfall.intu_id not in unfaelle_ids
    assert [
        int(unfall["intuId"]) for unfall in result.data["updateVflzData"]["unfaelle"]
    ] == unfaelle_ids

    # test if new object was created
    unfaelle_ids.remove(unfall.intu_id)
    assert len(unfaelle_ids) == 1
    assert unfaelle_ids[0] != unfall.intu_id


def test_update_unfallstoffe_of_vflz(session, run_query):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    unfallstoff = make_unfallstoff(session, unfall)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    unfallstoffe {
                        inumId
                        stoff
                        stoffmng
                        ausgelaufen
                        zurueckgewonnen
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "unfallstoffe": [
                                {
                                    "inumId": str(unfallstoff.inum_id),
                                    "stoff": "code:117:test2",
                                    "stoffmng": 3.2,
                                    "ausgelaufen": 4.0,
                                    "zurueckgewonnen": 2.0,
                                }
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"] == {
        "unfaelle": [
            {
                "unfallstoffe": [
                    {
                        "inumId": str(unfallstoff.inum_id),
                        "stoff": "code:117:test2",
                        "stoffmng": 3.2,
                        "ausgelaufen": 4.0,
                        "zurueckgewonnen": 2.0,
                    }
                ]
            }
        ]
    }


def test_update_vflz_delete_one_unfallstoff_update_one_and_create_one(
    session, run_query
):
    vflz = make_vflz(session, "My Site")
    unfall = make_unfall(session, vflz)
    unfallstoff = make_unfallstoff(session, unfall)
    other_unfallstoff = make_unfallstoff(session, unfall)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    unfallstoffe {
                        inumId
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "unfallstoffe": [
                                prefill_optional_fields(
                                    vflz_types.UnfallstoffInput,
                                    {
                                        "inumId": str(unfallstoff.inum_id),
                                        "stoffmng": 10.3,
                                    },
                                ),
                                prefill_optional_fields(
                                    vflz_types.UnfallstoffInput,
                                    {
                                        "stoffmng": 4.3,
                                    },
                                ),
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    unfallstoffe_ids = list(
        session.scalars(
            select(Unfallstoff.inum_id)
            .join(Unfall)
            .where(Unfall.vflz_id == vflz.vflz_id)
        ).all()
    )
    assert other_unfallstoff.inum_id not in unfallstoffe_ids
    assert [
        int(unfallstoff["inumId"])
        for unfallstoff in result.data["updateVflzData"]["unfaelle"][0]["unfallstoffe"]
    ] == unfallstoffe_ids

    # test if new object was created
    unfallstoffe_ids.remove(unfallstoff.inum_id)
    assert len(unfallstoffe_ids) == 1
    assert unfallstoffe_ids[0] != unfallstoff.inum_id


def test_update_kksk_of_vflz(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    kompartimentStoffklassen {
                        stoffklasse
                        teilvol
                        zeitraum {
                            von
                            bis
                            vonjahr
                            bisjahr
                            bisheute
                            genauigkeitVon
                            genauigkeitBis
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                {
                                    "kkskId": str(kksk.kksk_id),
                                    "stoffklasse": "code:94:test2",
                                    "teilvol": 4.2,
                                    "zeitraum": {
                                        "von": "2020-01-01",
                                        "bis": "2023-02-02",
                                        "vonjahr": False,
                                        "bisjahr": True,
                                        "bisheute": False,
                                        "genauigkeitVon": None,
                                        "genauigkeitBis": "code:90:test2",
                                    },
                                    "kompartimentStoffgruppen": [],
                                }
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["ablagerungen"][0][
        "kompartimentStoffklassen"
    ] == [
        {
            "stoffklasse": "code:94:test2",
            "teilvol": 4.2,
            "zeitraum": {
                "von": "2020-01-01",
                "bis": "2023-02-02",
                "vonjahr": False,
                "bisjahr": True,
                "bisheute": False,
                "genauigkeitVon": None,
                "genauigkeitBis": "code:90:test2",
            },
        }
    ]


def test_update_vflz_delete_one_kksk_update_one_and_create_one(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)
    other_kksk = make_kompartiment_stoffklasse(session, ablagerung)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    kompartimentStoffklassen {
                        kkskId
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                {
                                    "kkskId": str(kksk.kksk_id),
                                    "teilvol": 10.3,
                                    "stoffklasse": None,
                                    "zeitraum": None,
                                    "kompartimentStoffgruppen": [],
                                },
                                prefill_optional_fields(
                                    vflz_types.KompartimentStoffklasseInput,
                                    {
                                        "teilvol": 10.4,
                                    },
                                ),
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    kksk_ids = list(
        session.scalars(
            select(KompartimentStoffklasse.kksk_id)
            .join(Ablagerung)
            .where(Ablagerung.vflz_id == vflz.vflz_id)
        ).all()
    )
    assert other_kksk.kksk_id not in kksk_ids
    assert [
        int(kksk["kkskId"])
        for kksk in result.data["updateVflzData"]["ablagerungen"][0][
            "kompartimentStoffklassen"
        ]
    ] == kksk_ids

    # test if new object was created
    kksk_ids.remove(kksk.kksk_id)
    assert len(kksk_ids) == 1
    assert kksk_ids[0] != kksk.kksk_id


def test_update_kksg_of_vflz(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)
    kksg = make_kompartiment_stoffgruppe(session, kksk)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                    ablagerungen {
                    kompartimentStoffklassen {
                        kompartimentStoffgruppen {
                            stoffgruppe
                            teilvol
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                prefill_optional_fields(
                                    vflz_types.KompartimentStoffklasseInput,
                                    {
                                        "kkskId": str(kksk.kksk_id),
                                        "kompartimentStoffgruppen": [
                                            {
                                                "kksgId": str(kksg.kksg_id),
                                                "stoffgruppe": "code:110:test2",
                                                "teilvol": 5.0,
                                            }
                                        ],
                                    },
                                )
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["ablagerungen"][0][
        "kompartimentStoffklassen"
    ] == [
        {
            "kompartimentStoffgruppen": [
                {"stoffgruppe": "code:110:test2", "teilvol": 5.0}
            ]
        }
    ]


def test_update_vflz_delete_one_kksg_update_one_and_create_one(session, run_query):
    vflz = make_vflz(session, "My Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)
    kksg = make_kompartiment_stoffgruppe(session, kksk)
    other_kksg = make_kompartiment_stoffgruppe(session, kksk)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    kompartimentStoffklassen {
                        kompartimentStoffgruppen {
                            kksgId
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                {
                                    "kkskId": str(kksk.kksk_id),
                                    "kompartimentStoffgruppen": [
                                        {
                                            "kksgId": str(kksg.kksg_id),
                                            "teilvol": 3.0,
                                            "stoffgruppe": None,
                                        },
                                        {
                                            "kksgId": None,
                                            "teilvol": 5.0,
                                            "stoffgruppe": None,
                                        },
                                    ],
                                    "stoffklasse": None,
                                    "teilvol": None,
                                    "zeitraum": None,
                                }
                            ],
                        },
                    )
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    kksg_ids = list(
        session.scalars(
            select(KompartimentStoffgruppe.kksg_id)
            .join(KompartimentStoffklasse)
            .join(Ablagerung)
            .where(Ablagerung.vflz_id == vflz.vflz_id)
        ).all()
    )
    assert other_kksg.kksg_id not in kksg_ids
    assert [
        int(kksg["kksgId"])
        for kksg in result.data["updateVflzData"]["ablagerungen"][0][
            "kompartimentStoffklassen"
        ][0]["kompartimentStoffgruppen"]
    ] == kksg_ids

    # test if new object was created
    kksg_ids.remove(kksg.kksg_id)
    assert len(kksg_ids) == 1
    assert kksg_ids[0] != kksg.kksg_id


def test_delete_only_ablagerungen_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    ablagerung = make_ablagerung(session, vflz)

    vflz2 = make_vflz(session, "Second Site", 2)
    ablagerung2 = make_ablagerung(session, vflz2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    intaId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "ablagerungen": [], "bezeichnung": "bla"},
        )
    }

    ablagerungen_pre_delete: list[int] = list(
        session.scalars(select(Ablagerung).order_by("inta_id")).all()
    )
    assert ablagerungen_pre_delete == [ablagerung, ablagerung2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["ablagerungen"]

    ablagerungen_ids_post_delete = list(session.scalars(select(Ablagerung)).all())

    assert ablagerungen_ids_post_delete == [ablagerung2]


def test_delete_only_kompartiment_stoffklassen_of_one_ablagerung_object(
    session, run_query
):
    vflz = make_vflz(session, "First Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)

    vflz2 = make_vflz(session, "Second Site", 2)
    ablagerung2 = make_ablagerung(session, vflz2)
    kksk2 = make_kompartiment_stoffklasse(session, ablagerung2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    intaId
                    kompartimentStoffklassen {
                        kkskId
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [],
                        },
                    )
                ],
            },
        )
    }

    kksk_pre_delete: list[int] = list(
        session.scalars(select(KompartimentStoffklasse).order_by("kksk_id")).all()
    )
    assert kksk_pre_delete == [kksk, kksk2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["ablagerungen"][0][
        "kompartimentStoffklassen"
    ]

    kksk_ids_post_delete = list(session.scalars(select(KompartimentStoffklasse)).all())

    assert kksk_ids_post_delete == [kksk2]


def test_delete_only_kompartiment_stoffgruppen_of_one_kksk_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)
    kksg = make_kompartiment_stoffgruppe(session, kksk)

    vflz2 = make_vflz(session, "Second Site", 2)
    ablagerung2 = make_ablagerung(session, vflz2)
    kksk2 = make_kompartiment_stoffklasse(session, ablagerung2)
    kksg2 = make_kompartiment_stoffgruppe(session, kksk2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                ablagerungen {
                    intaId
                    kompartimentStoffklassen {
                        kkskId
                        kompartimentStoffgruppen {
                            kksgId
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "ablagerungen": [
                    prefill_optional_fields(
                        vflz_types.AblagerungInput,
                        {
                            "intaId": str(ablagerung.inta_id),
                            "kompartimentStoffklassen": [
                                prefill_optional_fields(
                                    vflz_types.KompartimentStoffklasseInput,
                                    {
                                        "kkskId": str(kksk.kksk_id),
                                        "kompartimentStoffgruppen": [],
                                    },
                                )
                            ],
                        },
                    )
                ],
            },
        )
    }

    kksg_pre_delete: list[int] = list(
        session.scalars(select(KompartimentStoffgruppe).order_by("kksg_id")).all()
    )
    assert kksg_pre_delete == [kksg, kksg2]

    result = run_query(mutation, variables)
    assert not (
        result.data["updateVflzData"]["ablagerungen"][0]["kompartimentStoffklassen"][0][
            "kompartimentStoffgruppen"
        ]
    )

    kksg_ids_post_delete = list(session.scalars(select(KompartimentStoffgruppe)).all())

    assert kksg_ids_post_delete == [kksg2]


def test_delete_only_betriebe_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    betrieb = make_betrieb(session, vflz)

    vflz2 = make_vflz(session, "Second Site", 2)
    betrieb2 = make_betrieb(session, vflz2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                betriebe {
                    intbId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "betriebe": [], "bezeichnung": "bla"},
        )
    }

    betriebe_pre_delete: list[int] = list(
        session.scalars(select(Betrieb).order_by("intb_id")).all()
    )
    assert betriebe_pre_delete == [betrieb, betrieb2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["betriebe"]

    betriebe_post_delete = list(session.scalars(select(Betrieb)).all())

    assert betriebe_post_delete == [betrieb2]


def test_delete_only_schiessanlagen_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    schiessanlage = make_schiessanlage(session, vflz)

    vflz2 = make_vflz(session, "Second Site", 2)
    schiessanlage2 = make_schiessanlage(session, vflz2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                schiessanlagen {
                    intbId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "schiessanlagen": [], "bezeichnung": "foo"},
        )
    }

    schiessanlagen_pre_delete: list[int] = list(
        session.scalars(select(Schiessanlage).order_by("intb_id")).all()
    )
    assert schiessanlagen_pre_delete == [schiessanlage, schiessanlage2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["schiessanlagen"]

    schiessanlagen_post_delete = list(session.scalars(select(Schiessanlage)).all())

    assert schiessanlagen_post_delete == [schiessanlage2]


def test_delete_only_unfaelle_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    unfall = make_unfall(session, vflz)

    vflz2 = make_vflz(session, "Second Site", 2)
    unfall2 = make_unfall(session, vflz2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    intuId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "unfaelle": [], "bezeichnung": "foo"},
        )
    }

    unfaelle_pre_delete: list[int] = list(
        session.scalars(select(Unfall).order_by("intu_id")).all()
    )
    assert unfaelle_pre_delete == [unfall, unfall2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["unfaelle"]

    unfaelle_post_delete = list(session.scalars(select(Unfall)).all())

    assert unfaelle_post_delete == [unfall2]


def test_delete_only_unfaellstoffe_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    unfall = make_unfall(session, vflz)
    unfallstoff = make_unfallstoff(session, unfall)

    vflz2 = make_vflz(session, "Second Site", 2)
    unfall2 = make_unfall(session, vflz2)
    unfallstoff2 = make_unfallstoff(session, unfall2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                unfaelle {
                    intuId
                    unfallstoffe {
                        inumId
                    }
                }
            }

        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "unfaelle": [
                    prefill_optional_fields(
                        vflz_types.UnfallInput,
                        {
                            "intuId": str(unfall.intu_id),
                            "unfallstoffe": [],
                        },
                    )
                ],
            },
        )
    }

    unfallstoffe_pre_delete: list[int] = list(
        session.scalars(select(Unfallstoff).order_by("inum_id")).all()
    )
    assert unfallstoffe_pre_delete == [unfallstoff, unfallstoff2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["unfaelle"][0]["unfallstoffe"]

    unfallstoffe_post_delete = list(
        session.scalars(select(Unfallstoff).order_by("inum_id")).all()
    )

    assert unfallstoffe_post_delete == [unfallstoff2]


def test_create_grundwasser(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                grundwasser {
                    relativeLage
                    flurabstand
                    nutzung
                    distanz
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "grundwasser": [
                    {
                        "gwasId": None,
                        "relativeLage": "code:71:test",
                        "flurabstand": 3.0,
                        "nutzung": "code:88:test",
                        "distanz": 3,
                    }
                ],
            },
        )
    }
    assert not list(session.scalars(select(Grundwasser)))

    result = run_query(mutation, variables)

    assert result.data["updateVflzData"]["grundwasser"] == [
        {
            "relativeLage": "code:71:test",
            "flurabstand": 3.0,
            "nutzung": "code:88:test",
            "distanz": 3,
        }
    ]

    assert len(list(session.scalars(select(Grundwasser)))) == 1


def test_update_existing_grundwasser(session, run_query):
    vflz = make_vflz(session, "My Site")
    gwas = make_grundwasser(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                grundwasser {
                    gwasId
                    relativeLage
                    flurabstand
                    nutzung
                    distanz
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "grundwasser": [
                    {
                        "gwasId": str(gwas.gwas_id),
                        "relativeLage": "code:71:test",
                        "flurabstand": 5.0,
                        "nutzung": "code:88:test",
                        "distanz": 7,
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["grundwasser"] == [
        {
            "gwasId": str(gwas.gwas_id),
            "relativeLage": "code:71:test",
            "flurabstand": 5.0,
            "nutzung": "code:88:test",
            "distanz": 7,
        }
    ]

    assert len(list(session.scalars(select(Grundwasser)))) == 1


def test_deleting_grundwasser_also_deletes_in_db(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_grundwasser(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                grundwasser {
                    relativeLage
                    flurabstand
                    nutzung
                    distanz
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "bezeichnung": "bla"},
        )
    }

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["grundwasser"]

    assert not list(session.scalars(select(Grundwasser)))


def test_create_oberflaechen_gewaesser(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                oberflaechenGewaesser {
                    artGewaesser
                    bauGewaesser
                    relativeLage
                    distanz
                    name
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "oberflaechenGewaesser": [
                    {
                        "ogwId": None,
                        "artGewaesser": "code:66:test2",
                        "bauGewaesser": "code:67:test2",
                        "relativeLage": "code:70:test2",
                        "distanz": 23,
                        "name": "bar ogw",
                    }
                ],
            },
        )
    }
    assert not list(session.scalars(select(OberflaechenGewaesser)))

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["oberflaechenGewaesser"][0] == {
        "artGewaesser": "code:66:test2",
        "bauGewaesser": "code:67:test2",
        "relativeLage": "code:70:test2",
        "distanz": 23,
        "name": "bar ogw",
    }

    assert len(list(session.scalars(select(OberflaechenGewaesser)))) == 1


def test_update_existing_oberflaechen_gewaesser(session, run_query):
    vflz = make_vflz(session, "My Site")
    ogw = make_oberflaechen_gewaesser(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                oberflaechenGewaesser {
                    ogwId
                    artGewaesser
                    bauGewaesser
                    relativeLage
                    distanz
                    name
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "oberflaechenGewaesser": [
                    {
                        "ogwId": str(ogw.ogw_id),
                        "artGewaesser": "code:66:test2",
                        "bauGewaesser": "code:67:test2",
                        "relativeLage": "code:70:test2",
                        "distanz": 23,
                        "name": "bar ogw",
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["oberflaechenGewaesser"] == [
        {
            "ogwId": str(ogw.ogw_id),
            "artGewaesser": "code:66:test2",
            "bauGewaesser": "code:67:test2",
            "relativeLage": "code:70:test2",
            "distanz": 23,
            "name": "bar ogw",
        }
    ]

    assert len(list(session.scalars(select(OberflaechenGewaesser)))) == 1


def test_deleting_oberflaechen_gewaesser_also_deletes_in_db(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_oberflaechen_gewaesser(session, vflz)
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                oberflaechenGewaesser {
                    artGewaesser
                    bauGewaesser
                    relativeLage
                    distanz
                    name
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "oberflaechenGewaesser": [],
                "bezeichnung": "bla",
            },
        )
    }
    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["oberflaechenGewaesser"]

    assert not list(session.scalars(select(OberflaechenGewaesser)))


def test_delete_only_nutzung_boden_of_one_vflz_object(session, run_query):
    vflz = make_vflz(session, "First Site")
    nubo = make_nutzung_boden(session, vflz)

    vflz2 = make_vflz(session, "Second Site", 2)
    nubo2 = make_nutzung_boden(session, vflz2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                nutzungenBoden {
                    nuboId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "nutzungenBoden": [], "bezeichnung": "bla"},
        )
    }

    nutzung_boden_pre_delete: list[int] = list(
        session.scalars(select(NutzungBoden).order_by("nubo_id")).all()
    )
    assert nutzung_boden_pre_delete == [nubo, nubo2]

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["nutzungenBoden"]

    nutzung_boden_post_delete = list(session.scalars(select(NutzungBoden)).all())

    assert nutzung_boden_post_delete == [nubo2]


def test_update_nutzung_boden(session, run_query):
    vflz = make_vflz(session, "First Site")
    nutzung_boden = make_nutzung_boden(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                nutzungenBoden {
                    nutzungsart
                    aktuelleNutzung
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "nutzungenBoden": [
                    {
                        "nuboId": str(nutzung_boden.nubo_id),
                        "nutzungsart": "code:87:test2",
                        "aktuelleNutzung": "code:92:test2",
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["nutzungenBoden"] == [
        {
            "nutzungsart": "code:87:test2",
            "aktuelleNutzung": "code:92:test2",
        }
    ]


def test_update_vflz_delete_one_nutzung_boden_update_one_and_create_one(
    session, run_query
):
    vflz = make_vflz(session, "My Site")
    nutzung_boden1 = make_nutzung_boden(session, vflz)
    nutzung_boden2 = make_nutzung_boden(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                nutzungenBoden {
                    nuboId
                    nutzungsart
                    aktuelleNutzung
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "nutzungenBoden": [
                    {
                        "nuboId": str(nutzung_boden1.nubo_id),
                        "nutzungsart": "code:87:test2",
                        "aktuelleNutzung": "code:92:test2",
                    },
                    {
                        "nuboId": None,
                        "nutzungsart": "code:87:test2",
                        "aktuelleNutzung": "code:92:test2",
                    },
                ],
            },
        )
    }

    result = run_query(mutation, variables)

    nubo_ids = list(
        session.scalars(
            select(NutzungBoden.nubo_id).where(NutzungBoden.vflz_id == vflz.vflz_id)
        ).all()
    )
    assert nutzung_boden2.nubo_id not in nubo_ids
    assert [
        int(nubo["nuboId"]) for nubo in result.data["updateVflzData"]["nutzungenBoden"]
    ] == nubo_ids

    # test if new object was created
    nubo_ids.remove(nutzung_boden1.nubo_id)
    assert len(nubo_ids) == 1
    assert nubo_ids[0] != nutzung_boden1.nubo_id


def test_update_umweltstoff(session, run_query):
    vflz = make_vflz(session, "My Site")
    umweltstoff = make_umweltstoff(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltStoffe {
                    gefaehrdeteBereiche
                    stoffGruppe
                    stoff
                    beurteilung
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "umweltStoffe": [
                    {
                        "stoffeId": str(umweltstoff.stoffe_id),
                        "gefaehrdeteBereiche": "code:299:test2",
                        "stoffGruppe": "code:300:test2",
                        "stoff": "code:301:test2",
                        "beurteilung": "code:330:test2",
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["umweltStoffe"] == [
        {
            "gefaehrdeteBereiche": "code:299:test2",
            "stoffGruppe": "code:300:test2",
            "stoff": "code:301:test2",
            "beurteilung": "code:330:test2",
        }
    ]


def test_delete_umweltstoff(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_umweltstoff(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltStoffe {
                    gefaehrdeteBereiche
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "umweltStoffe": [], "bezeichnung": "foo"},
        )
    }

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["umweltStoffe"]
    assert not list(session.scalars(select(UmweltStoff)).all())


def test_create_new_umweltstoff(session, run_query):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltStoffe {
                    gefaehrdeteBereiche
                    stoffGruppe
                    stoff
                    beurteilung
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "umweltStoffe": [
                    {
                        "stoffeId": None,
                        "gefaehrdeteBereiche": "code:299:test2",
                        "stoffGruppe": "code:300:test2",
                        "stoff": "code:301:test2",
                        "beurteilung": "code:330:test2",
                    }
                ],
            },
        )
    }
    assert not list(session.scalars(select(UmweltStoff)).all())

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["umweltStoffe"] == [
        {
            "gefaehrdeteBereiche": "code:299:test2",
            "stoffGruppe": "code:300:test2",
            "stoff": "code:301:test2",
            "beurteilung": "code:330:test2",
        }
    ]
    assert len(list(session.scalars(select(UmweltStoff)).all())) == 1


def test_update_einzelereignis(session, run_query):
    vflz = make_vflz(session, "My Site")
    einzelereignis = make_einzelereignis(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                einzelereignisse {
                    einzelereignis
                    datum
                    bemerkung { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "einzelereignisse": [
                    {
                        "veenId": str(einzelereignis.veen_id),
                        "einzelereignis": "code:61:test2",
                        "datum": "2020-01-01",
                        "bemerkung": {"bem": "Bemerkung Einzelereignis"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["einzelereignisse"] == [
        {
            "einzelereignis": "code:61:test2",
            "datum": "2020-01-01",
            "bemerkung": {"bem": "Bemerkung Einzelereignis"},
        }
    ]


def test_delete_einzelereignis(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_einzelereignis(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                einzelereignisse {
                    einzelereignis
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "einzelereignisse": [], "bezeichnung": "foo"},
        )
    }

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["einzelereignisse"]
    assert not list(session.scalars(select(Einzelereignis)).all())


def test_create_einzelereignis(session, run_query):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                einzelereignisse {
                    einzelereignis
                    datum
                    bemerkung { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "einzelereignisse": [
                    {
                        "veenId": None,
                        "einzelereignis": "code:61:test2",
                        "datum": "2020-01-01",
                        "bemerkung": {"bem": "Bemerkung Einzelereignis"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["einzelereignisse"] == [
        {
            "einzelereignis": "code:61:test2",
            "datum": "2020-01-01",
            "bemerkung": {"bem": "Bemerkung Einzelereignis"},
        }
    ]

    assert len(list(session.scalars(select(Einzelereignis)).all())) == 1


def test_update_umweltschaden(session, run_query):
    vflz = make_vflz(session, "My Site")
    umweltschaden = make_umweltschaden(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltschaeden {
                    artSchaden
                    schaeden
                    bemerkung { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "umweltschaeden": [
                    {
                        "vfusId": str(umweltschaden.vfus_id),
                        "artSchaden": "code:101:test2",
                        "schaeden": "code:102:test2",
                        "bemerkung": {"bem": "Bemerkung Umweltschaden"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["umweltschaeden"] == [
        {
            "artSchaden": "code:101:test2",
            "schaeden": "code:102:test2",
            "bemerkung": {"bem": "Bemerkung Umweltschaden"},
        }
    ]


def test_create_new_umweltschaden(session, run_query):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltschaeden {
                    artSchaden
                    schaeden
                    bemerkung { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "umweltschaeden": [
                    {
                        "vfusId": None,
                        "artSchaden": "code:101:test2",
                        "schaeden": "code:102:test2",
                        "bemerkung": {"bem": "Bemerkung Umweltschaden"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["umweltschaeden"] == [
        {
            "artSchaden": "code:101:test2",
            "schaeden": "code:102:test2",
            "bemerkung": {"bem": "Bemerkung Umweltschaden"},
        }
    ]

    assert len(list(session.scalars(select(Umweltschaden)).all())) == 1


def test_delete_umweltschaden(session, run_query):
    vflz = make_vflz(session, "My Site")
    umweltschaden = make_umweltschaden(session, vflz)

    bemerkung = bem_models.BemerkungUmweltschaden(bem="foo")
    bemerkung.key_value = umweltschaden.vfus_id

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                umweltschaeden {
                    vfusId
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "bezeichnung": "bla",
                "umweltschaeden": [],
            },
        )
    }

    result = run_query(mutation, variables)
    assert not result.data["updateVflzData"]["umweltschaeden"]

    assert not list(session.scalars(select(Umweltschaden)).all())


def test_update_gemeinde_of_vflz(session, run_query):
    vflz = make_vflz(session, "My Site")
    gemeinde2 = make_gemeinde(session, bfs_nummer=2)

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
                gemeinde {
                    hGemId
                }
            }
        }
    }
    """

    result = run_query(
        query=mutation,
        variable_values={
            "data": prefill_optional_fields(
                vflz_types.UpdateVflzDataInput,
                {
                    "vflzId": str(vflz.vflz_id),
                    "gemeinde": {"hGemId": str(gemeinde2.h_gem_id)},
                },
            )
        },
    )
    assert result.data["updateVflzData"]["gemeinde"]["hGemId"] == str(
        gemeinde2.h_gem_id
    )


def test_update_pool_with_new_bezeichnung_and_bemerkungen(session, run_query):
    pool = make_pool(session)
    mutation = """
    mutation m($data: UpdatePoolInfoInput!) {
        updatePoolInfo(data: $data) {
            ... on Pool {
                bemerkungen
                bezeichnung
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "poolId": str(pool.pool_id),
                "bemerkungen": "foo",
                "bezeichnung": "new bezeichnung",
            }
        },
    )

    assert result.data["updatePoolInfo"] == {
        "bemerkungen": "foo",
        "bezeichnung": "new bezeichnung",
    }


def test_update_pool_with_bezeichnung_that_already_exists_throws_error(
    session, run_query
):
    unique_bezeichnung = "i am unique"
    make_pool(session, unique_bezeichnung)
    pool2 = make_pool(session)

    mutation = """
    mutation m($data: UpdatePoolInfoInput!) {
        updatePoolInfo(data: $data) {
            ... on ProblemGroup {
                problems {
                    field
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "poolId": str(pool2.pool_id),
                "bezeichnung": unique_bezeichnung,
                "bemerkungen": "bar",
            }
        },
    )
    assert result.data["updatePoolInfo"]["problems"] == [{"field": "bezeichnung"}]


def test_update_pool_with_bezeichnung_that_already_exists_throws_no_error_for_ego_pool(
    session, run_query
):
    pool = make_pool(session, "foo")

    mutation = """
    mutation m($data: UpdatePoolInfoInput!) {
        updatePoolInfo(data: $data) {
            ... on Pool {
                poolId
                bezeichnung
                bemerkungen
            }
            ... on ProblemGroup {
                problems {
                    field
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "poolId": str(pool.pool_id),
                "bezeichnung": "foo",
                "bemerkungen": "bar",
            }
        },
    )
    assert result.data["updatePoolInfo"] == {
        "poolId": str(pool.pool_id),
        "bezeichnung": "foo",
        "bemerkungen": "bar",
    }


def test_add_new_vfl_to_pool(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz2 = make_vflz(session, "My Site2", 2)
    pool = make_pool(session)
    make_vfl_pool(session, vflz.vfl_id, pool)

    mutation = """
    mutation m($poolId: ID!, $vflId: ID!) {
        addToPool(poolId: $poolId, vflId: $vflId) {
            standorte {
                numPages
                numResultsTotal
                results {
                    vflzId
                }
            }
        }
    }
    """

    result = run_query(
        mutation, {"poolId": str(pool.pool_id), "vflId": str(vflz2.vfl_id)}
    )
    assert result.data["addToPool"]["standorte"] == {
        "numPages": 1,
        "numResultsTotal": 2,
        "results": [
            {"vflzId": str(vflz.vflz_id)},
            {"vflzId": str(vflz2.vflz_id)},
        ],
    }


def test_remove_vfl_from_pool(session, run_query):
    vflz = make_vflz(session, "My Site")
    vflz2 = make_vflz(session, "My Site2", 2)
    pool = make_pool(session)
    make_vfl_pool(session, vflz.vfl_id, pool)
    make_vfl_pool(session, vflz2.vfl_id, pool)

    mutation = """
    mutation m($poolId: ID!, $vflId: ID!) {
        removeFromPool(poolId: $poolId, vflId: $vflId) {
            standorte {
                numPages
                numResultsTotal
                results {
                    vflzId
                }
            }
        }
    }
    """

    result = run_query(
        mutation, {"poolId": str(pool.pool_id), "vflId": str(vflz2.vfl_id)}
    )
    assert result.data["removeFromPool"]["standorte"] == {
        "numPages": 1,
        "numResultsTotal": 1,
        "results": [{"vflzId": str(vflz.vflz_id)}],
    }


def test_copy_pool(session, run_query):
    vflz = make_vflz(session, "My One Site")
    vflz2 = make_vflz(session, "My Other Site", 2)
    pool = make_pool(session)
    make_vfl_pool(session, vflz.vfl_id, pool)
    make_vfl_pool(session, vflz2.vfl_id, pool)

    mutation = """
    mutation m($bezeichnung: String!, $poolId: ID!) {
        copyPool(poolId: $poolId, bezeichnung: $bezeichnung) {
            poolId
            standorte {
                numPages
                numResultsTotal
                results {
                    vflzId
                }
            }
            bezeichnung
        }
    }
    """

    result = run_query(
        mutation, {"poolId": str(pool.pool_id), "bezeichnung": "neue Bezeichnung"}
    )
    assert result.data["copyPool"]["poolId"] != str(pool.pool_id)
    assert result.data["copyPool"]["bezeichnung"] == "neue Bezeichnung"
    assert result.data["copyPool"]["standorte"] == {
        "numPages": 1,
        "numResultsTotal": 2,
        "results": [
            {"vflzId": str(vflz.vflz_id)},
            {"vflzId": str(vflz2.vflz_id)},
        ],
    }
    assert len(pool.vfl_pools) == 2


def test_delete_pool(session, run_query):
    vflz = make_vflz(session, "My Site")
    pool = make_pool(session)
    make_vfl_pool(session, vflz.vfl_id, pool)

    mutation = """
    mutation m($poolId: ID!) {
        deletePool(poolId: $poolId)
    }
    """

    result = run_query(mutation, {"poolId": str(pool.pool_id)})
    assert result.data["deletePool"] == str(pool.pool_id)
    assert not session.execute(
        select(Pool).where(Pool.pool_id == pool.pool_id)
    ).scalar_one_or_none()
    assert not session.execute(
        select(VflPool).where(VflPool.pool_id == pool.pool_id)
    ).scalar_one_or_none()


def test_create_pool_with_valid_data(session, run_query):
    mutation = """
    mutation m($data: CreatePoolInput!) {
        createPool(data: $data) {
            ... on Pool {
                poolId
                bezeichnung
                bemerkungen
            }
        }
    }
    """

    result = run_query(
        mutation, {"data": {"bezeichnung": "new bezeichnung", "bemerkungen": "bla"}}
    )
    db_pool = session.get_one(Pool, int(result.data["createPool"]["poolId"]))
    assert (
        db_pool.bezeichnung
        == result.data["createPool"]["bezeichnung"]
        == "new bezeichnung"
    )
    assert db_pool.bemerkungen == result.data["createPool"]["bemerkungen"] == "bla"


def test_create_pool_with_existing_bezeichnung_raises(session, run_query):
    make_pool(session, "exists")
    mutation = """
    mutation m($data: CreatePoolInput!) {
        createPool(data: $data) {
            ... on Pool {
                poolId
            }
            ... on ProblemGroup {
                problems {
                    field
                }
            }
        }
    }
    """

    result = run_query(
        mutation, {"data": {"bezeichnung": "exists", "bemerkungen": "bla"}}
    )
    assert result.data["createPool"]["problems"] == [{"field": "bezeichnung"}]


def test_update_vflz_beurteilung(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_vflz_beurteilung(session, vflz)
    mass = make_massnahme(session, vflz)
    sani = make_sanierungsziel(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                beurteilung {
                    beurteilung
                    prioUntersuch
                    prioSanier
                }
                massnahmen {
                    massnahme
                    bemerkung { bem }
                }
                sanierungsziele {
                    sanierungsziel
                    bemerkung { bem }
                }
                datRechtskraft
                datPublizieren
                rechtskraft
                publizieren
                begruendungBewertung {
                    bem
                }
                begruendungPrioUntersuchungsbedarf {
                    bem
                }
                begruendungPrioSanierungsbedarf {
                    bem
                }
                bearbeitungsStand
                untersuchungsStand
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": prefill_optional_fields(
                    vflz_types.BeurteilungInput,
                    {
                        "beurteilung": "code:103:test2",
                        "prioUntersuch": "code:26020:2024",
                        "prioSanier": "code:26021:2024",
                    },
                ),
                "massnahmen": [
                    {
                        "massId": str(mass.mass_id),
                        "massnahme": "code:10021:test2",
                        "datMassnahme": None,
                        "angMassnahme": None,
                        "bemerkung": {"bem": "Bemerkung Massnahme"},
                    }
                ],
                "sanierungsziele": [
                    {
                        "saniId": str(sani.sani_id),
                        "sanierungsziel": "code:10020:test2",
                        "bemerkung": {"bem": "Bemerkung Sanierungsziel"},
                    }
                ],
                "datRechtskraft": None,
                "datPublizieren": None,
                "rechtskraft": False,
                "publizieren": False,
                "begruendungBewertung": {"bem": "foo"},
                "begruendungPrioUntersuchungsbedarf": {"bem": "bar"},
                "begruendungPrioSanierungsbedarf": {"bem": "bazz"},
                "bearbeitungsStand": "code:55:test2",
                "untersuchungsStand": "code:10023:test2",
            },
        ),
    }
    assert len(list(session.scalars(select(Beurteilung)).all())) == 1
    assert len(list(session.scalars(select(Sanierungsziel)).all())) == 1
    assert len(list(session.scalars(select(Massnahme)).all())) == 1

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"] == {
        "beurteilung": {
            "beurteilung": "code:103:test2",
            "prioUntersuch": "code:26020:2024",
            "prioSanier": "code:26021:2024",
        },
        "sanierungsziele": [
            {
                "sanierungsziel": "code:10020:test2",
                "bemerkung": {"bem": "Bemerkung Sanierungsziel"},
            },
        ],
        "massnahmen": [
            {
                "massnahme": "code:10021:test2",
                "bemerkung": {"bem": "Bemerkung Massnahme"},
            }
        ],
        "datRechtskraft": None,
        "datPublizieren": None,
        "rechtskraft": False,
        "publizieren": False,
        "begruendungBewertung": {"bem": "foo"},
        "begruendungPrioUntersuchungsbedarf": {"bem": "bar"},
        "begruendungPrioSanierungsbedarf": {"bem": "bazz"},
        "bearbeitungsStand": "code:55:test2",
        "untersuchungsStand": "code:10023:test2",
    }

    # The beurteilung change triggers a historization. Therefore, we have 2 objects.
    assert len(list(session.scalars(select(Beurteilung)).all())) == 2
    assert len(list(session.scalars(select(Sanierungsziel)).all())) == 2
    assert len(list(session.scalars(select(Massnahme)).all())) == 2


def test_create_vflz_beurteilung(session, run_query):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                beurteilung {
                    beurteilung
                    prioUntersuch
                    prioSanier
                }
                massnahmen {
                    massnahme
                }
                sanierungsziele {
                    sanierungsziel
                }
            }
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": {
                    "beurteilung": "code:103:test2",
                    "prioUntersuch": "code:26020:2024",
                    "prioSanier": "code:26021:2024",
                },
                "massnahmen": [
                    {
                        "massId": None,
                        "massnahme": "code:10021:test2",
                        "datMassnahme": None,
                        "angMassnahme": None,
                        "bemerkung": None,
                    }
                ],
                "sanierungsziele": [
                    {
                        "saniId": None,
                        "sanierungsziel": "code:10020:test2",
                        "bemerkung": None,
                    }
                ],
                "rechtskraft": False,
                "publizieren": False,
            },
        )
    }

    assert not list(session.scalars(select(Beurteilung)).all())
    assert not list(session.scalars(select(Massnahme)).all())
    assert not list(session.scalars(select(Sanierungsziel)).all())

    result = run_query(mutation, variables)
    assert result.data["updateVflzEvaluation"] == {
        "beurteilung": {
            "beurteilung": "code:103:test2",
            "prioUntersuch": "code:26020:2024",
            "prioSanier": "code:26021:2024",
        },
        "sanierungsziele": [
            {"sanierungsziel": "code:10020:test2"},
        ],
        "massnahmen": [{"massnahme": "code:10021:test2"}],
    }

    assert len(list(session.scalars(select(Beurteilung)).all())) == 1
    assert len(list(session.scalars(select(Massnahme)).all())) == 1
    assert len(list(session.scalars(select(Sanierungsziel)).all())) == 1


def test_delete_vflz_beurteilung(session, run_query):
    vflz = make_vflz(session, "My Site")
    make_vflz_beurteilung(session, vflz)
    make_massnahme(session, vflz)
    make_sanierungsziel(session, vflz)

    mutation = """
    mutation m($data: UpdateVflzEvaluationInput!) {
        updateVflzEvaluation(data: $data) {
            ... on Vflz {
                beurteilung {
                    beurteilung
                    prioUntersuch
                    prioSanier
                }
            }
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzEvaluationInput,
            {
                "vflzId": str(vflz.vflz_id),
                "beurteilung": None,
                "publizieren": False,
                "rechtskraft": False,
            },
        )
    }
    assert len(list(session.scalars(select(Beurteilung)).all())) == 1
    assert len(list(session.scalars(select(Sanierungsziel)).all())) == 1
    assert len(list(session.scalars(select(Massnahme)).all())) == 1

    result = run_query(mutation, variables)
    assert not result.data["updateVflzEvaluation"]["beurteilung"]

    assert len(list(session.scalars(select(Beurteilung)).all())) == 1
    assert len(list(session.scalars(select(Massnahme)).all())) == 1
    assert len(list(session.scalars(select(Sanierungsziel)).all())) == 1


def test_update_vflz_with_empty_fields_returns_error(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) { ... on Vflz { vflzId } }
    }
    """

    with assert_raises(
        Exception, match="All fields of object are empty: UpdateVflzDataInput"
    ):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(vflz_types.UpdateVflzDataInput),
                }
            },
        )


def test_update_ablagerung_with_empty_fields_returns_error(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) { ... on Vflz { vflzId } }
    }
    """

    with assert_raises(
        Exception, match="All fields of object are empty: AblagerungInput"
    ):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(
                        vflz_types.UpdateVflzDataInput,
                        {
                            "ablagerungen": [
                                prefill_optional_fields(vflz_types.AblagerungInput)
                            ]
                        },
                    ),
                }
            },
        )


def test_update_betrieb_with_empty_fields_returns_error(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) { ... on Vflz { vflzId } }
    }
    """

    with assert_raises(Exception, match="All fields of object are empty: BetriebInput"):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(
                        vflz_types.UpdateVflzDataInput,
                        {
                            "betriebe": [
                                prefill_optional_fields(vflz_types.BetriebInput)
                            ]
                        },
                    ),
                }
            },
        )


def test_update_schiessanlagen_with_empty_fields_returns_error(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) { ... on Vflz { vflzId } }
    }
    """

    with assert_raises(
        Exception, match="All fields of object are empty: SchiessanlageInput"
    ):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(
                        vflz_types.UpdateVflzDataInput,
                        {
                            "schiessanlagen": [
                                prefill_optional_fields(vflz_types.SchiessanlageInput)
                            ]
                        },
                    ),
                }
            },
        )


def test_update_unfaelle_with_empty_fields_returns_error(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) { ... on Vflz { vflzId } }
    }
    """
    with assert_raises(Exception, match="All fields of object are empty: UnfallInput"):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(
                        vflz_types.UpdateVflzDataInput,
                        {"unfaelle": [prefill_optional_fields(vflz_types.UnfallInput)]},
                    ),
                }
            },
        )


def test_returns_problem_if_vflz_fields_updated_with_empty_ablagerung(
    session, run_query
):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                }
            }
        }
    }
    """

    with assert_raises(
        Exception, match="All fields of object are empty: AblagerungInput"
    ):
        run_query(
            query=mutation,
            variable_values={
                "data": {
                    "vflzId": str(vflz.vflz_id),
                    **prefill_optional_fields(
                        vflz_types.UpdateVflzDataInput,
                        {
                            "ablagerungen": [
                                prefill_optional_fields(vflz_types.AblagerungInput)
                            ],
                            "bezeichnung": "bla",
                        },
                    ),
                }
            },
        )


@pytest.mark.parametrize(
    "input_data, gemeinde, combined_id_created",
    [
        (
            {
                "combinedId": None,
                "gemeinde": None,
                "vftyp": None,
                "flugplatz": None,
                "ktu": None,
            },
            [{"hGemId": "6002"}, {"hGemId": "6003"}],
            False,
        ),
        (
            {
                "combinedId": None,
                "gemeinde": {"hGemId": "6002"},
                "vftyp": "code:63:01",
                "flugplatz": None,
                "ktu": None,
            },
            [{"hGemId": "6002"}],
            True,
        ),
        (
            {
                "combinedId": None,
                "gemeinde": {"hGemId": "6005"},
                "vftyp": "code:63:01",
                "flugplatz": None,
                "ktu": None,
            },
            [{"hGemId": "6002"}, {"hGemId": "6003"}],
            False,
        ),
        (
            {
                "combinedId": None,
                "gemeinde": {"hGemId": "6002"},
                "vftyp": None,
                "flugplatz": None,
                "ktu": None,
            },
            [{"hGemId": "6002"}],
            False,
        ),
    ],
)
def test_create_validation(
    session, run_query, input_data, gemeinde, combined_id_created
):
    flugplatz_ewkt = "SRID=2056;MULTIPOLYGON(((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765)))"

    gem = make_gemeinde(session, name="Brig-Glis", bfs_nummer=6002)
    gem.wkb_geometry = "SRID=2056;POLYGON((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765))"  # type: ignore[assignment]
    gem2 = make_gemeinde(session, name="Basel", bfs_nummer=6003)
    gem2.wkb_geometry = "SRID=2056;POLYGON((2638170 1127765,2638170 1127785,2638190 1127785,2638190 1127765,2638170 1127765))"  # type: ignore[assignment]

    flugplatz = make_flugplatz(session)
    flugplatz.wkb_geometry = flugplatz_ewkt  # type: ignore[assignment]

    session.commit()

    query = """
    query q($data: ValidateCreateVflzInput!) {
        validateCreateVflz(data: $data) {
            ... on ValidatedCreateVflzData {
                combinedId
                gemeinde {
                    hGemId
                }
                flugplatz
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [2638160, 1127765],
                        [2638160, 1127785],
                        [2638180, 1127785],
                        [2638180, 1127765],
                        [2638160, 1127765],
                    ]
                ],
            },
            **input_data,
        }
    }

    result = run_query(query=query, variable_values=variables)

    assert result.data["validateCreateVflz"]["gemeinde"] == gemeinde
    assert (
        result.data["validateCreateVflz"]["combinedId"] != []
    ) == combined_id_created
    assert result.data["validateCreateVflz"]["flugplatz"] == ["code:600:Test"]


def test_create_validation_ktu(session, run_query, test_settings):
    settings.combined_id_factory = CombinedIdFactoryName.ABUB_KTU

    ktu_bls = make_ktu(session)
    ktu_bls.rangefrom = 100
    ktu_bls.rangeto = 101
    gem = make_gemeinde(session, name="Brig-Glis", bfs_nummer=6002)
    gem.wkb_geometry = "SRID=2056;POLYGON((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765))"  # type: ignore[assignment]
    session.commit()
    query = """
    query q($data: ValidateCreateVflzInput!) {
        validateCreateVflz(data: $data) {
            ... on ValidatedCreateVflzData {
                combinedId
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [2638160, 1127765],
                        [2638160, 1127785],
                        [2638180, 1127785],
                        [2638180, 1127765],
                        [2638160, 1127765],
                    ]
                ],
            },
            "combinedId": None,
            "gemeinde": {"hGemId": "6002"},
            "vftyp": "code:63:01",
            "ktu": str(ktu_bls.ktu),
            "flugplatz": None,
        }
    }

    result = run_query(query=query, variable_values=variables)
    assert result.data["validateCreateVflz"]["combinedId"] == ["A100"]

    settings.combined_id_factory = CombinedIdFactoryName.BFS_DBUS_LFD_WHITESPACES


def test_create_vflz_validation_returns_new_number_if_combinedId_exists(
    session, run_query
):
    make_vflz(session, bezeichnung="My Site", combined_id="THIS IS ALREADY TAKEN")
    gem = make_gemeinde(session, name="Brig-Glis", bfs_nummer=6002)
    gem.wkb_geometry = "SRID=2056;POLYGON((2638150 1127765,2638150 1127785,2638170 1127785,2638170 1127765,2638150 1127765))"  # type: ignore[assignment]
    session.commit()
    query = """
    query q($data: ValidateCreateVflzInput!) {
        validateCreateVflz(data: $data) {
            ... on ValidatedCreateVflzData {
                combinedId
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": {
                "type": "Point",
                "coordinates": [2638150, 1127765],
            },
            "combinedId": "THIS IS ALREADY TAKEN",
            "gemeinde": {"hGemId": "6002"},
            "vftyp": "code:63:01",
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=query, variable_values=variables)
    assert result.data["validateCreateVflz"]["combinedId"] == ["6002 D 01"]


@freeze_time("2020-01-01")
def test_create_vflz_with_valid_data(session, run_query):
    make_vflz(session, "My Site", vfl_id=50)
    make_gemeinde(session, name="Brig-Glis", bfs_nummer=30)
    make_flugplatz(session)

    make_ktu(session)
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on Vflz {
                vflId
                gemeinde {
                    hGemId
                }
                combinedId
                bezeichnung
                zentroid
                vflgeo {
                    geometry
                }
                vflzCreatedDate
                flugplatz
                ktu
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2638160, 1127765],
                            [2638160, 1127775],
                            [2638170, 1127775],
                            [2638170, 1127765],
                            [2638160, 1127765],
                        ]
                    ]
                ],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "FOO001",
            "bezeichnung": "Foo",
            "zentroid": None,
            "flugplatz": "code:600:Test",
            "ktu": "code:210:bls",
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    assert result.data["createVflz"] == {
        "vflId": "51",
        "gemeinde": {"hGemId": "30"},
        "combinedId": "FOO001",
        "bezeichnung": "Foo",
        "vflgeo": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2638160, 1127765],
                            [2638160, 1127775],
                            [2638170, 1127775],
                            [2638170, 1127765],
                            [2638160, 1127765],
                        ]
                    ]
                ],
                "crs": {"properties": {"name": "EPSG:2056"}, "type": "name"},
            },
        },
        "zentroid": {
            "type": "Point",
            "coordinates": [2638165, 1127770, 0],
            "crs": {"properties": {"name": "EPSG:2056"}, "type": "name"},
        },
        "vflzCreatedDate": datetime.now().isoformat(),
        "flugplatz": "code:600:Test",
        "ktu": "code:210:bls",
    }


def test_create_vflz_updates_wfs(session, run_query, wfs_test_settings):
    make_vflz(session, "My Site", vfl_id=50)
    make_gemeinde(session, name="Brig-Glis", bfs_nummer=30)
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on Vflz {
                vflzId
                vflId
                gemeinde {
                    hGemId
                }
                combinedId
                bezeichnung
                zentroid
                vflgeo {
                    geometry
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2638160, 1127765],
                            [2638160, 1127775],
                            [2638170, 1127775],
                            [2638170, 1127765],
                            [2638160, 1127765],
                        ]
                    ]
                ],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "FOO001",
            "bezeichnung": "Foo",
            "zentroid": None,
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    vflz_id = result.data["createVflz"].pop("vflzId")
    assert result.data["createVflz"] == {
        "vflId": "51",
        "gemeinde": {"hGemId": "30"},
        "combinedId": "FOO001",
        "bezeichnung": "Foo",
        "vflgeo": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2638160, 1127765],
                            [2638160, 1127775],
                            [2638170, 1127775],
                            [2638170, 1127765],
                            [2638160, 1127765],
                        ]
                    ]
                ],
                "crs": {"properties": {"name": "EPSG:2056"}, "type": "name"},
            },
        },
        "zentroid": {
            "type": "Point",
            "coordinates": [2638165, 1127770, 0],
            "crs": {"properties": {"name": "EPSG:2056"}, "type": "name"},
        },
    }

    assert session.get(WfsUpdate, int(vflz_id))


def test_create_vflz_with_existing_combinedId_raises(session, run_query):
    make_vflz(session, bezeichnung="My Site", combined_id="THIS IS ALREADY TAKEN")
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "Point",
                "coordinates": [2638160, 1127765],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "THIS IS ALREADY TAKEN",
            "bezeichnung": "Foo",
            "zentroid": None,
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    assert result.data["createVflz"]["problems"] == [
        {"problemCode": "EXISTS", "field": "combinedId"}
    ]


def test_create_vflz_with_existing_combinedId_with_whitespaces_raises(
    session, run_query
):
    make_vflz(session, bezeichnung="My Site", combined_id="THIS IS ALREADY TAKEN")
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "Point",
                "coordinates": [2638160, 1127765],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "THIS IS ALREADY TAKEN ",
            "bezeichnung": "Foo",
            "zentroid": None,
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    assert result.data["createVflz"]["problems"] == [
        {"problemCode": "EXISTS", "field": "combinedId"}
    ]


def test_cannot_create_vflz_with_invalid_geometry(session, run_query):
    make_gemeinde(session, name="Brig-Glis", bfs_nummer=30)
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on ProblemGroup {
                problems {
                    problemCode
                    field
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[0, 0], [1, 1], [1, 2], [1, 1], [0, 0]]]],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "foo-123",
            "bezeichnung": "foo",
            "zentroid": None,
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    assert result.data["createVflz"]["problems"] == [
        {"problemCode": "VALIDATION_GEOM", "field": "geometry"}
    ]


def test_create_vflz_creates_vollzug(session, run_query):
    make_vflz(session, "My Site", vfl_id=50)
    make_gemeinde(session, name="Brig-Glis", bfs_nummer=30)
    mutation = """
    mutation m($data: CreateVflzInput!) {
        createVflz(data: $data) {
            ... on Vflz {
                vollzug {
                    aktiv
                    combinedId
                    behoerde
                }
                combinedId
            }
        }
    }
    """

    variables = {
        "data": {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2638160, 1127765],
                            [2638160, 1127775],
                            [2638170, 1127775],
                            [2638170, 1127765],
                            [2638160, 1127765],
                        ]
                    ]
                ],
            },
            "vftyp": "code:63:01",
            "gemeinde": {
                "hGemId": "30",
            },
            "combinedId": "FOO001",
            "bezeichnung": "Foo",
            "zentroid": None,
            "flugplatz": None,
            "ktu": None,
        }
    }

    result = run_query(query=mutation, variable_values=variables)
    assert result.data["createVflz"] == {
        "combinedId": "FOO001",
        "vollzug": [
            {"aktiv": True, "combinedId": "FOO001", "behoerde": "code:26030:geOps"}
        ],
    }


@freeze_time("2012-01-14 12:00:01")
def test_allow_flugplatz_override_in_validated_data(
    session, run_query, wfs_test_settings
):
    settings.combined_id_factory = CombinedIdFactoryName.FLUGPLATZ_DIUS_LFD_UNDERSCORE
    extent_geojson = {
        "type": "Point",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [2650000, 1300000],
    }
    flugplatz_geom_ewkt = "SRID=2056;MULTIPOLYGON(((2600000 1200000, 2640000 1200000, 2640000 1120000, 2600000 1120000, 2600000 1200000)))"

    vflz = make_vflz(session, "My Site")
    vflz.vflgeo = VflGeo()
    vflz.vflgeo.set_geometry(extent_geojson)  # outside of flugplatz
    session.commit()

    make_flugplatz(session, "Test", flugplatz_geom_ewkt)

    query = """
    query q($data: ValidateCreateVflzInput!) {
        validateCreateVflz(data: $data) {
            ... on ValidatedCreateVflzData {
                flugplatz
                combinedId
            }
        }
    }
    """
    variables = {
        "data": {
            "geometry": extent_geojson,
            "vftyp": "code:63:01",
            "gemeinde": None,
            "combinedId": None,
            "flugplatz": None,
            "ktu": None,
        }
    }
    result = run_query(query, variables)
    assert not result.data["validateCreateVflz"]["flugplatz"]
    assert not result.data["validateCreateVflz"]["combinedId"]

    variables["data"]["flugplatz"] = "code:600:Test"

    result = run_query(query, variables)
    assert result.data["validateCreateVflz"]["flugplatz"] == ["code:600:Test"]
    assert result.data["validateCreateVflz"]["combinedId"] != []


def test_update_vflz_with_beteiligte_creates_new_one(
    session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)
    user = User(sub="sub", username="username", email="user@geops.com")
    session.add(user)
    subj.user = user

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                sachbearbeitung {
                    beteiligter {
                        isSachbearbeiter
                        subjekt {
                            user {
                                username
                            }
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "vflzId": str(vflz.vflz_id),
            "sachbearbeitung": [
                {
                    "betArtId": None,
                    "subjId": str(subj.subj_id),
                }
            ],
            "sonstigeBeteiligte": [],
            "eigentum": [],
        }
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzBeteiligte"]["sachbearbeitung"] == [
        {
            "beteiligter": {
                "isSachbearbeiter": True,
                "subjekt": {"user": {"username": "username"}},
            }
        }
    ]


def test_update_vflz_with_beteiligte_delete_unassigned_and_create_new_one(
    session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)
    user = User(sub="sub", username="username", email="user@geops.com")
    session.add(user)
    subj.user = user

    subj2 = make_subj(session)
    user2 = User(sub="sub2", username="username2", email="user2@geops.com")
    subj2.user = user2
    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id, False, True)
    bet_art = make_sonstiger_beteiligte_standort(session, bet.bet_id, "test")

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                sachbearbeitung {
                    beteiligter {
                        isSachbearbeiter
                        subjekt {
                            user {
                                username
                            }
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "vflzId": str(vflz.vflz_id),
            "sachbearbeitung": [
                {
                    "betArtId": None,
                    "subjId": str(subj2.subj_id),
                },
            ],
            "sonstigeBeteiligte": [],
            "eigentum": [],
        }
    }

    assert session.get(Beteiligter, bet.bet_id)
    assert session.get(BeteiligterStandort, bet_art.bet_art_id)

    result = run_query(mutation, variables)
    assert result.data["updateVflzBeteiligte"]["sachbearbeitung"] == [
        {
            "beteiligter": {
                "isSachbearbeiter": True,
                "subjekt": {"user": {"username": "username2"}},
            }
        }
    ]
    assert not session.get(Beteiligter, bet.bet_id)
    assert not session.get(BeteiligterStandort, bet_art.bet_art_id)


def test_update_vflz_with_beteiligte_keep_assigned_and_create_new_one(
    session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session)
    user = User(sub="sub", username="username", email="user@geops.com")
    session.add(user)
    subj.user = user

    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id, False, True)
    bet_art = make_sonstiger_beteiligte_standort(session, bet.bet_id, "test")
    code_sachbearbeitung = session.scalars(
        select(BeziehungsartSachbearbeitung).where(
            BeziehungsartSachbearbeitung.code == "sachbearbeitung"
        )
    ).one()
    bet_art.beziehungsart = code_sachbearbeitung

    subj2 = make_subj(session)
    user2 = User(sub="sub2", username="username2", email="user2@geops.com")
    subj2.user = user2

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                sachbearbeitung {
                    beteiligter {
                        isSachbearbeiter
                        subjekt {
                            user {
                                username
                            }
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "vflzId": str(vflz.vflz_id),
            "sachbearbeitung": [
                {
                    "betArtId": str(bet_art.bet_art_id),
                    "subjId": str(subj.subj_id),
                },
                {
                    "betArtId": None,
                    "subjId": str(subj2.subj_id),
                },
            ],
            "sonstigeBeteiligte": [],
            "eigentum": [],
        }
    }

    assert session.get(Beteiligter, bet.bet_id)
    assert session.get(BeteiligterStandort, bet_art.bet_art_id)

    result = run_query(mutation, variables)
    assert result.data["updateVflzBeteiligte"]["sachbearbeitung"] == [
        {
            "beteiligter": {
                "isSachbearbeiter": True,
                "subjekt": {"user": {"username": "username"}},
            }
        },
        {
            "beteiligter": {
                "isSachbearbeiter": True,
                "subjekt": {"user": {"username": "username2"}},
            }
        },
    ]
    assert session.get(Beteiligter, bet.bet_id)
    assert session.get(BeteiligterStandort, bet_art.bet_art_id)


def test_update_vflz_with_beteiligte_update_beziehungsart(
    session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session, name="Test")

    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id, False, True)
    bet_art = make_sonstiger_beteiligte_standort(session, bet.bet_id, "test")

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                sonstigeBeteiligte {
                    beteiligter {
                        subjekt {
                            name
                        }
                    }
                    beziehungsart
                }
            }
        }
    }
    """

    variables = {
        "data": {
            "vflzId": str(vflz.vflz_id),
            "sachbearbeitung": [],
            "sonstigeBeteiligte": [
                {
                    "betArtId": str(bet_art.bet_art_id),
                    "subjId": str(subj.subj_id),
                    "beziehungsart": f"code:{constants.CodeListe.BeziehungsartSonstige}:test2",
                },
            ],
            "eigentum": [],
        }
    }
    result = run_query(mutation, variables)
    assert result.data["updateVflzBeteiligte"]["sonstigeBeteiligte"] == [
        {
            "beteiligter": {
                "subjekt": {"name": "Test"},
            },
            "beziehungsart": f"code:{constants.CodeListe.BeziehungsartSonstige}:test2",
        },
    ]
    assert session.get(Beteiligter, bet.bet_id)
    assert session.get(BeteiligterStandort, bet_art.bet_art_id)


def test_update_vflz_with_beteiligte_update_subjekt(
    session: Session, run_query, as_bearbeiten_sachdaten
):
    vflz = make_vflz(session, "My Site")
    subj = make_subj(session, name="Test")
    user = User(sub="sub", username="username", email="user@geops.com")
    session.add(user)
    subj.user = user

    subj2 = make_subj(session, name="Test 2")
    user2 = User(sub="sub2", username="username2", email="user2@geops.com")
    session.add(user2)
    subj2.user = user2

    bet = make_beteiligter(session, vflz.vflz_id, subj.subj_id, False, True)
    bet_art = make_sonstiger_beteiligte_standort(session, bet.bet_id, "test")

    bet_art2 = make_sonstiger_beteiligte_standort(session, bet.bet_id, "test")
    code_sachbearbeitung = session.scalars(
        select(BeziehungsartSachbearbeitung).where(
            BeziehungsartSachbearbeitung.code == "sachbearbeitung"
        )
    ).one()
    bet_art2.beziehungsart = code_sachbearbeitung

    mutation = """
    mutation m($data: UpdateVflzBeteiligteInput!) {
        updateVflzBeteiligte(data: $data) {
            ... on Vflz {
                sachbearbeitung { beteiligter { subjekt { name } isSachbearbeiter } }
                sonstigeBeteiligte { beteiligter { subjekt { name } isSachbearbeiter } }
            }
        }
    }
    """

    variables = {
        "data": {
            "vflzId": str(vflz.vflz_id),
            "sachbearbeitung": [
                {
                    "betArtId": str(bet_art2.bet_art_id),
                    "subjId": str(subj2.subj_id),
                }
            ],
            "sonstigeBeteiligte": [
                {
                    "betArtId": str(bet_art.bet_art_id),
                    "subjId": str(subj2.subj_id),
                    "beziehungsart": str(bet_art.beziehungsart),
                },
            ],
            "eigentum": [],
        }
    }
    result = run_query(mutation, variables)
    assert result.data["updateVflzBeteiligte"] == {
        "sachbearbeitung": [
            {
                "beteiligter": {
                    "subjekt": {"name": "Test 2"},
                    "isSachbearbeiter": True,
                }
            },
        ],
        "sonstigeBeteiligte": [
            {
                "beteiligter": {
                    "subjekt": {"name": "Test 2"},
                    "isSachbearbeiter": True,
                }
            },
        ],
    }
    assert session.get(Beteiligter, bet.bet_id)
    assert session.get(BeteiligterStandort, bet_art.bet_art_id)


def test_update_pfas_of_vflz(session, run_query):
    vflz = make_vflz(session, "My Site")
    pfas = make_pfas(session, vflz)
    # Optionally set all fields for PFAS here if make_pfas does not set them
    pfas.name = None
    pfas.strasse = None
    pfas.plz = None
    pfas.ort = None
    pfas.eva = None
    pfas.pfas_loeschmittel = True
    pfas.loeschschaum_einsatz = []
    pfas.menge_schaumgemisch = None
    pfas.menge_konzentrat = None
    pfas.beschreibungen_detail = None
    pfas.relevant = True
    session.commit()

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                pfas {
                    intpId
                    untersuchungsStand
                    beurteilung
                    branche
                    pfasTyp
                    pfasHaltigeLoeschmittel
                    pfasFreieLoeschmittel
                    loeschschaumEinsatz {
                        loeschschaumEinsatz
                        haeufigkeitNutzung
                    }
                    name
                    strasse
                    plz
                    ort
                    eva
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                        genauigkeitVon
                        genauigkeitBis
                    }
                    pfasLoeschmittel
                    relevant
                    mengeSchaumgemisch
                    mengeKonzentrat
                    beschreibungenDetail
                    zentroid
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": str(vflz.vflz_id),
                "pfas": [
                    {
                        "intpId": str(pfas.intp_id),
                        "untersuchungsStand": "code:10023:test",
                        "beurteilung": "code:103:test",
                        "branche": "code:25002:test",
                        "pfasTyp": "code:500:test",
                        "pfasHaltigeLoeschmittel": ["code:501:test"],
                        "pfasFreieLoeschmittel": ["code:502:test"],
                        "loeschschaumEinsatz": [
                            {
                                "intpLoeschschaumEinsatzId": None,
                                "loeschschaumEinsatz": "code:503:hand",
                                "haeufigkeitNutzung": "code:504:test",
                            }
                        ],
                        "name": "PFAS Standort",
                        "strasse": "PFAS-Strasse 1",
                        "plz": "12345",
                        "ort": "Bern",
                        "eva": "EVA-PFAS",
                        "zeitraum": {
                            "von": "2026-01-01",
                            "bis": "2027-02-02",
                            "vonjahr": False,
                            "bisjahr": False,
                            "bisheute": False,
                            "genauigkeitVon": "code:90:test",
                            "genauigkeitBis": "code:90:test",
                        },
                        "relevant": False,
                        "mengeSchaumgemisch": 100,
                        "mengeKonzentrat": 10,
                        "beschreibungenDetail": "Details zu PFAS",
                        "zentroid": {
                            "type": "Point",
                            "crs": {
                                "properties": {"name": "EPSG:2056"},
                                "type": "name",
                            },
                            "coordinates": [123, 321],
                        },
                        "bemerkung": {"bem": "bla"},
                        "bemerkungDatenimport": {"bem": "foo"},
                        "begruendungBewertung": {"bem": "bla"},
                        "pfasLoeschmittel": False,
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["pfas"] == [
        {
            "intpId": str(pfas.intp_id),
            "untersuchungsStand": "code:10023:test",
            "beurteilung": "code:103:test",
            "branche": "code:25002:test",
            "pfasTyp": "code:500:test",
            "pfasHaltigeLoeschmittel": ["code:501:test"],
            "pfasFreieLoeschmittel": ["code:502:test"],
            "loeschschaumEinsatz": [
                {
                    "loeschschaumEinsatz": "code:503:hand",
                    "haeufigkeitNutzung": "code:504:test",
                }
            ],
            "name": "PFAS Standort",
            "strasse": "PFAS-Strasse 1",
            "plz": "12345",
            "ort": "Bern",
            "eva": "EVA-PFAS",
            "zeitraum": {
                "von": "2026-01-01",
                "bis": "2027-02-02",
                "vonjahr": False,
                "bisjahr": False,
                "bisheute": False,
                "genauigkeitVon": "code:90:test",
                "genauigkeitBis": "code:90:test",
            },
            "pfasLoeschmittel": False,
            "relevant": False,
            "mengeSchaumgemisch": 100,
            "mengeKonzentrat": 10,
            "beschreibungenDetail": "Details zu PFAS",
            "zentroid": {
                "type": "Point",
                "crs": {
                    "properties": {"name": "EPSG:2056"},
                    "type": "name",
                },
                "coordinates": [123, 321],
            },
        }
    ]


def test_update_vflz_kinderspielplatz_gruenflaeche(session: Session, run_query):
    vflz = make_vflz(session, "My Site")
    intk = make_kinderspielplatz_gruenflaeche(session, vflz)
    intk.kinderspielplatz_gruenflache_typ = None
    intk.eigentumsform = None
    intk.beurteilung = None
    intk.untersuchungs_stand = None
    intk.genauigkeit_von = None
    intk.genauigkeit_bis = None
    intk.zeitraum_von = date(2016, 1, 1)
    intk.zeitraum_bis = date(2017, 2, 2)
    intk.zeitraum_vonjahr = True
    intk.zeitraum_bisjahr = True
    intk.zeitraum_bisheute = True
    intk.name = None
    intk.strasse = None
    intk.plz = None
    intk.ort = None
    intk.eva = None
    intk.relevant = True
    intk.belastung_ueber_sanierungswert = True
    intk.altersstufen_kinder = []
    intk.bemerkung = None
    intk.begruendung_bewertung = None
    intk.set_zentroid(
        {
            "type": "Point",
            "crs": {
                "properties": {"name": "EPSG:2056"},
                "type": "name",
            },
            "coordinates": [100, 200],
        }
    )

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                kinderspielplaetzeGruenflaechen {
                    intkId
                    kinderspielplatzGruenflacheTyp
                    eigentumsform
                    beurteilung
                    untersuchungsStand
                    name
                    strasse
                    plz
                    ort
                    eva
                    zeitraum {
                        von
                        bis
                        vonjahr
                        bisjahr
                        bisheute
                        genauigkeitVon
                        genauigkeitBis
                    }
                    relevant
                    belastungUeberSanierungswert
                    zentroid
                    altersstufenKinder
                    bemerkung { bem }
                    bemerkungDatenimport { bem }
                    begruendungBewertung { bem }
                }
            }
        }
    }
    """

    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {
                "vflzId": vflz.vflz_id,
                "kinderspielplaetzeGruenflaechen": [
                    {
                        "intkId": str(intk.intk_id),
                        "kinderspielplatzGruenflacheTyp": "code:400:Typ",
                        "eigentumsform": "code:401:Eigentumsform",
                        "beurteilung": "code:103:test",
                        "untersuchungsStand": "code:10023:test",
                        "name": "Foo Name",
                        "strasse": "Foo Strasse",
                        "plz": "1234",
                        "ort": "Foo Ort",
                        "eva": "Foo EVA",
                        "zeitraum": {
                            "von": "2026-01-01",
                            "bis": "2027-02-02",
                            "vonjahr": False,
                            "bisjahr": False,
                            "bisheute": False,
                            "genauigkeitVon": "code:90:test",
                            "genauigkeitBis": "code:90:test",
                        },
                        "relevant": False,
                        "belastungUeberSanierungswert": True,
                        "zentroid": {
                            "type": "Point",
                            "crs": {
                                "properties": {"name": "EPSG:2056"},
                                "type": "name",
                            },
                            "coordinates": [123, 321],
                        },
                        "altersstufenKinder": ["code:402:0-3"],
                        "bemerkung": {"bem": "bla"},
                        "bemerkungDatenimport": {"bem": "Datenimport"},
                        "begruendungBewertung": {"bem": "bla"},
                    }
                ],
            },
        )
    }

    result = run_query(mutation, variables)
    assert result.data["updateVflzData"]["kinderspielplaetzeGruenflaechen"] == [
        {
            "intkId": str(intk.intk_id),
            "kinderspielplatzGruenflacheTyp": "code:400:Typ",
            "eigentumsform": "code:401:Eigentumsform",
            "beurteilung": "code:103:test",
            "untersuchungsStand": "code:10023:test",
            "name": "Foo Name",
            "strasse": "Foo Strasse",
            "plz": "1234",
            "ort": "Foo Ort",
            "eva": "Foo EVA",
            "zeitraum": {
                "von": "2026-01-01",
                "bis": "2027-02-02",
                "vonjahr": False,
                "bisjahr": False,
                "bisheute": False,
                "genauigkeitVon": "code:90:test",
                "genauigkeitBis": "code:90:test",
            },
            "relevant": False,
            "belastungUeberSanierungswert": True,
            "zentroid": {
                "type": "Point",
                "crs": {
                    "properties": {"name": "EPSG:2056"},
                    "type": "name",
                },
                "coordinates": [123, 321],
            },
            "altersstufenKinder": ["code:402:0-3"],
            "bemerkung": {"bem": "bla"},
            "bemerkungDatenimport": {"bem": "Datenimport"},
            "begruendungBewertung": {"bem": "bla"},
        }
    ]
