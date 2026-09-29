import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { restrictToHorizontalAxis } from "@dnd-kit/modifiers";
import {
  arrayMove,
  horizontalListSortingStrategy,
  SortableContext,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { gql } from "graphql-request";
import { isString, padStart } from "lodash";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFormContext } from "react-hook-form";
import useSWRImmutable from "swr/immutable";
import useSWRInfinite from "swr/infinite";

import HandleIcon from "@/components/icons/HandleIcon";
import NoResultsIcon from "@/components/icons/NoResultsIcon";
import PublicationIcon from "@/components/icons/PublicationIcon";
import Spinner from "@/components/Spinner";
import { SearchField } from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import { makeAdvancedSearchQuery, makeSimpleSearchQuery } from "@/lib/search";
import useCurrentUser from "@/lib/useCurrentUser";
import useInfiniteScroll from "@/lib/useInfiniteScroll";

import { NoResultsInfo } from "./NoResultsInfo";

import type { DragEndEvent } from "@dnd-kit/core";
import type { Cell, Header, SortingState } from "@tanstack/react-table";

import type {
  ColorsQuery,
  EvaluationStatus,
  QuerySearchArgs,
  SearchFieldNamesQuery,
  SearchFieldTypesQuery,
  SearchTabularQuery,
  SortItemInput,
} from "@/lib/graphql";
import type { QuerySimpleSearchArgs } from "@/lib/search";

type SearchResultsData = (boolean | EvaluationStatus | number | string)[][];

function ArrowDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="16"
      width="16"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8 3.333v9.334m0 0L12.668 8m-4.666 4.667L3.334 8"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.333"
      />
    </svg>
  );
}

function ArrowUpIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="16"
      width="16"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8 12.667V3.333m0 0L3.335 8m4.667-4.667L12.667 8"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.333"
      />
    </svg>
  );
}

const querySearchTabular = gql`
  query searchTabular(
    $advanced: Boolean
    $query: String!
    $filters: [SearchFilter!]
    $page: Int
    $fields: [SearchField!]
    $sortBy: [SortItemInput!]
    $perPage: Int
  ) {
    search(
      advanced: $advanced
      query: $query
      filters: $filters
      fields: $fields
      page: $page
      perPage: $perPage
      sortBy: $sortBy
    ) {
      __typename
      page
      tabular {
        numPages
        numResultsTotal
        results
      }
    }
  }
`;

const queryBeurteilungColors = gql`
  query colors {
    kbsInfos {
      beurteilung
      color
    }
  }
`;

function makeTableData(
  fields: SearchField[],
  searchResult: SearchResultsData,
): Record<"EVALUATION_STATUS" | SearchField, EvaluationStatus | string>[] {
  if (!searchResult) {
    return [];
  }

  return searchResult.map((r) => {
    return fields.reduce(
      (
        acc: Record<
          "EVALUATION_STATUS" | SearchField,
          EvaluationStatus | string
        >,
        field,
        i,
      ) => {
        acc[field] = r[i + 1] as string;

        const evalStatus = r.at(-1) as EvaluationStatus;
        if (evalStatus) {
          acc.EVALUATION_STATUS = evalStatus;
        }

        return acc;
      },
      {} as Record<
        "EVALUATION_STATUS" | SearchField,
        EvaluationStatus | string
      >,
    );
  });
}

const querySearchFieldNames = gql`
  query SearchFieldNames($lang: Language!) {
    searchFieldNames(lang: $lang) {
      category
      field
      name
    }
  }
`;

const querySearchFieldTypes = gql`
  query SearchFieldTypes {
    searchFields {
      field
      type
    }
  }
`;

function DraggableTableHeader({
  header,
}: {
  header: Header<Record<SearchField, string>, unknown>;
}) {
  const { attributes, isDragging, listeners, setNodeRef, transform } =
    useSortable({
      id: header.column.id,
    });

  const style: React.CSSProperties = {
    minWidth: header.getSize() !== 150 ? header.getSize() : undefined,
    opacity: isDragging ? 0.5 : 1,
    position: "relative",
    transform: CSS.Translate.toString(transform),
    transition: "width transform 0.2s ease-in-out",
    whiteSpace: "nowrap",
    zIndex: isDragging ? 100 : 0,
  };

  return (
    <th
      className={`bg-gray-3 h-10 text-left text-xs font-normal ${
        header.column.getCanSort() && "cursor-pointer hover:underline"
      } ${header.getSize() !== 150 ? "w-auto" : "w-96"} ${header.getSize() < 48 ? "px-0 py-2" : "p-2"}`}
      colSpan={header.colSpan}
      onClick={header.column.getToggleSortingHandler()}
      ref={setNodeRef}
      style={style}
    >
      <button
        {...attributes}
        {...listeners}
        className="text-gray-5 relative top-0.25 cursor-move pr-1"
      >
        <HandleIcon className="size-3" />
      </button>
      {flexRender(header.column.columnDef.header, header.getContext())}
      {{
        asc: <ArrowUpIcon className="mx-1 inline" />,
        desc: <ArrowDownIcon className="mx-1 inline" />,
      }[header.column.getIsSorted() as string] ?? null}
    </th>
  );
}

function DragAlongCell({
  cell,
}: {
  cell: Cell<Record<SearchField, string>, unknown>;
}) {
  const { isDragging, setNodeRef, transform } = useSortable({
    id: cell.column.id,
  });

  const style: React.CSSProperties = {
    opacity: isDragging ? 0.7 : 1,
    position: "relative",
    transform: CSS.Translate.toString(transform),
    transition: "width transform 0.2s ease-in-out",
    width: cell.column.getSize(),
    zIndex: isDragging ? 1 : 0,
  };

  const value = cell.getValue();

  return (
    <td
      className={`text-sm ${cell.column.getSize() < 48 ? "p-0" : "p-3"}`}
      ref={setNodeRef}
      style={style}
    >
      <div
        className="line-clamp-5"
        title={isString(value) && value.length > 100 ? value : undefined}
      >
        {flexRender(cell.column.columnDef.cell, cell.getContext())}
      </div>
    </td>
  );
}

export function ErrorInfo({ errorId }: { errorId: string }) {
  const { t } = useI18n();
  return (
    <div className="text-blue-8 flex gap-2 bg-white p-5">
      <NoResultsIcon className="text-blue-7 shrink-0" />
      <div>
        <h3 className="font-semibold">{t(`${errorId}.title`)}</h3>
        <p className="mt-2 max-w-xl text-xs">{t(`${errorId}.message`)}</p>
      </div>
    </div>
  );
}

export default function SearchResultsTable({
  fields,
  filters,
  isGrouped,
}: {
  fields?: SearchField[];
  filters?: QuerySearchArgs | QuerySimpleSearchArgs;
  isGrouped?: boolean;
}) {
  const { activeLocale, pluralRules, t } = useI18n();
  const {
    getSetting,
    isLoading: userLoading,
    updateSetting,
  } = useCurrentUser();
  const { setError } = useFormContext();
  const [errorId, setErrorId] = useState<string | undefined>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnOrder, setColumnOrder] = useState<string[]>([]);
  const [columnVisibility, setColumnVisibility] = useState<
    Partial<Record<SearchField, boolean>>
  >({});
  const hiddenFields: SearchField[] = useMemo(() => {
    return [
      SearchField.AktuellstePublikation,
      SearchField.Beurteilung,
      SearchField.BfsNr,
      SearchField.VflzId,
    ];
  }, []);
  const { data: searchFieldTypes } = useSWRImmutable<SearchFieldTypesQuery>(
    querySearchFieldTypes,
  );

  const { data: colors } = useSWRImmutable<ColorsQuery>(queryBeurteilungColors);
  const getColor = (beurteilung: null | string) => {
    return (
      colors?.kbsInfos?.find((c) => {
        return c.beurteilung === beurteilung;
      })?.color ?? "var(--color-gray-5)"
    );
  };

  const getKey = (pageIndex: number, previousPageData: SearchTabularQuery) => {
    if (previousPageData && !previousPageData.search.tabular.results.length) {
      return null;
    }

    const mergedFields = fields ? [...fields] : [];
    for (const field of hiddenFields) {
      if (!mergedFields.includes(field)) {
        mergedFields.push(field);
      }
    }

    const baseQuery = {
      ...filters,
      fields: mergedFields,
      page: pageIndex + 1,
      perPage: 10,
      query: filters?.query ?? "",
      sortBy: sorting.map<SortItemInput>((i) => {
        return {
          field: i.id as SearchField,
          reverse: i.desc,
        };
      }),
    };
    return filters?.advanced
      ? [querySearchTabular, makeAdvancedSearchQuery(baseQuery)]
      : [querySearchTabular, makeSimpleSearchQuery(baseQuery)];
  };

  const {
    data: searchResultsPages,
    error,
    isLoading: searchResultsLoading,
    isValidating,
    setSize,
    size,
  } = useSWRInfinite<SearchTabularQuery, Error>(getKey, { initialSize: 2 });

  const searchResultsData = useMemo(() => {
    return searchResultsPages
      ? searchResultsPages.flatMap((page) => {
          return page.search.tabular.results;
        })
      : [];
  }, [searchResultsPages]);

  const numResultsTotal =
    searchResultsPages?.[0]?.search.tabular.numResultsTotal ?? 0;
  const isLoading =
    (!searchResultsPages && !isValidating) ||
    (searchResultsData.length < 1 && searchResultsLoading);

  useEffect(() => {
    if (error) {
      if (error.message.includes("error.Permissions.SearchQuery")) {
        setError("advancedQuery", {
          message: "error.Permissions.SearchQuery",
        });
        setErrorId("error.Permissions.SearchQuery");
      }
      return;
    }
    setErrorId(undefined);
  }, [error, setError]);

  const { data: searchFieldNames } = useSWRImmutable<SearchFieldNamesQuery>([
    querySearchFieldNames,
    { lang: activeLocale.toUpperCase() },
  ]);

  const getNameByField = useCallback(
    (field: SearchField) => {
      return (
        searchFieldNames?.searchFieldNames.find((f) => {
          return f.field === field;
        })?.name ?? "?"
      );
    },
    [searchFieldNames],
  );

  const makeDisplayValue = useCallback(
    (field: SearchField, value: string) => {
      const fieldType = searchFieldTypes?.searchFields.find((f) => {
        return f.field === field;
      })?.type;
      if (fieldType === "CODE") {
        return t(value);
      }
      return value;
    },
    [searchFieldTypes, t],
  );

  const columns = useMemo(() => {
    const columnHelper =
      createColumnHelper<
        Record<"EVALUATION_STATUS" | SearchField, EvaluationStatus | string>
      >();
    const cols = [];
    if (isGrouped) {
      cols.push(
        columnHelper.display({
          cell: ({ row }) => {
            return (
              row.getIsGrouped() &&
              row.subRows.length > 1 && (
                <button
                  className="text-gray-6 w-full p-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    row.toggleExpanded();
                  }}
                >
                  ({row.subRows.length})
                </button>
              )
            );
          },
          id: "grouping",
          size: 16,
        }),
      );
    }

    const topLevelFields: SearchField[] = [
      SearchField.Standortnummer,
      SearchField.Bezeichnung,
    ];

    fields?.forEach((field) => {
      cols.push(
        columnHelper.accessor(field, {
          cell: ({ row }) => {
            if (field === SearchField.Standortnummer) {
              if (isLoading) {
                return (
                  <div className="font-blokk flex gap-2 opacity-50 blur-sm">
                    <PublicationIcon className="w-5" preserveLayout />
                    <span>Skeleton</span>
                  </div>
                );
              }
              if (row.depth > 0) {
                return "";
              }
              return (
                <div className="flex gap-2">
                  <PublicationIcon
                    className="w-5"
                    preserveLayout
                    vflz={{
                      evaluationStatus: row.original
                        .EVALUATION_STATUS as EvaluationStatus,
                    }}
                  />
                  {row.original.STANDORTNUMMER as string}
                </div>
              );
            }
            if (isLoading) {
              return (
                <span className="font-blokk opacity-50 blur-sm">Skeleton</span>
              );
            }
            let rowValue = row.original[field]
              ? makeDisplayValue(field, row.original[field] as string)
              : "-";
            if (field === SearchField.Gemeinde) {
              const gemeinde = row.original[SearchField.Gemeinde] as string;
              const bfsNr = row.original.BFS_NR as string;
              rowValue = `${gemeinde} (${padStart(bfsNr, 4, "0")})`;
            }
            if (row.getIsGrouped() && row.subRows.length > 1) {
              if (topLevelFields.includes(field)) {
                return rowValue;
              }
              return "";
            }
            if (row.depth > 0 && topLevelFields.includes(field)) {
              return "";
            }
            return rowValue;
          },
          enableSorting: true,
          header: () => {
            return getNameByField(field);
          },
          id: field,
        }),
      );
    });

    hiddenFields?.forEach((field) => {
      if (!fields?.includes(field)) {
        cols.push(
          columnHelper.accessor(field, {
            cell: ({ row }) => {
              return row.original[field];
            },
            header: () => {
              return getNameByField(field);
            },
          }),
        );
      }
    });

    return cols;
  }, [
    isGrouped,
    fields,
    hiddenFields,
    isLoading,
    makeDisplayValue,
    getNameByField,
  ]);

  useEffect(() => {
    if (userLoading) {
      return;
    }
    const newColumnOrder = getSetting<null | string[]>(
      "searchResultsColumnOrder",
      null,
    );
    if (!newColumnOrder) {
      return;
    }
    setColumnOrder(
      newColumnOrder?.filter((c) => {
        return c != null;
      }),
    );
  }, [getSetting, userLoading]);

  useEffect(() => {
    if (columns.length < 1 || columnOrder.length < 1) {
      return;
    }
    const newColumnOrder = columnOrder;
    for (const column of columns) {
      if (column.id && !newColumnOrder.includes(column.id)) {
        newColumnOrder.push(column.id);
      }
    }
    setColumnOrder(newColumnOrder);
  }, [columns, columnOrder]);

  useEffect(() => {
    if (columnOrder.length < 1) {
      return;
    }
    void updateSetting("searchResultsColumnOrder", columnOrder);
  }, [columnOrder, updateSetting]);

  const tableData = useMemo(() => {
    if (!fields || !searchResultsData) {
      return [];
    }
    return makeTableData(
      [
        ...fields,
        ...hiddenFields.filter((f) => {
          return !fields.includes(f);
        }),
      ],
      searchResultsData as SearchResultsData,
    );
  }, [fields, hiddenFields, searchResultsData]);

  const table = useReactTable({
    columns,
    //@ts-expect-error not sure how to define the type properly
    data: isLoading ? Array<Record<SearchField, string>>(10) : tableData,
    getCoreRowModel: getCoreRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    groupedColumnMode: false,
    initialState: {
      expanded: true,
    },
    manualPagination: true,
    manualSorting: true,
    onColumnOrderChange: setColumnOrder,
    onSortingChange: (sortingState) => {
      const newSortingState =
        typeof sortingState === "function"
          ? sortingState(sorting)
          : sortingState;
      const params = new URLSearchParams(searchParams);
      params.delete("sort");
      newSortingState.forEach((s) => {
        params.append("sort", `${s.id}${s.desc ? ",desc" : ""}`);
      });
      params.delete("p");
      void router.push(`?${params.toString()}`);
    },
    state: {
      columnOrder,
      columnVisibility: columnVisibility,
      grouping: useMemo(() => {
        return isGrouped ? [SearchField.Standortnummer] : [];
      }, [isGrouped]),
      sorting,
    },
  });

  useEffect(() => {
    setColumnVisibility(
      hiddenFields
        .filter((field) => {
          return !fields?.includes(field);
        })
        .reduce(
          (acc, item) => {
            acc[item] = false;
            return acc;
          },
          {} as Record<SearchField, boolean>,
        ),
    );
  }, [fields, hiddenFields]);

  useEffect(() => {
    const sort = searchParams.getAll("sort").map((s) => {
      const sortParamSplit = s.split(",");
      return { desc: sortParamSplit[1] === "desc", id: sortParamSplit[0] };
    });
    setSorting(sort);
  }, [searchParams]);

  const sensors = useSensors(
    useSensor(MouseSensor, {}),
    useSensor(TouchSensor, {}),
    useSensor(KeyboardSensor, {}),
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (active && over && active.id !== over.id) {
      setColumnOrder((colOrder) => {
        const oldIndex = colOrder.indexOf(active.id as string);
        const newIndex = colOrder.indexOf(over.id as string);
        return arrayMove(colOrder, oldIndex, newIndex);
      });
    }
  }

  const scrollContainerRef = useInfiniteScroll(() => {
    if (!isValidating && searchResultsData.length < numResultsTotal) {
      void setSize(size + 1);
    }
  });

  if (error) {
    return <NoResultsInfo />;
  }

  return (
    <div className="border-gray-4 relative mt-4 overflow-hidden rounded-xl border-2">
      <div className="bg-gray-4 p-2 text-xs font-bold">
        {isLoading ? (
          <Spinner className="size-4" />
        ) : (
          (() => {
            return t(`search.results.${pluralRules.select(numResultsTotal)}`, {
              count: numResultsTotal.toString(),
            });
          })()
        )}
      </div>
      <div
        className="relative max-h-[calc(100vh-320px)] overflow-x-scroll"
        ref={scrollContainerRef}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center backdrop-blur-sm">
            <Spinner className="w-8" />
          </div>
        )}
        {errorId ? (
          <ErrorInfo errorId={errorId} />
        ) : (
          <>
            <DndContext
              collisionDetection={closestCenter}
              modifiers={[restrictToHorizontalAxis]}
              onDragEnd={handleDragEnd}
              sensors={sensors}
            >
              <table data-test="searchResultsTable">
                <thead className="sticky top-0 left-0 z-10">
                  {table.getHeaderGroups().map((headerGroup) => {
                    return (
                      <tr key={headerGroup.id}>
                        <SortableContext
                          items={columnOrder}
                          strategy={horizontalListSortingStrategy}
                        >
                          {headerGroup.headers.map((header) => {
                            return (
                              <DraggableTableHeader
                                header={
                                  header as Header<
                                    Record<SearchField, string>,
                                    unknown
                                  >
                                }
                                key={header.id}
                              />
                            );
                          })}
                        </SortableContext>
                      </tr>
                    );
                  })}
                </thead>
                {numResultsTotal > 0 && (
                  <tbody className="bg-white">
                    {table.getRowModel().rows.map((row) => {
                      if (
                        row.depth === 1 &&
                        row.getParentRow()?.subRows.length === 1
                      ) {
                        return;
                      }

                      const handleVflzRouting = () => {
                        if (SearchField.VflzId in row.original) {
                          void router.push(
                            `/vflz/${row.original.VFLZ_ID as string}`,
                          );
                        }
                      };

                      const beurteilung =
                        SearchField.Beurteilung in row.original
                          ? (row.original.BEURTEILUNG as string)
                          : null;

                      return (
                        <tr
                          className="border-gray-4 border-y bg-(--kbs-color)/20 last:border-y-0 hover:cursor-pointer hover:bg-(--kbs-color)/10"
                          key={row.id}
                          onClick={() => {
                            handleVflzRouting();
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              handleVflzRouting();
                            }
                          }}
                          style={
                            {
                              "--kbs-color": getColor(beurteilung),
                            } as React.CSSProperties
                          }
                          tabIndex={0}
                        >
                          {row.getVisibleCells().map((cell) => {
                            return (
                              <SortableContext
                                items={columnOrder}
                                key={cell.id}
                                strategy={horizontalListSortingStrategy}
                              >
                                <DragAlongCell
                                  cell={
                                    cell as Cell<
                                      Record<SearchField, string>,
                                      unknown
                                    >
                                  }
                                  key={cell.id}
                                />
                              </SortableContext>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                )}
              </table>
            </DndContext>
            {numResultsTotal === 0 && !isLoading ? <NoResultsInfo /> : null}
          </>
        )}
      </div>
    </div>
  );
}
