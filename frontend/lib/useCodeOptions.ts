import { gql } from "graphql-request";
import { useMemo } from "react";
import { useFormContext } from "react-hook-form";
import useSWRImmutable from "swr/immutable";

import { useI18n } from "@/lib/i18n";
import { useModelContext } from "@/lib/modelContext";

import type { CodeListsQuery } from "@/lib/graphql";

type MappingModel =
  | "BeteiligterParzelle"
  | "BeteiligterStandort"
  | "Betrieb"
  | "Beurteilung"
  | "Einzelereignis"
  | "Gemeinde"
  | "Grundwasser"
  | "KinderspielplatzGruenflaeche"
  | "KompartimentStoffgruppe"
  | "KompartimentStoffklasse"
  | "Kontakt"
  | "Massnahme"
  | "NutzungBoden"
  | "OberflaechenGewaesser"
  | "Sanierungsziel"
  | "Schiessanlage"
  | "Subjekt"
  | "Task"
  | "Umweltschaden"
  | "UmweltStoff"
  | "Unfall"
  | "Unfallstoff"
  | "Vflz"
  | "Vollzug"
  | "ZeitraumMitGenauigkeit";

type MappingField =
  | "aktuelleNutzung"
  | "altersstufenKinder"
  | "anrede"
  | "artGewaesser"
  | "artSchaden"
  | "bauGewaesser"
  | "bearbeitungsStand"
  | "behoerde"
  | "beurteilung"
  | "beziehungsart"
  | "branche"
  | "brancheAsw"
  | "brancheNoga"
  | "deponietyp"
  | "durchlaessigkeit"
  | "eigentumsform"
  | "einzelereignis"
  | "flugplatz"
  | "gefaehrdeteBereiche"
  | "genauigkeitBis"
  | "genauigkeitVon"
  | "genauigkeitZeitpunkt"
  | "gwsBereich"
  | "gwsZone"
  | "haeufigkeitNutzung"
  | "handlungsbedarf"
  | "kanton"
  | "karstgeb"
  | "kategorie"
  | "kategorien"
  | "kinderspielplatzGruenflacheTyp"
  | "kontaktTyp"
  | "ktu"
  | "land"
  | "loeschschaumEinsatz"
  | "massnahme"
  | "nutzung"
  | "nutzungsart"
  | "pfasFreieLoeschmittel"
  | "pfasHaltigeLoeschmittel"
  | "pfasTyp"
  | "prioSanier"
  | "prioUntersuch"
  | "rechtlicherBezug"
  | "relativeLage"
  | "sanierungsziel"
  | "schaeden"
  | "stoff"
  | "stoffGruppe"
  | "stoffgruppe"
  | "stoffklasse"
  | "typ"
  | "untersuchungsStand"
  | "vftyp";

type Result = [string, Record<string, number>] | number[];

interface MappingQuery {
  mappingCodelisten: Record<MappingModel, Record<MappingField, Result>>;
}

const queryMapping = gql`
  query mapping {
    mappingCodelisten
  }
`;

const queryCodeLists = gql`
  query codeLists($cliIds: [ID!]!) {
    codeLists(cliIds: $cliIds) {
      results {
        entries {
          code
          isActive
        }
      }
    }
  }
`;

export interface Props {
  name: `${string}.${MappingField}` | MappingField;
  required?: boolean;
}

export default function useCodeOptions({ name, required }: Props) {
  const { t } = useI18n();
  const { watch } = useFormContext();
  const model = useModelContext() as MappingModel;
  const { data: mapping } = useSWRImmutable<MappingQuery>(queryMapping);

  let cliId: null | string | undefined;
  let cliIds: string[] | undefined;
  const fieldName = name.split(".").at(-1) as MappingField;
  const result = mapping?.mappingCodelisten[model][fieldName];
  if (result && result.length > 0) {
    if (
      result.every((r) => {
        return Number.isInteger(r);
      })
    ) {
      cliIds = result.map((r) => {
        return (r as number).toString();
      });
    } else if (typeof result[0] === "string" && typeof result[1] === "object") {
      const fieldNameRegExp = new RegExp(`${fieldName}$`);
      const dependingFieldName = name.replace(fieldNameRegExp, result[0]);
      const dependingFieldValue = watch(dependingFieldName) as string;
      cliId = Number.isInteger(result[1][dependingFieldValue])
        ? result[1][dependingFieldValue].toString()
        : null;
      cliIds = Object.values(result[1])
        .filter((c) => {
          return Number.isInteger(c);
        })
        .map((c) => {
          return c.toString();
        });
    }
  }

  const { data } = useSWRImmutable<CodeListsQuery>(
    cliIds && [queryCodeLists, { cliIds }],
  );

  const options = useMemo(() => {
    let originalSortIndex = 0;
    return [
      ...(required ? [] : [{ label: "-", originalSortIndex: -1, value: null }]),
      ...(data?.codeLists.results
        .flatMap((codeList) => {
          return codeList.entries;
        })
        .filter((c) => {
          return cliId === undefined || c.code.startsWith(`code:${cliId}:`);
        })
        .map((c) => {
          return {
            disabled: !c.isActive,
            label:
              cliIds && cliIds.length > 1 && cliId === undefined
                ? `${t(`codelist:${c.code.split(":").at(1)}`)}: ${t(c.code)}`
                : t(c.code),
            originalSortIndex: originalSortIndex++,
            value: c.code,
          };
        }) ?? []),
    ];
  }, [required, cliId, cliIds, data, t]);

  return options;
}
