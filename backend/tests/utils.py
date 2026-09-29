from datetime import date, datetime, timedelta
from typing import Any, TypeVar

from business_workflow_manager.models import (
    DocumentNode,
    FormNode,
    Node,
    NoteNode,
    Task,
    TaskNode,
    Workflow,
    WorkflowNode,
)
from business_workflow_manager.types import NodeStatus
from graphql import GraphQLError
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.types.base import (
    StrawberryList,
    StrawberryOptional,
    get_object_definition,
    has_object_definition,
)
from strawberry.utils.str_converters import to_camel_case

from alma import constants
from alma.constants import Language
from alma.models import codes
from alma.models.auth import User, UserSetting
from alma.models.cache import WfsUpdate
from alma.models.flugplatz import Flugplatz
from alma.models.gem import Gemeinde
from alma.models.grun import Nummerierungsbereich, Parzelle
from alma.models.report import (
    ParamType,
    Report,
    ReportContext,
    ReportParam,
    ReportQuery,
)
from alma.models.search import Search, SearchExport
from alma.models.subj import (
    Beteiligter,
    BeteiligterStandort,
    Kontakt,
    Subjekt,
)
from alma.models.task_status import TaskCategory, TaskStatus, TaskStatusEnum
from alma.models.translations import Translation
from alma.models.umwelt import (
    Einzelereignis,
    Grundwasser,
    NutzungBoden,
    OberflaechenGewaesser,
    Umweltschaden,
    UmweltStoff,
)
from alma.models.vflz import (
    KTU,
    PFAS,
    Ablagerung,
    Betrieb,
    Beurteilung,
    KinderspielplatzGruenflaeche,
    KompartimentStoffgruppe,
    KompartimentStoffklasse,
    LoeschschaumEinsatz,
    Massnahme,
    Objekt,
    Pool,
    Sanierungsziel,
    Schiessanlage,
    Unfall,
    Unfallstoff,
    VflPool,
    Vflz,
    Vollzug,
)
from alma.models.workflow import (
    BeteiligterGeschaeft,
)
from alma.search import SearchField
from alma.search.constants import DASHBOARD_SAVED_SEARCH_SETTINGS_KEY
from alma.search.export import ExportFormat


def make_grundwasser(session: Session, vflz: Vflz) -> Grundwasser:
    relative_lage_test_code = session.scalars(
        select(codes.RelativeLageGrundwasser).where(
            codes.RelativeLageGrundwasser.code == "test"
        )
    ).one()

    nutzung_test_code = session.scalars(
        select(codes.NutzungGrundwasserAbstrom).where(
            codes.NutzungGrundwasserAbstrom.code == "test"
        )
    ).one()

    gwas = Grundwasser(
        relative_lage=relative_lage_test_code,
        flurabstand=3.1,
        nutzung=nutzung_test_code,
        distanz=3,
    )
    vflz.grundwasser.append(gwas)
    session.commit()

    return gwas


def make_oberflaechen_gewaesser(session: Session, vflz: Vflz) -> OberflaechenGewaesser:
    art_gewaesser_test_code = session.scalars(
        select(codes.GewaesserArt).where(codes.GewaesserArt.code == "test")
    ).one()

    bau_gewaesser_test_code = session.scalars(
        select(codes.GewaesserBau).where(codes.GewaesserBau.code == "test")
    ).one()

    relative_lage_ogw_test_code = session.scalars(
        select(codes.RelativeLageOberflaechenGewaesser).where(
            codes.RelativeLageOberflaechenGewaesser.code == "test"
        )
    ).one()

    ogw = OberflaechenGewaesser(
        art_gewaesser=art_gewaesser_test_code,
        bau_gewaesser=bau_gewaesser_test_code,
        relative_lage=relative_lage_ogw_test_code,
        distanz=3,
        name="foo OGW",
    )
    vflz.oberflaechen_gewaesser.append(ogw)
    session.commit()

    return ogw


def make_nutzung_boden(session: Session, vflz: Vflz) -> NutzungBoden:
    nutzung_gelaende_test_code = session.scalars(
        select(codes.Flaechennutzung).where(codes.Flaechennutzung.code == "test")
    ).one()

    aktuelle_nutzung_test_code = session.scalars(
        select(codes.FlaechennutzungSiedlungsgebiet).where(
            codes.FlaechennutzungSiedlungsgebiet.code == "test"
        )
    ).one()

    nutzung_boden = NutzungBoden(
        nutzungsart=nutzung_gelaende_test_code,
        aktuelle_nutzung=aktuelle_nutzung_test_code,
    )
    vflz.nutzungen_boden.append(nutzung_boden)
    session.commit()

    return nutzung_boden


def make_umweltstoff(session: Session, vflz: Vflz) -> UmweltStoff:
    gefaehrdete_bereiche_test_code = session.scalars(
        select(codes.GefaehrdeteUmweltbereiche).where(
            codes.GefaehrdeteUmweltbereiche.code == "test"
        )
    ).one()
    umwelt_stoffgruppe_test_code = session.scalars(
        select(codes.UmweltStoffgruppe).where(codes.UmweltStoffgruppe.code == "test")
    ).one()
    umwelt_stoffgruppe_ckw_test_code = session.scalars(
        select(codes.StoffgruppeCKW).where(codes.StoffgruppeCKW.code == "test")
    ).one()
    umwelt_stoff_beurteilung_test_code = session.scalars(
        select(codes.UmweltStoffBeurteilung).where(
            codes.UmweltStoffBeurteilung.code == "test"
        )
    ).one()

    umwelt_stoff = UmweltStoff(
        gefaehrdete_bereiche=gefaehrdete_bereiche_test_code,
        stoff_gruppe=umwelt_stoffgruppe_test_code,
        stoff=umwelt_stoffgruppe_ckw_test_code,
        beurteilung=umwelt_stoff_beurteilung_test_code,
    )
    vflz.umwelt_stoffe.append(umwelt_stoff)
    session.commit()

    return umwelt_stoff


def make_umweltschaden(session: Session, vflz: Vflz) -> Umweltschaden:
    umweltbereich_test_code = session.scalars(
        select(codes.Umweltbereich).where(codes.Umweltbereich.code == "test")
    ).one()

    umweltschaeden_wasser_test_code = session.scalars(
        select(codes.UmweltschaedenWasser).where(
            codes.UmweltschaedenWasser.code == "test"
        )
    ).one()

    umweltschaden = Umweltschaden(
        art_schaden=umweltbereich_test_code,
        schaeden=umweltschaeden_wasser_test_code,
    )
    vflz.umweltschaeden.append(umweltschaden)
    session.commit()

    return umweltschaden


class QueryError(Exception):
    errors: list[GraphQLError]


def prefill_optional_fields(
    input_type: type, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    if data is None:
        data = {}
    assert has_object_definition(input_type)
    for field in get_object_definition(input_type, strict=True).fields:
        graphql_field_name = to_camel_case(field.name)
        if graphql_field_name not in data:
            if isinstance(field.type, StrawberryOptional):
                data[graphql_field_name] = None
            elif isinstance(field.type, StrawberryList):
                data[graphql_field_name] = []
    return data


T_Code = TypeVar("T_Code", bound=codes.Code)


def make_code(session: Session, type_: type[T_Code], code: str) -> T_Code:
    c_cli_id = type_.__mapper_args__["polymorphic_identity"]
    codeliste = session.get(codes.CodeListe, c_cli_id)
    if codeliste is None:
        codeliste = codes.CodeListe(c_cli_id=c_cli_id)
        session.add(codeliste)

    code_obj = type_(codeliste=codeliste, code=code)
    session.add(code_obj)
    session.flush()
    return code_obj


def make_translation(
    session: Session, lang: Language, key: str, value: str | None = None
):
    if value is None:
        value = f"{key}:{lang}"
    translation = Translation(key=key, value=value, locale=lang)
    session.add(translation)
    session.commit()

    return translation


def make_kbsinfo(
    session: Session, beurteilung: codes.Beurteilung, belastet: bool, color: str
) -> codes.KbsInfo:
    beurteilung_gruppe = session.scalars(
        select(codes.BeurteilungGruppe).where(codes.BeurteilungGruppe.code == "Test")
    ).one()
    kbsinfo = codes.KbsInfo(
        beurteilung=beurteilung,
        beurteilung_gruppe=beurteilung_gruppe,
        belastet=belastet,
        color=color,
        color_rgb=None,
    )
    session.add(kbsinfo)
    session.flush()
    return kbsinfo


def make_vflz(
    session: Session,
    bezeichnung: str,
    vfl_id: int = 1,
    combined_id: str = "combined-id-1",
) -> Vflz:
    standorttyp_betrieb = session.scalars(
        select(codes.StandortTyp).where(
            codes.StandortTyp.code == constants.StandortTyp.BETRIEB
        )
    ).one()
    deponietyp_test = session.scalars(
        select(codes.DeponieTyp).where(codes.DeponieTyp.code == "test")
    ).one()
    bearbeitungs_stand_test = session.scalars(
        select(codes.Bearbeitungsstand).where(codes.Bearbeitungsstand.code == "test")
    ).one()
    untersuchungs_stand_test = session.scalars(
        select(codes.UntersuchungsStand).where(codes.UntersuchungsStand.code == "test")
    ).one()
    behoerde = session.scalars(
        select(codes.BehoerdenKuerzel).where(codes.BehoerdenKuerzel.code == "geOps")
    ).one()

    vflz = Vflz(
        bezeichnung=bezeichnung,
        vfl_id=vfl_id,
        combined_id=combined_id,
        objekt=Objekt(),
        vftyp=standorttyp_betrieb,
        strasse="strasse 3a",
        postleitzahl="7123",
        ort="Bern",
        dat_rechtskraft=None,
        dat_publizieren=None,
        rechtskraft=False,
        publizieren=False,
        behoerde=behoerde,
    )
    vflz.set_zentroid({"type": "Point", "coordinates": [30, 10, 40]})
    vflz.bearbeitungs_stand = bearbeitungs_stand_test
    vflz.untersuchungs_stand = untersuchungs_stand_test
    vflz.message = "Initial version"
    vflz.gemeinde = make_gemeinde(session)
    vflz.deponietyp = deponietyp_test
    vflz.in_betrieb = True
    vflz.nachsorge = False

    session.add(vflz)
    session.commit()

    return vflz


def make_gemeinde(
    session: Session,
    name: str = "Aeugst am Albis",
    bfs_nummer: int = 1,
    kanton: str = "ZH",
) -> Gemeinde:
    if gemeinde := session.get(Gemeinde, bfs_nummer):
        return gemeinde
    gemeinde = Gemeinde(
        bfs_nummer=bfs_nummer,
        gemeinde=name,
        kanton=session.get_one(codes.Kanton, (constants.CodeListe.Kanton, kanton)),
    )
    session.add(gemeinde)
    session.commit()
    return gemeinde


def make_ablagerung(session: Session, vflz: Vflz) -> Ablagerung:
    ablagerung = Ablagerung(
        vol_kompartiment=3.0,
        tiefe="32",
        zeitraum_von=date(2021, 1, 1),
        zeitraum_bis=date(2022, 2, 2),
        zeitraum_vonjahr=True,
        zeitraum_bisjahr=False,
        zeitraum_bisheute=False,
    )
    vflz.ablagerungen.append(ablagerung)
    session.commit()

    return ablagerung


def make_kompartiment_stoffklasse(
    session: Session, ablagerung: Ablagerung
) -> KompartimentStoffklasse:
    stoffklasse_test_code = session.scalars(
        select(codes.Stoffklasse).where(codes.Stoffklasse.code == "test")
    ).one()
    genauigkeit_test_code = session.scalars(
        select(codes.Genauigkeit).where(codes.Genauigkeit.code == "test")
    ).one()

    kksk = KompartimentStoffklasse(
        stoffklasse=stoffklasse_test_code,
        genauigkeit_von=genauigkeit_test_code,
        genauigkeit_bis=genauigkeit_test_code,
        teilvol=0.5,
        zeitraum_von=date(2021, 1, 1),
        zeitraum_bis=date(2022, 2, 2),
        zeitraum_vonjahr=True,
        zeitraum_bisjahr=False,
        zeitraum_bisheute=False,
    )
    ablagerung.kompartiment_stoffklassen.append(kksk)
    session.commit()

    return kksk


def make_kompartiment_stoffgruppe(
    session: Session, kompartiment_stoffklasse: KompartimentStoffklasse
):
    stoffgruppe_test_code = session.scalars(
        select(codes.Stoffgruppen).where(codes.Stoffgruppen.code == "test")
    ).one()

    kksg = KompartimentStoffgruppe(
        stoffgruppe=stoffgruppe_test_code,
        teilvol=4.0,
    )
    kompartiment_stoffklasse.kompartiment_stoffgruppen.append(kksg)
    session.commit()

    return kksg


def make_betrieb(
    session: Session, vflz: Vflz, firma_name: str = "Foo Firma Name"
) -> Betrieb:
    branche_asw_test_code = session.scalars(
        select(codes.BrancheASW).where(codes.BrancheASW.code == "test")
    ).one()
    branche_noga_test_code = session.scalars(
        select(codes.BrancheNOGA).where(codes.BrancheNOGA.code == "test")
    ).one()
    untersuchungs_stand_test_code = session.scalars(
        select(codes.UntersuchungsStand).where(codes.UntersuchungsStand.code == "test")
    ).one()
    beurteilung_betrieb_test_code = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == "test")
    ).one()
    genauigkeit_test_code = session.scalars(
        select(codes.Genauigkeit).where(codes.Genauigkeit.code == "test")
    ).one()

    betrieb = Betrieb(
        branche_asw=branche_asw_test_code,
        branche_noga=branche_noga_test_code,
        untersuchungs_stand=untersuchungs_stand_test_code,
        beurteilung=beurteilung_betrieb_test_code,
        zeitraum_von=date(2027, 1, 1),
        zeitraum_bis=date(2028, 2, 2),
        zeitraum_vonjahr=False,
        zeitraum_bisjahr=True,
        zeitraum_bisheute=False,
        genauigkeit_von=genauigkeit_test_code,
        genauigkeit_bis=genauigkeit_test_code,
        firma_name=firma_name,
        firma_strasse="Foo Firma Strasse",
        firma_plz="1234",
        firma_ort="Foo Firma Ort",
        groesse=10,
        eva="Foo EVA",
        relevant=False,
        mobile_stoffe=True,
    )
    betrieb.set_zentroid({"type": "Point", "coordinates": [30, 10]})
    vflz.betriebe.append(betrieb)
    session.commit()

    return betrieb


def make_schiessanlage(session: Session, vflz: Vflz) -> Schiessanlage:
    branche_asw_test_code = session.scalars(
        select(codes.BrancheASW).where(codes.BrancheASW.code == "test")
    ).one()
    branche_noga_test_code = session.scalars(
        select(codes.BrancheNOGA).where(codes.BrancheNOGA.code == "test")
    ).one()
    untersuchungs_stand_test_code = session.scalars(
        select(codes.UntersuchungsStand).where(codes.UntersuchungsStand.code == "test")
    ).one()
    beurteilung_betrieb_test_code = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == "test")
    ).one()
    typ_test_code = session.scalars(
        select(codes.SchiessanlageTyp).where(codes.SchiessanlageTyp.code == "test")
    ).one()
    genauigkeit_test_code = session.scalars(
        select(codes.Genauigkeit).where(codes.Genauigkeit.code == "test")
    ).one()

    schiessanlage = Schiessanlage(
        branche_asw=branche_asw_test_code,
        branche_noga=branche_noga_test_code,
        untersuchungs_stand=untersuchungs_stand_test_code,
        beurteilung=beurteilung_betrieb_test_code,
        zeitraum_von=date(2027, 1, 1),
        zeitraum_bis=date(2028, 2, 2),
        zeitraum_vonjahr=False,
        zeitraum_bisjahr=True,
        zeitraum_bisheute=False,
        genauigkeit_von=genauigkeit_test_code,
        genauigkeit_bis=genauigkeit_test_code,
        firma_name="Foo Firma Name",
        firma_strasse="Foo Firma Strasse",
        firma_plz="1234",
        firma_ort="Foo Firma Ort",
        eva="Foo EVA",
        groesse=10,
        relevant=False,
        mobile_stoffe=True,
        typ=typ_test_code,
        schusszahl=3,
        scheibenzahl=4,
        hat_kugelfang=True,
    )
    schiessanlage.set_zentroid({"type": "Point", "coordinates": [30, 10]})
    vflz.schiessanlagen.append(schiessanlage)
    session.commit()

    return schiessanlage


def make_unfall(session: Session, vflz: Vflz) -> Unfall:
    genauigkeit_test_code = session.scalars(
        select(codes.Genauigkeit).where(codes.Genauigkeit.code == "test")
    ).one()

    unfall = Unfall(
        genauigkeit_zeitpunkt=genauigkeit_test_code,
        name="Foo Unfall",
        zeitpunkt=date(2020, 1, 1),
        zeitpunkt_jahr=True,
    )
    vflz.unfaelle.append(unfall)
    session.commit()

    return unfall


def make_unfallstoff(session: Session, unfall: Unfall) -> Unfallstoff:
    unfallstoff_test_code = session.scalars(
        select(codes.Stoff).where(codes.Stoff.code == "test")
    ).one()

    unfallstoff = Unfallstoff(
        stoff=unfallstoff_test_code,
        stoffmng=3.0,
        ausgelaufen=4.0,
        zurueckgewonnen=2.0,
    )
    unfall.unfallstoffe.append(unfallstoff)
    session.commit()

    return unfallstoff


def make_einzelereignis(session: Session, vflz: Vflz) -> Einzelereignis:
    einzelereignis_test_code = session.scalars(
        select(codes.Einzelereignis).where(codes.Einzelereignis.code == "test")
    ).one()

    einzelereignis = Einzelereignis(
        einzelereignis=einzelereignis_test_code,
        datum=date(2021, 3, 4),
    )
    vflz.einzelereignisse.append(einzelereignis)
    session.commit()

    return einzelereignis


def make_vflz_beurteilung(
    session: Session, vflz: Vflz, code_beurteilung: str = "test"
) -> Beurteilung:
    beurteilung_code = session.scalars(
        select(codes.Beurteilung).where(codes.Beurteilung.code == code_beurteilung)
    ).one()
    prio_untersuch = session.scalars(
        select(codes.PrioUntersuchung).where(
            codes.PrioUntersuchung.code == "2024",
        )
    ).one()
    prio_sanier = session.scalars(
        select(codes.PrioSanierung).where(
            codes.PrioSanierung.code == "2024",
        )
    ).one()

    vflz.beurteilung = Beurteilung(
        beurteilung=beurteilung_code,
        prio_untersuch=prio_untersuch,
        prio_sanier=prio_sanier,
    )
    session.commit()

    return vflz.beurteilung


def make_massnahme(session: Session, vflz: Vflz) -> Massnahme:
    massnahme_code = session.scalars(
        select(codes.Massnahme).where(codes.Massnahme.code == "test")
    ).one()

    massnahme = Massnahme(
        massnahme=massnahme_code,
        dat_massnahme=date(2020, 3, 4),
        ang_massnahme=date(2020, 5, 3),
    )
    vflz.massnahmen.append(massnahme)
    session.commit()

    return massnahme


def make_sanierungsziel(session: Session, vflz: Vflz) -> Sanierungsziel:
    sanierungsziel_code = session.scalars(
        select(codes.Sanierungsziel).where(codes.Sanierungsziel.code == "test")
    ).one()

    sz = Sanierungsziel(sanierungsziel=sanierungsziel_code)
    vflz.sanierungsziele.append(sz)
    session.commit()

    return sz


def make_pool(session: Session, bezeichnung: str = "foo") -> Pool:
    pool = Pool(bezeichnung=bezeichnung, bemerkungen="bar")
    session.add(pool)
    session.commit()

    return pool


def make_vfl_pool(session: Session, vfl_id: int, pool: Pool) -> VflPool:
    vfl_pool = VflPool(vfl_id=vfl_id)
    pool.vfl_pools.append(vfl_pool)
    session.add(vfl_pool)
    session.commit()
    return vfl_pool


def make_parzelle(
    session: Session,
    gb_nummer: str,
    geom_ewkt: str | None = None,
    gemeinde: Gemeinde | None = None,
) -> Parzelle:
    if not gemeinde:
        gemeinde = make_gemeinde(session)
    status_parzelle_code = session.scalars(
        select(codes.StatusParzelle).where(codes.StatusParzelle.code == "1")
    ).one()
    parzelle = Parzelle(
        gb_nummer=gb_nummer, gemeinde=gemeinde, status=status_parzelle_code
    )
    if geom_ewkt:
        parzelle.wkb_geometry = geom_ewkt  # type: ignore[assignment]
    else:
        parzelle.wkb_geometry = "SRID=2056;POLYGON ((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000))"  # type: ignore[assignment]
    # we can ignore type checker,
    # cf. https://geoalchemy-2.readthedocs.io/en/latest/gallery/test_orm_mapped_v2.html

    session.add(parzelle)
    session.commit()

    return parzelle


def make_nummerierungsbereich(
    session: Session,
    h_nb_id: str,
    geom_ewkt: str | None = None,
    bezeichnung: str | None = None,
) -> Nummerierungsbereich:
    nb = Nummerierungsbereich(
        bezeichnung=bezeichnung if bezeichnung else "foo", h_nb_id=h_nb_id
    )
    if geom_ewkt:
        nb.wkb_geometry = geom_ewkt  # type: ignore[assignment]
    else:
        nb.wkb_geometry = "SRID=2056;POLYGON ((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000))"  # type: ignore[assignment]

    session.add(nb)
    session.commit()
    return nb


def make_subj(
    session: Session,
    name: str = "",
    vorname: str = "",
    taetigkeit: str = "",
    ort: str = "",
    postleitzahl: str = "",
    strasse: str = "",
    anrede: str | None = None,
) -> Subjekt:
    anrede_code = None
    if anrede is not None:
        anrede_code = session.scalars(
            select(codes.Anrede).where(codes.Anrede.code == anrede)
        ).one()
    subjekt = Subjekt()
    subjekt.name = name
    subjekt.vorname = vorname
    subjekt.taetigkeit = taetigkeit
    subjekt.ort = ort
    subjekt.postleitzahl = postleitzahl
    subjekt.strasse = strasse
    subjekt.anrede = anrede_code
    session.add(subjekt)
    session.commit()

    return subjekt


def make_email_kontakt(session: Session, subj: Subjekt) -> Kontakt:
    email_kontakt_code = session.scalars(
        select(codes.KontaktTyp).where(
            codes.KontaktTyp.code == constants.KontaktTyp.EMAIL_BUSINESS
        )
    ).one()
    kontakt = Kontakt()
    kontakt.kontakt_typ = email_kontakt_code
    kontakt.kontakt = "unit@geops.com"
    subj.kontakte.append(kontakt)
    session.commit()
    return kontakt


def make_phone_private_kontakt(session: Session, subj: Subjekt) -> Kontakt:
    email_kontakt_code = session.scalars(
        select(codes.KontaktTyp).where(
            codes.KontaktTyp.code == constants.KontaktTyp.PHONE_PRIVATE
        )
    ).one()
    kontakt = Kontakt()
    kontakt.kontakt_typ = email_kontakt_code
    kontakt.kontakt = "0123456"
    subj.kontakte.append(kontakt)
    session.commit()
    return kontakt


def make_beteiligter(
    session: Session,
    vflz_id: int,
    subj_id: int,
    is_eigentuemer: bool = False,
    is_sachbearbeiter: bool = False,
) -> Beteiligter:
    beteiligter = Beteiligter(
        is_eigentuemer=is_eigentuemer, is_sachbearbeiter=is_sachbearbeiter
    )
    beteiligter.vflz_id = vflz_id
    beteiligter.subj_id = subj_id
    session.add(beteiligter)
    session.commit()
    return beteiligter


def make_sonstiger_beteiligte_standort(
    session, bet_id: int, bez_art_code: str = "test"
) -> BeteiligterStandort:
    beziehungsart_code = session.scalars(
        select(codes.BeziehungsartSonstige).where(
            codes.BeziehungsartSonstige.code == bez_art_code
        )
    ).one()

    beteiligter_standort = BeteiligterStandort(beziehungsart=beziehungsart_code)
    beteiligter_standort.bet_id = bet_id
    session.add(beteiligter_standort)
    session.commit()
    return beteiligter_standort


def make_sachbearbeiter_standort(
    session, bet_id: int, bez_art_code: str = "test"
) -> BeteiligterStandort:
    beziehungsart_code = session.scalars(
        select(codes.BeziehungsartSachbearbeitung).where(
            codes.BeziehungsartSachbearbeitung.code == bez_art_code
        )
    ).one()

    beteiligter_standort = BeteiligterStandort(beziehungsart=beziehungsart_code)
    beteiligter_standort.bet_id = bet_id
    session.add(beteiligter_standort)
    session.commit()
    return beteiligter_standort


def make_eigentuemer_standort(
    session,
    bet_id: int,
    grun_id: int,
    bez_art_code: str = "eigentuemer",
) -> BeteiligterStandort:
    beziehungsart_code = session.scalars(
        select(codes.BeziehungsartEigentum).where(
            codes.BeziehungsartSonstige.code == bez_art_code
        )
    ).one()
    beteiligter_parzelle = BeteiligterStandort(beziehungsart=beziehungsart_code)
    beteiligter_parzelle.bet_id = bet_id
    beteiligter_parzelle.grun_id = grun_id
    session.add(beteiligter_parzelle)
    session.commit()
    return beteiligter_parzelle


def make_beteiligter_geschaeft(
    session,
    subjekt: Subjekt,
    node: Node,
) -> BeteiligterGeschaeft:
    beziehungsart_code = session.scalars(
        select(codes.BeziehungsartSachbearbeitung).where(
            codes.BeziehungsartSachbearbeitung.code == "sachbearbeitung"
        )
    ).one()
    beteiligter_geschaeft = BeteiligterGeschaeft(
        node=node,
        subjekt=subjekt,
        beziehungsart=beziehungsart_code,
        vfl_id=node.entity.vfl_id,  # pyright: ignore
    )
    session.add(beteiligter_geschaeft)
    session.commit()
    return beteiligter_geschaeft


def finish_wfs_update(
    session, now: datetime, vflz: Vflz, max_update_interval: float = 10.0
) -> WfsUpdate:
    wfs_update = WfsUpdate()
    wfs_update.vflz_id = vflz.vflz_id
    wfs_update.last_update = now - timedelta(seconds=max_update_interval + 1)
    session.add(wfs_update)
    session.commit()
    return wfs_update


def mock_busy_wfs_update(
    session, now: datetime, vflz: Vflz, max_update_interval: float = 10.0
):
    wfs_update = WfsUpdate()
    wfs_update.vflz_id = vflz.vflz_id
    wfs_update.last_update = now - timedelta(seconds=max_update_interval - 1)
    session.add(wfs_update)
    session.commit()
    return wfs_update


def make_vollzug(
    session,
    vflz: Vflz,
    behoerden_kuerzel_code: codes.BehoerdenKuerzel,
    nummer: str = "vollzugnummer",
) -> Vollzug:
    vollzug = Vollzug(behoerde=behoerden_kuerzel_code, combined_id=nummer)
    vflz.vollzug.append(vollzug)
    session.commit()
    return vollzug


def make_report(session, context: ReportContext, title: str = "My Report") -> Report:
    report = Report()
    report.title = title
    report.context = context
    report.template = "render_template.jinja2.html"
    report.style = "style.css"
    report.is_active = True
    session.add(report)
    session.commit()
    return report


def make_report_param(
    session, report: Report, name: str, type: ParamType
) -> ReportParam:
    param = ReportParam(name=name, type=type)
    report.parameters.append(param)
    session.commit()
    return param


def make_report_query(session, name: str, query: str, report: Report) -> ReportQuery:
    report_query = ReportQuery(name=name)
    report_query.query = query
    report.queries.append(report_query)
    session.add(report_query)
    session.commit()
    return report_query


def make_workflow_config(session: Session, title: str = "My Workflow") -> Workflow:
    wf_config = Workflow(
        title=title,
        version=1,
        workflow_id=None,
        min_per_entity=0,
        max_per_entity=None,
    )
    session.add(wf_config)
    session.flush()
    wf_config.workflow_id = wf_config.wf_config_id
    session.commit()
    return wf_config


def make_task_config(
    session: Session, workflow_config: Workflow, name: str, title: str = "My Task"
) -> Task:
    task_config = Task(
        name=name,
        workflow_id=workflow_config.workflow_id,
        version=workflow_config.version,
        title=title,
    )
    session.add(task_config)
    session.commit()
    return task_config


def make_document_node(session, vflz: Vflz, title="My Document") -> DocumentNode:
    node = DocumentNode(
        title=title,
        version=None,
        status=NodeStatus.STARTED,
        config=None,
        entity_id=str(vflz.vflz_id),
        document_ref="test.pdf",
    )
    session.add(node)
    session.commit()
    return node


def make_task_node(session, vflz: Vflz, title="My Task") -> TaskNode:
    node = TaskNode(
        title=title,
        version=None,
        status=NodeStatus.STARTED,
        config=None,
        entity_id=str(vflz.vflz_id),
    )
    session.add(node)
    session.commit()
    return node


def make_workflow_node(session, vflz: Vflz, title: str | None = None) -> WorkflowNode:
    if title is None:
        title = "My Task"
    node = WorkflowNode(
        title=title,
        version=None,
        status=NodeStatus.STARTED,
        config=None,
        entity_id=str(vflz.vflz_id),
    )
    session.add(node)
    session.commit()
    return node


def make_note_node(session, vflz: Vflz, title="My Task") -> NoteNode:
    node = NoteNode(
        title=title,
        version=None,
        status=NodeStatus.STARTED,
        config=None,
        entity_id=str(vflz.vflz_id),
    )
    session.add(node)
    session.commit()
    return node


def make_form_node(session, vflz: Vflz, title="My Task") -> FormNode:
    node = FormNode(
        title=title,
        version=None,
        status=NodeStatus.STARTED,
        config=None,
        entity_id=str(vflz.vflz_id),
        form_config={"name": "my_form"},
    )
    session.add(node)
    session.commit()
    return node


def make_user(
    session: Session,
    username: str = "test",
    email: str = "test@example.com",
    sub: str = "sub",
) -> User:
    user = User(email=email, username=username, sub=sub)
    user.subjekt = Subjekt()
    session.add(user)
    session.commit()
    return user


def make_saved_search(
    session,
    query: list[dict[str, Any]],
    user: User,
    name="My Saved Search",
    is_temporary=False,
    show_on_dashboard=False,
) -> Search:
    saved_search = Search(
        name=name,
        user=user,
        query=query,
        fields=[SearchField.VFLZ_ID.value],
        sort_by=[],
        is_temporary=is_temporary,
    )
    session.add(saved_search)
    session.flush()

    if not (
        user_setting := session.scalars(
            select(UserSetting).where(
                UserSetting.key == DASHBOARD_SAVED_SEARCH_SETTINGS_KEY,
                UserSetting.user_id == user.id,
            )
        ).one_or_none()
    ):
        user_setting = UserSetting(
            key=DASHBOARD_SAVED_SEARCH_SETTINGS_KEY, value=[], user_id=user.id
        )
        session.add(user_setting)
    if show_on_dashboard:
        user_setting = session.scalars(
            select(UserSetting).where(
                UserSetting.key == DASHBOARD_SAVED_SEARCH_SETTINGS_KEY,
                UserSetting.user_id == user.id,
            )
        ).one()
        if saved_search.search_id not in user_setting.value:
            user_setting.value = user_setting.value + [saved_search.search_id]
    session.commit()
    return saved_search


def make_search_export(session, search: Search) -> SearchExport:
    export = SearchExport(
        export_id=search.name,
        search=search,
        user=search.user,
        format=ExportFormat.GEOPACKAGE,
        lang=Language.DE,
    )
    session.add(export)
    session.commit()
    return export


def make_task_status(
    session, task_status: TaskStatusEnum, category: TaskCategory, name: str
):
    status = TaskStatus(
        category=category,
        last_update=datetime.now(),
        name=name,
        status=task_status,
        detail="",
    )
    session.add(status)
    session.commit()
    return status


def make_pfas(session: Session, vflz: Vflz):
    pfas = PFAS()
    pfas.name = "PFAS"
    pfas.strasse = "geops Strasse"
    pfas.plz = "1234"
    pfas.ort = "Freiburg"
    pfas.eva = "12345"
    pfas.untersuchungs_stand = None
    pfas.beurteilung = None
    pfas.branche = None
    pfas.pfas_typ = None
    pfas.pfas_loeschmittel = False
    pfas.relevant = False

    vflz.pfas.append(pfas)
    session.commit()
    return pfas


def make_loeschschaum_einsatz(session: Session, pfas: PFAS):
    loeschschaum_einsatz_code = session.scalars(
        select(codes.LoeschschaumEinsatz).where(
            codes.LoeschschaumEinsatz.code == "hand"
        )
    ).one()
    haeufigkeit_nutzung_code = session.scalars(
        select(codes.HaeufigkeitNutzungHandfeuerloescher).where(
            codes.HaeufigkeitNutzungHandfeuerloescher.code == "test"
        )
    ).one()

    loeschschaum_einsatz = LoeschschaumEinsatz(
        loeschschaum_einsatz=loeschschaum_einsatz_code
    )
    loeschschaum_einsatz.haeufigkeit_nutzung = haeufigkeit_nutzung_code

    pfas.loeschschaum_einsatz.append(loeschschaum_einsatz)
    session.commit()
    return loeschschaum_einsatz


def make_flugplatz(
    session: Session, bezeichnung: str = "Test", geom_ewkt: str | None = None
) -> Flugplatz:
    if not geom_ewkt:
        geom_ewkt = "SRID=2056;MULTIPOLYGON (((2600000 1200000, 2600000 1200100, 2600100 1200100, 2600100 1200000, 2600000 1200000)))"

    bezeichnung_code = session.scalars(
        select(codes.FlugplatzBezeichnung).where(
            codes.FlugplatzBezeichnung.code == bezeichnung
        )
    ).one()
    flugplatz = Flugplatz(
        bezeichnung=bezeichnung_code,
        icao="LSMP",
        art="Militärflugplatz",
        c_kt="ZH",
        abk="abk",
        zusatz="zusatz",
    )
    flugplatz.wkb_geometry = geom_ewkt  # type: ignore[assignment]

    session.add(flugplatz)
    session.commit()
    return flugplatz


def make_ktu(session, code: str = "bls") -> KTU:
    ktu_code = session.scalars(select(codes.KTU).where(codes.KTU.code == code)).one()
    ktu = KTU(rangefrom=0, rangeto=10)
    ktu.ktu = ktu_code

    session.add(ktu)
    session.commit()
    return ktu


def make_kinderspielplatz_gruenflaeche(session: Session, vflz: Vflz):
    kinderspielplatz = KinderspielplatzGruenflaeche(
        name="foo",
        eva="3",
        strasse="strasse 3a",
        plz="7123",
        ort="Bern",
        zeitraum_von=date(2027, 1, 1),
        zeitraum_bis=date(2028, 2, 2),
        zeitraum_vonjahr=False,
        zeitraum_bisjahr=False,
        zeitraum_bisheute=False,
        belastung_ueber_sanierungswert=False,
        relevant=True,
    )
    kinderspielplatz.set_zentroid({"type": "Point", "coordinates": [30, 10]})
    vflz.kinderspielplaetze_gruenflaechen.append(kinderspielplatz)
    session.add(kinderspielplatz)
    session.commit()
    return kinderspielplatz
