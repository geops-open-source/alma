from enum import IntEnum, StrEnum, unique


@unique
class Language(StrEnum):
    DE = "de"
    FR = "fr"
    IT = "it"


@unique
class CodeListe(IntEnum):
    Land = 14
    Kanton = 15
    BeziehungsartEigentum = 2200
    BeziehungsartSonstige = 2201
    BeziehungsartSachbearbeitung = 2202
    BeziehungsartGeschaefte = 2203
    KontaktTyp = 33
    StandortTyp = 63
    JaNeinUnbekannt = 80
    Genauigkeit = 90
    Stoffklasse = 94
    Stoffgruppen = 110
    StoffeKlasseI = 111
    StoffeKlasseII = 112
    StoffeKlasseIII = 113
    StoffeKlasseIV = 115
    BrancheASW = 25
    BrancheNOGA = 25001
    UntersuchungsStand = 10023
    Beurteilung = 103
    RechtlicherBezug = 10104
    Handlungsbedarf = 10105
    Stoff = 117
    NutzungGrundwasserAbstrom = 88
    RelativeLageGrundwasser = 71
    RelativeLageOberflaechenGewaesser = 70
    GewaesserArt = 66
    GewaesserBau = 67
    GefaehrdeteUmweltbereiche = 299
    UmweltStoffgruppe = 300
    StoffgruppeCKW = 301
    StoffgruppeSchwermetalle = 302
    StoffgruppeMKW = 303
    StoffgruppeBTEX = 304
    StoffgruppePAK = 305
    StoffgruppeDioxine = 306
    StoffgruppePCB = 307
    StoffgruppePFAS = 308
    StoffgruppeBenzinartige = 309
    StoffgruppeNichtmetalle = 310
    StoffgruppeHalogenierteKW = 311
    StoffgruppeFreone = 312
    StoffgruppeSonstige = 313
    StoffgruppePhenole = 314
    UmweltStoffBeurteilung = 330
    Einzelereignis = 61
    Umweltbereich = 101
    UmweltschaedenBoden = 99
    UmweltschaedenLuft = 100
    UmweltschaedenWasser = 102
    Massnahme = 10021
    Sanierungsziel = 10020
    SchiessanlageTyp = 11410
    Flaechennutzung = 87
    FlaechennutzungWald = 104
    FlaechennutzungLandwirtschaft = 83
    FlaechennutzungSiedlungsgebiet = 92
    FlaechennutzungUngenutz = 97
    DeponieTyp = 12001
    Gewaesserschutzbereiche = 10017
    Gewaesserschutzzonen = 10018
    Durchlaessigkeit = 58
    Bearbeitungsstand = 55
    StatusParzelle = 26000
    PrioUntersuchung = 26020
    PrioSanierung = 26021
    SubjektKategorie = 10019
    Anrede = 31
    BehoerdenKuerzel = 26030
    BehoerdenLangBezeichnung = 26031
    TaskTyp = 30000
    TaskStatus = 30001
    TaskKategorie = 10022
    BranchePFAS = 25002
    PFASTyp = 500
    LoeschmittelPFASHaltig = 501
    LoeschmittelPFASFrei = 502
    LoeschschaumEinsatz = 503
    HaeufigkeitNutzungHandfeuerloescher = 504
    HaeufigkeitNutzungBeimischer = 505
    HaeufigkeitNutzungTankloescher = 506
    KTU = 210
    KinderspielplatzGruenflaecheTyp = 400
    Eigentumsform = 401
    AltersstufeKinder = 402
    FlugplatzBezeichnung = 600
    BeurteilungGruppe = 1031


READ_ONLY_CODE_LISTS: list[CodeListe] = [
    CodeListe.StandortTyp,
    CodeListe.UmweltStoffgruppe,
    CodeListe.Umweltbereich,
    CodeListe.KontaktTyp,
    CodeListe.Flaechennutzung,
    CodeListe.FlugplatzBezeichnung,
]


@unique
class KategorieBemerkung(IntEnum):
    Standort = 1
    Betrieb = 2
    Ablagerung = 3
    Unfall = 4
    Umwelt = 5
    Subjekt = 6
    Intern = 8
    Bewertung = 9
    PrioUntersuchung = 10
    PrioSanierung = 11
    Massnahme = 13
    Sanierung = 14
    Umweltschaden = 15
    Einzelereignis = 16
    BegruendungBewertungBetrieb = 17
    PFAS = 20
    BegruendungBewertungPFAS = 21
    KinderspielplatzGruenflaeche = 18
    BegruendungBewertungKinderspielplatzGruenflaeche = 19
    DatenimportAblagerung = 22
    DatenimportBetrieb = 23
    DatenimportUnfall = 24
    DatenimportSchiessanlage = 25
    DatenimportKinderspielplatzGruenflaeche = 26
    DatenimportPFAS = 27
    DatenimportStandort = 28


@unique
class StandortTyp(StrEnum):
    ABLAGERUNG = "01"
    BETRIEB = "02"
    UNFALL = "03"
    SCHIESSANLAGE = "04"
    KINDERSPIELPLATZ_GRUENFLAECHE = "05"
    PFAS = "06"


@unique
class Nutzungsart(StrEnum):
    WALD = "01"
    LANDWIRTSCHAFT = "02"
    UNGENUTZT = "03"
    SIEDLUNGSGEBIET = "04"
    ANDERE = "05"
    KEINE_ANGABEN = "06"
    GAERTEN = "07"
    SPIELPLATZ = "08"
    SPORT_FREIZEIT = "09"
    GEWERBE_WOHNEN = "10"
    GEWERBE = "11"
    INDUSTRIE = "12"
    VERSIEGELT = "13"
    BAUMSCHULEN_ZIERGAERTEN = "14"


@unique
class Stoffgruppe(StrEnum):
    CKW = "01"
    Schwermetalle = "02"
    MKW = "03"
    BTEX = "04"
    PAK = "05"
    Dioxine = "06"
    PCB = "07"
    PFAS = "08"
    BenzinartigeKW = "09"
    Nichtmetalle = "10"
    HalogenierteKW = "11"
    Freone = "12"
    Sonstige = "13"
    Phenole = "14"


@unique
class Umweltbereich(StrEnum):
    Keiner = "01"
    Grundwasser = "02"
    Oberflaechengewaesser = "03"
    Luft = "04"
    Boden = "05"
    NichtBekannt = "06"


@unique
class KontaktTyp(StrEnum):
    PHONE_BUSINESS = "1"
    PHONE_PRIVATE = "2"
    EMAIL_BUSINESS = "EMAIL"
    EMAIL_PRIVATE = "4"
    MOBILE = "NATEL"
    WEB = "WWW"


@unique
class StatusParzelle(StrEnum):
    AKTUELL = "1"
    NICHT_AKTUELL = "0"


@unique
class LoeschschaumEinsatz(StrEnum):
    HANDLÖSCHER = "hand"
    BEIMISCHER = "bei"
    TANKLÖSCHER = "tank"


LV_95_SRID = 2056
