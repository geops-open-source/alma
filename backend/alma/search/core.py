from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, StrEnum, auto, unique
from typing import Any

from business_workflow_manager.models import DocumentNode, Node
from sqlalchemy import Integer, Select, SQLColumnExpression, and_, cast, func, tuple_
from sqlalchemy.orm import aliased

from alma.constants import CodeListe, Language
from alma.models import codes
from alma.models.bem import (
    BegruendungBewertung,
    BegruendungBewertungBetrieb,
    BegruendungBewertungPFAS,
    BegruendungPrioSanierungsbedarf,
    BegruendungPrioUntersuchungsbedarf,
    BemerkungAblagerung,
    BemerkungBetrieb,
    BemerkungEinzelereignis,
    BemerkungKinderspielplatzGruenflaeche,
    BemerkungMassnahme,
    BemerkungPFAS,
    BemerkungSanierung,
    BemerkungStandort,
    BemerkungSubjekt,
    BemerkungUmwelt,
    BemerkungUmweltschaden,
    BemerkungUnfall,
)
from alma.models.flugplatz import Flugplatz
from alma.models.gem import Gemeinde
from alma.models.grun import Nummerierungsbereich, Parzelle
from alma.models.subj import (
    Beteiligter,
    BeteiligterStandort,
    Subjekt,
)
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
    BasisBetrieb,
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
    VflGeo,
    VflPool,
    Vflz,
    VflzStatusPublikation,
    Vollzug,
)
from alma.models.workflow import BeteiligterGeschaeft, NodeKategorie


@unique
class SearchField(StrEnum):
    VFLZ_ID = "vflz_id"
    STANDORTNUMMER = "standortnummer"
    STANDORTTYP = "standorttyp"
    BEZEICHNUNG = "bezeichnung"
    STRASSE = "strasse"
    ORT = "ort"
    PUBLIZIERT = "publiziert"
    GEMEINDE = "gemeinde"
    BFS_NR = "bfs_nr"
    BEURTEILUNG = "beurteilung"
    FIRMA_NAME = "firma_name"
    FIRMA_STRASSE = "firma_strasse"
    POOL = "pool"
    ERFASSUNG = "erfassung"
    ZEITRAUM_VON = "zeitraum_von"
    ZEITRAUM_BIS = "zeitraum_bis"
    PLZ = "plz"
    FLAECHE = "flaeche"
    FLURNAME = "flurname"
    X_KOORDINATE = "x_koordinate"
    Y_KOORDINATE = "y_koordinate"
    SPRACHE = "sprache"
    KANTON = "kanton"
    GRUNDDATEN_BEMERKUNGEN = "grunddaten_bemerkungen"
    IN_BETRIEB = "in_betrieb"
    NACHSORGE = "nachsorge"
    DEPONIETYP = "deponietyp"
    KOMPARTIMENT_VOLUMEN = "kompartiment_volumen"
    KOMPARTIMENT_TIEFE = "kompartiment_tiefe"
    KOMPARTIMENT_VON = "kompartiment_von"
    KOMPARTIMENT_BIS = "kompartiment_bis"
    KOMPARTIMENT_BEMERKUNGEN = "kompartiment_bemerkungen"
    STOFFKLASSE_STOFFKLASSE = "stoffklasse_stoffklasse"
    STOFFKLASSE_TEILVOLUMEN = "stoffklasse_teilvolumen"
    STOFFKLASSE_VON = "stoffklasse_von"
    STOFFKLASSE_BIS = "stoffklasse_bis"
    STOFFGRUPPE_STOFFGRUPPE = "stoffgruppe_stoffgruppe"
    STOFFGRUPPE_TEILVOLUMEN = "stoffgruppe_teilvolumen"
    EVA_NUMMER = "eva_nummer"
    BRANCHE = "branche"
    FIRMA_PLZ = "firma_plz"
    FIRMA_ORT = "firma_ort"
    FIRMA_VON = "firma_von"
    FIRMA_BIS = "firma_bis"
    BRANCHE_NOGA = "branche_noga"
    SCHIESSANLAGE_TYP = "schiessanlage_typ"
    KUGELFANG_VORHANDEN = "kugelfang_vorhanden"
    SCHEIBENZAHL = "scheibenzahl"
    SCHUSSANZAHL = "schussanzahl"
    BETRIEBSGROESSE = "betriebsgroesse"
    FIRMA_KATASTERRELEVANZ = "firma_katasterrelevanz"
    MOBILE_STOFFE = "mobile_stoffe"
    FIRMA_UNTERSUCHUNGSSTAND = "firma_untersuchungsstand"
    FIRMA_BEURTEILUNG = "firma_beurteilung"
    FIRMA_BEMERKUNGEN = "firma_bemerkungen"
    BEGRUENDUNG_BEWERTUNG_BETRIEB = "begruendung_bewertung_betrieb"
    FIRMA_X_KOORDINATE = "firma_x_koordinate"
    FIRMA_Y_KOORDINATE = "firma_y_koordinate"
    UNFALL_NAME = "unfall_name"
    UNFALL_ZEITPUNKT = "unfall_zeitpunkt"
    UNFALL_GENAUIGKEIT = "unfall_genauigkeit"
    UNFALLSTOFF_STOFFE = "unfallstoff_stoffe"
    UNFALLSTOFF_AUSGELAUFEN = "unfallstoff_ausgelaufen"
    UNFALLSTOFF_ZURUECKGEW = "unfallstoff_zurueckgew"
    UNFALLSTOFF_RESTMENGE = "unfallstoff_restmenge"
    UNFALL_BEMERKUNG = "unfall_bemerkung"
    GEWAESSERSCHUTZBEREICH = "gewaesserschutzbereich"
    SCHUTZZONE = "schutzzone"
    KARSTGEBIET = "karstgebiet"
    DURCHLAESSIGKEIT = "durchlaessigkeit"
    UMWELT_BEMERKUNGEN = "umwelt_bemerkungen"
    RELATIVE_LAGE_GRUNDWASSER = "relative_lage_grundwasser"
    FLURABSTAND = "flurabstand"
    NUTZUNG_GW_ABSTROMBEREICH = "nutzung_gw_abstrombereich"
    DISTANZ_NUTZUNG_GW_ABSTROMBEREICH = "distanz_nutzung_gw_abstrombereich"
    NAME_OBERFL_GEWAESSER = "name_oberfl_gewaesser"
    DISTANZ_OBERFL_GEWAESSER = "distanz_obefl_gewaesser"
    ART_OBERFL_GEWAESSER = "art_obefl_gewaesser"
    GEWAESSERBAU = "gewaesserbau"
    RELATIVE_LAGE_OBERFL_GEWAESSER = "relative_lage_oberfl_gewaesser"
    UMWELTSTOFF_GRUPPE = "umweltstoff_gruppe"
    SPEZIFISCHER_STOFF = "spezifischer_stoff"
    UMWELT = "umwelt"
    UMWELTSTOFFE_BEURTEILUNG = "umweltstoffe_beurteilung"
    NUTZUNGSZONE = "nutzungszone"
    AKTUELLE_NUTZUNG = "aktuelle_nutzung"
    GEFAEHRDETE_UMWELTBEREICHE = "gefaehrtdete_umweltbereiche"
    FESTGESTELLTE_EINWIRKUNGEN = "festgestellte_einwirkungen"
    UMWELTSCHADEN_BEMERKUNG = "umweltschaden_bemerkung"
    VORKOMMNIS_DATUM = "vorkommnis_datum"
    VORKOMMNIS = "vorkommnis"
    BEMERKUNG_EINZELEREIGNIS = "bemerkung_einzelereignis"
    BEGRUENDUNG_BEURTEILUNG = "begruendung_beurteilung"
    BEARBEITUNGSSTAND = "bearbeitungsstand"
    UNTERSUCHUNGSSTAND = "untersuchungsstand"
    RECHTSKRAEFTIG = "rechtskraeftig"
    DATUM_ERSTEINTRAG = "datum_ersteintrag"
    DATUM_PUBLIKATION_KBS = "datum_publikation_kbs"
    AKTUELLSTE_PUBLIKATION = "aktuellste_publikation"
    MASSNAHME = "massnahme"
    MASSNAHME_ANGEORDNET_AM = "massnahme_angeordnet_am"
    MASSNAHME_ERLEDIGT_AM = "massnahme_erledigt_am"
    MASSNAHME_BEMERKUNG = "massnahme_bemerkung"
    BETEILIGTE = "beteiligte"
    BEZIEHUNGSART_EIGENTUM = "beziehungsart_eigentum"
    BEZIEHUNGSART_SACHBEARBEITUNG = "beziehungsart_sachbearbeitung"
    BEZIEHUNGSART_SONSTIGE = "beziehungsart_sonstige"
    STANDORT_EIGENTUEMER = "standort_eigentuemer"
    VORNAME = "vorname"
    NACHNAME = "nachname"
    TAETIGKEIT = "taetigkeit"
    PRIO_UNTERSUCHUNGSBEDARF = "prio_untersuchungsbedarf"
    BEGRUENDUNG_PRIO_UNTERSUCHUNGSBEDARF = "begruendung_prio_untersuchungsbedarf"
    PRIO_SANIERUNGSBEDARF = "prio_sanierungsbedarf"
    BEGRUENDUNG_PRIO_SANIERUNGSBDEDARF = "begruendung_prio_sanierungsbdedarf"
    SANIERUNGSZIEL = "sanierungsziel"
    SANIERUNGSZIEL_BEMERKUNGEN = "sanierungsziel_bemerkungen"
    KARTENAUSSCHNITT = "kartenausschnitt"
    TASK_TITEL = "task_titel"
    TASK_START_DATUM = "task_start_datum"
    TASK_END_DATUM = "task_end_datum"
    TASK_FAELLIGKEIT = "task_faelligkeit"
    DOKUMENT_REFERENZ = "dokument_referenz"
    NOTIZ = "task_note"
    TASK_BETEILIGTE = "task_beteiligte"
    TASK_BEZIEHUNGSART_EIGENTUM = "task_beziehungsart_eigentum"
    TASK_BEZIEHUNGSART_SACHBEARBEITUNG = "task_beziehungsart_sachbearbeitung"
    TASK_BEZIEHUNGSART_SONSTIGE = "task_beziehungsart_sonstige"
    TASK_BEZIEHUNGSART_GESCHAEFTE = "task_beziehungsart_geschaefte"
    TASK_STATUS = "task_status"
    TASK_TYP = "task_typ"
    TASK_KATEGORIE = "task_kategorie"
    BEMERKUNG_ADRESSE = "bemerkung_adresse"
    KINDERSPIELPLATZ_NAME = "kinderspielplatz_name"
    KINDERSPIELPLATZ_STRASSE = "kinderspielplatz_strasse"
    KINDERSPIELPLATZ_PLZ = "kinderspielplatz_plz"
    KINDERSPIELPLATZ_ORT = "kinderspielplatz_ort"
    KINDERSPIELPLATZ_EVA = "kinderspielplatz_eva"
    KINDERSPIELPLATZ_BEMERKUNG = "kinderspielplatz_bemerkung"
    KINDERSPIELPLATZ_KATASTERRELEVANZ = "kinderspielplatz_katasterrelevanz"
    KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND = "kinderspielplatz_untersuchungsstand"
    KINDERSPIELPLATZ_BEURTEILUNG = "kinderspielplatz_beurteilung"
    EIGENTUMSFORM = "eigentumsform"
    BELASTUNG_UEBER_SANIERUNGSWERT = "belastung_ueber_sanierungswert"
    KINDERSPIELPLATZ_TYP = "kinderspielplatz_typ"
    ALTERSSTUFE_KINDER = "altersstufe_kinder"
    KINDERSPIELPLATZ_ZEITRAUM_VON = "kinderspielplatz_zeitraum_von"
    KINDERSPIELPLATZ_ZEITRAUM_BIS = "kinderspielplatz_zeitraum_bis"
    KINDERSPIELPLATZ_X_KOORDINATE = "kinderspielplatz_x_koordinate"
    KINDERSPIELPLATZ_Y_KOORDINATE = "kinderspielplatz_y_koordinate"
    VOLLZUG = "vollzug"
    BEHOERDE = "behoerde"
    ALTERNATIVE_STANDORTNUMMER = "alternative_standortnummer"
    PARZELLE = "parzelle"
    NB_IDENT = "nb_ident"
    PFAS_NAME = "pfas_name"
    BEMERKUNG_PFAS = "bemerkung_pfas"
    PFAS_UNTERSUCHUNGSSTAND = "pfas_untersuchungsstand"
    PFAS_BEURTEILUNG = "pfas_beurteilung"
    PFAS_BRANCHE = "pfas_branche"
    PFAS_TYP = "pfas_typ"
    BEGRUENDUNG_BEWERTUNG_PFAS = "begruendung_bewertung_pfas"
    PFAS_HALTIGE_LOESCHMITTEL = "pfas_haltige_loeschmittel"
    PFAS_FREIE_LOESCHMITTEL = "pfas_freie_loeschmittel"
    PFAS_LOESCHSCHAUM_EINSATZ = "pfas_loeschschaum_einsatz"
    PFAS_HAEUFIGKEIT_NUTZUNG = "pfas_haeufigkeit_nutzung"
    PFAS_STRASSE = "pfas_strasse"
    PFAS_PLZ = "pfas_plz"
    PFAS_ORT = "pfas_ort"
    PFAS_EVA_NUMMER = "pfas_eva_nummer"
    PFAS_ZEITRAUM_VON = "pfas_zeitraum_von"
    PFAS_ZEITRAUM_BIS = "pfas_zeitraum_bis"
    PFAS_LOESCHMITTEL = "pfas_loeschmittel"
    PFAS_KATASTERRELEVANZ = "pfas_katasterrelevanz"
    PFAS_MENGE_SCHAUMGEMISCH = "pfas_menge_schaumgemisch"
    PFAS_MENGE_KONZENTRAT = "pfas_menge_konzentrat"
    PFAS_BESCHREIBUNGEN_DETAIL = "pfas_beschreibungen_detail"
    PFAS_X_KOORDINATE = "pfas_x_koordinate"
    PFAS_Y_KOORDINATE = "pfas_y_koordinate"
    FLUGPLATZ_BEZEICHNUNG = "flugplatz_bezeichnung"
    KTU = "ktu"
    GRUNDBUCH_BEZEICHNUNG = "grundbuch_bezeichnung"


@unique
class FieldCategory(Enum):
    STANDORT = 1
    GRUNDDATEN = 2
    ABLAGERUNGEN = 3
    BETRIEBE = 4  # Betriebe und Schiessanlagen
    UNFAELLE = 5
    NATUERLICHES_UMFELD = 6
    GRUNDWASSER = 7
    OBERFLAECHENGEWAESSER = 8
    UMWELTSTOFFE = 9
    NUTZUNGEN_GELAENDE = 10
    UMWELTEINWIRKUNGEN = 11
    VORKOMMNISSE = 12
    BEURTEILUNG = 13
    PRIORISIERUNG = 14
    ZIELE = 15
    MASSNAHMEN = 16
    BETEILIGTE = 17
    LOKALISIERUNG = 18
    VOLLZUG = 19
    GESCHAEFT = 20
    KINDERSPIELPLATZ = 21
    PFAS = 22


@unique
class FieldType(Enum):
    TEXT = auto()
    CODE = auto()
    NUMBER = auto()
    DATE = auto()
    BOOL = auto()
    BBOX = auto()  # xmin, ymin, xmax, ymax


# Valid operators by field type
OPERATORS = {
    FieldType.TEXT: ["~", "="],
    FieldType.CODE: ["=", "!="],
    FieldType.NUMBER: [">", "<", ">=", "<=", "="],
    FieldType.DATE: [">", "<", ">=", "<=", "=", "!="],
    FieldType.BOOL: ["="],
    FieldType.BBOX: ["="],  # intersection
}

# Lookup: Which code list IDs correspond to which search field
# TODO changes here must be kept in sync with 'alma.codelisten.MAPPING_CODE_LISTS'!
CODELISTE_LOOKUP = {
    SearchField.STANDORTTYP: [CodeListe.StandortTyp],
    SearchField.BEURTEILUNG: [CodeListe.Beurteilung],
    SearchField.KANTON: [CodeListe.Kanton],
    SearchField.DEPONIETYP: [CodeListe.DeponieTyp],
    SearchField.STOFFKLASSE_STOFFKLASSE: [CodeListe.Stoffklasse],
    SearchField.STOFFGRUPPE_STOFFGRUPPE: [
        CodeListe.Stoffgruppen,
        CodeListe.StoffeKlasseI,
        CodeListe.StoffeKlasseII,
        CodeListe.StoffeKlasseIII,
        CodeListe.StoffeKlasseIV,
    ],
    SearchField.BRANCHE: [CodeListe.BrancheASW],
    SearchField.BRANCHE_NOGA: [CodeListe.BrancheNOGA],
    SearchField.SCHIESSANLAGE_TYP: [CodeListe.SchiessanlageTyp],
    SearchField.FIRMA_UNTERSUCHUNGSSTAND: [CodeListe.UntersuchungsStand],
    SearchField.FIRMA_BEURTEILUNG: [CodeListe.Beurteilung],
    SearchField.UNFALL_GENAUIGKEIT: [CodeListe.Genauigkeit],
    SearchField.UNFALLSTOFF_STOFFE: [CodeListe.Stoff],
    SearchField.GEWAESSERSCHUTZBEREICH: [CodeListe.Gewaesserschutzbereiche],
    SearchField.SCHUTZZONE: [CodeListe.Gewaesserschutzzonen],
    SearchField.KARSTGEBIET: [CodeListe.JaNeinUnbekannt],
    SearchField.DURCHLAESSIGKEIT: [CodeListe.Durchlaessigkeit],
    SearchField.RELATIVE_LAGE_GRUNDWASSER: [CodeListe.RelativeLageGrundwasser],
    SearchField.NUTZUNG_GW_ABSTROMBEREICH: [CodeListe.NutzungGrundwasserAbstrom],
    SearchField.ART_OBERFL_GEWAESSER: [CodeListe.GewaesserArt],
    SearchField.GEWAESSERBAU: [CodeListe.GewaesserBau],
    SearchField.RELATIVE_LAGE_OBERFL_GEWAESSER: [
        CodeListe.RelativeLageOberflaechenGewaesser
    ],
    SearchField.UMWELTSTOFF_GRUPPE: [CodeListe.UmweltStoffgruppe],
    SearchField.SPEZIFISCHER_STOFF: [
        CodeListe.StoffgruppeCKW,
        CodeListe.StoffgruppeSchwermetalle,
        CodeListe.StoffgruppeMKW,
        CodeListe.StoffgruppeBTEX,
        CodeListe.StoffgruppePAK,
        CodeListe.StoffgruppeDioxine,
        CodeListe.StoffgruppePCB,
        CodeListe.StoffgruppePFAS,
    ],
    SearchField.UMWELT: [CodeListe.GefaehrdeteUmweltbereiche],
    SearchField.UMWELTSTOFFE_BEURTEILUNG: [CodeListe.UmweltStoffBeurteilung],
    SearchField.NUTZUNGSZONE: [CodeListe.Flaechennutzung],
    SearchField.AKTUELLE_NUTZUNG: [
        CodeListe.FlaechennutzungWald,
        CodeListe.FlaechennutzungLandwirtschaft,
        CodeListe.FlaechennutzungSiedlungsgebiet,
    ],
    SearchField.GEFAEHRDETE_UMWELTBEREICHE: [CodeListe.Umweltbereich],
    SearchField.FESTGESTELLTE_EINWIRKUNGEN: [
        CodeListe.UmweltschaedenWasser,
        CodeListe.UmweltschaedenLuft,
        CodeListe.UmweltschaedenBoden,
    ],
    SearchField.VORKOMMNIS: [CodeListe.Einzelereignis],
    SearchField.BEARBEITUNGSSTAND: [CodeListe.Bearbeitungsstand],
    SearchField.UNTERSUCHUNGSSTAND: [CodeListe.UntersuchungsStand],
    SearchField.MASSNAHME: [CodeListe.Massnahme],
    SearchField.BEZIEHUNGSART_EIGENTUM: [CodeListe.BeziehungsartEigentum],
    SearchField.BEZIEHUNGSART_SACHBEARBEITUNG: [CodeListe.BeziehungsartSachbearbeitung],
    SearchField.BEZIEHUNGSART_SONSTIGE: [
        CodeListe.BeziehungsartSonstige,
    ],
    SearchField.PRIO_UNTERSUCHUNGSBEDARF: [CodeListe.PrioUntersuchung],
    SearchField.PRIO_SANIERUNGSBEDARF: [CodeListe.PrioSanierung],
    SearchField.SANIERUNGSZIEL: [CodeListe.Sanierungsziel],
    SearchField.TASK_BEZIEHUNGSART_EIGENTUM: [
        CodeListe.BeziehungsartEigentum,
    ],
    SearchField.TASK_BEZIEHUNGSART_SACHBEARBEITUNG: [
        CodeListe.BeziehungsartSachbearbeitung,
    ],
    SearchField.TASK_BEZIEHUNGSART_SONSTIGE: [
        CodeListe.BeziehungsartSonstige,
    ],
    SearchField.TASK_BEZIEHUNGSART_GESCHAEFTE: [
        CodeListe.BeziehungsartGeschaefte,
    ],
    SearchField.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND: [CodeListe.UntersuchungsStand],
    SearchField.KINDERSPIELPLATZ_BEURTEILUNG: [CodeListe.Beurteilung],
    SearchField.EIGENTUMSFORM: [CodeListe.Eigentumsform],
    SearchField.KINDERSPIELPLATZ_TYP: [CodeListe.KinderspielplatzGruenflaecheTyp],
    SearchField.ALTERSSTUFE_KINDER: [CodeListe.AltersstufeKinder],
    SearchField.BEHOERDE: [CodeListe.BehoerdenKuerzel],
    SearchField.PFAS_UNTERSUCHUNGSSTAND: [CodeListe.UntersuchungsStand],
    SearchField.PFAS_BEURTEILUNG: [CodeListe.Beurteilung],
    SearchField.PFAS_BRANCHE: [CodeListe.BranchePFAS],
    SearchField.PFAS_TYP: [CodeListe.PFASTyp],
    SearchField.PFAS_HALTIGE_LOESCHMITTEL: [CodeListe.LoeschmittelPFASHaltig],
    SearchField.PFAS_FREIE_LOESCHMITTEL: [CodeListe.LoeschmittelPFASFrei],
    SearchField.PFAS_LOESCHSCHAUM_EINSATZ: [CodeListe.LoeschschaumEinsatz],
    SearchField.PFAS_HAEUFIGKEIT_NUTZUNG: [
        CodeListe.HaeufigkeitNutzungHandfeuerloescher,
        CodeListe.HaeufigkeitNutzungBeimischer,
        CodeListe.HaeufigkeitNutzungTankloescher,
    ],
    SearchField.KTU: [CodeListe.KTU],
    SearchField.FLUGPLATZ_BEZEICHNUNG: [CodeListe.FlugplatzBezeichnung],
    # These currently exist only inside the search code, to treat these fields
    # like code values instead of strings.
    SearchField.TASK_TYP: [CodeListe.TaskTyp],
    SearchField.TASK_STATUS: [CodeListe.TaskStatus],
    SearchField.TASK_KATEGORIE: [CodeListe.TaskKategorie],
}


@unique
class JoinType(Enum):
    NONE = auto()
    STANDORTTYP = auto()
    GEMEINDE = auto()
    VFLZ_BEURTEILUNG = auto()
    BEURTEILUNG = auto()
    BASISBETRIEB = auto()
    STATUS_PUBLIKATION = auto()
    POOL = auto()
    OBJEKT = auto()
    VFLGEO = auto()
    KANTON = auto()
    BEMERKUNG_STANDORT = auto()
    DEPONIETYP = auto()
    ABLAGERUNG = auto()
    BEMERKUNG_ABLAGERUNG = auto()
    STOFFKLASSE = auto()
    KOMPARTIMENT_STOFFKLASSE = auto()
    KOMPARTIMENT_STOFFGRUPPE = auto()
    STOFFGRUPPE = auto()
    BRANCHE_ASW = auto()
    BRANCHE_NOGA = auto()
    SCHIESSANLAGE_TYP = auto()
    BETRIEB_BEURTEILUNG = auto()
    BETRIEB_UNTERSUCHUNGSTAND = auto()
    BEMERKUNG_BETRIEB = auto()
    BEGRUENDUNG_BEWERTUNG_BETRIEB = auto()
    UNFALL = auto()
    UNFALL_GENAUIGKEIT = auto()
    UNFALLSTOFF = auto()
    STOFF = auto()
    BEMERKUNG_UNFALL = auto()
    GWS_BEREICH = auto()
    GWS_ZONE = auto()
    KARSTGEBIET = auto()
    DURCHLAESSIGKEIT = auto()
    BEMERKUNG_UMWELT = auto()
    GW = auto()
    RELATIVE_LAGE_GW = auto()
    NUTZUNG_GW_ABSTROM = auto()
    OBERFL_GEWAESSER = auto()
    ART_OBERFL_GEWAESSER = auto()
    GEWAESSERBAU = auto()
    RELATIVE_LAGE_OGW = auto()
    UMWELTSTOFF = auto()
    UMWELTSTOFF_GRUPPE = auto()
    UMWELTSTOFF_STOFF = auto()
    UMWELTSTOFF_BEREICHE = auto()
    UMWELTSTOFF_BEURTEILUNG = auto()
    NUTZUNG_BODEN = auto()
    NUTZUNGS_ZONE = auto()
    AKTUELLE_NUTZUNG = auto()
    UMWELTBEREICH = auto()
    UMWELTSCHADEN = auto()
    UMWELTSCHADEN_SCHADEN = auto()
    BEMERKUNG_UMWELTSCHADEN = auto()
    EINZELEREIGNIS = auto()
    EINZELEREIGNIS_CODE = auto()
    BEMERKUNG_EINZELEREIGNIS = auto()
    BEGRUENDUNG_BEWERTUNG = auto()
    BEARBEITUNGSSTAND = auto()
    UNTERSUCHUNGSSTAND = auto()
    MASSNAHME = auto()
    MASSNAHME_CODE = auto()
    BEMERKUNG_MASSNAHME = auto()
    BETEILIGTER = auto()
    BETEILIGTER_SUBJ = auto()
    EIGENTUEMER_SUBJ = auto()
    BEZIEHUNGSART_EIGENTUM = auto()
    BEZIEHUNGSART_SACHBEARBEITUNG = auto()
    BEZIEHUNGSART_SONSTIGE = auto()
    PRIO_UNTERSUCHUNG = auto()
    BEGRUENDUNG_PRIO_UNTERSUCHUNG = auto()
    PRIO_SANIERUNG = auto()
    BEGRUENDUNG_PRIO_SANIERUNG = auto()
    VFLZ_SANIERUNGSZIEL = auto()
    SANIERUNGSZIEL = auto()
    BEMERKUNG_SANIERUNG = auto()
    VFLZ_VFL_ID = auto()
    TASK = auto()
    TASK_BETEILIGTE = auto()
    TASK_BETEILIGTE_SUBJ = auto()
    TASK_BEZIEHUNGSART_EIGENTUM = auto()
    TASK_BEZIEHUNGSART_SACHBEARBEITUNG = auto()
    TASK_BEZIEHUNGSART_SONSTIGE = auto()
    TASK_BEZIEHUNGSART_GESCHAEFTE = auto()
    TASK_TYP = auto()
    TASK_STATUS = auto()
    TASK_KATEGORIE = auto()
    BEMERKUNG_ADRESSE = auto()
    KINDERSPIELPLATZ = auto()
    KINDERSPIELPLATZ_BEMERKUNG = auto()
    KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND = auto()
    KINDERSPIELPLATZ_BEURTEILUNG = auto()
    EIGENTUMSFORM = auto()
    BELASTUNG_UEBER_SANIERUNGSWERT = auto()
    KINDERSPIELPLATZ_TYP = auto()
    ALTERSSTUFE_KINDER = auto()
    VOLLZUG = auto()
    BEHOERDE = auto()
    ALTERNATIVE_STANDORTNUMMER = auto()
    GRUNDBUCH_NUMMER = auto()
    BETEILIGTER_STANDORT = auto()
    PARZELLE = auto()
    PFAS = auto()
    BEMERKUNG_PFAS = auto()
    PFAS_UNTERSUCHUNGSSTAND = auto()
    PFAS_BEURTEILUNG = auto()
    PFAS_BRANCHE = auto()
    PFAS_TYP = auto()
    BEGRUENDUNG_BEWERTUNG_PFAS = auto()
    PFAS_HALTIGE_LOESCHMITTEL = auto()
    PFAS_FREIE_LOESCHMITTEL = auto()
    LOESCHSCHAUM_EINSATZ = auto()
    PFAS_LOESCHSCHAUM_EINSATZ = auto()
    PFAS_HAEUFIGKEIT_NUTZUNG = auto()
    FLUGPLATZ_BEZEICHNUNG = auto()
    KTU = auto()
    KTU_CODE = auto()
    FLUGPLATZ = auto()
    GRUNDBUCH_BEZEICHNUNG = auto()


@dataclass
class FieldConfig:
    type: FieldType
    expr: SQLColumnExpression[Any]
    join_type: JoinType
    category: FieldCategory


# If the underlying table can be joined in multiple ways,
# we need to use separate aliases for each kind.

standorttyp_code_alias = aliased(codes.StandortTyp, name="standorttyp")
beurteilung_code_alias = aliased(codes.Beurteilung, name="beurteilung")
kanton_code_alias = aliased(codes.Kanton, name="kanton")
deponietyp_code_alias = aliased(codes.DeponieTyp, name="deponietyp")
stoffklasse_code_alias = aliased(codes.Stoffklasse, name="stoffklasse")
stoffgruppe_code_alias = aliased(codes.StoffgruppeVariante, name="stoffgruppe")
branche_asw_code_alias = aliased(codes.BrancheASW, name="branche_asw")
branche_noga_code_alias = aliased(codes.BrancheNOGA, name="branche_noga")
schiessanlage_typ_code_alias = aliased(codes.SchiessanlageTyp, name="schiessanlage_typ")
betrieb_beurteilung_code_alias = aliased(codes.Beurteilung, name="betrieb_beurteilung")
betrieb_untersuchungsstand_code_alias = aliased(
    codes.UntersuchungsStand, name="betrieb_untersuchungsstand"
)
kinderspielplatz_untersuchungsstand_code_alias = aliased(
    codes.UntersuchungsStand, name="kinderspielplatz_untersuchungsstand"
)
kinderspielplatz_beurteilung_code_alias = aliased(
    codes.Beurteilung, name="kinderspielplatz_beurteilung"
)
kinderspielplatz_typ_code_alias = aliased(
    codes.KinderspielplatzGruenflaecheTyp, name="kinderspielplatz_typ"
)

eigentumsform_code_alias = aliased(codes.Eigentumsform, name="eigentumsform")
eigentumsform_translation_alias = aliased(
    Translation, name="eigentumsform_translation_alias"
)
altersstufe_kinder_code_alias = aliased(
    codes.AltersstufeKinder, name="altersstufe_kinder"
)
altersstufe_kinder_translation_alias = aliased(
    Translation, name="altersstufe_kinder_translation_alias"
)
stoff_code_alias = aliased(codes.Stoff, name="stoff")
unfall_genauigkeit_code_alias = aliased(codes.Genauigkeit, name="unfall_genauigkeit")
gws_bereich_code_alias = aliased(codes.Gewaesserschutzbereich, name="gws_bereich")
gws_zone_code_alias = aliased(codes.Gewaesserschutzzone, name="gws_zone")
karstgebiet_code_alias = aliased(codes.JaNeinUnbekannt, name="karstgebiet")
durchlaessigkeit_code_alias = aliased(codes.Durchlaessigkeit, name="durchlaessigkeit")
relative_lage_gw_code_alias = aliased(
    codes.RelativeLageGrundwasser, name="relative_lage_gw"
)
nutzung_gw_abstrom_code_alias = aliased(
    codes.NutzungGrundwasserAbstrom, name="nutzung_gw_abstrom"
)
gewaesser_art_code_alias = aliased(codes.GewaesserArt, name="gewaesser_art")
gewaesser_bau_code_alias = aliased(codes.GewaesserBau, name="gewaesser_bau")
relative_lage_ogw_code_alias = aliased(
    codes.RelativeLageOberflaechenGewaesser, name="relative_lage_ogw"
)
umweltstoff_gruppe_code_alias = aliased(
    codes.UmweltStoffgruppe, name="umweltstoff_gruppe"
)
umweltstoff_stoff_code_alias = aliased(
    codes.UmweltStoffgruppeVariante, name="umweltstoff_stoff"
)
umweltstoff_bereiche_code_alias = aliased(
    codes.GefaehrdeteUmweltbereiche, name="umweltstoff_bereiche"
)
umweltstoff_beurteilung_code_alias = aliased(
    codes.UmweltStoffBeurteilung, name="umweltstoff_beurteilung"
)
nutzungsart_code_alias = aliased(codes.Flaechennutzung, name="nutzungsart")
aktuelle_nutzung_code_alias = aliased(
    codes.FlaechennutzungVariante, name="aktuelle_nutzung"
)
umweltbereich_code_alias = aliased(codes.Umweltbereich, name="umweltbereich")
umweltschaeden_code_alias = aliased(codes.UmweltschaedenVariante, name="umweltschaeden")
einzelereignis_code_alias = aliased(codes.Einzelereignis, name="einzelereignis")
bearbeitungsstand_code_alias = aliased(
    codes.Bearbeitungsstand, name="bearbeitungsstand"
)
untersuchungsstand_code_alias = aliased(
    codes.UntersuchungsStand, name="untersuchungsstand"
)
massnahme_code_alias = aliased(codes.Massnahme, name="massnahme")
beziehungsart_eigentum_code_alias = aliased(
    codes.BeziehungsartEigentum, name="beziehungsart_eigentum"
)
beziehungsart_sachbearbeitung_code_alias = aliased(
    codes.BeziehungsartSachbearbeitung, name="beziehungsart_sachbearbeitung"
)
beziehungsart_sonstige_code_alias = aliased(
    codes.BeziehungsartSonstige, name="beziehungsart_sonstige"
)
prio_untersuchung_code_alias = aliased(codes.PrioUntersuchung, name="prio_untersuchung")
prio_sanierung_code_alias = aliased(codes.PrioSanierung, name="prio_sanierung")
sanierungsziel_code_alias = aliased(codes.Sanierungsziel, name="sanierungsziel")
task_beziehungsart_eigentum_code_alias = aliased(
    codes.BeziehungsartEigentum, name="task_beziehungsart_eigentum"
)
task_beziehungsart_sachbearbeitung_code_alias = aliased(
    codes.BeziehungsartSachbearbeitung, name="task_beziehungsart_sachbearbeitung"
)
task_beziehungsart_sonstige_code_alias = aliased(
    codes.BeziehungsartSonstige, name="task_beziehungsart_sonstige"
)
task_beziehungsart_geschaefte_code_alias = aliased(
    codes.BeziehungsartGeschaefte, name="task_beziehungsart_geschaefte"
)
task_typ_code_alias = aliased(codes.TaskTyp, name="task_typ")
task_status_code_alias = aliased(codes.TaskStatus, name="task_status")
pfas_untersuchungsstand_code_alias = aliased(
    codes.UntersuchungsStand, name="pfas_untersuchungsstand"
)
pfas_beurteilung_code_alias = aliased(codes.Beurteilung, name="pfas_beurteilung")
pfas_branche_code_alias = aliased(codes.BranchePFAS, name="pfas_branche")
pfas_typ_code_alias = aliased(codes.PFASTyp, name="pfas_typ")
pfas_haltige_loeschmittel_code_alias = aliased(
    codes.LoeschmittelPFASHaltig, name="pfas_haltige_loeschmittel"
)
pfas_freie_loeschmittel_code_alias = aliased(
    codes.LoeschmittelPFASFrei, name="pfas_freie_loeschmittel"
)
loeschschaum_einsatz_code_alias = aliased(
    codes.LoeschschaumEinsatz, name="loeschschaum_einsatz"
)
pfas_haeufigkeit_nutzung_code_alias = aliased(
    codes.HaeufigkeitNutzungVariante, name="pfas_haeufigkeit_nutzung"
)
flugplatz_bezeichnung_code_alias = aliased(
    codes.FlugplatzBezeichnung, name="flugplatz_bezeichnung"
)

kinderspielplatz_typ_translation_alias = aliased(
    Translation, name="kinderspielplatz_typ_translation_alias"
)
standorttyp_translation_alias = aliased(Translation, name="standorttyp_translation")
beurteilung_translation_alias = aliased(Translation, name="beurteilung_translation")
deponietyp_translation_alias = aliased(Translation, name="deponietyp_translation")
stoffklasse_translation_alias = aliased(Translation, name="stoffklasse_translation")
stoffgruppe_translation_alias = aliased(Translation, name="stoffgruppe_translation")
branche_asw_translation_alias = aliased(Translation, name="branche_asw_translation")
branche_noga_translation_alias = aliased(Translation, name="branche_noga_translation")
schiessanlage_typ_translation_alias = aliased(
    Translation, name="schiessanlage_typ_translation"
)
betrieb_beurteilung_translation_alias = aliased(
    Translation, name="betrieb_beurteilung_translation"
)
kinderspielplatz_beurteilung_translation_alias = aliased(
    Translation, name="kinderspielplatz_beurteilung_translation"
)
kinderspielplatz_untersuchungsstand_translation_alias = aliased(
    Translation, name="kinderspielplatz_untersuchungsstand_translation"
)
betrieb_untersuchungsstand_translation_alias = aliased(
    Translation, name="betrieb_untersuchungsstand_translation"
)
stoff_translation_alias = aliased(Translation, name="stoff_translation")
unfall_genauigkeit_translation_alias = aliased(
    Translation, name="unfall_genauigket_translation"
)
gws_bereich_translation_alias = aliased(Translation, name="gws_bereich_translation")
gws_zone_translation_alias = aliased(Translation, name="gws_zone_translation")
karstgebiet_translation_alias = aliased(Translation, name="karstgebiet_translation")
durchlaessigkeit_translation_alias = aliased(
    Translation, name="durchlaessigkeit_translation"
)
relative_lage_gw_translation_alias = aliased(
    Translation, name="relative_lage_gw_translation"
)
nutzung_gw_abstrom_translation_alias = aliased(
    Translation, name="nutzung_gw_abstrom_translation"
)
gewaesser_art_translation_alias = aliased(Translation, name="gewaesser_art_translation")
gewaesser_bau_translation_alias = aliased(Translation, name="gewaesser_bau_translation")
relative_lage_ogw_translation_alias = aliased(
    Translation, name="relative_lage_ogw_translation"
)
umweltstoff_gruppe_translation_alias = aliased(
    Translation, name="umweltstoff_gruppe_translation"
)
umweltstoff_stoff_translation_alias = aliased(
    Translation, name="umweltstoff_stoff_translation"
)
umweltstoff_bereiche_translation_alias = aliased(
    Translation, name="umweltstoff_bereiche_translation"
)
umweltstoff_beurteilung_translation_alias = aliased(
    Translation, name="umweltstoff_beurteilung_translation"
)
nutzungsart_translation_alias = aliased(Translation, name="nutzungsart_translation")
aktuelle_nutzung_translation_alias = aliased(
    Translation, name="aktuelle_nutzung_translation"
)
umweltbereich_translation_alias = aliased(Translation, name="umweltbereich_translation")
umweltschaeden_translation_alias = aliased(
    Translation, name="umweltschaeden_translation"
)
einzelereignis_translation_alias = aliased(
    Translation, name="einzelereignis_translation"
)
bearbeitungsstand_translation_alias = aliased(
    Translation, name="bearbeitungsstand_translation"
)
untersuchungsstand_translation_alias = aliased(
    Translation, name="untersuchungsstand_translation"
)
massnahme_translation_alias = aliased(Translation, name="massnahme_translation")
beziehungsart_eigentum_translation_alias = aliased(
    Translation, name="beziehungsart_eigentum_translation"
)
beziehungsart_sachbearbeitung_translation_alias = aliased(
    Translation, name="beziehungsart_sachbearbeitung_translation"
)
beziehungsart_sonstige_translation_alias = aliased(
    Translation, name="beziehungsart_sonstige_translation"
)
prio_untersuchung_translation_alias = aliased(
    Translation, name="prio_untersuchung_translation"
)
prio_sanierung_translation_alias = aliased(
    Translation, name="prio_sanierung_translation"
)
sanierungsziel_translation_alias = aliased(
    Translation, name="sanierungsziel_translation"
)
task_beziehungsart_eigentum_translation_alias = aliased(
    Translation, name="task_beziehungsart_eigentum_translation"
)
task_beziehungsart_sachbearbeitung_translation_alias = aliased(
    Translation, name="task_beziehungsart_sachbearbeitung_translation"
)
task_beziehungsart_sonstige_translation_alias = aliased(
    Translation, name="task_beziehungsart_sonstige_translation"
)
task_beziehungsart_geschaefte_translation_alias = aliased(
    Translation, name="task_beziehungsart_geschaefte_translation"
)
task_typ_translation_alias = aliased(Translation, name="task_typ_translation")
task_status_translation_alias = aliased(Translation, name="task_status_translation")
pfas_untersuchungsstand_translation_alias = aliased(
    Translation, name="pfas_untersuchungsstand_translation"
)
pfas_beurteilung_translation_alias = aliased(
    Translation, name="pfas_beurteilung_translation"
)
pfas_branche_translation_alias = aliased(Translation, name="pfas_branche_translation")
pfas_typ_translation_alias = aliased(Translation, name="pfas_typ_translation")
pfas_haltige_loeschmittel_translation_alias = aliased(
    Translation, name="pfas_haltige_loeschmittel_translation"
)
pfas_freie_loeschmittel_translation_alias = aliased(
    Translation, name="pfas_freie_loeschmittel_translation"
)
loeschschaum_einsatz_translation_alias = aliased(
    Translation, name="loeschschaum_einsatz_translation"
)
pfas_haeufigkeit_nutzung_translation_alias = aliased(
    Translation, name="pfas_haeufigkeit_nutzung_translation"
)
flugplatz_bezeichnung_translation_alias = aliased(
    Translation, name="flugplatz_bezeichnung_translation"
)


subjekt_beteiligter_alias = aliased(Subjekt, name="beteiligter")
subjekt_eigentuemer_alias = aliased(Subjekt, name="eigentuemer")
bet_eigentuemer_alias = aliased(Beteiligter, name="bet_eigentuemer")
beteiligter_standort_alias = aliased(BeteiligterStandort, name="beteiligter_standort")

bemerkung_subjekt_alias = aliased(BemerkungSubjekt, name="bemerkung_subjekt")
bemerkung_standort_alias = aliased(BemerkungStandort, name="bemerkung_standort")
bemerkung_ablagerung_alias = aliased(BemerkungAblagerung, name="bemerkung_ablagerung")
bemerkung_betrieb_alias = aliased(BemerkungBetrieb, name="bemerkung_betrieb")
begruendung_bew_betrieb_alias = aliased(
    BegruendungBewertungBetrieb, name="begruendung_bew_betrieb"
)
bemerkung_unfall_alias = aliased(BemerkungUnfall, name="bemerkung_unfall")
bemerkung_umwelt_alias = aliased(BemerkungUmwelt, name="bemerkung_umwelt")
bemerkung_umweltschaden_alias = aliased(
    BemerkungUmweltschaden, name="bemerkung_umweltschaden"
)
bemerkung_einzelereignis_alias = aliased(
    BemerkungEinzelereignis, name="bemerkung_einzelereignis"
)
begruendung_bewertung_alias = aliased(
    BegruendungBewertung, name="begruendung_bewertung"
)
bemerkung_massnahme_alias = aliased(BemerkungMassnahme, name="bemerkung_massnahme")
begruendung_prio_untersuchung_alias = aliased(
    BegruendungPrioUntersuchungsbedarf, name="begruendung_prio_untersuchung"
)
begruendung_prio_sanierung_alias = aliased(
    BegruendungPrioSanierungsbedarf, name="begruendung_prio_sanierung"
)
bemerkung_sanierung_alias = aliased(BemerkungSanierung, name="bemerkung_sanierung")
bemerkung_pfas_alias = aliased(BemerkungPFAS, name="bemerkung_pfas")
bemerkung_kinderspielplatz_alias = aliased(
    BemerkungKinderspielplatzGruenflaeche, name="bemerkung_kinderspielplatz"
)

subjekt_beteiligter_geschaeft_alias = aliased(
    Subjekt, name="subjekt_beteiligter_geschaeft"
)
vflz_vfl_id_alias = aliased(Vflz, name="vflz_vfl_id")
task_kategorie_translation_alias = aliased(
    Translation, name="task_kategorie_translation"
)
task_kategorie_alias = aliased(codes.TaskKategorie, name="task_kategorie_alias")
behoerde_code_alias = aliased(codes.BehoerdenKuerzel, name="behoerde_code")
behoerde_translation_alias = aliased(Translation, name="behoerde_translation")
vollzug_alias = aliased(Vollzug, name="vollzug")
begruendung_bew_pfas_alias = aliased(
    BegruendungBewertungPFAS, name="begruendung_bew_pfas"
)
ktu_code_alias = aliased(codes.KTU, name="ktu_code")
ktu_translation_alias = aliased(Translation, name="ktu_translation")

#
# Global list of available search fields and their configuration
#
FIELD_CONFIG: dict[SearchField, FieldConfig] = {
    SearchField.VFLZ_ID: FieldConfig(
        FieldType.NUMBER,
        Vflz.vflz_id,
        JoinType.NONE,
        FieldCategory.STANDORT,
    ),
    SearchField.STANDORTNUMMER: FieldConfig(
        FieldType.TEXT,
        Vflz.combined_id,
        JoinType.NONE,
        FieldCategory.STANDORT,
    ),
    SearchField.STANDORTTYP: FieldConfig(
        FieldType.CODE,
        standorttyp_code_alias.search_key(),
        JoinType.STANDORTTYP,
        FieldCategory.STANDORT,
    ),
    SearchField.BEZEICHNUNG: FieldConfig(
        FieldType.TEXT,
        Vflz.bezeichnung,
        JoinType.NONE,
        FieldCategory.STANDORT,
    ),
    SearchField.STRASSE: FieldConfig(
        FieldType.TEXT,
        Vflz.strasse,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.ORT: FieldConfig(
        FieldType.TEXT,
        Vflz.ort,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.GEMEINDE: FieldConfig(
        FieldType.TEXT,
        Gemeinde.gemeinde,
        JoinType.GEMEINDE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.BFS_NR: FieldConfig(
        FieldType.NUMBER,
        Vflz.h_gem_id,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.FIRMA_NAME: FieldConfig(
        FieldType.TEXT,
        BasisBetrieb.firma_name,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_STRASSE: FieldConfig(
        FieldType.TEXT,
        BasisBetrieb.firma_strasse,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.POOL: FieldConfig(
        FieldType.TEXT,
        Pool.bezeichnung,
        JoinType.POOL,
        FieldCategory.STANDORT,
    ),
    SearchField.ERFASSUNG: FieldConfig(
        FieldType.DATE,
        func.date(Objekt.erfassungs_datum),
        JoinType.OBJEKT,
        FieldCategory.STANDORT,
    ),
    SearchField.ZEITRAUM_VON: FieldConfig(
        FieldType.DATE,
        Vflz.zeitraum_von,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.ZEITRAUM_BIS: FieldConfig(
        FieldType.DATE,
        Vflz.zeitraum_bis,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.PLZ: FieldConfig(
        FieldType.NUMBER,
        Vflz.postleitzahl,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.FLAECHE: FieldConfig(
        FieldType.NUMBER,
        VflGeo.flaeche,
        JoinType.VFLGEO,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.FLURNAME: FieldConfig(
        FieldType.TEXT,
        Vflz.flurname,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.X_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_X(Vflz.zentroid),
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.Y_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_Y(Vflz.zentroid),
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.SPRACHE: FieldConfig(
        FieldType.TEXT,
        Vflz.lang,
        JoinType.NONE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.KANTON: FieldConfig(
        FieldType.CODE,
        kanton_code_alias.search_key(),
        JoinType.KANTON,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.GRUNDDATEN_BEMERKUNGEN: FieldConfig(
        FieldType.TEXT,
        bemerkung_standort_alias.bem,
        JoinType.BEMERKUNG_STANDORT,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.IN_BETRIEB: FieldConfig(
        FieldType.BOOL,
        Vflz.in_betrieb,
        JoinType.NONE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.NACHSORGE: FieldConfig(
        FieldType.BOOL,
        Vflz.nachsorge,
        JoinType.NONE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.DEPONIETYP: FieldConfig(
        FieldType.CODE,
        deponietyp_code_alias.search_key(),
        JoinType.DEPONIETYP,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.KOMPARTIMENT_VON: FieldConfig(
        FieldType.DATE,
        Ablagerung.zeitraum_von,
        JoinType.ABLAGERUNG,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.KOMPARTIMENT_BIS: FieldConfig(
        FieldType.DATE,
        Ablagerung.zeitraum_bis,
        JoinType.ABLAGERUNG,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.KOMPARTIMENT_BEMERKUNGEN: FieldConfig(
        FieldType.TEXT,
        bemerkung_ablagerung_alias.bem,
        JoinType.BEMERKUNG_ABLAGERUNG,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFKLASSE_STOFFKLASSE: FieldConfig(
        FieldType.CODE,
        stoffklasse_code_alias.search_key(),
        JoinType.STOFFKLASSE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFKLASSE_TEILVOLUMEN: FieldConfig(
        FieldType.NUMBER,
        KompartimentStoffklasse.teilvol,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.KOMPARTIMENT_VOLUMEN: FieldConfig(
        FieldType.NUMBER,
        Ablagerung.vol_kompartiment,
        JoinType.ABLAGERUNG,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.KOMPARTIMENT_TIEFE: FieldConfig(
        FieldType.TEXT,
        Ablagerung.tiefe,
        JoinType.ABLAGERUNG,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFKLASSE_VON: FieldConfig(
        FieldType.DATE,
        KompartimentStoffklasse.zeitraum_von,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFKLASSE_BIS: FieldConfig(
        FieldType.DATE,
        KompartimentStoffklasse.zeitraum_bis,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFGRUPPE_STOFFGRUPPE: FieldConfig(
        FieldType.CODE,
        stoffgruppe_code_alias.search_key(),
        JoinType.STOFFGRUPPE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.STOFFGRUPPE_TEILVOLUMEN: FieldConfig(
        FieldType.NUMBER,
        KompartimentStoffgruppe.teilvol,
        JoinType.KOMPARTIMENT_STOFFGRUPPE,
        FieldCategory.ABLAGERUNGEN,
    ),
    SearchField.EVA_NUMMER: FieldConfig(
        FieldType.TEXT,
        BasisBetrieb.eva,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_PLZ: FieldConfig(
        FieldType.NUMBER,
        BasisBetrieb.firma_plz,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_ORT: FieldConfig(
        FieldType.TEXT,
        BasisBetrieb.firma_ort,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_VON: FieldConfig(
        FieldType.DATE,
        BasisBetrieb.zeitraum_von,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_BIS: FieldConfig(
        FieldType.DATE,
        BasisBetrieb.zeitraum_bis,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.BRANCHE: FieldConfig(
        FieldType.CODE,
        branche_asw_code_alias.search_key(),
        JoinType.BRANCHE_ASW,
        FieldCategory.BETRIEBE,
    ),
    SearchField.BRANCHE_NOGA: FieldConfig(
        FieldType.CODE,
        branche_noga_code_alias.search_key(),
        JoinType.BRANCHE_NOGA,
        FieldCategory.BETRIEBE,
    ),
    SearchField.SCHIESSANLAGE_TYP: FieldConfig(
        FieldType.CODE,
        schiessanlage_typ_code_alias.search_key(),
        JoinType.SCHIESSANLAGE_TYP,
        FieldCategory.BETRIEBE,
    ),
    SearchField.KUGELFANG_VORHANDEN: FieldConfig(
        FieldType.BOOL,
        # Workaround for https://github.com/sqlalchemy/sqlalchemy/issues/12395
        # See https://github.com/sqlalchemy/sqlalchemy/discussions/12394#discussioncomment-12389761
        Schiessanlage.__table__.c.intb_schiessanlage_hat_kugelfang,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.SCHEIBENZAHL: FieldConfig(
        FieldType.NUMBER,
        # Workaround for https://github.com/sqlalchemy/sqlalchemy/issues/12395
        # See https://github.com/sqlalchemy/sqlalchemy/discussions/12394#discussioncomment-12389761
        Schiessanlage.__table__.c.intb_schiessanlage_scheibenzahl,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.SCHUSSANZAHL: FieldConfig(
        FieldType.NUMBER,
        # Workaround for https://github.com/sqlalchemy/sqlalchemy/issues/12395
        # See https://github.com/sqlalchemy/sqlalchemy/discussions/12394#discussioncomment-12389761
        Schiessanlage.__table__.c.intb_schiessanlage_schusszahl,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.BETRIEBSGROESSE: FieldConfig(
        FieldType.NUMBER,
        BasisBetrieb.groesse,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_KATASTERRELEVANZ: FieldConfig(
        FieldType.BOOL,
        BasisBetrieb.relevant,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.MOBILE_STOFFE: FieldConfig(
        FieldType.BOOL,
        BasisBetrieb.mobile_stoffe,
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_UNTERSUCHUNGSSTAND: FieldConfig(
        FieldType.CODE,
        betrieb_untersuchungsstand_code_alias.search_key(),
        JoinType.BETRIEB_UNTERSUCHUNGSTAND,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_BEURTEILUNG: FieldConfig(
        FieldType.CODE,
        betrieb_beurteilung_code_alias.search_key(),
        JoinType.BETRIEB_BEURTEILUNG,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_BEMERKUNGEN: FieldConfig(
        FieldType.TEXT,
        bemerkung_betrieb_alias.bem,
        JoinType.BEMERKUNG_BETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.BEGRUENDUNG_BEWERTUNG_BETRIEB: FieldConfig(
        FieldType.TEXT,
        begruendung_bew_betrieb_alias.bem,
        JoinType.BEGRUENDUNG_BEWERTUNG_BETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_X_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_X(BasisBetrieb.zentroid),
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.FIRMA_Y_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_Y(BasisBetrieb.zentroid),
        JoinType.BASISBETRIEB,
        FieldCategory.BETRIEBE,
    ),
    SearchField.UNFALL_NAME: FieldConfig(
        FieldType.TEXT,
        Unfall.name,
        JoinType.UNFALL,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALL_ZEITPUNKT: FieldConfig(
        FieldType.DATE,
        Unfall.zeitpunkt,
        JoinType.UNFALL,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALL_GENAUIGKEIT: FieldConfig(
        FieldType.CODE,
        unfall_genauigkeit_code_alias.search_key(),
        JoinType.UNFALL_GENAUIGKEIT,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALLSTOFF_STOFFE: FieldConfig(
        FieldType.CODE,
        stoff_code_alias.search_key(),
        JoinType.STOFF,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALLSTOFF_AUSGELAUFEN: FieldConfig(
        FieldType.NUMBER,
        Unfallstoff.ausgelaufen,
        JoinType.UNFALLSTOFF,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALLSTOFF_ZURUECKGEW: FieldConfig(
        FieldType.NUMBER,
        Unfallstoff.zurueckgewonnen,
        JoinType.UNFALLSTOFF,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALLSTOFF_RESTMENGE: FieldConfig(
        FieldType.NUMBER,
        Unfallstoff.stoffmng,
        JoinType.UNFALLSTOFF,
        FieldCategory.UNFAELLE,
    ),
    SearchField.UNFALL_BEMERKUNG: FieldConfig(
        FieldType.TEXT,
        bemerkung_unfall_alias.bem,
        JoinType.BEMERKUNG_UNFALL,
        FieldCategory.UNFAELLE,
    ),
    SearchField.GEWAESSERSCHUTZBEREICH: FieldConfig(
        FieldType.CODE,
        gws_bereich_code_alias.search_key(),
        JoinType.GWS_BEREICH,
        FieldCategory.NATUERLICHES_UMFELD,
    ),
    SearchField.SCHUTZZONE: FieldConfig(
        FieldType.CODE,
        gws_zone_code_alias.search_key(),
        JoinType.GWS_ZONE,
        FieldCategory.NATUERLICHES_UMFELD,
    ),
    SearchField.KARSTGEBIET: FieldConfig(
        FieldType.CODE,
        karstgebiet_code_alias.search_key(),
        JoinType.KARSTGEBIET,
        FieldCategory.NATUERLICHES_UMFELD,
    ),
    SearchField.DURCHLAESSIGKEIT: FieldConfig(
        FieldType.CODE,
        durchlaessigkeit_code_alias.search_key(),
        JoinType.DURCHLAESSIGKEIT,
        FieldCategory.NATUERLICHES_UMFELD,
    ),
    SearchField.UMWELT_BEMERKUNGEN: FieldConfig(
        FieldType.TEXT,
        bemerkung_umwelt_alias.bem,
        JoinType.BEMERKUNG_UMWELT,
        FieldCategory.NATUERLICHES_UMFELD,
    ),
    SearchField.RELATIVE_LAGE_GRUNDWASSER: FieldConfig(
        FieldType.CODE,
        relative_lage_gw_code_alias.search_key(),
        JoinType.RELATIVE_LAGE_GW,
        FieldCategory.GRUNDWASSER,
    ),
    SearchField.FLURABSTAND: FieldConfig(
        FieldType.NUMBER,
        Grundwasser.flurabstand,
        JoinType.GW,
        FieldCategory.GRUNDWASSER,
    ),
    SearchField.NUTZUNG_GW_ABSTROMBEREICH: FieldConfig(
        FieldType.CODE,
        nutzung_gw_abstrom_code_alias.search_key(),
        JoinType.NUTZUNG_GW_ABSTROM,
        FieldCategory.GRUNDWASSER,
    ),
    SearchField.DISTANZ_NUTZUNG_GW_ABSTROMBEREICH: FieldConfig(
        FieldType.NUMBER,
        Grundwasser.distanz,
        JoinType.GW,
        FieldCategory.GRUNDWASSER,
    ),
    SearchField.NAME_OBERFL_GEWAESSER: FieldConfig(
        FieldType.TEXT,
        OberflaechenGewaesser.name,
        JoinType.OBERFL_GEWAESSER,
        FieldCategory.OBERFLAECHENGEWAESSER,
    ),
    SearchField.DISTANZ_OBERFL_GEWAESSER: FieldConfig(
        FieldType.NUMBER,
        OberflaechenGewaesser.distanz,
        JoinType.OBERFL_GEWAESSER,
        FieldCategory.OBERFLAECHENGEWAESSER,
    ),
    SearchField.ART_OBERFL_GEWAESSER: FieldConfig(
        FieldType.CODE,
        gewaesser_art_code_alias.search_key(),
        JoinType.ART_OBERFL_GEWAESSER,
        FieldCategory.OBERFLAECHENGEWAESSER,
    ),
    SearchField.GEWAESSERBAU: FieldConfig(
        FieldType.CODE,
        gewaesser_bau_code_alias.search_key(),
        JoinType.GEWAESSERBAU,
        FieldCategory.OBERFLAECHENGEWAESSER,
    ),
    SearchField.RELATIVE_LAGE_OBERFL_GEWAESSER: FieldConfig(
        FieldType.CODE,
        relative_lage_ogw_code_alias.search_key(),
        JoinType.RELATIVE_LAGE_OGW,
        FieldCategory.OBERFLAECHENGEWAESSER,
    ),
    SearchField.UMWELTSTOFF_GRUPPE: FieldConfig(
        FieldType.CODE,
        umweltstoff_gruppe_code_alias.search_key(),
        JoinType.UMWELTSTOFF_GRUPPE,
        FieldCategory.UMWELTSTOFFE,
    ),
    SearchField.SPEZIFISCHER_STOFF: FieldConfig(
        FieldType.CODE,
        umweltstoff_stoff_code_alias.search_key(),
        JoinType.UMWELTSTOFF_STOFF,
        FieldCategory.UMWELTSTOFFE,
    ),
    SearchField.UMWELT: FieldConfig(
        FieldType.CODE,
        umweltstoff_bereiche_code_alias.search_key(),
        JoinType.UMWELTSTOFF_BEREICHE,
        FieldCategory.UMWELTSTOFFE,
    ),
    SearchField.UMWELTSTOFFE_BEURTEILUNG: FieldConfig(
        FieldType.CODE,
        umweltstoff_beurteilung_code_alias.search_key(),
        JoinType.UMWELTSTOFF_BEURTEILUNG,
        FieldCategory.UMWELTSTOFFE,
    ),
    SearchField.NUTZUNGSZONE: FieldConfig(
        FieldType.CODE,
        nutzungsart_code_alias.search_key(),
        JoinType.NUTZUNGS_ZONE,
        FieldCategory.NUTZUNGEN_GELAENDE,
    ),
    SearchField.AKTUELLE_NUTZUNG: FieldConfig(
        FieldType.CODE,
        aktuelle_nutzung_code_alias.search_key(),
        JoinType.AKTUELLE_NUTZUNG,
        FieldCategory.NUTZUNGEN_GELAENDE,
    ),
    SearchField.GEFAEHRDETE_UMWELTBEREICHE: FieldConfig(
        FieldType.CODE,
        umweltbereich_code_alias.search_key(),
        JoinType.UMWELTBEREICH,
        FieldCategory.UMWELTEINWIRKUNGEN,
    ),
    SearchField.FESTGESTELLTE_EINWIRKUNGEN: FieldConfig(
        FieldType.CODE,
        umweltschaeden_code_alias.search_key(),
        JoinType.UMWELTSCHADEN_SCHADEN,
        FieldCategory.UMWELTEINWIRKUNGEN,
    ),
    SearchField.UMWELTSCHADEN_BEMERKUNG: FieldConfig(
        FieldType.TEXT,
        bemerkung_umweltschaden_alias.bem,
        JoinType.BEMERKUNG_UMWELTSCHADEN,
        FieldCategory.UMWELTEINWIRKUNGEN,
    ),
    SearchField.VORKOMMNIS_DATUM: FieldConfig(
        FieldType.DATE,
        Einzelereignis.datum,
        JoinType.EINZELEREIGNIS,
        FieldCategory.VORKOMMNISSE,
    ),
    SearchField.VORKOMMNIS: FieldConfig(
        FieldType.CODE,
        einzelereignis_code_alias.search_key(),
        JoinType.EINZELEREIGNIS_CODE,
        FieldCategory.VORKOMMNISSE,
    ),
    SearchField.BEMERKUNG_EINZELEREIGNIS: FieldConfig(
        FieldType.TEXT,
        bemerkung_einzelereignis_alias.bem,
        JoinType.BEMERKUNG_EINZELEREIGNIS,
        FieldCategory.VORKOMMNISSE,
    ),
    SearchField.BEURTEILUNG: FieldConfig(
        FieldType.CODE,
        beurteilung_code_alias.search_key(),
        JoinType.BEURTEILUNG,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.BEGRUENDUNG_BEURTEILUNG: FieldConfig(
        FieldType.TEXT,
        begruendung_bewertung_alias.bem,
        JoinType.BEGRUENDUNG_BEWERTUNG,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.BEARBEITUNGSSTAND: FieldConfig(
        FieldType.CODE,
        bearbeitungsstand_code_alias.search_key(),
        JoinType.BEARBEITUNGSSTAND,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.UNTERSUCHUNGSSTAND: FieldConfig(
        FieldType.CODE,
        untersuchungsstand_code_alias.search_key(),
        JoinType.UNTERSUCHUNGSSTAND,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.RECHTSKRAEFTIG: FieldConfig(
        FieldType.BOOL,
        Vflz.rechtskraft,
        JoinType.NONE,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.DATUM_ERSTEINTRAG: FieldConfig(
        FieldType.DATE,
        Vflz.dat_rechtskraft,
        JoinType.NONE,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.PUBLIZIERT: FieldConfig(
        FieldType.BOOL,
        Vflz.publizieren,
        JoinType.NONE,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.DATUM_PUBLIKATION_KBS: FieldConfig(
        FieldType.DATE,
        Vflz.dat_publizieren,
        JoinType.NONE,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.AKTUELLSTE_PUBLIKATION: FieldConfig(
        FieldType.BOOL,
        VflzStatusPublikation.belastet,
        JoinType.STATUS_PUBLIKATION,
        FieldCategory.BEURTEILUNG,
    ),
    SearchField.MASSNAHME: FieldConfig(
        FieldType.CODE,
        massnahme_code_alias.search_key(),
        JoinType.MASSNAHME_CODE,
        FieldCategory.MASSNAHMEN,
    ),
    SearchField.MASSNAHME_ANGEORDNET_AM: FieldConfig(
        FieldType.DATE,
        Massnahme.ang_massnahme,
        JoinType.MASSNAHME,
        FieldCategory.MASSNAHMEN,
    ),
    SearchField.MASSNAHME_ERLEDIGT_AM: FieldConfig(
        FieldType.DATE,
        Massnahme.dat_massnahme,
        JoinType.MASSNAHME,
        FieldCategory.MASSNAHMEN,
    ),
    SearchField.MASSNAHME_BEMERKUNG: FieldConfig(
        FieldType.TEXT,
        bemerkung_massnahme_alias.bem,
        JoinType.BEMERKUNG_MASSNAHME,
        FieldCategory.MASSNAHMEN,
    ),
    SearchField.BETEILIGTE: FieldConfig(
        FieldType.TEXT,
        subjekt_beteiligter_alias.search_key(),
        JoinType.BETEILIGTER_SUBJ,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.BEZIEHUNGSART_EIGENTUM: FieldConfig(
        FieldType.CODE,
        beziehungsart_eigentum_code_alias.search_key(),
        JoinType.BEZIEHUNGSART_EIGENTUM,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.BEZIEHUNGSART_SACHBEARBEITUNG: FieldConfig(
        FieldType.CODE,
        beziehungsart_sachbearbeitung_code_alias.search_key(),
        JoinType.BEZIEHUNGSART_SACHBEARBEITUNG,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.BEZIEHUNGSART_SONSTIGE: FieldConfig(
        FieldType.CODE,
        beziehungsart_sonstige_code_alias.search_key(),
        JoinType.BEZIEHUNGSART_SONSTIGE,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.STANDORT_EIGENTUEMER: FieldConfig(
        FieldType.TEXT,
        subjekt_eigentuemer_alias.search_key(),
        JoinType.EIGENTUEMER_SUBJ,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.VORNAME: FieldConfig(
        FieldType.TEXT,
        subjekt_beteiligter_alias.vorname,
        JoinType.BETEILIGTER_SUBJ,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.NACHNAME: FieldConfig(
        FieldType.TEXT,
        subjekt_beteiligter_alias.name,
        JoinType.BETEILIGTER_SUBJ,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.TAETIGKEIT: FieldConfig(
        FieldType.TEXT,
        subjekt_beteiligter_alias.taetigkeit,
        JoinType.BETEILIGTER_SUBJ,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.PRIO_UNTERSUCHUNGSBEDARF: FieldConfig(
        FieldType.CODE,
        prio_untersuchung_code_alias.search_key(),
        JoinType.PRIO_UNTERSUCHUNG,
        FieldCategory.PRIORISIERUNG,
    ),
    SearchField.BEGRUENDUNG_PRIO_UNTERSUCHUNGSBEDARF: FieldConfig(
        FieldType.TEXT,
        begruendung_prio_untersuchung_alias.bem,
        JoinType.BEGRUENDUNG_PRIO_UNTERSUCHUNG,
        FieldCategory.PRIORISIERUNG,
    ),
    SearchField.PRIO_SANIERUNGSBEDARF: FieldConfig(
        FieldType.CODE,
        prio_sanierung_code_alias.search_key(),
        JoinType.PRIO_SANIERUNG,
        FieldCategory.ZIELE,
    ),
    SearchField.BEGRUENDUNG_PRIO_SANIERUNGSBDEDARF: FieldConfig(
        FieldType.TEXT,
        begruendung_prio_sanierung_alias.bem,
        JoinType.BEGRUENDUNG_PRIO_SANIERUNG,
        FieldCategory.ZIELE,
    ),
    SearchField.SANIERUNGSZIEL: FieldConfig(
        FieldType.CODE,
        sanierungsziel_code_alias.search_key(),
        JoinType.SANIERUNGSZIEL,
        FieldCategory.ZIELE,
    ),
    SearchField.SANIERUNGSZIEL_BEMERKUNGEN: FieldConfig(
        FieldType.TEXT,
        bemerkung_sanierung_alias.bem,
        JoinType.BEMERKUNG_SANIERUNG,
        FieldCategory.ZIELE,
    ),
    SearchField.KARTENAUSSCHNITT: FieldConfig(
        FieldType.BBOX,
        Vflz.zentroid,
        JoinType.NONE,
        FieldCategory.LOKALISIERUNG,
    ),
    SearchField.TASK_TYP: FieldConfig(
        FieldType.CODE,
        task_typ_code_alias.search_key(),
        JoinType.TASK_TYP,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_TITEL: FieldConfig(
        FieldType.TEXT, Node.title, JoinType.TASK, FieldCategory.GESCHAEFT
    ),
    SearchField.TASK_STATUS: FieldConfig(
        FieldType.CODE,
        task_status_code_alias.search_key(),
        JoinType.TASK_STATUS,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_START_DATUM: FieldConfig(
        FieldType.DATE,
        func.date(Node.started_at),
        JoinType.TASK,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_END_DATUM: FieldConfig(
        FieldType.DATE,
        func.date(Node.finished_at),
        JoinType.TASK,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_FAELLIGKEIT: FieldConfig(
        FieldType.DATE, func.date(Node.deadline), JoinType.TASK, FieldCategory.GESCHAEFT
    ),
    SearchField.NOTIZ: FieldConfig(
        FieldType.TEXT, Node.note, JoinType.TASK, FieldCategory.GESCHAEFT
    ),
    SearchField.TASK_BETEILIGTE: FieldConfig(
        FieldType.TEXT,
        subjekt_beteiligter_geschaeft_alias.search_key(),
        JoinType.TASK_BETEILIGTE_SUBJ,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.DOKUMENT_REFERENZ: FieldConfig(
        FieldType.TEXT,
        DocumentNode.__table__.c.document_ref,
        JoinType.TASK,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_BEZIEHUNGSART_EIGENTUM: FieldConfig(
        FieldType.CODE,
        task_beziehungsart_eigentum_code_alias.search_key(),
        JoinType.TASK_BEZIEHUNGSART_EIGENTUM,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_BEZIEHUNGSART_SACHBEARBEITUNG: FieldConfig(
        FieldType.CODE,
        task_beziehungsart_sachbearbeitung_code_alias.search_key(),
        JoinType.TASK_BEZIEHUNGSART_SACHBEARBEITUNG,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_BEZIEHUNGSART_SONSTIGE: FieldConfig(
        FieldType.CODE,
        task_beziehungsart_sonstige_code_alias.search_key(),
        JoinType.TASK_BEZIEHUNGSART_SONSTIGE,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_BEZIEHUNGSART_GESCHAEFTE: FieldConfig(
        FieldType.CODE,
        task_beziehungsart_geschaefte_code_alias.search_key(),
        JoinType.TASK_BEZIEHUNGSART_GESCHAEFTE,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.TASK_KATEGORIE: FieldConfig(
        FieldType.CODE,
        task_kategorie_alias.search_key(),
        JoinType.TASK_KATEGORIE,
        FieldCategory.GESCHAEFT,
    ),
    SearchField.BEMERKUNG_ADRESSE: FieldConfig(
        FieldType.TEXT,
        bemerkung_subjekt_alias.bem,
        JoinType.BEMERKUNG_ADRESSE,
        FieldCategory.BETEILIGTE,
    ),
    SearchField.KINDERSPIELPLATZ_NAME: FieldConfig(
        FieldType.TEXT,
        KinderspielplatzGruenflaeche.name,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_STRASSE: FieldConfig(
        FieldType.TEXT,
        KinderspielplatzGruenflaeche.strasse,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_PLZ: FieldConfig(
        FieldType.TEXT,
        KinderspielplatzGruenflaeche.plz,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_ORT: FieldConfig(
        FieldType.TEXT,
        KinderspielplatzGruenflaeche.ort,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_EVA: FieldConfig(
        FieldType.TEXT,
        KinderspielplatzGruenflaeche.eva,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_BEMERKUNG: FieldConfig(
        FieldType.TEXT,
        bemerkung_kinderspielplatz_alias.bem,
        JoinType.KINDERSPIELPLATZ_BEMERKUNG,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_KATASTERRELEVANZ: FieldConfig(
        FieldType.BOOL,
        KinderspielplatzGruenflaeche.relevant,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND: FieldConfig(
        FieldType.CODE,
        kinderspielplatz_untersuchungsstand_code_alias.search_key(),
        JoinType.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_BEURTEILUNG: FieldConfig(
        FieldType.CODE,
        kinderspielplatz_beurteilung_code_alias.search_key(),
        JoinType.KINDERSPIELPLATZ_BEURTEILUNG,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.EIGENTUMSFORM: FieldConfig(
        FieldType.CODE,
        eigentumsform_code_alias.search_key(),
        JoinType.EIGENTUMSFORM,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.BELASTUNG_UEBER_SANIERUNGSWERT: FieldConfig(
        FieldType.BOOL,
        KinderspielplatzGruenflaeche.belastung_ueber_sanierungswert,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_TYP: FieldConfig(
        FieldType.CODE,
        kinderspielplatz_typ_code_alias.search_key(),
        JoinType.KINDERSPIELPLATZ_TYP,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.ALTERSSTUFE_KINDER: FieldConfig(
        FieldType.CODE,
        altersstufe_kinder_code_alias.search_key(),
        JoinType.ALTERSSTUFE_KINDER,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_ZEITRAUM_VON: FieldConfig(
        FieldType.DATE,
        KinderspielplatzGruenflaeche.zeitraum_von,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_ZEITRAUM_BIS: FieldConfig(
        FieldType.DATE,
        KinderspielplatzGruenflaeche.zeitraum_bis,
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_X_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_X(KinderspielplatzGruenflaeche.zentroid),
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.KINDERSPIELPLATZ_Y_KOORDINATE: FieldConfig(
        FieldType.NUMBER,
        func.ST_Y(KinderspielplatzGruenflaeche.zentroid),
        JoinType.KINDERSPIELPLATZ,
        FieldCategory.KINDERSPIELPLATZ,
    ),
    SearchField.VOLLZUG: FieldConfig(
        FieldType.BOOL, vollzug_alias.aktiv, JoinType.VOLLZUG, FieldCategory.VOLLZUG
    ),
    SearchField.BEHOERDE: FieldConfig(
        FieldType.CODE,
        behoerde_code_alias.search_key(),
        JoinType.BEHOERDE,
        FieldCategory.VOLLZUG,
    ),
    SearchField.ALTERNATIVE_STANDORTNUMMER: FieldConfig(
        FieldType.TEXT,
        vollzug_alias.combined_id,
        JoinType.VOLLZUG,
        FieldCategory.VOLLZUG,
    ),
    SearchField.PARZELLE: FieldConfig(
        FieldType.TEXT, Parzelle.gb_nummer, JoinType.PARZELLE, FieldCategory.BETEILIGTE
    ),
    SearchField.NB_IDENT: FieldConfig(
        FieldType.TEXT, Parzelle.h_nb_id, JoinType.PARZELLE, FieldCategory.BETEILIGTE
    ),
    SearchField.PFAS_NAME: FieldConfig(
        FieldType.TEXT, PFAS.name, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.BEMERKUNG_PFAS: FieldConfig(
        FieldType.TEXT,
        bemerkung_pfas_alias.bem,
        JoinType.BEMERKUNG_PFAS,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_UNTERSUCHUNGSSTAND: FieldConfig(
        FieldType.CODE,
        pfas_untersuchungsstand_code_alias.search_key(),
        JoinType.PFAS_UNTERSUCHUNGSSTAND,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_BEURTEILUNG: FieldConfig(
        FieldType.CODE,
        pfas_beurteilung_code_alias.search_key(),
        JoinType.PFAS_BEURTEILUNG,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_BRANCHE: FieldConfig(
        FieldType.CODE,
        pfas_branche_code_alias.search_key(),
        JoinType.PFAS_BRANCHE,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_TYP: FieldConfig(
        FieldType.CODE,
        pfas_typ_code_alias.search_key(),
        JoinType.PFAS_TYP,
        FieldCategory.PFAS,
    ),
    SearchField.BEGRUENDUNG_BEWERTUNG_PFAS: FieldConfig(
        FieldType.TEXT,
        begruendung_bew_pfas_alias.bem,
        JoinType.BEGRUENDUNG_BEWERTUNG_PFAS,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_HALTIGE_LOESCHMITTEL: FieldConfig(
        FieldType.CODE,
        pfas_haltige_loeschmittel_code_alias.search_key(),
        JoinType.PFAS_HALTIGE_LOESCHMITTEL,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_FREIE_LOESCHMITTEL: FieldConfig(
        FieldType.CODE,
        pfas_freie_loeschmittel_code_alias.search_key(),
        JoinType.PFAS_FREIE_LOESCHMITTEL,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_LOESCHSCHAUM_EINSATZ: FieldConfig(
        FieldType.CODE,
        loeschschaum_einsatz_code_alias.search_key(),
        JoinType.PFAS_LOESCHSCHAUM_EINSATZ,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_HAEUFIGKEIT_NUTZUNG: FieldConfig(
        FieldType.CODE,
        pfas_haeufigkeit_nutzung_code_alias.search_key(),
        JoinType.PFAS_HAEUFIGKEIT_NUTZUNG,
        FieldCategory.PFAS,
    ),
    SearchField.PFAS_STRASSE: FieldConfig(
        FieldType.TEXT, PFAS.strasse, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_PLZ: FieldConfig(
        FieldType.TEXT, PFAS.plz, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_ORT: FieldConfig(
        FieldType.TEXT, PFAS.ort, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_EVA_NUMMER: FieldConfig(
        FieldType.TEXT, PFAS.eva, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_ZEITRAUM_VON: FieldConfig(
        FieldType.DATE, PFAS.zeitraum_von, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_ZEITRAUM_BIS: FieldConfig(
        FieldType.DATE, PFAS.zeitraum_bis, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_LOESCHMITTEL: FieldConfig(
        FieldType.BOOL, PFAS.pfas_loeschmittel, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_KATASTERRELEVANZ: FieldConfig(
        FieldType.BOOL, PFAS.relevant, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_MENGE_SCHAUMGEMISCH: FieldConfig(
        FieldType.NUMBER, PFAS.menge_schaumgemisch, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_MENGE_KONZENTRAT: FieldConfig(
        FieldType.NUMBER, PFAS.menge_konzentrat, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_BESCHREIBUNGEN_DETAIL: FieldConfig(
        FieldType.TEXT, PFAS.beschreibungen_detail, JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_X_KOORDINATE: FieldConfig(
        FieldType.NUMBER, func.ST_X(PFAS.zentroid), JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.PFAS_Y_KOORDINATE: FieldConfig(
        FieldType.NUMBER, func.ST_Y(PFAS.zentroid), JoinType.PFAS, FieldCategory.PFAS
    ),
    SearchField.FLUGPLATZ_BEZEICHNUNG: FieldConfig(
        FieldType.CODE,
        flugplatz_bezeichnung_code_alias.search_key(),
        JoinType.FLUGPLATZ_BEZEICHNUNG,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.KTU: FieldConfig(
        FieldType.CODE,
        ktu_code_alias.search_key(),
        JoinType.KTU_CODE,
        FieldCategory.GRUNDDATEN,
    ),
    SearchField.GRUNDBUCH_BEZEICHNUNG: FieldConfig(
        FieldType.TEXT,
        Nummerierungsbereich.bezeichnung,
        JoinType.GRUNDBUCH_BEZEICHNUNG,
        FieldCategory.BETEILIGTE,
    ),
}

#
# Table of join paths
#
# For each JoinType that is not applied directly to Vflz, list the joins that need
# to be added before, excluding the actual join.
#
# This ensures that joins can be properly deduplicated in all cases.
#
JOIN_PATH: dict[JoinType, list[JoinType]] = {
    JoinType.BEURTEILUNG: [JoinType.VFLZ_BEURTEILUNG],
    JoinType.KANTON: [JoinType.GEMEINDE],
    JoinType.BEMERKUNG_ABLAGERUNG: [JoinType.ABLAGERUNG],
    JoinType.KOMPARTIMENT_STOFFKLASSE: [JoinType.ABLAGERUNG],
    JoinType.STOFFKLASSE: [
        JoinType.ABLAGERUNG,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
    ],
    JoinType.KOMPARTIMENT_STOFFGRUPPE: [
        JoinType.ABLAGERUNG,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
    ],
    JoinType.STOFFGRUPPE: [
        JoinType.ABLAGERUNG,
        JoinType.KOMPARTIMENT_STOFFKLASSE,
        JoinType.KOMPARTIMENT_STOFFGRUPPE,
    ],
    JoinType.BRANCHE_ASW: [JoinType.BASISBETRIEB],
    JoinType.BRANCHE_NOGA: [JoinType.BASISBETRIEB],
    JoinType.SCHIESSANLAGE_TYP: [JoinType.BASISBETRIEB],
    JoinType.BETRIEB_UNTERSUCHUNGSTAND: [JoinType.BASISBETRIEB],
    JoinType.BETRIEB_BEURTEILUNG: [JoinType.BASISBETRIEB],
    JoinType.BEMERKUNG_BETRIEB: [JoinType.BASISBETRIEB],
    JoinType.BEGRUENDUNG_BEWERTUNG_BETRIEB: [JoinType.BASISBETRIEB],
    JoinType.UNFALL_GENAUIGKEIT: [JoinType.UNFALL],
    JoinType.UNFALLSTOFF: [JoinType.UNFALL],
    JoinType.STOFF: [JoinType.UNFALL, JoinType.UNFALLSTOFF],
    JoinType.BEMERKUNG_UNFALL: [JoinType.UNFALL],
    JoinType.RELATIVE_LAGE_GW: [JoinType.GW],
    JoinType.NUTZUNG_GW_ABSTROM: [JoinType.GW],
    JoinType.ART_OBERFL_GEWAESSER: [JoinType.OBERFL_GEWAESSER],
    JoinType.GEWAESSERBAU: [JoinType.OBERFL_GEWAESSER],
    JoinType.RELATIVE_LAGE_OGW: [JoinType.OBERFL_GEWAESSER],
    JoinType.UMWELTSTOFF_GRUPPE: [JoinType.UMWELTSTOFF],
    JoinType.UMWELTSTOFF_STOFF: [JoinType.UMWELTSTOFF],
    JoinType.UMWELTSTOFF_BEREICHE: [JoinType.UMWELTSTOFF],
    JoinType.UMWELTSTOFF_BEURTEILUNG: [JoinType.UMWELTSTOFF],
    JoinType.NUTZUNGS_ZONE: [JoinType.NUTZUNG_BODEN],
    JoinType.AKTUELLE_NUTZUNG: [JoinType.NUTZUNG_BODEN],
    JoinType.UMWELTSCHADEN_SCHADEN: [JoinType.UMWELTSCHADEN],
    JoinType.BEMERKUNG_UMWELTSCHADEN: [JoinType.UMWELTSCHADEN],
    JoinType.EINZELEREIGNIS_CODE: [JoinType.EINZELEREIGNIS],
    JoinType.BEMERKUNG_EINZELEREIGNIS: [JoinType.EINZELEREIGNIS],
    JoinType.MASSNAHME_CODE: [JoinType.MASSNAHME],
    JoinType.BEMERKUNG_MASSNAHME: [JoinType.MASSNAHME],
    JoinType.BETEILIGTER_SUBJ: [JoinType.BETEILIGTER],
    JoinType.BEZIEHUNGSART_EIGENTUM: [
        JoinType.BETEILIGTER,
        JoinType.BETEILIGTER_STANDORT,
    ],
    JoinType.BEZIEHUNGSART_SACHBEARBEITUNG: [
        JoinType.BETEILIGTER,
        JoinType.BETEILIGTER_STANDORT,
    ],
    JoinType.BEZIEHUNGSART_SONSTIGE: [
        JoinType.BETEILIGTER,
        JoinType.BETEILIGTER_STANDORT,
    ],
    JoinType.PRIO_UNTERSUCHUNG: [JoinType.VFLZ_BEURTEILUNG],
    JoinType.PRIO_SANIERUNG: [JoinType.VFLZ_BEURTEILUNG],
    JoinType.SANIERUNGSZIEL: [JoinType.VFLZ_SANIERUNGSZIEL],
    JoinType.BEMERKUNG_SANIERUNG: [JoinType.VFLZ_SANIERUNGSZIEL],
    JoinType.TASK: [JoinType.VFLZ_VFL_ID],
    JoinType.TASK_BETEILIGTE: [JoinType.VFLZ_VFL_ID, JoinType.TASK],
    JoinType.TASK_BETEILIGTE_SUBJ: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
        JoinType.TASK_BETEILIGTE,
    ],
    JoinType.TASK_BEZIEHUNGSART_EIGENTUM: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
        JoinType.TASK_BETEILIGTE,
    ],
    JoinType.TASK_BEZIEHUNGSART_SACHBEARBEITUNG: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
        JoinType.TASK_BETEILIGTE,
    ],
    JoinType.TASK_BEZIEHUNGSART_SONSTIGE: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
        JoinType.TASK_BETEILIGTE,
    ],
    JoinType.TASK_BEZIEHUNGSART_GESCHAEFTE: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
        JoinType.TASK_BETEILIGTE,
    ],
    JoinType.TASK_TYP: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
    ],
    JoinType.TASK_STATUS: [
        JoinType.VFLZ_VFL_ID,
        JoinType.TASK,
    ],
    JoinType.TASK_KATEGORIE: [JoinType.VFLZ_VFL_ID, JoinType.TASK],
    JoinType.BEMERKUNG_ADRESSE: [JoinType.BETEILIGTER, JoinType.BETEILIGTER_SUBJ],
    JoinType.KINDERSPIELPLATZ_BEMERKUNG: [JoinType.KINDERSPIELPLATZ],
    JoinType.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND: [JoinType.KINDERSPIELPLATZ],
    JoinType.KINDERSPIELPLATZ_BEURTEILUNG: [JoinType.KINDERSPIELPLATZ],
    JoinType.EIGENTUMSFORM: [JoinType.KINDERSPIELPLATZ],
    JoinType.KINDERSPIELPLATZ_TYP: [JoinType.KINDERSPIELPLATZ],
    JoinType.ALTERSSTUFE_KINDER: [JoinType.KINDERSPIELPLATZ],
    JoinType.BEHOERDE: [JoinType.VOLLZUG],
    JoinType.PARZELLE: [JoinType.VFLGEO],
    JoinType.BEMERKUNG_PFAS: [JoinType.PFAS],
    JoinType.PFAS_UNTERSUCHUNGSSTAND: [JoinType.PFAS],
    JoinType.PFAS_BEURTEILUNG: [JoinType.PFAS],
    JoinType.PFAS_BRANCHE: [JoinType.PFAS],
    JoinType.PFAS_TYP: [JoinType.PFAS],
    JoinType.BEGRUENDUNG_BEWERTUNG_PFAS: [JoinType.PFAS],
    JoinType.PFAS_HALTIGE_LOESCHMITTEL: [JoinType.PFAS],
    JoinType.PFAS_FREIE_LOESCHMITTEL: [JoinType.PFAS],
    JoinType.PFAS_LOESCHSCHAUM_EINSATZ: [JoinType.PFAS, JoinType.LOESCHSCHAUM_EINSATZ],
    JoinType.PFAS_HAEUFIGKEIT_NUTZUNG: [JoinType.PFAS, JoinType.LOESCHSCHAUM_EINSATZ],
    JoinType.KTU_CODE: [JoinType.KTU],
    JoinType.FLUGPLATZ_BEZEICHNUNG: [JoinType.FLUGPLATZ],
    JoinType.GRUNDBUCH_BEZEICHNUNG: [JoinType.VFLGEO, JoinType.PARZELLE],
}

#
# Table of joins by JoinType
#
# Each entry is a function that applies the relevant JOIN conditions to a query.
#
# Each function should normally only apply a *single* join. Intermediate joins
# that are shared with any other JoinType must be split into their own entry and added
# to the JOIN_PATH entries of the JoinType that require them. This ensures that joins
# can be properly deduplicated in all cases.
JOINS: dict[JoinType, Callable[[Select[Any]], Select[Any]]] = {
    JoinType.NONE: lambda q: q,
    JoinType.STANDORTTYP: lambda q: q.outerjoin(
        Vflz.vftyp.of_type(standorttyp_code_alias)
    ),
    JoinType.VFLZ_BEURTEILUNG: lambda q: q.outerjoin(Vflz.beurteilung),
    JoinType.BEURTEILUNG: lambda q: q.outerjoin(
        Beurteilung.beurteilung.of_type(beurteilung_code_alias)
    ),
    JoinType.GEMEINDE: lambda q: q.outerjoin(Vflz.gemeinde),
    JoinType.BASISBETRIEB: lambda q: q.outerjoin(Vflz.betriebe_und_schiessanlagen),
    JoinType.STATUS_PUBLIKATION: lambda q: q.outerjoin_from(
        Vflz, VflzStatusPublikation, Vflz.vfl_id == VflzStatusPublikation.vfl_id
    ),
    JoinType.POOL: lambda q: q.outerjoin_from(
        Vflz, VflPool, Vflz.vfl_id == VflPool.vfl_id
    ).outerjoin_from(VflPool, Pool, VflPool.pool_id == Pool.pool_id),
    JoinType.OBJEKT: lambda q: q.outerjoin(Vflz.objekt),
    JoinType.VFLGEO: lambda q: q.outerjoin(Vflz.vflgeo),
    JoinType.KANTON: lambda q: q.outerjoin(Gemeinde.kanton.of_type(kanton_code_alias)),
    JoinType.BEMERKUNG_STANDORT: lambda q: q.outerjoin(
        Vflz.bemerkung_standort.of_type(bemerkung_standort_alias)
    ),
    JoinType.DEPONIETYP: lambda q: q.outerjoin(
        Vflz.deponietyp.of_type(deponietyp_code_alias)
    ),
    JoinType.ABLAGERUNG: lambda q: q.outerjoin(Vflz.ablagerungen),
    JoinType.BEMERKUNG_ABLAGERUNG: lambda q: q.outerjoin(
        Ablagerung.bemerkung.of_type(bemerkung_ablagerung_alias)
    ),
    JoinType.STOFFKLASSE: lambda q: q.outerjoin(
        KompartimentStoffklasse.stoffklasse.of_type(stoffklasse_code_alias)
    ),
    JoinType.KOMPARTIMENT_STOFFKLASSE: lambda q: q.outerjoin(
        Ablagerung.kompartiment_stoffklassen
    ),
    JoinType.KOMPARTIMENT_STOFFGRUPPE: lambda q: q.outerjoin(
        KompartimentStoffklasse.kompartiment_stoffgruppen
    ),
    JoinType.STOFFGRUPPE: lambda q: q.outerjoin(
        KompartimentStoffgruppe.stoffgruppe.of_type(stoffgruppe_code_alias)
    ),
    JoinType.BRANCHE_ASW: lambda q: q.outerjoin(
        BasisBetrieb.branche_asw.of_type(branche_asw_code_alias)
    ),
    JoinType.BRANCHE_NOGA: lambda q: q.outerjoin(
        BasisBetrieb.branche_noga.of_type(branche_noga_code_alias)
    ),
    # Note: we can join on BasisBetrieb and still filter by attributes of the Schiessanlage
    # subclass, since we're using single table inheritance
    JoinType.SCHIESSANLAGE_TYP: lambda q: q.outerjoin(
        Schiessanlage.typ.of_type(schiessanlage_typ_code_alias)
    ),
    JoinType.BETRIEB_UNTERSUCHUNGSTAND: lambda q: q.outerjoin(
        BasisBetrieb.untersuchungs_stand.of_type(betrieb_untersuchungsstand_code_alias)
    ),
    JoinType.BETRIEB_BEURTEILUNG: lambda q: q.outerjoin(
        BasisBetrieb.beurteilung.of_type(betrieb_beurteilung_code_alias)
    ),
    JoinType.BEMERKUNG_BETRIEB: lambda q: q.outerjoin(
        BasisBetrieb.bemerkung.of_type(bemerkung_betrieb_alias)
    ),
    JoinType.BEGRUENDUNG_BEWERTUNG_BETRIEB: lambda q: q.outerjoin(
        BasisBetrieb.begruendung_bewertung.of_type(begruendung_bew_betrieb_alias)
    ),
    JoinType.UNFALL: lambda q: q.outerjoin(Vflz.unfaelle),
    JoinType.UNFALL_GENAUIGKEIT: lambda q: q.outerjoin(
        Unfall.genauigkeit_zeitpunkt.of_type(unfall_genauigkeit_code_alias)
    ),
    JoinType.UNFALLSTOFF: lambda q: q.outerjoin(Unfall.unfallstoffe),
    JoinType.STOFF: lambda q: q.outerjoin(Unfallstoff.stoff.of_type(stoff_code_alias)),
    JoinType.BEMERKUNG_UNFALL: lambda q: q.outerjoin(
        Unfall.bemerkung.of_type(bemerkung_unfall_alias)
    ),
    JoinType.GWS_BEREICH: lambda q: q.outerjoin(
        Vflz.gws_bereich.of_type(gws_bereich_code_alias)
    ),
    JoinType.GWS_ZONE: lambda q: q.outerjoin(
        Vflz.gws_zone.of_type(gws_zone_code_alias)
    ),
    JoinType.KARSTGEBIET: lambda q: q.outerjoin(
        Vflz.karstgeb.of_type(karstgebiet_code_alias)
    ),
    JoinType.DURCHLAESSIGKEIT: lambda q: q.outerjoin(
        Vflz.durchlaessigkeit.of_type(durchlaessigkeit_code_alias)
    ),
    JoinType.BEMERKUNG_UMWELT: lambda q: q.outerjoin(
        Vflz.bemerkung_umwelt.of_type(bemerkung_umwelt_alias)
    ),
    JoinType.GW: lambda q: q.outerjoin(Vflz.grundwasser),
    JoinType.RELATIVE_LAGE_GW: lambda q: q.outerjoin(
        Grundwasser.relative_lage.of_type(relative_lage_gw_code_alias)
    ),
    JoinType.NUTZUNG_GW_ABSTROM: lambda q: q.outerjoin(
        Grundwasser.nutzung.of_type(nutzung_gw_abstrom_code_alias)
    ),
    JoinType.OBERFL_GEWAESSER: lambda q: q.outerjoin(Vflz.oberflaechen_gewaesser),
    JoinType.ART_OBERFL_GEWAESSER: lambda q: q.outerjoin(
        OberflaechenGewaesser.art_gewaesser.of_type(gewaesser_art_code_alias)
    ),
    JoinType.GEWAESSERBAU: lambda q: q.outerjoin(
        OberflaechenGewaesser.bau_gewaesser.of_type(gewaesser_bau_code_alias)
    ),
    JoinType.RELATIVE_LAGE_OGW: lambda q: q.outerjoin(
        OberflaechenGewaesser.relative_lage.of_type(relative_lage_ogw_code_alias)
    ),
    JoinType.UMWELTSTOFF: lambda q: q.outerjoin(Vflz.umwelt_stoffe),
    JoinType.UMWELTSTOFF_GRUPPE: lambda q: q.outerjoin(
        UmweltStoff.stoff_gruppe.of_type(umweltstoff_gruppe_code_alias)
    ),
    JoinType.UMWELTSTOFF_STOFF: lambda q: q.outerjoin(
        UmweltStoff.stoff.of_type(umweltstoff_stoff_code_alias)
    ),
    JoinType.UMWELTSTOFF_BEREICHE: lambda q: q.outerjoin(
        UmweltStoff.gefaehrdete_bereiche.of_type(umweltstoff_bereiche_code_alias)
    ),
    JoinType.UMWELTSTOFF_BEURTEILUNG: lambda q: q.outerjoin(
        UmweltStoff.beurteilung.of_type(umweltstoff_beurteilung_code_alias)
    ),
    JoinType.NUTZUNG_BODEN: lambda q: q.outerjoin(Vflz.nutzungen_boden),
    JoinType.NUTZUNGS_ZONE: lambda q: q.outerjoin(
        NutzungBoden.nutzungsart.of_type(nutzungsart_code_alias)
    ),
    JoinType.AKTUELLE_NUTZUNG: lambda q: q.outerjoin(
        NutzungBoden.aktuelle_nutzung.of_type(aktuelle_nutzung_code_alias)
    ),
    JoinType.UMWELTBEREICH: lambda q: q.outerjoin(Vflz.umweltschaeden).outerjoin(
        Umweltschaden.art_schaden.of_type(umweltbereich_code_alias)
    ),
    JoinType.UMWELTSCHADEN: lambda q: q.outerjoin(Vflz.umweltschaeden),
    JoinType.UMWELTSCHADEN_SCHADEN: lambda q: q.outerjoin(
        Umweltschaden.schaeden.of_type(umweltschaeden_code_alias)
    ),
    JoinType.BEMERKUNG_UMWELTSCHADEN: lambda q: q.outerjoin(
        Umweltschaden.bemerkung.of_type(bemerkung_umweltschaden_alias)
    ),
    JoinType.EINZELEREIGNIS: lambda q: q.outerjoin(Vflz.einzelereignisse),
    JoinType.EINZELEREIGNIS_CODE: lambda q: q.outerjoin(
        Einzelereignis.einzelereignis.of_type(einzelereignis_code_alias)
    ),
    JoinType.BEMERKUNG_EINZELEREIGNIS: lambda q: q.outerjoin(
        Einzelereignis.bemerkung.of_type(bemerkung_einzelereignis_alias)
    ),
    JoinType.BEGRUENDUNG_BEWERTUNG: lambda q: q.outerjoin(
        Vflz.begruendung_bewertung.of_type(begruendung_bewertung_alias)
    ),
    JoinType.BEARBEITUNGSSTAND: lambda q: q.outerjoin(
        Vflz.bearbeitungs_stand.of_type(bearbeitungsstand_code_alias)
    ),
    JoinType.UNTERSUCHUNGSSTAND: lambda q: q.outerjoin(
        Vflz.untersuchungs_stand.of_type(untersuchungsstand_code_alias)
    ),
    JoinType.MASSNAHME: lambda q: q.outerjoin(Vflz.massnahmen),
    JoinType.MASSNAHME_CODE: lambda q: q.outerjoin(
        Massnahme.massnahme.of_type(massnahme_code_alias)
    ),
    JoinType.BEMERKUNG_MASSNAHME: lambda q: q.outerjoin(
        Massnahme.bemerkung.of_type(bemerkung_massnahme_alias)
    ),
    JoinType.BETEILIGTER: lambda q: q.outerjoin(Vflz.beteiligte),
    JoinType.BETEILIGTER_SUBJ: lambda q: q.outerjoin_from(
        Beteiligter,
        subjekt_beteiligter_alias,
        Beteiligter.subj_id == subjekt_beteiligter_alias.subj_id,
    ),
    JoinType.EIGENTUEMER_SUBJ: lambda q: q.outerjoin_from(
        Vflz,
        bet_eigentuemer_alias,
        and_(
            bet_eigentuemer_alias.vflz_id == Vflz.vflz_id,
            bet_eigentuemer_alias.is_eigentuemer,
        ),
    ).outerjoin_from(
        bet_eigentuemer_alias,
        subjekt_eigentuemer_alias,
    ),
    JoinType.BEZIEHUNGSART_EIGENTUM: lambda q: q.outerjoin(
        beteiligter_standort_alias.beziehungsart.of_type(
            beziehungsart_eigentum_code_alias
        )
    ),
    JoinType.BEZIEHUNGSART_SACHBEARBEITUNG: lambda q: q.outerjoin(
        beteiligter_standort_alias.beziehungsart.of_type(
            beziehungsart_sachbearbeitung_code_alias
        )
    ),
    JoinType.BEZIEHUNGSART_SONSTIGE: lambda q: q.outerjoin(
        beteiligter_standort_alias.beziehungsart.of_type(
            beziehungsart_sonstige_code_alias
        )
    ),
    JoinType.PRIO_UNTERSUCHUNG: lambda q: q.outerjoin(
        Beurteilung.prio_untersuch.of_type(prio_untersuchung_code_alias)
    ),
    JoinType.BEGRUENDUNG_PRIO_UNTERSUCHUNG: lambda q: q.outerjoin(
        Vflz.begruendung_prio_untersuchungsbedarf.of_type(
            begruendung_prio_untersuchung_alias
        )
    ),
    JoinType.PRIO_SANIERUNG: lambda q: q.outerjoin(
        Beurteilung.prio_sanier.of_type(prio_sanierung_code_alias)
    ),
    JoinType.BEGRUENDUNG_PRIO_SANIERUNG: lambda q: q.outerjoin(
        Vflz.begruendung_prio_sanierungsbedarf.of_type(begruendung_prio_sanierung_alias)
    ),
    JoinType.VFLZ_SANIERUNGSZIEL: lambda q: q.outerjoin(Vflz.sanierungsziele),
    JoinType.SANIERUNGSZIEL: lambda q: q.outerjoin(
        Sanierungsziel.sanierungsziel.of_type(sanierungsziel_code_alias)
    ),
    JoinType.BEMERKUNG_SANIERUNG: lambda q: q.outerjoin(
        Sanierungsziel.bemerkung.of_type(bemerkung_sanierung_alias)
    ),
    JoinType.VFLZ_VFL_ID: lambda q: q.outerjoin_from(
        Vflz,
        vflz_vfl_id_alias,
        Vflz.vfl_id == vflz_vfl_id_alias.vfl_id,
    ),
    JoinType.TASK: lambda q: q.outerjoin(
        Node,
        cast(Node.entity_id, Integer) == vflz_vfl_id_alias.vflz_id,
    ),
    JoinType.TASK_BETEILIGTE: lambda q: q.outerjoin(Node.beteiligte),  # pyright: ignore
    JoinType.TASK_BETEILIGTE_SUBJ: lambda q: q.outerjoin(
        BeteiligterGeschaeft.subjekt.of_type(subjekt_beteiligter_geschaeft_alias),
    ),
    JoinType.TASK_BEZIEHUNGSART_EIGENTUM: lambda q: q.outerjoin(
        BeteiligterGeschaeft.beziehungsart.of_type(
            task_beziehungsart_eigentum_code_alias
        )
    ),
    JoinType.TASK_BEZIEHUNGSART_SACHBEARBEITUNG: lambda q: q.outerjoin(
        BeteiligterGeschaeft.beziehungsart.of_type(
            task_beziehungsart_sachbearbeitung_code_alias
        )
    ),
    JoinType.TASK_BEZIEHUNGSART_SONSTIGE: lambda q: q.outerjoin(
        BeteiligterGeschaeft.beziehungsart.of_type(
            task_beziehungsart_sonstige_code_alias
        )
    ),
    JoinType.TASK_BEZIEHUNGSART_GESCHAEFTE: lambda q: q.outerjoin(
        BeteiligterGeschaeft.beziehungsart.of_type(
            task_beziehungsart_geschaefte_code_alias
        )
    ),
    JoinType.TASK_TYP: lambda q: q.outerjoin_from(
        Node,
        task_typ_code_alias,
        Node.type == task_typ_code_alias.code,
    ),
    JoinType.TASK_STATUS: lambda q: q.outerjoin_from(
        Node,
        task_status_code_alias,
        Node.status == task_status_code_alias.code,
    ),
    JoinType.TASK_KATEGORIE: lambda q: q.outerjoin(Node.kategorie).outerjoin_from(  # pyright: ignore
        NodeKategorie,
        task_kategorie_alias,
        tuple_(task_kategorie_alias.c_cli_id, task_kategorie_alias.code)
        == tuple_(NodeKategorie.h_category, NodeKategorie.c_category),
    ),
    JoinType.BEMERKUNG_ADRESSE: lambda q: q.outerjoin(
        Subjekt.bemerkung.of_type(bemerkung_subjekt_alias)
    ),
    JoinType.KINDERSPIELPLATZ: lambda q: q.outerjoin(
        Vflz.kinderspielplaetze_gruenflaechen
    ),
    JoinType.KINDERSPIELPLATZ_BEMERKUNG: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.bemerkung.of_type(bemerkung_kinderspielplatz_alias)
    ),
    JoinType.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.untersuchungs_stand.of_type(
            kinderspielplatz_untersuchungsstand_code_alias
        )
    ),
    JoinType.KINDERSPIELPLATZ_BEURTEILUNG: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.beurteilung.of_type(
            kinderspielplatz_beurteilung_code_alias
        )
    ),
    JoinType.EIGENTUMSFORM: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.eigentumsform.of_type(eigentumsform_code_alias)
    ),
    JoinType.KINDERSPIELPLATZ_TYP: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.kinderspielplatz_gruenflache_typ.of_type(
            kinderspielplatz_typ_code_alias
        )
    ),
    JoinType.ALTERSSTUFE_KINDER: lambda q: q.outerjoin(
        KinderspielplatzGruenflaeche.altersstufen_kinder.of_type(
            altersstufe_kinder_code_alias
        )
    ),
    JoinType.VOLLZUG: lambda q: q.outerjoin(Vflz.vollzug.of_type(vollzug_alias)),
    JoinType.BEHOERDE: lambda q: q.outerjoin(
        vollzug_alias.behoerde.of_type(behoerde_code_alias)
    ),
    JoinType.PARZELLE: lambda q: q.outerjoin_from(
        VflGeo,
        Parzelle,
        func.ST_Intersects(VflGeo.wkb_geometry, Parzelle.wkb_geometry),
    ),
    JoinType.BETEILIGTER_STANDORT: lambda q: q.outerjoin_from(
        Beteiligter,
        beteiligter_standort_alias,
        Beteiligter.bet_id == beteiligter_standort_alias.bet_id,
    ),
    JoinType.PFAS: lambda q: q.outerjoin(Vflz.pfas),
    JoinType.BEMERKUNG_PFAS: lambda q: q.outerjoin(
        PFAS.bemerkung.of_type(bemerkung_pfas_alias)
    ),
    JoinType.PFAS_UNTERSUCHUNGSSTAND: lambda q: q.outerjoin(
        PFAS.untersuchungs_stand.of_type(pfas_untersuchungsstand_code_alias)
    ),
    JoinType.PFAS_BEURTEILUNG: lambda q: q.outerjoin(
        PFAS.beurteilung.of_type(pfas_beurteilung_code_alias)
    ),
    JoinType.PFAS_BRANCHE: lambda q: q.outerjoin(
        PFAS.branche.of_type(pfas_branche_code_alias)
    ),
    JoinType.PFAS_TYP: lambda q: q.outerjoin(
        PFAS.pfas_typ.of_type(pfas_typ_code_alias)
    ),
    JoinType.BEGRUENDUNG_BEWERTUNG_PFAS: lambda q: q.outerjoin(
        PFAS.begruendung_bewertung.of_type(begruendung_bew_pfas_alias)
    ),
    JoinType.PFAS_HALTIGE_LOESCHMITTEL: lambda q: q.outerjoin(
        PFAS.pfas_haltige_loeschmittel.of_type(pfas_haltige_loeschmittel_code_alias)
    ),
    JoinType.PFAS_FREIE_LOESCHMITTEL: lambda q: q.outerjoin(
        PFAS.pfas_freie_loeschmittel.of_type(pfas_freie_loeschmittel_code_alias)
    ),
    JoinType.LOESCHSCHAUM_EINSATZ: lambda q: q.outerjoin(PFAS.loeschschaum_einsatz),
    JoinType.PFAS_LOESCHSCHAUM_EINSATZ: lambda q: q.outerjoin(
        LoeschschaumEinsatz.loeschschaum_einsatz.of_type(
            loeschschaum_einsatz_code_alias
        )
    ),
    JoinType.PFAS_HAEUFIGKEIT_NUTZUNG: lambda q: q.outerjoin(
        LoeschschaumEinsatz.haeufigkeit_nutzung.of_type(
            pfas_haeufigkeit_nutzung_code_alias
        )
    ),
    JoinType.FLUGPLATZ_BEZEICHNUNG: lambda q: q.outerjoin(
        Flugplatz.bezeichnung.of_type(flugplatz_bezeichnung_code_alias)
    ),
    JoinType.FLUGPLATZ: lambda q: q.outerjoin(Vflz.flugplatz),
    JoinType.KTU: lambda q: q.outerjoin(Vflz.ktu),
    JoinType.KTU_CODE: lambda q: q.outerjoin(KTU.ktu.of_type(ktu_code_alias)),
    JoinType.GRUNDBUCH_BEZEICHNUNG: lambda q: q.outerjoin(
        Parzelle.nummerierungsbereich
    ),
}

#
# List of table aliases for joining translations to code fields
#
# Maps fields names to aliases for the 'cod' and 'translations' table that are needed
# to join the translations for a given code value.
#
# This is only used for sorting the reuslt rows by translated code values in
# the tabular search result.
#
# Kanton does not need a translation alias, since the code is the canton code in all languages
CODE_TRANSLATION_ALIASES: dict[
    SearchField, tuple[type[codes.Code], type[Translation]]
] = {
    SearchField.BEURTEILUNG: (beurteilung_code_alias, beurteilung_translation_alias),
    SearchField.STANDORTTYP: (standorttyp_code_alias, standorttyp_translation_alias),
    SearchField.DEPONIETYP: (deponietyp_code_alias, deponietyp_translation_alias),
    SearchField.STOFFKLASSE_STOFFKLASSE: (
        stoffklasse_code_alias,
        stoffklasse_translation_alias,
    ),
    SearchField.STOFFGRUPPE_STOFFGRUPPE: (
        stoffgruppe_code_alias,
        stoffgruppe_translation_alias,
    ),
    SearchField.BRANCHE: (
        branche_asw_code_alias,
        branche_asw_translation_alias,
    ),
    SearchField.BRANCHE_NOGA: (
        branche_noga_code_alias,
        branche_noga_translation_alias,
    ),
    SearchField.SCHIESSANLAGE_TYP: (
        schiessanlage_typ_code_alias,
        schiessanlage_typ_translation_alias,
    ),
    SearchField.FIRMA_BEURTEILUNG: (
        betrieb_beurteilung_code_alias,
        betrieb_beurteilung_translation_alias,
    ),
    SearchField.FIRMA_UNTERSUCHUNGSSTAND: (
        betrieb_untersuchungsstand_code_alias,
        betrieb_untersuchungsstand_translation_alias,
    ),
    SearchField.UNFALL_GENAUIGKEIT: (
        unfall_genauigkeit_code_alias,
        unfall_genauigkeit_translation_alias,
    ),
    SearchField.UNFALLSTOFF_STOFFE: (
        stoff_code_alias,
        stoff_translation_alias,
    ),
    SearchField.GEWAESSERSCHUTZBEREICH: (
        gws_bereich_code_alias,
        gws_bereich_translation_alias,
    ),
    SearchField.SCHUTZZONE: (
        gws_zone_code_alias,
        gws_zone_translation_alias,
    ),
    SearchField.KARSTGEBIET: (
        karstgebiet_code_alias,
        karstgebiet_translation_alias,
    ),
    SearchField.DURCHLAESSIGKEIT: (
        durchlaessigkeit_code_alias,
        durchlaessigkeit_translation_alias,
    ),
    SearchField.RELATIVE_LAGE_GRUNDWASSER: (
        relative_lage_gw_code_alias,
        relative_lage_gw_translation_alias,
    ),
    SearchField.NUTZUNG_GW_ABSTROMBEREICH: (
        nutzung_gw_abstrom_code_alias,
        nutzung_gw_abstrom_translation_alias,
    ),
    SearchField.ART_OBERFL_GEWAESSER: (
        gewaesser_art_code_alias,
        gewaesser_art_translation_alias,
    ),
    SearchField.GEWAESSERBAU: (
        gewaesser_bau_code_alias,
        gewaesser_bau_translation_alias,
    ),
    SearchField.RELATIVE_LAGE_OBERFL_GEWAESSER: (
        relative_lage_ogw_code_alias,
        relative_lage_ogw_translation_alias,
    ),
    SearchField.UMWELTSTOFF_GRUPPE: (
        umweltstoff_gruppe_code_alias,
        umweltstoff_gruppe_translation_alias,
    ),
    SearchField.SPEZIFISCHER_STOFF: (
        umweltstoff_stoff_code_alias,
        umweltstoff_stoff_translation_alias,
    ),
    SearchField.UMWELT: (
        umweltstoff_bereiche_code_alias,
        umweltstoff_bereiche_translation_alias,
    ),
    SearchField.UMWELTSTOFFE_BEURTEILUNG: (
        umweltstoff_beurteilung_code_alias,
        umweltstoff_beurteilung_translation_alias,
    ),
    SearchField.NUTZUNGSZONE: (
        nutzungsart_code_alias,
        nutzungsart_translation_alias,
    ),
    SearchField.AKTUELLE_NUTZUNG: (
        aktuelle_nutzung_code_alias,
        aktuelle_nutzung_translation_alias,
    ),
    SearchField.GEFAEHRDETE_UMWELTBEREICHE: (
        umweltbereich_code_alias,
        umweltbereich_translation_alias,
    ),
    SearchField.FESTGESTELLTE_EINWIRKUNGEN: (
        umweltschaeden_code_alias,
        umweltschaeden_translation_alias,
    ),
    SearchField.VORKOMMNIS: (
        einzelereignis_code_alias,
        einzelereignis_translation_alias,
    ),
    SearchField.BEARBEITUNGSSTAND: (
        bearbeitungsstand_code_alias,
        bearbeitungsstand_translation_alias,
    ),
    SearchField.UNTERSUCHUNGSSTAND: (
        untersuchungsstand_code_alias,
        untersuchungsstand_translation_alias,
    ),
    SearchField.MASSNAHME: (
        massnahme_code_alias,
        massnahme_translation_alias,
    ),
    SearchField.BEZIEHUNGSART_EIGENTUM: (
        beziehungsart_eigentum_code_alias,
        beziehungsart_eigentum_translation_alias,
    ),
    SearchField.BEZIEHUNGSART_SACHBEARBEITUNG: (
        beziehungsart_sachbearbeitung_code_alias,
        beziehungsart_sachbearbeitung_translation_alias,
    ),
    SearchField.BEZIEHUNGSART_SONSTIGE: (
        beziehungsart_sonstige_code_alias,
        beziehungsart_sonstige_translation_alias,
    ),
    SearchField.PRIO_UNTERSUCHUNGSBEDARF: (
        prio_untersuchung_code_alias,
        prio_untersuchung_translation_alias,
    ),
    SearchField.PRIO_SANIERUNGSBEDARF: (
        prio_sanierung_code_alias,
        prio_sanierung_translation_alias,
    ),
    SearchField.SANIERUNGSZIEL: (
        sanierungsziel_code_alias,
        sanierungsziel_translation_alias,
    ),
    SearchField.TASK_BEZIEHUNGSART_EIGENTUM: (
        task_beziehungsart_eigentum_code_alias,
        task_beziehungsart_eigentum_translation_alias,
    ),
    SearchField.TASK_BEZIEHUNGSART_SACHBEARBEITUNG: (
        task_beziehungsart_sachbearbeitung_code_alias,
        task_beziehungsart_sachbearbeitung_translation_alias,
    ),
    SearchField.TASK_BEZIEHUNGSART_SONSTIGE: (
        task_beziehungsart_sonstige_code_alias,
        task_beziehungsart_sonstige_translation_alias,
    ),
    SearchField.TASK_BEZIEHUNGSART_GESCHAEFTE: (
        task_beziehungsart_geschaefte_code_alias,
        task_beziehungsart_geschaefte_translation_alias,
    ),
    SearchField.TASK_TYP: (
        task_typ_code_alias,
        task_typ_translation_alias,
    ),
    SearchField.TASK_STATUS: (
        task_status_code_alias,
        task_status_translation_alias,
    ),
    SearchField.KINDERSPIELPLATZ_UNTERSUCHUNGSSTAND: (
        kinderspielplatz_untersuchungsstand_code_alias,
        kinderspielplatz_untersuchungsstand_translation_alias,
    ),
    SearchField.KINDERSPIELPLATZ_BEURTEILUNG: (
        kinderspielplatz_beurteilung_code_alias,
        kinderspielplatz_beurteilung_translation_alias,
    ),
    SearchField.EIGENTUMSFORM: (
        eigentumsform_code_alias,
        eigentumsform_translation_alias,
    ),
    SearchField.KINDERSPIELPLATZ_TYP: (
        kinderspielplatz_typ_code_alias,
        kinderspielplatz_typ_translation_alias,
    ),
    SearchField.ALTERSSTUFE_KINDER: (
        altersstufe_kinder_code_alias,
        altersstufe_kinder_translation_alias,
    ),
    SearchField.BEHOERDE: (
        behoerde_code_alias,
        behoerde_translation_alias,
    ),
    SearchField.PFAS_UNTERSUCHUNGSSTAND: (
        pfas_untersuchungsstand_code_alias,
        pfas_untersuchungsstand_translation_alias,
    ),
    SearchField.PFAS_BEURTEILUNG: (
        pfas_beurteilung_code_alias,
        pfas_beurteilung_translation_alias,
    ),
    SearchField.PFAS_BRANCHE: (pfas_branche_code_alias, pfas_branche_translation_alias),
    SearchField.PFAS_TYP: (pfas_typ_code_alias, pfas_typ_translation_alias),
    SearchField.PFAS_HALTIGE_LOESCHMITTEL: (
        pfas_haltige_loeschmittel_code_alias,
        pfas_haltige_loeschmittel_translation_alias,
    ),
    SearchField.PFAS_FREIE_LOESCHMITTEL: (
        pfas_freie_loeschmittel_code_alias,
        pfas_freie_loeschmittel_translation_alias,
    ),
    SearchField.PFAS_LOESCHSCHAUM_EINSATZ: (
        loeschschaum_einsatz_code_alias,
        loeschschaum_einsatz_translation_alias,
    ),
    SearchField.PFAS_HAEUFIGKEIT_NUTZUNG: (
        pfas_haeufigkeit_nutzung_code_alias,
        pfas_haeufigkeit_nutzung_translation_alias,
    ),
    SearchField.KTU: (
        ktu_code_alias,
        ktu_translation_alias,
    ),
    SearchField.FLUGPLATZ_BEZEICHNUNG: (
        flugplatz_bezeichnung_code_alias,
        flugplatz_bezeichnung_translation_alias,
    ),
}

#
# List of TEXT fields whose underlying column may contain a translation key
# (msgid) instead of literal text, e.g. task titles generated from workflow
# templates. When filtering these fields, we
# additionally need to match against any translation of the key, since the
# literal column value is not necessarily human-readable text.
#
TEXT_TRANSLATION_KEY_COLUMNS: dict[SearchField, SQLColumnExpression[Any]] = {
    SearchField.TASK_TITEL: Node.title,
}


FTS_FIELDS = [
    Vflz.bezeichnung,
    Vflz.strasse,
    Vflz.ort,
    Vflz.combined_id,
    Vflz.bezeichnung,
    bemerkung_standort_alias.bem,
    bemerkung_umwelt_alias.bem,
    subjekt_beteiligter_alias.search_key(),
    Betrieb.firma_name,
    Node.note,
    Unfall.name,
    PFAS.name,
    KinderspielplatzGruenflaeche.name,
    begruendung_bewertung_alias.bem,
    begruendung_prio_untersuchung_alias.bem,
    begruendung_prio_sanierung_alias.bem,
    bemerkung_betrieb_alias.bem,
    bemerkung_ablagerung_alias.bem,
    bemerkung_unfall_alias.bem,
    bemerkung_massnahme_alias.bem,
    bemerkung_sanierung_alias.bem,
    bemerkung_umweltschaden_alias.bem,
    bemerkung_einzelereignis_alias.bem,
    begruendung_bew_betrieb_alias.bem,
    bemerkung_subjekt_alias.bem,
    bemerkung_pfas_alias.bem,
    bemerkung_kinderspielplatz_alias.bem,
    PFAS.beschreibungen_detail,
    begruendung_bew_pfas_alias.bem,
]


FTS_JOIN_FIELDS: list[SearchField] = [
    SearchField.BEZEICHNUNG,
    SearchField.STRASSE,
    SearchField.ORT,
    SearchField.STANDORTNUMMER,
    SearchField.BEZEICHNUNG,
    SearchField.GRUNDDATEN_BEMERKUNGEN,
    SearchField.UMWELT_BEMERKUNGEN,
    SearchField.BETEILIGTE,
    SearchField.FIRMA_NAME,
    SearchField.NOTIZ,
    SearchField.UNFALL_NAME,
    SearchField.PFAS_NAME,
    SearchField.KINDERSPIELPLATZ_NAME,
    SearchField.BEGRUENDUNG_BEURTEILUNG,
    SearchField.BEGRUENDUNG_PRIO_UNTERSUCHUNGSBEDARF,
    SearchField.BEGRUENDUNG_PRIO_SANIERUNGSBDEDARF,
    SearchField.FIRMA_BEMERKUNGEN,
    SearchField.KOMPARTIMENT_BEMERKUNGEN,
    SearchField.UNFALL_BEMERKUNG,
    SearchField.MASSNAHME_BEMERKUNG,
    SearchField.SANIERUNGSZIEL_BEMERKUNGEN,
    SearchField.UMWELTSCHADEN_BEMERKUNG,
    SearchField.BEMERKUNG_EINZELEREIGNIS,
    SearchField.BEGRUENDUNG_BEWERTUNG_BETRIEB,
    SearchField.BEMERKUNG_ADRESSE,
    SearchField.BEMERKUNG_PFAS,
    SearchField.KINDERSPIELPLATZ_BEMERKUNG,
    SearchField.PFAS_BESCHREIBUNGEN_DETAIL,
    SearchField.BEGRUENDUNG_BEWERTUNG_PFAS,
]


#
# Mapping from Language to Postgresq FTS search config name
#
FTS_CONFIG: dict[Language, str] = {
    Language.DE: "german",
    Language.FR: "french",
    Language.IT: "italian",
}
