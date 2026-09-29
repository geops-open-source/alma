import { gql } from "graphql-request";
import dynamic from "next/dynamic";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import AddToPoolDialog from "@/components/AddToPoolDialog";
import Button from "@/components/Button";
import PoolIcon from "@/components/icons/PoolIcon";
import SaveIcon from "@/components/icons/SaveIcon";
import Layout from "@/components/Layout";
import { Menu, MenuItem } from "@/components/Menu";
import SearchFieldSelector from "@/components/SearchLayout/SearchFieldSelector";
import StableWidthText from "@/components/StableWidthText";
import Switch from "@/components/Switch";
import client from "@/lib/client";
import {
  SearchExportFormat,
  SearchExportStatus,
  SearchField,
} from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import { makeSimpleSearchQuery } from "@/lib/search";
import useCurrentUser from "@/lib/useCurrentUser";

import SavedSearch from "./SavedSearch";
import { SearchResultsPreview } from "./SearchResultsPreview";
import SearchResultsTable from "./SearchResultsTable";

import type { ReactNode } from "react";

import type {
  ExportSearchMutation,
  QuerySearchArgs,
  SavedSearchFragment,
  SearchFilter,
} from "@/lib/graphql";
import type { QuerySimpleSearchArgs } from "@/lib/search";

const SearchResultsMap = dynamic(
  () => {
    return import("./SearchResultsMap");
  },
  {
    loading: () => {
      return (
        <div className="bg-gray-4 h-[calc(100vh-10rem)] w-full rounded-lg" />
      );
    },
    ssr: false,
  },
);

type ResultsMode = "map" | "preview" | "table";

const exportSearch = gql`
  mutation exportSearch($data: ExportSearchInput!) {
    exportId: exportSearch(data: $data)
  }
`;

function TableIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M2.5 7.5h15m-10-5v15m-1-15h7c1.4 0 2.1 0 2.635.272a2.5 2.5 0 0 1 1.092 1.093C17.5 4.4 17.5 5.1 17.5 6.5v7c0 1.4 0 2.1-.273 2.635a2.5 2.5 0 0 1-1.092 1.092c-.535.273-1.235.273-2.635.273h-7c-1.4 0-2.1 0-2.635-.273a2.5 2.5 0 0 1-1.093-1.092C2.5 15.6 2.5 14.9 2.5 13.5v-7c0-1.4 0-2.1.272-2.635a2.5 2.5 0 0 1 1.093-1.093C4.4 2.5 5.1 2.5 6.5 2.5Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function PreviewIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M10 2.5v15m-3.5-15h7c1.4 0 2.1 0 2.635.272a2.5 2.5 0 0 1 1.092 1.093C17.5 4.4 17.5 5.1 17.5 6.5v7c0 1.4 0 2.1-.273 2.635a2.5 2.5 0 0 1-1.092 1.092c-.535.273-1.235.273-2.635.273h-7c-1.4 0-2.1 0-2.635-.273a2.5 2.5 0 0 1-1.093-1.092C2.5 15.6 2.5 14.9 2.5 13.5v-7c0-1.4 0-2.1.272-2.635a2.5 2.5 0 0 1 1.093-1.093C4.4 2.5 5.1 2.5 6.5 2.5Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function MapIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m7.5 15-5.834 3.333V5l5.833-3.333M7.5 15l5.834 3.333M7.499 15V1.666m5.834 16.667 5-3.333V1.666l-5 3.334m0 13.333V5m0 0L7.499 1.667"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function ColumnsIcon() {
  return (
    <svg fill="none" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M7.5 2.5v15m5-15v15m-6-15h7c1.4 0 2.1 0 2.64.27.47.24.85.62 1.09 1.1.27.53.27 1.23.27 2.63v7c0 1.4 0 2.1-.27 2.64a2.5 2.5 0 0 1-1.1 1.09c-.53.27-1.23.27-2.63.27h-7c-1.4 0-2.1 0-2.63-.27a2.5 2.5 0 0 1-1.1-1.1c-.27-.53-.27-1.23-.27-2.63v-7c0-1.4 0-2.1.27-2.63a2.5 2.5 0 0 1 1.1-1.1C4.4 2.5 5.1 2.5 6.5 2.5Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.67"
      />
    </svg>
  );
}

function ColumnsIconLarge() {
  return (
    <svg fill="none" height="48" width="48" xmlns="http://www.w3.org/2000/svg">
      <path d="M0 24a24 24 0 1 1 48 0 24 24 0 0 1-48 0Z" fill="#E0F2FE" />
      <path
        d="M21 15v18m6-18v18m-7.2-18h8.4c1.68 0 2.52 0 3.16.33a3 3 0 0 1 1.31 1.3c.33.65.33 1.49.33 3.17v8.4c0 1.68 0 2.52-.33 3.16a3 3 0 0 1-1.3 1.31c-.65.33-1.49.33-3.17.33h-8.4c-1.68 0-2.52 0-3.16-.33a3 3 0 0 1-1.31-1.3C15 30.71 15 29.87 15 28.2v-8.4c0-1.68 0-2.52.33-3.16a3 3 0 0 1 1.3-1.31c.65-.33 1.49-.33 3.17-.33Z"
        stroke="#0086C9"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

const exportFormats = [
  SearchExportFormat.Excel,
  SearchExportFormat.Shapefile,
  SearchExportFormat.Geopackage,
];

const getGoodViewMode = (view: null | string): ResultsMode => {
  if (view && (view === "table" || view === "map" || view === "preview")) {
    return view;
  }
  return "table";
};

export default function SearchLayout({ children }: { children?: ReactNode }) {
  const router = useRouter();
  const { activeLocale, t } = useI18n();
  const { getSetting, id, isLoading } = useCurrentUser();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const view = searchParams.get("v") ?? "table";
  const [resultsViewMode, setResultsViewMode] = useState<ResultsMode>(
    getGoodViewMode(view),
  );
  const [searchValues, setSearchValues] = useState<
    QuerySearchArgs | QuerySimpleSearchArgs
  >();
  const [isGrouped, setIsGrouped] = useState(false);
  const [fieldSelection, setFieldSelection] = useState<SearchField[]>();
  const [savedSearch, setSavedSearch] = useState<SavedSearchFragment>();
  const [isAddToPoolDialogOpen, setIsAddToPoolDialogOpen] = useState(false);

  useEffect(() => {
    if (isLoading) {
      return;
    }
    const searchParamsFields = searchParams.getAll("field");
    setFieldSelection(
      searchParamsFields.length > 0
        ? (searchParamsFields as SearchField[])
        : (getSetting<null | SearchField[]>("searchFields", null) ?? [
            SearchField.Standortnummer,
            SearchField.Bezeichnung,
            SearchField.Gemeinde,
            SearchField.Beurteilung,
            SearchField.Standorttyp,
          ]),
    );
  }, [getSetting, isLoading, searchParams]);

  const alwaysSelectedFields: SearchField[] = [SearchField.Standortnummer];
  useEffect(() => {
    if (!view) {
      return;
    }
    setResultsViewMode(getGoodViewMode(view));
  }, [view]);

  function switchResultsViewMode(mode: ResultsMode) {
    const params = new URLSearchParams(searchParams);
    params.set("v", mode);
    params.delete("p");
    void router.push(`?${params.toString()}`);
  }

  useEffect(() => {
    let valuesFromSearchParams = {
      advanced: pathname === "/search/advanced",
      page: searchParams.get("p") ? parseInt(searchParams.get("p") ?? "0") : 1,
      perPage: searchParams.get("perPage")
        ? parseInt(searchParams.get("perPage") ?? "0")
        : 10,
      query: searchParams.get("q") ?? "",
    };

    if (!valuesFromSearchParams.advanced) {
      valuesFromSearchParams = {
        ...valuesFromSearchParams,
        ...{
          beurteilung: searchParams.get("beurteilung")
            ? {
                beurteilung:
                  searchParams
                    .get("beurteilung")
                    ?.split(",")
                    .map((b) => {
                      return { label: "", value: b };
                    }) ?? [],
              }
            : undefined,
          hGemId: searchParams
            .get("gemeinde")
            ?.split(",")
            .filter(Boolean)
            .map((g) => {
              return {
                bfsNummer: parseInt(g),
                gemeinde: "",
                label: "",
                value: g,
              };
            }),
          publiziert:
            searchParams.get("publiziert") !== null &&
            searchParams.get("publiziert") === "true",
          vftyp: searchParams
            .get("vftyp")
            ?.split(",")
            .filter(Boolean)
            .map((s) => {
              return { label: "", value: s };
            }),
        },
      };
    }

    setSearchValues(valuesFromSearchParams);
    setIsGrouped(searchParams.get("g") === "1");
  }, [pathname, searchParams]);

  useEffect(() => {
    const key = `search-params-${pathname === "/search" ? "" : "advanced"}`;
    if (searchParams.size > 0) {
      localStorage.setItem(key, searchParams.toString());
      return;
    }

    const params = localStorage.getItem(key);
    if (!params) {
      return;
    }

    // In dev (strict) mode, useEffect gets called twice, whereby searchParams are not set during first render.
    // We only want to write searchParams from localStorage if searchParams are definitely not set.

    const loadSearchParamsFromStorage = setTimeout(() => {
      void router.push(`?${params.toString()}`);
    }, 100);

    return () => {
      clearTimeout(loadSearchParamsFromStorage);
    };
  }, [pathname, searchParams, router]);

  const sortBy = useMemo(() => {
    return (
      searchParams.getAll("sort").map((s) => {
        const [field, desc] = s.split(",");
        return { field, reverse: desc === "desc" };
      }) ?? []
    );
  }, [searchParams]);

  function getClassName(forPathname: string) {
    return `border-b-gray-7 -mb-px py-2 text-sm hover:border-b-2 ${pathname === forPathname ? "border-b-2 font-bold" : "font-medium"}`;
  }

  return (
    <Layout container title="Suche">
      <div
        className="border-b-gray-4 flex justify-between border-b"
        data-test="toggleSearchType"
      >
        <div className="text-gray-7 flex gap-4">
          <Link
            className={getClassName("/search")}
            href={"/search"}
            onClick={() => {
              localStorage.setItem("last-search-mode", "simple");
            }}
          >
            {t("search.simple")}
          </Link>
          <Link
            className={getClassName("/search/advanced")}
            href={"/search/advanced"}
            onClick={() => {
              localStorage.setItem("last-search-mode", "advanced");
            }}
          >
            {t("search.advanced")}
          </Link>
        </div>
        <SavedSearch
          savedSearch={savedSearch}
          setSavedSearch={setSavedSearch}
        />
      </div>
      <div className="border-gray-4 border-b">{children}</div>
      <div className="flex justify-between">
        <div
          className="my-2 inline-flex shadow-xs"
          data-test="resultsViewMode"
          role="group"
        >
          <Button
            active={resultsViewMode === "table"}
            group
            onClick={() => {
              switchResultsViewMode("table");
            }}
          >
            <TableIcon />
            <StableWidthText value={t("search.results.table")} />
          </Button>
          <Button
            active={resultsViewMode === "preview"}
            group
            onClick={() => {
              switchResultsViewMode("preview");
            }}
          >
            <PreviewIcon />
            <StableWidthText value={t("search.results.preview")} />
          </Button>
          <Button
            active={resultsViewMode === "map"}
            group
            onClick={() => {
              switchResultsViewMode("map");
            }}
          >
            <MapIcon />
            <StableWidthText value={t("search.results.map")} />
          </Button>
        </div>
        <div className="flex items-center gap-4">
          {resultsViewMode === "table" && (
            <>
              <Switch
                checked={isGrouped}
                label={t("search.results.group")}
                onChange={(checked) => {
                  setIsGrouped(checked);
                  const params = new URLSearchParams(searchParams);
                  params.set("g", checked ? "1" : "0");
                  void router.push(`?${params.toString()}`);
                }}
              />
              <SearchFieldSelector
                alwaysSelectedFields={alwaysSelectedFields}
                className="h-10"
                icon={<ColumnsIconLarge />}
                initialSelection={fieldSelection}
                multiSelect={true}
                onSelect={(values) => {
                  const newFieldSelection = Array.isArray(values)
                    ? values
                    : [values];
                  const params = new URLSearchParams(searchParams);
                  params.delete("field");
                  newFieldSelection.forEach((value) => {
                    params.append("field", value);
                  });
                  void router.push(`?${params.toString()}`);
                }}
                subtitle={t("search.columnSelector.subheading")}
                title={t("search.columnSelector.heading")}
              >
                <ColumnsIcon />
              </SearchFieldSelector>
            </>
          )}
          {pathname === "/search/advanced" && id ? (
            <>
              <Button
                className="h-10"
                data-test="search-savedSearchDialog"
                onClick={() => {
                  setSavedSearch({
                    fields: fieldSelection ?? [],
                    isGrouped,
                    isShared: false,
                    name: "",
                    query: searchValues?.query ?? "",
                    savedSearchId: "",
                    showOnDashboard: false,
                    sortBy: sortBy as {
                      field: SearchField;
                      reverse: boolean;
                    }[],
                    user: { id, username: "" },
                  });
                }}
                outline
              >
                <SaveIcon />
              </Button>
              <AddToPoolDialog
                isOpen={isAddToPoolDialogOpen}
                onClose={() => {
                  setIsAddToPoolDialogOpen(false);
                }}
                searchQuery={searchValues?.query}
              />
              <Menu title={t("search.export.title")}>
                {exportFormats.map((format) => {
                  return (
                    <MenuItem
                      key={format}
                      onClick={() => {
                        const bc = new BroadcastChannel("SearchExport");

                        // sort fieldSelection by columnOrder
                        const columnOrder = getSetting<null | string[]>(
                          "searchResultsColumnOrder",
                          null,
                        );
                        const fields = fieldSelection?.slice() ?? [];
                        if (columnOrder) {
                          fields.sort((a, b) => {
                            const aIndex = columnOrder.indexOf(a);
                            const bIndex = columnOrder.indexOf(b);
                            return aIndex - bIndex;
                          });
                        }

                        client
                          .request<ExportSearchMutation>(exportSearch, {
                            data: {
                              fields,
                              format,
                              lang: activeLocale.toUpperCase(),
                              query: searchValues?.query ?? "",
                              sortBy,
                            },
                          })
                          .then(({ exportId }) => {
                            bc.postMessage({
                              exportId,
                              type: SearchExportStatus.Started,
                            });
                          })
                          .catch(() => {
                            bc.postMessage({
                              type: SearchExportStatus.Error,
                            });
                          });
                      }}
                    >
                      {t(`search.export.${format}`)}
                    </MenuItem>
                  );
                })}
                <MenuItem
                  onClick={() => {
                    setIsAddToPoolDialogOpen(true);
                  }}
                >
                  <PoolIcon className="mr-2 size-4" />
                  {t("search.addToPool")}
                </MenuItem>
              </Menu>
            </>
          ) : null}
        </div>
      </div>
      {resultsViewMode === "table" && (
        <SearchResultsTable
          fields={fieldSelection}
          filters={searchValues}
          isGrouped={isGrouped}
        />
      )}
      {resultsViewMode === "preview" && (
        <SearchResultsPreview filters={searchValues} />
      )}
      {resultsViewMode === "map" && (
        <SearchResultsMap
          advanced={searchValues?.advanced}
          filters={
            searchValues?.advanced
              ? []
              : (makeSimpleSearchQuery(searchValues ?? { query: "" })
                  .filters as SearchFilter[])
          }
          query={searchValues?.query ?? ""}
        />
      )}
    </Layout>
  );
}
