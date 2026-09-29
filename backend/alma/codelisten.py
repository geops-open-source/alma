from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Mapper
from strawberry.utils.str_converters import to_camel_case

from alma.models import gem, subj
from alma.models import umwelt as mu
from alma.models import vflz as mv
from alma.models import workflow as wf
from alma.models.codes import Code

from . import constants as const

MAPPING_CODE_LISTS: dict[
    str,
    dict[
        str,
        list[const.CodeListe] | tuple[str, dict[str, const.CodeListe | None]],
    ],
] = {}


def map_code_lists(cls: type):
    mapper = inspect(cls)  # type: ignore
    assert isinstance(mapper, Mapper)
    for name, rel in mapper.relationships.items():
        if (
            issubclass(rel.mapper.entity, Code)
            and rel.mapper.polymorphic_identity is not None
        ):
            MAPPING_CODE_LISTS.setdefault(cls.__name__, {})[name] = [
                rel.mapper.polymorphic_identity
            ]


# Any new models with code fields need to be added here.
# TODO: Can we use a decorator based approach instead?
map_code_lists(mv.Objekt)
map_code_lists(mv.KompartimentStoffgruppe)
map_code_lists(mv.KompartimentStoffklasse)
map_code_lists(mv.Ablagerung)
map_code_lists(mv.Betrieb)
map_code_lists(mv.Schiessanlage)
map_code_lists(mv.Unfallstoff)
map_code_lists(mv.Unfall)
map_code_lists(mv.Beurteilung)
map_code_lists(mv.Massnahme)
map_code_lists(mv.Sanierungsziel)
map_code_lists(mv.Vflz)
map_code_lists(mu.Grundwasser)
map_code_lists(mu.OberflaechenGewaesser)
map_code_lists(mu.NutzungBoden)
map_code_lists(mu.UmweltStoff)
map_code_lists(mu.Einzelereignis)
map_code_lists(mu.Umweltschaden)
map_code_lists(gem.Gemeinde)
map_code_lists(mv.Vollzug)
map_code_lists(subj.Kontakt)
map_code_lists(subj.Subjekt)
map_code_lists(subj.BeteiligterStandort)
map_code_lists(wf.NodeKategorie)
map_code_lists(mv.PFAS)
map_code_lists(mv.KinderspielplatzGruenflaeche)
map_code_lists(mv.LoeschschaumEinsatz)

# Mappings with multiple possible lists.
# TODO changes here must be kept in sync with 'alma.search.core.CODELISTE_LOOKUP'!
MAPPING_CODE_LISTS.setdefault("KompartimentStoffgruppe", {}).update(
    {
        "stoffgruppe": [
            const.CodeListe.Stoffgruppen,
            const.CodeListe.StoffeKlasseI,
            const.CodeListe.StoffeKlasseII,
            const.CodeListe.StoffeKlasseIII,
            const.CodeListe.StoffeKlasseIV,
        ]
    }
)

MAPPING_CODE_LISTS.setdefault("BeteiligterStandort", {}).update(
    {
        "beziehungsart": [
            const.CodeListe.BeziehungsartEigentum,
            const.CodeListe.BeziehungsartSachbearbeitung,
            const.CodeListe.BeziehungsartSonstige,
        ]
    }
)

# Mappings where the codelist used for field A depends on the code of field B.
MAPPING_CODE_LISTS["NutzungBoden"].update(
    {
        "aktuelle_nutzung": (
            "nutzungsart",
            {
                const.Nutzungsart.WALD: const.CodeListe.FlaechennutzungWald,
                const.Nutzungsart.LANDWIRTSCHAFT: const.CodeListe.FlaechennutzungLandwirtschaft,
                const.Nutzungsart.UNGENUTZT: const.CodeListe.FlaechennutzungUngenutz,
                const.Nutzungsart.SIEDLUNGSGEBIET: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.ANDERE: None,
                const.Nutzungsart.KEINE_ANGABEN: None,
                const.Nutzungsart.GAERTEN: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.SPIELPLATZ: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.SPORT_FREIZEIT: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.GEWERBE_WOHNEN: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.GEWERBE: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.INDUSTRIE: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.VERSIEGELT: const.CodeListe.FlaechennutzungSiedlungsgebiet,
                const.Nutzungsart.BAUMSCHULEN_ZIERGAERTEN: const.CodeListe.FlaechennutzungLandwirtschaft,
            },
        ),
    }
)
MAPPING_CODE_LISTS["UmweltStoff"].update(
    {
        "stoff": (
            "stoff_gruppe",
            {
                const.Stoffgruppe.CKW: const.CodeListe.StoffgruppeCKW,
                const.Stoffgruppe.Schwermetalle: const.CodeListe.StoffgruppeSchwermetalle,
                const.Stoffgruppe.MKW: const.CodeListe.StoffgruppeMKW,
                const.Stoffgruppe.BTEX: const.CodeListe.StoffgruppeBTEX,
                const.Stoffgruppe.PAK: const.CodeListe.StoffgruppePAK,
                const.Stoffgruppe.Dioxine: const.CodeListe.StoffgruppeDioxine,
                const.Stoffgruppe.PCB: const.CodeListe.StoffgruppePCB,
                const.Stoffgruppe.PFAS: const.CodeListe.StoffgruppePFAS,
                const.Stoffgruppe.Nichtmetalle: const.CodeListe.StoffgruppeNichtmetalle,
                const.Stoffgruppe.HalogenierteKW: const.CodeListe.StoffgruppeHalogenierteKW,
                const.Stoffgruppe.Freone: const.CodeListe.StoffgruppeFreone,
                const.Stoffgruppe.Sonstige: const.CodeListe.StoffgruppeSonstige,
                const.Stoffgruppe.BenzinartigeKW: const.CodeListe.StoffgruppeBenzinartige,
                const.Stoffgruppe.Phenole: const.CodeListe.StoffgruppePhenole,
            },
        ),
    }
)
MAPPING_CODE_LISTS["Umweltschaden"].update(
    {
        "schaeden": (
            "art_schaden",
            {
                const.Umweltbereich.Keiner: None,
                const.Umweltbereich.Grundwasser: const.CodeListe.UmweltschaedenWasser,
                const.Umweltbereich.Oberflaechengewaesser: const.CodeListe.UmweltschaedenWasser,
                const.Umweltbereich.Luft: const.CodeListe.UmweltschaedenLuft,
                const.Umweltbereich.Boden: const.CodeListe.UmweltschaedenBoden,
                const.Umweltbereich.NichtBekannt: None,
            },
        ),
    }
)
MAPPING_CODE_LISTS["LoeschschaumEinsatz"].update(
    {
        "haeufigkeit_nutzung": (
            "loeschschaum_einsatz",
            {
                const.LoeschschaumEinsatz.HANDLÖSCHER: const.CodeListe.HaeufigkeitNutzungHandfeuerloescher,
                const.LoeschschaumEinsatz.BEIMISCHER: const.CodeListe.HaeufigkeitNutzungBeimischer,
                const.LoeschschaumEinsatz.TANKLÖSCHER: const.CodeListe.HaeufigkeitNutzungTankloescher,
            },
        )
    }
)

# For GraphQL output, translate the MAPPING_CODE_LISTS by resolving code constants into
# their string form ("code:<list-id>:<value>"), and translate field names to camelCase.
MAPPING_CODE_LISTS_TRANSLATED: dict[str, Any] = {}

for type_name, field_map in MAPPING_CODE_LISTS.items():
    MAPPING_CODE_LISTS_TRANSLATED[type_name] = {}
    for field_name, value in field_map.items():
        field_name = to_camel_case(field_name)
        if isinstance(value, tuple):
            discriminator_field, value_map = value
            discriminator_value = field_map[discriminator_field]
            assert (
                isinstance(discriminator_value, list) and len(discriminator_value) == 1
            )
            discriminator_list_id = discriminator_value[0]
            MAPPING_CODE_LISTS_TRANSLATED[type_name][field_name] = [
                to_camel_case(discriminator_field),
                {},
            ]
            for code_value, list_id in value_map.items():
                translated_code = f"code:{discriminator_list_id}:{code_value}"
                MAPPING_CODE_LISTS_TRANSLATED[type_name][field_name][1][
                    translated_code
                ] = list_id
        else:
            MAPPING_CODE_LISTS_TRANSLATED[type_name][field_name] = value

# These objects only exists at the GraphQL level
MAPPING_CODE_LISTS_TRANSLATED["ZeitraumMitGenauigkeit"] = {
    "genauigkeitVon": [const.CodeListe.Genauigkeit],
    "genauigkeitBis": [const.CodeListe.Genauigkeit],
}
MAPPING_CODE_LISTS_TRANSLATED["Beurteilung"]["rechtlicherBezug"] = [
    const.CodeListe.RechtlicherBezug
]
MAPPING_CODE_LISTS_TRANSLATED["Beurteilung"]["handlungsbedarf"] = [
    const.CodeListe.Handlungsbedarf
]

MAPPING_CODE_LISTS_TRANSLATED["BeteiligterStandort"]["beziehungsart"] = [
    const.CodeListe.BeziehungsartSonstige,
]
MAPPING_CODE_LISTS_TRANSLATED["SachbearbeiterStandort"] = MAPPING_CODE_LISTS_TRANSLATED[
    "BeteiligterStandort"
].copy()
MAPPING_CODE_LISTS_TRANSLATED["SachbearbeiterStandort"]["beziehungsart"] = [
    const.CodeListe.BeziehungsartSachbearbeitung
]
MAPPING_CODE_LISTS_TRANSLATED["EigentuemerStandort"] = MAPPING_CODE_LISTS_TRANSLATED[
    "BeteiligterStandort"
].copy()
MAPPING_CODE_LISTS_TRANSLATED["EigentuemerStandort"]["beziehungsart"] = [
    const.CodeListe.BeziehungsartEigentum
]


MAPPING_CODE_LISTS_TRANSLATED["Task"] = MAPPING_CODE_LISTS_TRANSLATED.pop(
    "NodeKategorie"
)
MAPPING_CODE_LISTS_TRANSLATED["Vflz"]["ktu"] = [const.CodeListe.KTU]
MAPPING_CODE_LISTS_TRANSLATED["Vflz"]["flugplatz"] = [
    const.CodeListe.FlugplatzBezeichnung
]
