import { gql } from "graphql-request";
import dynamic from "next/dynamic";
import { useEffect, useMemo } from "react";
import { useFormContext } from "react-hook-form";
import useSWRImmutable from "swr/immutable";

import Button from "@/components/Button";
import DatePicker from "@/components/DatePicker";
import Form from "@/components/Form";
import Listbox from "@/components/Listbox";
import VflzMapFragment from "@/components/VflzMap.fragment";
import VflzSachbearbeiter from "@/components/VflzSachbearbeiter";
import VflzSummary from "@/components/VflzSummary";
import WorkflowList from "@/components/Workflow/List";
import { workflowItemFragment } from "@/components/Workflow/queries";
import { useI18n } from "@/lib/i18n";
import useCurrentUser from "@/lib/useCurrentUser";
import useSetting from "@/lib/useSetting";

import type { PropsWithChildren } from "react";

import type {
  BeteiligteFieldSubjektFragment,
  ReportConfigQuery,
  VflzOverviewFragment,
} from "@/lib/graphql";

const VflzMap = dynamic(
  () => {
    return import("@/components/VflzMap");
  },
  {
    loading: () => {
      return <div className="bg-gray-4 h-96 w-96 rounded-lg" />;
    },
    ssr: false,
  },
);

function ReportDownloadIcon() {
  return (
    <svg fill="none" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M16.667 10.417v-4.75c0-1.4 0-2.1-.273-2.635a2.5 2.5 0 0 0-1.092-1.093c-.535-.272-1.235-.272-2.635-.272H7.333c-1.4 0-2.1 0-2.635.272a2.5 2.5 0 0 0-1.092 1.093c-.273.534-.273 1.235-.273 2.635v8.666c0 1.4 0 2.1.273 2.635a2.5 2.5 0 0 0 1.092 1.093c.535.272 1.235.272 2.635.272h3.084m1.25-9.166h-5M8.333 12.5H6.667m6.666-6.667H6.667m5.833 10 2.5 2.5m0 0 2.5-2.5m-2.5 2.5v-5"
        stroke="#fff"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

const queryReportConfig = gql`
  query reportConfig {
    reportConfigurations(context: STANDORT) {
      reportId
      params {
        name
        paramType
      }
      title
    }
  }
`;

function ReportForm({ lang }: { lang?: string }) {
  const { activeLocale, t } = useI18n();
  const { reset } = useFormContext();
  const { data } = useSWRImmutable<ReportConfigQuery>(queryReportConfig);
  const languageOptions = useMemo(() => {
    return [
      { label: t("language.DE"), value: "de" },
      { label: t("language.FR"), value: "fr" },
      { label: t("language.IT"), value: "it" },
    ];
  }, [t]);

  useEffect(() => {
    if (!data) {
      return;
    }
    if (data.reportConfigurations.length < 1) {
      return;
    }

    reset({
      date: new Date().toISOString().split("T")[0],
      language: (lang ?? activeLocale).toLowerCase(),
      reportId: data?.reportConfigurations[0].reportId,
    });
  }, [activeLocale, data, lang, reset]);

  return (
    <div className="flex max-w-96 flex-col gap-4">
      <Listbox
        name="reportId"
        options={data?.reportConfigurations.map((r) => {
          return {
            label: t(r.title),
            value: r.reportId,
          };
        })}
        required={true}
      />
      <Listbox name="language" options={languageOptions} />
      <DatePicker name="date" />
      <Button className="flex w-fit space-x-1.5" type="submit">
        <ReportDownloadIcon />
        <span>{t("fields.Report.submit")}</span>
      </Button>
    </div>
  );
}

function VflzReport({ lang, vflzId }: { lang?: string; vflzId: string }) {
  const { activeLocale, t } = useI18n();

  return (
    <div>
      <h3 className="my-4 font-semibold">{t("fields.Report.heading")}</h3>
      <Form
        model="Report"
        onSubmit={(v) => {
          const params = new URLSearchParams({
            date: new Date(v.date ? (v.date as string) : "").toISOString(),
            language: (v.language ?? activeLocale) as string,
            vflz_id: vflzId,
          });
          window.open(`/api/report/${v.reportId}?${params}`);
        }}
      >
        <ReportForm lang={lang} />
      </Form>
    </div>
  );
}

function List({ children, ...props }: PropsWithChildren) {
  return (
    <dl className="grid grid-cols-3 gap-y-1 py-4 text-sm" {...props}>
      {children}
    </dl>
  );
}

function ListItem({
  children,
  className = "flex items-center space-x-2",
  title,
}: PropsWithChildren<{ className?: string; title: string }>) {
  return (
    <>
      <dt className="hyphens-auto">{title}</dt>
      <dd className={`col-span-2 font-medium ${className}`}>{children}</dd>
    </>
  );
}

interface GemeindeParzellen {
  gemeinde?: string;
  nummerierungsbereich?: string;
  withoutSubjekt: { parzellen: string[] }[];
  withSubjekt: {
    parzellen: string[];
    subjekt?: BeteiligteFieldSubjektFragment | null;
  }[];
}

type GemeindeEntry = [string, GemeindeParzellen];
type EigentumEntry = NonNullable<VflzOverviewFragment["eigentum"]>[number];

const naturalSortCollator = new Intl.Collator("de", {
  numeric: true,
  sensitivity: "base",
});

function sortStringsNaturally(values: string[]) {
  return [...values].sort((left, right) => {
    return naturalSortCollator.compare(left, right);
  });
}

function compareNatural(left?: string, right?: string) {
  return naturalSortCollator.compare(left ?? "", right ?? "");
}

function getSubjektDisplayValue(subjekt: BeteiligteFieldSubjektFragment) {
  const name = [subjekt.vorname, subjekt.name].filter(Boolean).join(" ");
  return `${name}${name && subjekt.taetigkeit ? ", " : ""}${subjekt.taetigkeit}`;
}

function GemeindeHeading({
  gemeinde,
  nummerierungsbereich,
}: {
  gemeinde?: string;
  nummerierungsbereich?: string;
}) {
  if (!gemeinde && !nummerierungsbereich) {
    return null;
  }

  if (!nummerierungsbereich) {
    return <span className="font-bold">{gemeinde}</span>;
  }

  return (
    <div className="flex flex-wrap items-baseline gap-x-2">
      <span className="font-bold">{gemeinde}</span>
      <span className="text-sm font-normal">{nummerierungsbereich}</span>
    </div>
  );
}

function getGemeindeData(
  eigentum: EigentumEntry,
  displayType: string,
): Pick<GemeindeParzellen, "gemeinde" | "nummerierungsbereich"> {
  const gemeinde = eigentum.gemeinde?.displayValue ?? undefined;
  const nummerierungsbereich =
    eigentum.nummerierungsbereich?.bezeichnung ?? undefined;

  if (displayType === "nummerierungsbereich") {
    return {
      gemeinde: nummerierungsbereich,
      nummerierungsbereich: undefined,
    };
  }

  return {
    gemeinde,
    nummerierungsbereich:
      displayType === "both" ? nummerierungsbereich : undefined,
  };
}

function createGemeindeParzellen(
  eigentum: EigentumEntry,
  displayType: string,
): GemeindeParzellen {
  return {
    ...getGemeindeData(eigentum, displayType),
    withoutSubjekt: [],
    withSubjekt: [],
  };
}

function mergeParzellen(existingParzellen: string[], nextParzellen: string[]) {
  return sortStringsNaturally(
    Array.from(new Set([...existingParzellen, ...nextParzellen])),
  );
}

function addEigentumToGroup(group: GemeindeParzellen, eigentum: EigentumEntry) {
  if (eigentum.subjekt) {
    const existingSubjekt = group.withSubjekt.find((entry) => {
      return entry.subjekt?.subjId === eigentum.subjekt?.subjId;
    });

    if (existingSubjekt) {
      existingSubjekt.parzellen = mergeParzellen(
        existingSubjekt.parzellen,
        eigentum.parzellen,
      );
      return;
    }

    group.withSubjekt.push({
      ...eigentum,
      parzellen: sortStringsNaturally(eigentum.parzellen),
    });
    return;
  }

  group.withoutSubjekt.push({
    ...eigentum,
    parzellen: sortStringsNaturally(eigentum.parzellen),
  });
}

function sortGemeindeParzellen(group: GemeindeParzellen): GemeindeParzellen {
  return {
    ...group,
    withSubjekt: [...group.withSubjekt].sort((left, right) => {
      return compareNatural(
        left.subjekt ? getSubjektDisplayValue(left.subjekt) : undefined,
        right.subjekt ? getSubjektDisplayValue(right.subjekt) : undefined,
      );
    }),
  };
}

function sortGemeindeEntries(entries: GemeindeEntry[]) {
  return [...entries].sort(([, left], [, right]) => {
    return compareNatural(left.gemeinde, right.gemeinde);
  });
}

function useParzellenEigentumEntries({
  displayType,
  eigentum,
}: {
  displayType: string;
  eigentum: undefined | VflzOverviewFragment["eigentum"];
}) {
  return useMemo(() => {
    const groupedByBfsAndSubj = eigentum?.reduce(
      (acc, eigentumEntry) => {
        let key: null | number | string | undefined =
          eigentumEntry.gemeinde?.bfsNummer ?? null;
        if (!key && displayType === "nummerierungsbereich") {
          key = eigentumEntry?.nummerierungsbereich?.bezeichnung;
        }
        if (key == null || eigentumEntry.parzellen.length === 0) {
          return acc;
        }

        const group =
          acc[key] ?? createGemeindeParzellen(eigentumEntry, displayType);
        addEigentumToGroup(group, eigentumEntry);
        acc[key] = group;

        return acc;
      },
      {} as Record<number | string, GemeindeParzellen>,
    );

    if (!groupedByBfsAndSubj) {
      return { withoutSubjektEntries: [], withSubjektEntries: [] };
    }

    const withSubjektEntries: GemeindeEntry[] = [];
    const withoutSubjektEntries: GemeindeEntry[] = [];

    for (const [bfs, data] of Object.entries(groupedByBfsAndSubj)) {
      if (data.withSubjekt.length > 0) {
        withSubjektEntries.push([bfs, sortGemeindeParzellen(data)]);
      }
      if (data.withoutSubjekt.length > 0) {
        withoutSubjektEntries.push([bfs, data]);
      }
    }

    return {
      withoutSubjektEntries: sortGemeindeEntries(withoutSubjektEntries),
      withSubjektEntries: sortGemeindeEntries(withSubjektEntries),
    };
  }, [displayType, eigentum]);
}

function ParzellenEigentum({ vflz }: { vflz?: VflzOverviewFragment }) {
  const { t } = useI18n();
  const [displayType] = useSetting<string>(
    "ui.display.gemeindenUndNummerierungsbereiche",
    "gemeinde",
  );

  const { withoutSubjektEntries, withSubjektEntries } =
    useParzellenEigentumEntries({
      displayType,
      eigentum: vflz?.eigentum,
    });

  if (withSubjektEntries.length === 0 && withoutSubjektEntries.length === 0) {
    return null;
  }

  return (
    <>
      {withSubjektEntries.length > 0 && (
        <List>
          <ListItem title={t("VflzOverview.parzellenWithEigentum")}>
            <div className="space-y-2">
              {withSubjektEntries.map(([bfsNummer, data]) => {
                return (
                  <div
                    data-test="VflzOverview-parzellen-mit-eigentum"
                    key={`bfs_with_${bfsNummer}`}
                  >
                    <h3>
                      <GemeindeHeading {...data} />
                    </h3>
                    {data.withSubjekt.map((e) => {
                      return (
                        e.subjekt && (
                          <div key={`subj${e.subjekt.subjId}`}>
                            <span className="my-1 mr-2">
                              {getSubjektDisplayValue(e.subjekt)}:
                            </span>
                            {e.parzellen.join(", ")}
                          </div>
                        )
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </ListItem>
        </List>
      )}
      {withoutSubjektEntries.length > 0 && (
        <List>
          <ListItem title={t("VflzOverview.parzellenWithoutEigentum")}>
            <div className="space-y-2">
              {withoutSubjektEntries.map(([bfsNummer, data]) => {
                return (
                  <div
                    data-test="VflzOverview-parzellen-ohne-eigentum"
                    key={`bfs_without_${bfsNummer}`}
                  >
                    <h3>
                      <GemeindeHeading {...data} />
                    </h3>
                    <span>
                      {sortStringsNaturally(
                        data.withoutSubjekt.flatMap((e) => {
                          return e.parzellen;
                        }),
                      ).join(", ")}
                    </span>
                  </div>
                );
              })}
            </div>
          </ListItem>
        </List>
      )}
    </>
  );
}

function SonstigeBeteiligte({ vflz }: { vflz: VflzOverviewFragment }) {
  const beteiligte = Array.from(
    new Map(
      vflz.sonstigeBeteiligte.map((b) => {
        return [b.beteiligter.subjekt?.subjId, b.beteiligter.subjekt];
      }),
    ).values(),
  ).sort((left, right) => {
    return naturalSortCollator.compare(
      getSubjektDisplayValue(left),
      getSubjektDisplayValue(right),
    );
  });
  return (
    <div>
      {beteiligte.map((b) => {
        return (
          <span className="block pr-3" key={b.subjId}>
            {getSubjektDisplayValue(b)}
          </span>
        );
      })}
    </div>
  );
}

function TasksButton({ vflz }: { vflz: VflzOverviewFragment }) {
  const { t } = useI18n();
  const numResults = vflz?.geschaefte?.numResultsTotal ?? 0;
  return (
    <Button
      className="text-gray-7 mt-4 w-full text-sm"
      href={`/vflz/${vflz?.vflzId}/workflow${numResults > 5 ? "?status=OFFEN" : ""}`}
      outline={true}
    >
      {numResults > 5
        ? t("workflow.showAllOpen", {
            count: vflz?.geschaefte?.numResultsTotal.toString() ?? "",
          })
        : t("workflow.showAll")}
    </Button>
  );
}

function VflzOverview({
  className,
  hideMapControls = false,
  showReport = false,
  vflz,
}: {
  className?: string;
  hideMapControls?: boolean;
  showReport?: boolean;
  vflz?: VflzOverviewFragment;
}) {
  const { t } = useI18n();
  const { permissions } = useCurrentUser();
  return (
    <div className="@container scroll-mt-32" id="content">
      <div
        className={`border-gray-4 flex flex-wrap gap-5 rounded-lg border bg-white p-5 @2xl:flex-nowrap ${className}`}
        data-test="VflzOverview"
      >
        <div className="order-last w-full shrink-0 @2xl:order-0 @2xl:w-96">
          <VflzMap
            className="h-96"
            hideControls={hideMapControls}
            hideZentroid
            updateExtent
            vflz={vflz}
          />
          {showReport && vflz?.vflzId && (
            <VflzReport lang={vflz.lang} vflzId={vflz.vflzId} />
          )}
        </div>
        <div className="divide-gray-4 text-gray-7 grow divide-y">
          <VflzSummary className="pb-4" vflz={vflz} />
          <List data-test="VflzOverview-beurteilung">
            <ListItem title={t("fields.Vflz.bearbeitungsStand")}>
              {vflz?.bearbeitungsStand ? t(vflz.bearbeitungsStand) : "-"}
            </ListItem>
            <ListItem title={t("fields.Vflz.untersuchungsStand")}>
              {vflz?.untersuchungsStand ? t(vflz.untersuchungsStand) : "-"}
            </ListItem>
          </List>
          <List>
            <ListItem title={t("VflzOverview.beteiligteStandort")}>
              <VflzSachbearbeiter
                beteiligteStandort={vflz?.beteiligteStandort}
              />
            </ListItem>
          </List>
          <ParzellenEigentum vflz={vflz} />
          <List>
            <ListItem title={t("VflzOverview.sonstigeBeteiligte")}>
              {vflz && <SonstigeBeteiligte vflz={vflz} />}
            </ListItem>
          </List>
          {permissions.canViewProcess && (
            <List>
              <ListItem title={t("workflow.openTasks")}>
                <div className="flex w-full flex-col">
                  {vflz?.geschaefte?.numResultsTotal ? (
                    <WorkflowList
                      compactView={true}
                      items={vflz ? vflz.geschaefte?.results : []}
                      withVflzInfo={false}
                    />
                  ) : (
                    <div>{t("workflow.noneOpen")}</div>
                  )}
                  {vflz && <TasksButton vflz={vflz} />}
                </div>
              </ListItem>
            </List>
          )}
        </div>
      </div>
    </div>
  );
}

VflzOverview.fragment = gql`
  fragment VflzOverview on Vflz {
    vflzId
    lang
    bearbeitungsStand
    untersuchungsStand
    parzellen {
      gbNummer
      gemeinde {
        displayValue
      }
      nummerierungsbereich {
        bezeichnung
      }
    }
    eigentum {
      subjekt {
        subjId
        vorname
        name
        taetigkeit
      }
      parzellen
      gemeinde {
        bfsNummer
        displayValue
      }
      nummerierungsbereich {
        bezeichnung
      }
    }
    sonstigeBeteiligte {
      beteiligter {
        subjekt {
          subjId
          vorname
          name
          taetigkeit
        }
      }
    }
    geschaefte(
      asTree: false
      sortBy: Faelligkeit
      page: 1
      perPage: 5
      filter: {
        status: OFFEN
        eigene: null
        faelligkeit: null
        taskTyp: null
        teilflaechen: null
        titel: null
      }
    ) @include(if: $withGeschaefte) {
      numResultsTotal
      results {
        ...WorkflowItem
      }
    }
    ...VflzSachbearbeiter
    ...VflzSummary
    ...VflzMap
  }
  ${workflowItemFragment}
  ${VflzMapFragment}
  ${VflzSachbearbeiter.fragment}
`;

export default VflzOverview;
