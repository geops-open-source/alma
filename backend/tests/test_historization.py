from datetime import date, datetime, timedelta

import pytest
from pytest import raises as assert_raises
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils import (
    make_ablagerung,
    make_beteiligter,
    make_betrieb,
    make_eigentuemer_standort,
    make_kompartiment_stoffklasse,
    make_parzelle,
    make_sachbearbeiter_standort,
    make_schiessanlage,
    make_subj,
    make_unfall,
    make_vflz,
)

from alma.models import codes
from alma.models.snapshots import ImmutableInstanceError
from alma.models.vflz import Beurteilung, Vflz, is_read_only

# Fixture required by all tests in this module
pytestmark = pytest.mark.usefixtures("generate_codes")


def test_can_historize_vflz(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    original_vflz_id = vflz.vflz_id

    vflz.historize("My message")
    new_vflz_id = vflz.vflz_id

    session.commit()

    assert new_vflz_id > original_vflz_id

    versions = session.scalars(
        select(Vflz).where(Vflz.vfl_id == 1).order_by(Vflz.vflz_id.desc())
    ).all()
    assert len(versions) == 2

    assert versions[0] is vflz
    assert versions[0].is_current is True
    assert versions[0].message == "My message"
    assert versions[0].parent_id == original_vflz_id

    assert versions[1] is not vflz
    assert versions[1].vflz_id == original_vflz_id
    assert versions[1].is_current is False
    assert versions[1].message == "Initial version"
    assert versions[1].parent_id is None


def test_historization_resets_publication_status_of_vflz(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    vflz.publizieren = True
    vflz.dat_publizieren = date.today()

    vflz.historize("My message")
    session.commit()

    versions = session.scalars(
        select(Vflz).where(Vflz.vfl_id == 1).order_by(Vflz.vflz_id.desc())
    ).all()
    assert len(versions) == 2

    assert versions[0].is_current is True
    assert versions[0].publizieren is False
    assert versions[0].dat_publizieren is None

    assert versions[1].is_current is False
    assert versions[1].publizieren is True
    assert versions[1].dat_publizieren == date.today()


def test_historization_updates_created_date_of_vflz(session: Session):
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    vflz = make_vflz(session, "My site", vfl_id=1)
    vflz.vflz_created_date = yesterday

    vflz.historize("My message")
    session.commit()

    versions = session.scalars(
        select(Vflz).where(Vflz.vfl_id == 1).order_by(Vflz.vflz_id.desc())
    ).all()
    assert len(versions) == 2

    assert versions[0].is_current is True
    assert versions[0].vflz_created_date
    assert versions[0].vflz_created_date.date() == now.date()

    assert versions[1].is_current is False
    assert versions[1].vflz_created_date
    assert versions[1].vflz_created_date.date() == yesterday.date()


def test_is_current_property_is_immutable(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    assert vflz.is_current is True

    with assert_raises(AttributeError, match="Attribute Vflz.is_current is read-only"):
        vflz.is_current = False


def test_snapshots_are_immutable(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    vflz.bezeichnung = "Initial description"
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    with assert_raises(
        ImmutableInstanceError, match="Trying to modify immutable snapshot"
    ):
        snapshot.bezeichnung = "Updated description"
        session.flush()


def test_related_objects_are_historized(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    betrieb = make_betrieb(session, vflz)
    betrieb.firma_name = "Company name"
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    assert len(vflz.betriebe) == 1
    assert len(snapshot.betriebe) == 1
    assert vflz.betriebe[0] is betrieb
    assert vflz.betriebe[0].intb_id > snapshot.betriebe[0].intb_id
    assert snapshot.betriebe[0] is not betrieb
    assert snapshot.betriebe[0].firma_name == "Company name"


def test_snapshots_of_related_objects_are_immutable(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    betrieb = make_betrieb(session, vflz)
    betrieb.firma_name = "Company name"
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    with assert_raises(
        ImmutableInstanceError, match="Trying to modify immutable snapshot"
    ):
        snapshot.betriebe[0].firma_name = "Updated name"
        session.flush()


def test_related_objects_are_historized_schiessanlage(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    schiessanlage = make_schiessanlage(session, vflz)
    schiessanlage.firma_name = "Piff Paff GmbH"
    schiessanlage.scheibenzahl = 1
    schiessanlage.schusszahl = 999
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    assert len(vflz.schiessanlagen) == 1
    assert len(snapshot.schiessanlagen) == 1
    assert vflz.schiessanlagen[0] is schiessanlage
    assert vflz.schiessanlagen[0].firma_name == "Piff Paff GmbH"
    assert vflz.schiessanlagen[0].scheibenzahl == 1
    assert vflz.schiessanlagen[0].schusszahl == 999
    assert vflz.schiessanlagen[0].intb_id > snapshot.schiessanlagen[0].intb_id
    assert snapshot.schiessanlagen[0] is not schiessanlage
    assert snapshot.schiessanlagen[0].firma_name == "Piff Paff GmbH"
    assert snapshot.schiessanlagen[0].scheibenzahl == 1
    assert snapshot.schiessanlagen[0].schusszahl == 999


def test_nested_related_objects_are_historized_kksk(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    ablagerung = make_ablagerung(session, vflz)
    kksk = make_kompartiment_stoffklasse(session, ablagerung)
    kksk.teilvol = 0.111
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    assert snapshot.ablagerungen[0].kompartiment_stoffklassen[0] is not kksk
    assert snapshot.ablagerungen[0].kompartiment_stoffklassen[0].teilvol == 0.111
    assert not snapshot.ablagerungen[0].is_current
    assert not snapshot.ablagerungen[0].kompartiment_stoffklassen[0].is_current


def test_nested_related_objects_are_historized_unfall(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    unfall = make_unfall(session, vflz)
    unfall.name = "Unfall name"
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    assert snapshot.unfaelle[0] is not unfall
    assert snapshot.unfaelle[0].name == "Unfall name"
    assert not snapshot.unfaelle[0].is_current


def test_nested_related_objects_are_historized_beurteilung_with_kbsinfo(
    session: Session,
):
    """
    Beurteilung.color is a readonly one-to-one relation based on a query, and can not be historized.
    """
    vflz = make_vflz(session, "My site", vfl_id=1)
    code_beurteilung = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == "test")
    ).one()
    code_beurteilung_gruppe = session.scalars(
        select(codes.BeurteilungGruppe).where(codes.BeurteilungGruppe.code == "Test")
    ).one()
    kbs_info = codes.KbsInfo(
        beurteilung=code_beurteilung,
        beurteilung_gruppe=code_beurteilung_gruppe,
        color="#ff0000",
        color_rgb="255 0 0",
        belastet=True,
    )
    vflz.beurteilung = Beurteilung(beurteilung=code_beurteilung)
    session.add(kbs_info)
    session.commit()

    vflz.historize("My message")
    session.commit()

    assert vflz.beurteilung.kbs_info is kbs_info

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    assert snapshot.beurteilung
    assert snapshot.beurteilung is not vflz.beurteilung
    assert not snapshot.beurteilung.is_current
    assert snapshot.beurteilung.beurteilung is code_beurteilung
    assert snapshot.beurteilung.kbs_info is kbs_info


def test_beteiligte_are_historized_with_standort_relations(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    sachbearbeitung_subj = make_subj(session, name="Sach", vorname="Bearbeitung")
    eigentuemer_subj = make_subj(session, name="Eigentum", vorname="Person")
    parzelle = make_parzelle(session, "1000")

    sachbearbeitung = make_beteiligter(
        session,
        vflz.vflz_id,
        sachbearbeitung_subj.subj_id,
        is_sachbearbeiter=True,
    )
    eigentuemer = make_beteiligter(
        session,
        vflz.vflz_id,
        eigentuemer_subj.subj_id,
        is_eigentuemer=True,
    )

    make_sachbearbeiter_standort(
        session, bet_id=sachbearbeitung.bet_id, bez_art_code="sachbearbeitung"
    )

    make_eigentuemer_standort(
        session, eigentuemer.bet_id, parzelle.grun_id, "eigentuemer"
    )

    vflz.historize("My message")
    session.commit()

    snapshot = session.scalars(
        select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    ).one()

    assert all(not b.is_current for b in snapshot.beteiligte)
    assert all(b.is_current for b in vflz.beteiligte)
    assert len(snapshot.beteiligte) == 2
    assert len(vflz.beteiligte) == 2


def test_snapshot_cannot_be_historized(session: Session):
    vflz = make_vflz(session, "My site", vfl_id=1)
    vflz.historize("My message")
    session.commit()

    query = select(Vflz).where(Vflz.vfl_id == 1, ~Vflz.is_current)
    snapshot = session.scalars(query).one()

    with assert_raises(
        ImmutableInstanceError, match="Trying to modify immutable snapshot"
    ):
        snapshot.historize("Trying to historize snapshot")


def test_historized_vflz_is_read_only(session: Session):
    vflz = make_vflz(session, "My Site", vfl_id=1)
    old_vflz_id = vflz.vflz_id
    vflz.historize("My Message")
    session.commit()
    new_vflz_id = vflz.vflz_id

    old_vflz = session.get_one(Vflz, old_vflz_id)
    new_vflz = session.get_one(Vflz, new_vflz_id)

    assert not old_vflz.is_current
    assert new_vflz.is_current
    assert is_read_only(session, old_vflz)
    assert not is_read_only(session, new_vflz)
