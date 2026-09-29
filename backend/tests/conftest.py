import os
from pathlib import Path
from secrets import token_urlsafe

from business_workflow_manager.manager import WorkflowManager
from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from utils import QueryError

from alma import constants
from alma.db import get_engine, get_session
from alma.graphql.context import Context
from alma.graphql.schema import schema
from alma.models.auth import Role, RoleName, User
from alma.models.codes import Code, CodeListe
from alma.models.subj import Subjekt
from alma.models.translations import Translation
from alma.settings import settings
from alma.workflow_integration import add_event_handlers, wf_manager_config


@fixture
def client():
    from alma.api import app

    with TestClient(app) as client:
        yield client


@fixture(autouse=True, scope="session")
def test_settings():
    settings.database.url = settings.database.test_url
    settings.debug.enable_e2e_test_user = False
    settings.secret_key = token_urlsafe(32)
    settings.height_api = None
    settings.behoerde = "geOps"


@fixture
def wfs_test_settings(test_settings):
    test_dir = Path(__file__).parent.resolve()
    settings.wfs_config_path = os.path.join(test_dir, "wfs_cache", "wfs_config.yaml")
    settings.load_wfs_config()
    yield
    settings.wfs_config = {}
    settings.wfs_config_path = None


@fixture(scope="session")
def conn(test_settings):
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


@fixture
def session(conn):
    txn = conn.begin()
    try:
        with get_session(bind=conn, testing=True) as session:
            yield session
    finally:
        txn.rollback()


@fixture
def clear_translations(session: Session):
    session.execute(delete(Translation))


@fixture
def generate_codes(session: Session):
    # TODO CodeListe should be pre-populated from a fixture.
    # TODO Value should come from an Enum
    standorttyp = CodeListe(constants.CodeListe.StandortTyp)
    standorttyp_ablagerung = Code(
        codeliste=standorttyp, code=constants.StandortTyp.ABLAGERUNG
    )
    standorttyp_betrieb = Code(
        codeliste=standorttyp, code=constants.StandortTyp.BETRIEB
    )
    standorttyp_unfall = Code(codeliste=standorttyp, code=constants.StandortTyp.UNFALL)
    standorttyp_schiessanlage = Code(
        codeliste=standorttyp, code=constants.StandortTyp.SCHIESSANLAGE
    )

    genauigkeit = CodeListe(constants.CodeListe.Genauigkeit)
    genauigkeit_test = Code(codeliste=genauigkeit, code="test")
    genauigkeit_test2 = Code(codeliste=genauigkeit, code="test2")

    stoffklasse = CodeListe(constants.CodeListe.Stoffklasse)
    stoffklasse_test = Code(codeliste=stoffklasse, code="test")
    stoffklasse_test2 = Code(codeliste=stoffklasse, code="test2")

    stoffgruppe = CodeListe(constants.CodeListe.Stoffgruppen)
    stoffgruppe_test = Code(codeliste=stoffgruppe, code="test")
    stoffgruppe_test2 = Code(codeliste=stoffgruppe, code="test2")

    branche_asw = CodeListe(constants.CodeListe.BrancheASW)
    branche_asw_test = Code(codeliste=branche_asw, code="test")
    branche_asw_test2 = Code(codeliste=branche_asw, code="test2")

    branche_noga = CodeListe(constants.CodeListe.BrancheNOGA)
    branche_noga_test = Code(codeliste=branche_noga, code="test")
    branche_noga_test2 = Code(codeliste=branche_noga, code="test2")

    untersuchungs_stand = CodeListe(constants.CodeListe.UntersuchungsStand)
    untersuchungs_stand_test = Code(codeliste=untersuchungs_stand, code="test")
    untersuchungs_stand_test2 = Code(codeliste=untersuchungs_stand, code="test2")

    beurteilung = CodeListe(constants.CodeListe.Beurteilung)
    beurteilung_test = Code(codeliste=beurteilung, code="test")
    beurteilung_test2 = Code(codeliste=beurteilung, code="test2")

    handlungsbedarf = CodeListe(constants.CodeListe.Handlungsbedarf)
    handlungsbedarf_test = Code(codeliste=handlungsbedarf, code="test")
    handlungsbedarf_test2 = Code(codeliste=handlungsbedarf, code="test2")

    unfallstoff = CodeListe(constants.CodeListe.Stoff)
    unfallstoff_test = Code(codeliste=unfallstoff, code="test")
    unfallstoff_test2 = Code(codeliste=unfallstoff, code="test2")

    nutzung_grundwasser_abstrom = CodeListe(
        constants.CodeListe.NutzungGrundwasserAbstrom
    )
    nutzung_grundwasser_abstrom_test = Code(
        codeliste=nutzung_grundwasser_abstrom, code="test"
    )

    art_gewaesser = CodeListe(constants.CodeListe.GewaesserArt)
    art_gewaesser_test = Code(codeliste=art_gewaesser, code="test")
    art_gewaesser_test2 = Code(codeliste=art_gewaesser, code="test2")

    bau_gewaesser = CodeListe(constants.CodeListe.GewaesserBau)
    bau_gewaesser_test = Code(codeliste=bau_gewaesser, code="test")
    bau_gewaesser_test2 = Code(codeliste=bau_gewaesser, code="test2")

    relative_lage_ogw = CodeListe(constants.CodeListe.RelativeLageOberflaechenGewaesser)
    relative_lage_ogw_test = Code(codeliste=relative_lage_ogw, code="test")
    relative_lage_ogw_test2 = Code(codeliste=relative_lage_ogw, code="test2")

    relative_lage_gw = CodeListe(constants.CodeListe.RelativeLageGrundwasser)
    relative_lage_gw_test = Code(codeliste=relative_lage_gw, code="test")
    relative_lage_gw_test2 = Code(codeliste=relative_lage_gw, code="test2")

    nutzungsart = CodeListe(constants.CodeListe.Flaechennutzung)
    nutzungsart_test = Code(codeliste=nutzungsart, code="test")
    nutzungsart_test2 = Code(codeliste=nutzungsart, code="test2")

    aktuelle_nutzung = CodeListe(constants.CodeListe.FlaechennutzungSiedlungsgebiet)
    aktuelle_nutzung_test = Code(codeliste=aktuelle_nutzung, code="test")
    aktuelle_nutzung_test2 = Code(codeliste=aktuelle_nutzung, code="test2")

    gefaehrdete_bereiche = CodeListe(constants.CodeListe.GefaehrdeteUmweltbereiche)
    gefaehrdete_bereiche_test = Code(codeliste=gefaehrdete_bereiche, code="test")
    gefaehrdete_bereiche_test2 = Code(codeliste=gefaehrdete_bereiche, code="test2")

    umwelt_stoffgruppe = CodeListe(constants.CodeListe.UmweltStoffgruppe)
    umwelt_stoffgruppe_test = Code(codeliste=umwelt_stoffgruppe, code="test")
    umwelt_stoffgruppe_test2 = Code(codeliste=umwelt_stoffgruppe, code="test2")

    umwelt_stoffgruppe_ckw = CodeListe(constants.CodeListe.StoffgruppeCKW)
    umwelt_stoffgruppe_ckw_test = Code(codeliste=umwelt_stoffgruppe_ckw, code="test")
    umwelt_stoffgruppe_ckw_test2 = Code(codeliste=umwelt_stoffgruppe_ckw, code="test2")

    umwelt_stoff_beurteilung = CodeListe(constants.CodeListe.UmweltStoffBeurteilung)
    umwelt_stoff_beurteilung_test = Code(
        codeliste=umwelt_stoff_beurteilung, code="test"
    )
    umwelt_stoff_beurteilung_test2 = Code(
        codeliste=umwelt_stoff_beurteilung, code="test2"
    )

    einzelereignis = CodeListe(constants.CodeListe.Einzelereignis)
    einzelereignis_test = Code(codeliste=einzelereignis, code="test")
    einzelereignis_test2 = Code(codeliste=einzelereignis, code="test2")

    umweltschaden_wasser = CodeListe(constants.CodeListe.UmweltschaedenWasser)
    umweltschaden_wasser_test = Code(codeliste=umweltschaden_wasser, code="test")
    umweltschaden_wasser_test2 = Code(codeliste=umweltschaden_wasser, code="test2")

    art_umweltschaden = CodeListe(constants.CodeListe.Umweltbereich)
    art_umweltschaden_test = Code(codeliste=art_umweltschaden, code="test")
    art_umweltschaden_test2 = Code(codeliste=art_umweltschaden, code="test2")

    massnahme = CodeListe(constants.CodeListe.Massnahme)
    massnahme_test = Code(codeliste=massnahme, code="test")
    massnahme_test2 = Code(codeliste=massnahme, code="test2")

    sanierungs_ziel = CodeListe(constants.CodeListe.Sanierungsziel)
    sanierungs_ziel_test = Code(codeliste=sanierungs_ziel, code="test")
    sanierungs_ziel_test2 = Code(codeliste=sanierungs_ziel, code="test2")

    schiessanlage_typ = CodeListe(constants.CodeListe.SchiessanlageTyp)
    schiessanlage_typ_test = Code(codeliste=schiessanlage_typ, code="test")
    schiessanlage_typ_test2 = Code(codeliste=schiessanlage_typ, code="test2")

    kanton = CodeListe(constants.CodeListe.Kanton)
    kanton_codes = [
        Code(codeliste=kanton, code="AG"),
        Code(codeliste=kanton, code="AI"),
        Code(codeliste=kanton, code="AR"),
        Code(codeliste=kanton, code="BE"),
        Code(codeliste=kanton, code="BL"),
        Code(codeliste=kanton, code="BS"),
        Code(codeliste=kanton, code="FR"),
        Code(codeliste=kanton, code="GE"),
        Code(codeliste=kanton, code="GL"),
        Code(codeliste=kanton, code="GR"),
        Code(codeliste=kanton, code="JU"),
        Code(codeliste=kanton, code="LU"),
        Code(codeliste=kanton, code="NE"),
        Code(codeliste=kanton, code="NW"),
        Code(codeliste=kanton, code="OW"),
        Code(codeliste=kanton, code="SG"),
        Code(codeliste=kanton, code="SH"),
        Code(codeliste=kanton, code="SO"),
        Code(codeliste=kanton, code="SZ"),
        Code(codeliste=kanton, code="TG"),
        Code(codeliste=kanton, code="TI"),
        Code(codeliste=kanton, code="UR"),
        Code(codeliste=kanton, code="VD"),
        Code(codeliste=kanton, code="VS"),
        Code(codeliste=kanton, code="ZG"),
        Code(codeliste=kanton, code="ZH"),
    ]

    deponie_typ = CodeListe(constants.CodeListe.DeponieTyp)
    deponie_typ_test = Code(codeliste=deponie_typ, code="test")
    deponie_typ_test2 = Code(codeliste=deponie_typ, code="test2")

    deponie_typ = CodeListe(constants.CodeListe.DeponieTyp)
    deponie_typ_test = Code(codeliste=deponie_typ, code="test")
    deponie_typ_test2 = Code(codeliste=deponie_typ, code="test2")

    ja_nein_unbek = CodeListe(constants.CodeListe.JaNeinUnbekannt)
    ja_nein_unbek_ja = Code(codeliste=ja_nein_unbek, code="ja")
    ja_nein_unbek_nein = Code(codeliste=ja_nein_unbek, code="nein")
    ja_nein_unbek_unbek = Code(codeliste=ja_nein_unbek, code="unbek")

    gws_bereich = CodeListe(constants.CodeListe.Gewaesserschutzbereiche)
    gws_bereich_test = Code(codeliste=gws_bereich, code="test")
    gws_bereich_keine = Code(codeliste=gws_bereich, code="keine", is_null_code=True)

    gws_zone = CodeListe(constants.CodeListe.Gewaesserschutzzonen)
    gws_zone_test = Code(codeliste=gws_zone, code="test")
    gws_zone_keine = Code(codeliste=gws_zone, code="keine", is_null_code=True)

    durchlaessigkeit = CodeListe(constants.CodeListe.Durchlaessigkeit)
    durchlaessigkeit_test = Code(codeliste=durchlaessigkeit, code="test")

    beabeitungs_stand = CodeListe(constants.CodeListe.Bearbeitungsstand)
    beabeitungs_stand_test = Code(codeliste=beabeitungs_stand, code="test")
    beabeitungs_stand_test2 = Code(codeliste=beabeitungs_stand, code="test2")

    status_parzelle = CodeListe(constants.CodeListe.StatusParzelle)
    status_parzelle_aktuell = Code(codeliste=status_parzelle, code="1")
    status_parzelle_nicht_aktuell = Code(codeliste=status_parzelle, code="0")

    beziehungsart_sonstige = CodeListe(constants.CodeListe.BeziehungsartSonstige)
    beziehungsart_sonstige_test = Code(codeliste=beziehungsart_sonstige, code="test")
    beziehungsart_sonstige_test_2 = Code(codeliste=beziehungsart_sonstige, code="test2")

    beziehungsart_sachbearbeitung = CodeListe(
        constants.CodeListe.BeziehungsartSachbearbeitung
    )
    beziehungsart_sachbearbeitung_sachbearbeitug = Code(
        codeliste=beziehungsart_sachbearbeitung, code="sachbearbeitung"
    )

    beziehungsart_eigentum = CodeListe(constants.CodeListe.BeziehungsartEigentum)
    beziehungsart_eigentum_eigentuemer = Code(
        codeliste=beziehungsart_eigentum, code="eigentuemer"
    )

    beziehungsart_geschaefte = CodeListe(constants.CodeListe.BeziehungsartGeschaefte)
    beziehungsart_geschaefte_geschaefte = Code(
        codeliste=beziehungsart_geschaefte, code="geschaefte"
    )

    prio_untersuch = CodeListe(constants.CodeListe.PrioUntersuchung)
    prio_untersuch_2024 = Code(codeliste=prio_untersuch, code="2024")

    prio_sanier = CodeListe(constants.CodeListe.PrioSanierung)
    prio_sanier_2024 = Code(codeliste=prio_sanier, code="2024")

    subj_kategorie = CodeListe(constants.CodeListe.SubjektKategorie)
    subj_kategorie_sachbearbeiter = Code(
        codeliste=subj_kategorie, code="Sachbearbeiter"
    )

    kontakt_typ = CodeListe(constants.CodeListe.KontaktTyp)
    kontakt_typ_email_privat = Code(codeliste=kontakt_typ, code="EMAIL")
    kontakt_typ_telefon_privat = Code(codeliste=kontakt_typ, code="2")

    anrede = CodeListe(constants.CodeListe.Anrede)
    anrede_frau = Code(codeliste=anrede, code="Frau")
    anrede_herr = Code(codeliste=anrede, code="Herr")
    behoerden_kuerzel = CodeListe(constants.CodeListe.BehoerdenKuerzel)
    behoerden_kuerzel_geops = Code(codeliste=behoerden_kuerzel, code="geOps")

    behoerden_lang_beschreibung = CodeListe(
        constants.CodeListe.BehoerdenLangBezeichnung
    )
    behoerden_lang_beschreibung_geops = Code(
        codeliste=behoerden_lang_beschreibung, code="geOps"
    )

    land = CodeListe(constants.CodeListe.Land)
    land_schweiz = Code(codeliste=land, code="Schweiz")

    task_kategorie = CodeListe(constants.CodeListe.TaskKategorie)
    task_kategorie_kategorie = Code(codeliste=task_kategorie, code="Kategorie")

    pfas_typ = CodeListe(constants.CodeListe.PFASTyp)
    pfas_typ_test = Code(codeliste=pfas_typ, code="test")

    pfas_loeschmittel_haltig = CodeListe(constants.CodeListe.LoeschmittelPFASHaltig)
    pfas_loeschmittel_haltig_test = Code(
        codeliste=pfas_loeschmittel_haltig, code="test"
    )

    pfas_loeschmittel_frei = CodeListe(constants.CodeListe.LoeschmittelPFASFrei)
    pfas_loeschmittel_frei_test = Code(codeliste=pfas_loeschmittel_frei, code="test")

    branche_pfas = CodeListe(constants.CodeListe.BranchePFAS)
    branche_pfas_test = Code(codeliste=branche_pfas, code="test")

    loeschschaum_einsatz = CodeListe(constants.CodeListe.LoeschschaumEinsatz)
    loeschschaum_einsatz_hand = Code(codeliste=loeschschaum_einsatz, code="hand")

    haeufigkeit_nutzung = CodeListe(
        constants.CodeListe.HaeufigkeitNutzungHandfeuerloescher
    )
    haeufigkeit_nutzung_hand = Code(codeliste=haeufigkeit_nutzung, code="test")

    ktu = CodeListe(constants.CodeListe.KTU)
    ktu_bls = Code(codeliste=ktu, code="bls")

    kinderspielplatz_gruenflaeche_typ = CodeListe(
        constants.CodeListe.KinderspielplatzGruenflaecheTyp
    )
    kinderspielplatz_gruenflaeche_typ_typ = Code(
        codeliste=kinderspielplatz_gruenflaeche_typ, code="Typ"
    )

    eigentumsform = CodeListe(constants.CodeListe.Eigentumsform)
    eigentumsform_test = Code(codeliste=eigentumsform, code="Eigentumsform")

    altersstufe_kinder = CodeListe(constants.CodeListe.AltersstufeKinder)
    altersstufe_kinder_0_3 = Code(codeliste=altersstufe_kinder, code="0-3")

    flugplatz_bezeichnung = CodeListe(constants.CodeListe.FlugplatzBezeichnung)
    flugplatz_bezeichnung_test = Code(codeliste=flugplatz_bezeichnung, code="Test")

    beurteilung_gruppe = CodeListe(constants.CodeListe.BeurteilungGruppe)
    beurteilung_gruppe_test = Code(codeliste=beurteilung_gruppe, code="Test")
    beurteilung_gruppe_test2 = Code(codeliste=beurteilung_gruppe, code="Test2")

    session.add_all(
        [
            standorttyp,
            standorttyp_ablagerung,
            standorttyp_betrieb,
            standorttyp_unfall,
            standorttyp_schiessanlage,
            genauigkeit,
            genauigkeit_test,
            genauigkeit_test2,
            stoffklasse,
            stoffklasse_test,
            stoffklasse_test2,
            stoffgruppe,
            stoffgruppe_test,
            stoffgruppe_test2,
            branche_asw,
            branche_asw_test,
            branche_asw_test2,
            branche_noga,
            branche_noga_test,
            branche_noga_test2,
            untersuchungs_stand,
            untersuchungs_stand_test,
            untersuchungs_stand_test2,
            beurteilung,
            beurteilung_test,
            beurteilung_test2,
            unfallstoff,
            unfallstoff_test,
            unfallstoff_test2,
            nutzung_grundwasser_abstrom,
            nutzung_grundwasser_abstrom_test,
            relative_lage_gw,
            relative_lage_gw_test,
            relative_lage_gw_test2,
            art_gewaesser,
            art_gewaesser_test,
            art_gewaesser_test2,
            bau_gewaesser,
            bau_gewaesser_test,
            bau_gewaesser_test2,
            relative_lage_ogw,
            relative_lage_ogw_test,
            relative_lage_ogw_test2,
            nutzungsart,
            nutzungsart_test,
            nutzungsart_test2,
            aktuelle_nutzung,
            aktuelle_nutzung_test,
            aktuelle_nutzung_test2,
            gefaehrdete_bereiche,
            gefaehrdete_bereiche_test,
            gefaehrdete_bereiche_test2,
            umwelt_stoffgruppe,
            umwelt_stoffgruppe_test,
            umwelt_stoffgruppe_test2,
            umwelt_stoffgruppe_ckw,
            umwelt_stoffgruppe_ckw_test,
            umwelt_stoffgruppe_ckw_test2,
            umwelt_stoff_beurteilung,
            umwelt_stoff_beurteilung_test,
            umwelt_stoff_beurteilung_test2,
            einzelereignis,
            einzelereignis_test,
            einzelereignis_test2,
            umweltschaden_wasser,
            umweltschaden_wasser_test,
            umweltschaden_wasser_test2,
            art_umweltschaden,
            art_umweltschaden_test,
            art_umweltschaden_test2,
            massnahme,
            massnahme_test,
            massnahme_test2,
            sanierungs_ziel,
            sanierungs_ziel_test,
            sanierungs_ziel_test2,
            schiessanlage_typ,
            schiessanlage_typ_test,
            schiessanlage_typ_test2,
            kanton,
            deponie_typ,
            deponie_typ_test,
            deponie_typ_test2,
            ja_nein_unbek,
            ja_nein_unbek_ja,
            ja_nein_unbek_nein,
            ja_nein_unbek_unbek,
            gws_bereich,
            gws_bereich_test,
            gws_zone,
            gws_zone_test,
            durchlaessigkeit,
            durchlaessigkeit_test,
            beabeitungs_stand,
            beabeitungs_stand_test,
            beabeitungs_stand_test2,
            status_parzelle,
            status_parzelle_aktuell,
            status_parzelle_nicht_aktuell,
            beziehungsart_sonstige,
            beziehungsart_sonstige_test,
            beziehungsart_sonstige_test_2,
            beziehungsart_sachbearbeitung,
            beziehungsart_sachbearbeitung_sachbearbeitug,
            beziehungsart_eigentum,
            beziehungsart_eigentum_eigentuemer,
            beziehungsart_geschaefte,
            beziehungsart_geschaefte_geschaefte,
            handlungsbedarf,
            handlungsbedarf_test,
            handlungsbedarf_test2,
            prio_untersuch,
            prio_untersuch_2024,
            prio_sanier,
            prio_sanier_2024,
            gws_bereich_keine,
            gws_zone_keine,
            subj_kategorie,
            subj_kategorie_sachbearbeiter,
            kontakt_typ,
            kontakt_typ_email_privat,
            kontakt_typ_telefon_privat,
            anrede,
            anrede_herr,
            anrede_frau,
            behoerden_kuerzel,
            behoerden_kuerzel_geops,
            behoerden_lang_beschreibung,
            behoerden_lang_beschreibung_geops,
            land,
            land_schweiz,
            task_kategorie,
            task_kategorie_kategorie,
            pfas_typ,
            pfas_typ_test,
            pfas_loeschmittel_haltig,
            pfas_loeschmittel_haltig_test,
            pfas_loeschmittel_frei,
            pfas_loeschmittel_frei_test,
            branche_pfas,
            branche_pfas_test,
            loeschschaum_einsatz,
            loeschschaum_einsatz_hand,
            haeufigkeit_nutzung,
            haeufigkeit_nutzung_hand,
            ktu,
            ktu_bls,
            kinderspielplatz_gruenflaeche_typ,
            kinderspielplatz_gruenflaeche_typ_typ,
            eigentumsform,
            eigentumsform_test,
            altersstufe_kinder,
            altersstufe_kinder_0_3,
            flugplatz_bezeichnung,
            flugplatz_bezeichnung_test,
            beurteilung_gruppe,
            beurteilung_gruppe_test,
            beurteilung_gruppe_test2,
        ]
        + kanton_codes,
    )

    # Also add translations for canton codes in all languages
    kanton_translations = [
        Translation(
            key=f"code:{constants.CodeListe.Kanton}:{code.code}",
            value=code.code,
            locale=lang,
        )
        for code in kanton_codes
        for lang in constants.Language
    ]
    session.add_all(kanton_translations)

    session.commit()


@fixture
def test_user(session: Session) -> User:
    user = User(
        username="alma-test",
        email="alma-test@example.com",
        sub="sub-alma-test-user",
    )
    session.add(user)

    # Create an associated Subjekt entry
    # so the current user is a valid Sachbearbeiter
    subj = Subjekt(name="alma test user")
    subj.user = user
    session.add(subj)

    session.flush()
    return user


@fixture
def workflow_manager(session: Session, test_user: User):
    workflow_manager = WorkflowManager(
        session, wf_manager_config, context={"user": test_user}
    )
    add_event_handlers(workflow_manager)
    return workflow_manager


@fixture
def context(
    session: Session, test_user: User, workflow_manager: WorkflowManager
) -> Context:
    return Context(db=session, user=test_user, workflow_manager=workflow_manager)


@fixture
def as_admin(context: Context):
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.ADMINISTRATION)
    ).one()
    return context


@fixture
def as_lesen_sachdaten(context: Context):
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.LESEN_SACHDATEN)
    ).one()
    return context


@fixture
def as_lesen_geschaefte(context: Context):
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.LESEN_GESCHAEFTE)
    ).one()
    return context


@fixture
def as_bearbeiten_sachdaten(context: Context):
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.BEARBEITEN_SACHDATEN)
    ).one()
    return context


@fixture
def as_bearbeiten_geschaefte(context: Context):
    context.user.role = context.db.scalars(
        select(Role).where(Role.name == RoleName.BEARBEITEN_GESCHAEFTE)
    ).one()
    return context


@fixture
def run_query(context: Context):
    def _run_query(*args, **kw):
        result = schema.execute_sync(*args, **kw, context_value=context)
        if result.errors:
            raise QueryError(result.errors)
        return result

    return _run_query
