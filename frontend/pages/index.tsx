import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  rectSortingStrategy,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { captureException } from "@sentry/nextjs";
import { gql } from "graphql-request";
import Link from "next/link";
import { useMemo } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import useSWR from "swr";
import useSWRImmutable from "swr/immutable";

import Button from "@/components/Button";
import DatePicker from "@/components/DatePicker";
import Form from "@/components/Form";
import HandleIcon from "@/components/icons/HandleIcon";
import PlusIcon from "@/components/icons/PlusIcon";
import XCircleIcon from "@/components/icons/XCircleIcon";
import Layout from "@/components/Layout";
import Spinner from "@/components/Spinner";
import VflzItem from "@/components/VflzItem";
import client from "@/lib/client";
import { dayEnd } from "@/lib/date";
import { FaelligkeitStatus, StandortTyp } from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import {
  getSearchURL,
  querySearchGraph,
  savedSearchesQuery,
  updateSavedSearchMutation,
} from "@/lib/search";
import toLocaleDateString from "@/lib/toLocaleDateString";
import tw from "@/lib/tw";
import useCurrentUser from "@/lib/useCurrentUser";

import type { DragEndEvent } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { KeyedMutator } from "swr";

import type {
  DashboardReportConfigsQuery,
  DashboardStatisticQuery,
  SavedSearchesQuery,
  SavedSearchFragment,
  SearchGraphQuery,
  UpdateSavedSearchMutation,
} from "@/lib/graphql";

interface DashboardFormValues {
  date: string;
}

function Card({
  children,
  ...props
}: {
  children: ReactNode;
  style?: { transform: string | undefined; transition?: string };
}) {
  return (
    <div
      className="border-gray-4 overflow-hidden rounded-xl border bg-white p-5 shadow-xs"
      {...props}
    >
      {children}
    </div>
  );
}

function CardHeader({ children }: { children: ReactNode }) {
  return (
    <div className="border-gray-4 bg-gray-2 -mx-5 -mt-5 mb-2 border-b p-2.5 pl-5 font-semibold">
      {children}
    </div>
  );
}

function SavedSearchCard({
  enableDelete,
  mutateSavedSearches,
  search,
}: {
  enableDelete: boolean;
  mutateSavedSearches: KeyedMutator<SavedSearchesQuery>;
  search: SavedSearchFragment;
}) {
  const { data, isLoading } = useSWR<SearchGraphQuery>([
    querySearchGraph,
    {
      advanced: true,
      fields: search.fields,
      perPage: 10,
      query: search.query,
      sortBy: search.sortBy,
    },
  ]);
  const searchResults = data?.search?.graph.results ?? [];
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: search.savedSearchId });

  return (
    <Card
      data-test="savedSearchCard"
      key={search.savedSearchId}
      style={{ transform: CSS.Translate.toString(transform), transition }}
    >
      <CardHeader>
        <div
          className="flex items-center justify-between gap-2"
          ref={setNodeRef}
        >
          <div {...listeners} {...attributes} className="cursor-move">
            <HandleIcon className="text-gray-5 size-3" />
          </div>
          <Link
            className="grow py-2 text-sm font-semibold"
            href={getSearchURL(search)}
          >
            {search.name}
          </Link>
          {enableDelete ? (
            <Button
              data-test="savedSearchCard-deleteButton"
              onClick={() => {
                void (async () => {
                  await client.request<UpdateSavedSearchMutation>(
                    updateSavedSearchMutation,
                    {
                      data: {
                        isShared: search.isShared,
                        name: search.name,
                        savedSearchId: search.savedSearchId,
                        showOnDashboard: false,
                      },
                    },
                  );
                  void mutateSavedSearches();
                })();
              }}
              plain
              size="small"
            >
              <XCircleIcon />
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <div className="divide-gray-4 -mt-2 -mb-5 divide-y">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner className="size-8" />
          </div>
        ) : (
          searchResults.map((vflz) => {
            return (
              <VflzItem
                className="-mx-5 px-5 py-2"
                key={vflz.vflzId}
                vflz={vflz}
              />
            );
          })
        )}
      </div>
    </Card>
  );
}

function SavedSearches() {
  const { activeLocale, t } = useI18n();
  const { getSetting, updateSetting } = useCurrentUser();
  const { data: savedSearches, mutate: mutateSavedSearches } =
    useSWR<SavedSearchesQuery>([
      savedSearchesQuery,
      { lang: activeLocale.toUpperCase() },
    ]);
  const searchesSorting = useMemo(() => {
    return getSetting<string[]>("dashboardSearchesSorting", []);
  }, [getSetting]);

  const sortedSearches = useMemo(() => {
    if (!savedSearches) {
      return;
    }
    return savedSearches.savedSearches
      .filter((search) => {
        return search.showOnDashboard;
      })
      .sort((a, b) => {
        const indexA = searchesSorting.findIndex((i) => {
          return i === a.savedSearchId;
        });
        const indexB = searchesSorting.findIndex((i) => {
          return i === b.savedSearchId;
        });
        return indexA - indexB;
      });
  }, [savedSearches, searchesSorting]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  function handleDragEnd(event: DragEndEvent) {
    if (!sortedSearches) {
      return;
    }
    const { active, over } = event;
    const oldIndex = sortedSearches.findIndex((s) => {
      return s.savedSearchId === active.id;
    });
    const newIndex = sortedSearches.findIndex((s) => {
      return s.savedSearchId === over?.id;
    });
    const newOrder = arrayMove(sortedSearches, oldIndex, newIndex);
    const newOrderIds = newOrder.map((s) => {
      return s.savedSearchId;
    });
    void updateSetting("dashboardSearchesSorting", newOrderIds);
  }

  return sortedSearches && sortedSearches.length > 0 ? (
    <div className="col-span-2 space-y-4">
      <div className="border-gray-4 text-gray-7 flex items-center justify-between border-b pb-2 font-semibold">
        {t("dashboard.savedSearches.title")}
      </div>
      <DndContext
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
        sensors={sensors}
      >
        <div className="grid grid-cols-2 items-start gap-5">
          <SortableContext
            items={sortedSearches.map((i) => {
              return i.savedSearchId;
            })}
            strategy={rectSortingStrategy}
          >
            {sortedSearches.map((search) => {
              return (
                <SavedSearchCard
                  enableDelete={sortedSearches.length > 2}
                  key={search.savedSearchId}
                  mutateSavedSearches={mutateSavedSearches}
                  search={{ ...search, user: { id: "", username: "" } }}
                />
              );
            })}
          </SortableContext>
        </div>
      </DndContext>
    </div>
  ) : null;
}

const queryReportConfigs = gql`
  query dashboardReportConfigs {
    reportConfigurations(context: DASHBOARD) {
      reportId
      params {
        name
        paramType
      }
      title
    }
  }
`;

function DownloadIcon() {
  return (
    <svg
      fill="none"
      height="17"
      viewBox="0 0 17 17"
      width="17"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M15.8335 15.8334H0.833496M13.3335 7.50004L8.3335 12.5M8.3335 12.5L3.3335 7.50004M8.3335 12.5V0.833374"
        stroke="white"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.66667"
      />
    </svg>
  );
}

function DashboardReportIcon() {
  return (
    <svg
      fill="none"
      height="32"
      viewBox="0 0 33 32"
      width="33"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M16.02 3.65234C16.6406 3.20183 17.4518 3.02314 18.2515 3.2373L30.0854 6.4082C31.4915 6.7852 32.3255 8.23059 31.9487 9.63672L27.3237 26.9004C26.9467 28.3061 25.5011 29.1402 24.0952 28.7637L16.0181 26.5996L7.94385 28.7637C6.53775 29.1403 5.09127 28.3064 4.71436 26.9004L0.090332 9.63672C-0.286347 8.23061 0.547601 6.78515 1.95361 6.4082L13.7866 3.2373C14.5862 3.02305 15.3986 3.20094 16.02 3.65234ZM16.0503 5.35938C15.8163 4.4868 14.9181 3.96929 14.0454 4.20312L2.2124 7.37402C1.33986 7.60803 0.822413 8.50529 1.05615 9.37793L5.68018 26.6416C5.91414 27.5141 6.81243 28.0315 7.68506 27.7979L19.5181 24.627C20.3909 24.3931 20.9092 23.4949 20.6753 22.6221L16.0503 5.35938ZM17.9927 4.20312C17.5394 4.08178 17.0793 4.16341 16.7085 4.39258C16.8417 4.60719 16.9473 4.84401 17.0161 5.10059L18.5229 10.7246C19.4166 9.16446 21.2777 8.33624 23.0962 8.82324C23.6277 8.9657 24.1062 9.20797 24.5171 9.52344C24.5187 9.5247 24.5204 9.52698 24.522 9.52832C24.8141 9.75346 25.0723 10.0158 25.2905 10.3066C25.3101 10.3327 25.3302 10.3592 25.3491 10.3857C25.425 10.4921 25.4967 10.6018 25.562 10.7148L25.6577 10.8906C25.7016 10.9761 25.7402 11.0642 25.7778 11.1523C25.8171 11.2443 25.8547 11.3378 25.8872 11.4326C25.9176 11.5216 25.9441 11.6122 25.9683 11.7031C26.1452 12.367 26.1569 13.0846 25.9663 13.7959L25.9077 13.9971C25.7292 14.5493 25.4398 15.0376 25.0737 15.4473C25.0698 15.4517 25.066 15.4575 25.062 15.4619C25.0569 15.4675 25.0505 15.4729 25.0454 15.4785C25.0039 15.524 24.9619 15.5689 24.9185 15.6123C24.9078 15.623 24.897 15.634 24.8862 15.6445C24.728 15.7992 24.5577 15.941 24.3774 16.0674C24.3516 16.0855 24.3246 16.1026 24.2983 16.1201C24.2593 16.1462 24.2201 16.1726 24.1802 16.1973C24.1619 16.2086 24.143 16.2194 24.1245 16.2305C24.0734 16.261 24.0217 16.2911 23.9692 16.3193C23.9555 16.3267 23.9411 16.3336 23.9272 16.3408C23.7932 16.411 23.6545 16.4734 23.5132 16.5283C23.5088 16.5301 23.5038 16.5335 23.4995 16.5352C23.4977 16.5357 23.4954 16.5356 23.4937 16.5361C22.7221 16.8315 21.8537 16.8971 20.9946 16.667C20.64 16.5719 20.3087 16.4329 20.0054 16.2568L21.6421 22.3633C22.0189 23.7696 21.1831 25.216 19.7769 25.5928L17.9497 26.082L24.354 27.7979C25.2265 28.0314 26.1238 27.5139 26.3579 26.6416L30.9829 9.37793C31.2167 8.50527 30.6992 7.60808 29.8267 7.37402L17.9927 4.20312ZM9.69189 8.62988C9.78083 8.61373 9.89829 8.602 10.0298 8.62988C10.2064 8.66753 10.3679 8.75934 10.4888 8.89355C10.5787 8.99367 10.6263 9.10238 10.6567 9.1875C10.6852 9.26712 10.7113 9.36306 10.7349 9.45117L11.1948 11.1699L12.2251 10.8936C12.3133 10.8699 12.4085 10.8433 12.4917 10.8281C12.5585 10.816 12.642 10.806 12.7349 10.8135L12.8315 10.8271L12.9595 10.8652C13.0428 10.8973 13.1215 10.9429 13.1909 10.999L13.2896 11.0918L13.3491 11.1689C13.4017 11.2454 13.4347 11.323 13.4575 11.3867C13.4859 11.4662 13.5111 11.5616 13.5347 11.6494L14.1616 13.9883C14.1852 14.0764 14.2109 14.1718 14.2261 14.2549C14.2423 14.3439 14.256 14.4621 14.228 14.5938C14.1904 14.7702 14.0974 14.931 13.9634 15.0518C13.8631 15.142 13.7537 15.1892 13.6685 15.2197C13.5888 15.2482 13.493 15.2742 13.4048 15.2979L8.31494 16.6611C8.22684 16.6847 8.13149 16.7104 8.04834 16.7256C7.9595 16.7418 7.84197 16.7553 7.71045 16.7275C7.53399 16.69 7.37332 16.5968 7.25244 16.4629C7.16235 16.3628 7.114 16.2541 7.0835 16.1689C7.05503 16.0893 7.029 15.9935 7.00537 15.9053L6.01025 12.1914C5.98664 12.1033 5.96098 12.007 5.9458 11.9238C5.92961 11.8348 5.91687 11.7167 5.94482 11.585L5.98291 11.4561C6.03112 11.3308 6.10881 11.2176 6.20947 11.127L6.28564 11.0664C6.36224 11.0137 6.43961 10.9818 6.50342 10.959C6.58298 10.9306 6.67806 10.9045 6.76611 10.8809L7.79639 10.6055L7.70459 10.2627C7.681 10.1747 7.65533 10.0792 7.64014 9.99609C7.62393 9.90711 7.61125 9.78901 7.63916 9.65723L7.67725 9.52734C7.72541 9.40218 7.80325 9.28984 7.90381 9.19922L7.97998 9.13867C8.05684 9.08564 8.13473 9.05315 8.19873 9.03027C8.27822 9.00192 8.37352 8.97668 8.46143 8.95312L9.42432 8.69531C9.51251 8.67168 9.60869 8.64505 9.69189 8.62988ZM22.3442 9.69922C20.8798 9.55392 19.4828 10.4853 19.0894 11.9531C19.0543 12.0841 19.0276 12.2153 19.0103 12.3457C19.0055 12.3812 18.9964 12.4149 18.9849 12.4473L19.5347 14.5C19.5412 14.508 19.5491 14.5149 19.5552 14.5234C19.9532 15.0814 20.5396 15.5098 21.2534 15.7012C21.7287 15.8285 22.2075 15.832 22.6587 15.7393L21.5776 12.9248C21.5399 12.8265 21.5349 12.718 21.562 12.6162L22.3442 9.69922ZM6.9585 11.8652L7.97119 15.6465C7.97781 15.6712 7.98535 15.6931 7.99072 15.7129L9.08643 15.4199L8.05518 11.5713L6.9585 11.8652ZM23.5933 15.3828C23.684 15.3296 23.7721 15.2713 23.8569 15.209C23.9155 15.1659 23.9734 15.1205 24.0288 15.0732C24.0398 15.0639 24.0522 15.0554 24.063 15.0459C24.1253 14.9912 24.1848 14.9328 24.2427 14.873C24.3281 14.785 24.4081 14.6913 24.4829 14.5928C24.6202 14.4116 24.7368 14.2162 24.8306 14.0098L22.8638 13.4824L23.5933 15.3828ZM8.65283 9.93652L10.0522 15.1611L11.1509 14.8662L9.76904 9.70996C9.7624 9.68516 9.75491 9.66241 9.74951 9.64258L8.65283 9.93652ZM11.4536 12.1357L12.1167 14.6074L13.2134 14.3135L12.5513 11.8418L11.4536 12.1357ZM22.6577 12.3916L25.0874 13.043C25.1076 12.8369 25.1073 12.6295 25.0854 12.4229C25.0825 12.3947 25.0814 12.3659 25.0776 12.3379C25.0245 11.9424 24.8944 11.5605 24.6948 11.2148C24.6269 11.0972 24.5489 10.986 24.4663 10.8789C24.4275 10.8285 24.3901 10.7765 24.3481 10.7285C24.3315 10.7095 24.3115 10.6924 24.2944 10.6738C24.2441 10.619 24.1936 10.5638 24.1392 10.5127C24.0658 10.4439 23.9878 10.3788 23.9077 10.3174C23.7225 10.1754 23.5206 10.057 23.3091 9.96094L22.6577 12.3916Z"
        fill="#475467"
      />
    </svg>
  );
}

function DashboardReport() {
  const { getValues } = useFormContext<DashboardFormValues>();
  const { t } = useI18n();
  const { data } =
    useSWRImmutable<DashboardReportConfigsQuery>(queryReportConfigs);

  const reportConfig = data?.reportConfigurations.find((config) => {
    return config.title === "report.title.jahresbericht";
  });

  if (!reportConfig) {
    return null;
  }

  return (
    <div className="border-gray-5 mt-1.5 flex h-fit w-full items-center justify-between rounded-lg border p-1 pl-2 text-sm shadow-xs">
      <div className="flex items-center space-x-1 truncate">
        <DashboardReportIcon />
        <span className="truncate">{t(reportConfig.title)}</span>
      </div>
      <Button
        className="px-2!"
        onClick={() => {
          const params = new URLSearchParams();
          params.append("language", "de");
          params.append("date", dayEnd(getValues("date")));

          void fetch(`/api/report/${reportConfig.reportId}?${params}`, {
            headers: {
              ...(process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER
                ? {
                    "alma-e2e-test-user":
                      process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER,
                  }
                : undefined),
            },
            method: "GET",
          })
            .then((response) => {
              if (!response.ok) {
                throw new Error(`Report download failed: ${response.status}`);
              }
              return response.blob();
            })
            .then((blob) => {
              // Trigger download so users can access the exported report offline.
              const url = window.URL.createObjectURL(blob);
              const anchor = document.createElement("a");
              anchor.href = url;
              anchor.download = "jahresbericht.xlsx";
              document.body.appendChild(anchor);
              anchor.click();
              anchor.remove();
              window.URL.revokeObjectURL(url);
            })
            .catch((error) => {
              captureException(error);
            });
        }}
      >
        <DownloadIcon />
      </Button>
    </div>
  );
}

const defaultColors = [
  tw`bg-blue-8`,
  tw`bg-blue-7`,
  tw`bg-blue-6`,
  tw`bg-blue-5`,
  tw`bg-blue-4`,
  tw`bg-blue-3`,
  tw`bg-blue-1`,
];

function DashboardBarChart({
  items,
  subtitle,
  title,
  total,
}: {
  items: { color?: string; count: number; label: string; order?: number }[];
  subtitle?: string;
  title: string;
  total: number;
}) {
  if (total === 0) {
    return null;
  }

  const max = Math.max(
    ...items.map((item) => {
      return item.count;
    }),
  );

  return (
    <div className="border-gray-4 rounded-xl border p-5">
      <div className="font-semibold">{title}</div>
      <div className="mb-4 text-xs tracking-wide">{subtitle}</div>
      <div className="space-y-2">
        {items
          .filter(({ count }) => {
            return count > 0;
          })
          .sort((a, b) => {
            return (b.order ?? b.count) - (a.order ?? a.count);
          })
          .map(({ color, count, label }, index) => {
            return (
              <div className="space-y-0.5" key={label}>
                <div className="text-xs tracking-wide">
                  {label}: <span className="font-bold">{count}</span>
                </div>
                <div
                  className={`bg-blue-5 h-4 ${color ?? defaultColors[index]}`}
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
            );
          })}
      </div>
    </div>
  );
}

const faelligkeitStatusColors = {
  [FaelligkeitStatus.FaelligNaechsteWoche]: tw`bg-orange-5`,
  [FaelligkeitStatus.FaelligSpaeter]: tw`bg-green-4`,
  [FaelligkeitStatus.Ruhend]: tw`bg-gray-5`,
  [FaelligkeitStatus.Ueberfaellig]: tw`bg-red-4`,
} as const;

const faelligkeitStatusOrder = [
  FaelligkeitStatus.Ruhend,
  FaelligkeitStatus.FaelligSpaeter,
  FaelligkeitStatus.FaelligNaechsteWoche,
  FaelligkeitStatus.Ueberfaellig,
] as const;

const standortTypColors = {
  [StandortTyp.Ablagerung]: tw`bg-purple-5`,
  [StandortTyp.Betrieb]: tw`bg-blue-5`,
  [StandortTyp.KinderspielplatzGruenflaeche]: tw`bg-olive-5`,
  [StandortTyp.Pfas]: tw`bg-brown-5`,
  [StandortTyp.Schiessanlage]: tw`bg-gray-6`,
  [StandortTyp.Unfall]: tw`bg-green-4`,
} as const;

const queryDashboardStatistic = gql`
  query dashboardStatistic($stichtag: Date!) {
    dashboardStatistic(stichtag: $stichtag) {
      standortTypen {
        typ
        count
      }
      beurteilungen {
        beurteilungGruppe
        count
      }
      geschaefte {
        faelligkeit
        count
      }
    }
  }
`;

function useValidStichtag() {
  const stichtag = useWatch<DashboardFormValues>({ name: "date" });
  return useMemo(() => {
    if (!stichtag) {
      return null;
    }
    const date = new Date(stichtag);
    if (Number.isNaN(date.getTime())) {
      return null;
    }
    const year = date.getUTCFullYear();
    if (year < 1000 || year > 9999) {
      return null;
    }
    return stichtag;
  }, [stichtag]);
}

function DashboardStatistic() {
  const { t } = useI18n();
  const stichtag = useValidStichtag();
  const { data } = useSWR<DashboardStatisticQuery>(
    stichtag && [queryDashboardStatistic, { stichtag }],
  );

  return Object.entries(data?.dashboardStatistic ?? {}).map((statistic) => {
    const items = statistic[1].map(({ count, ...item }) => {
      let color, order;
      let label = "";
      if ("beurteilungGruppe" in item) {
        label = t(item.beurteilungGruppe); // key is a code
      } else if ("faelligkeit" in item) {
        label = t(`FaelligkeitStatus.${item.faelligkeit}`); // key is a FaelligkeitStatus enum
        color = faelligkeitStatusColors[item.faelligkeit];
        order = faelligkeitStatusOrder.indexOf(item.faelligkeit);
      } else if ("typ" in item) {
        label = t(`StandortTyp.${item.typ}`); // key is a StandortTyp enum
        color = standortTypColors[item.typ];
      }
      return { color, count, label, order };
    });

    const total = items.reduce((sum, item) => {
      return sum + item.count;
    }, 0);

    return (
      <DashboardBarChart
        items={items}
        key={statistic[0]}
        subtitle={t("dashboard.statistic.subtitle", {
          stichtag: toLocaleDateString(stichtag),
          total: total.toString(),
        })}
        title={t(`dashboard.statistic.${statistic[0]}`)}
        total={total}
      />
    );
  });
}

function Dashboard() {
  const { t } = useI18n();
  return (
    <Form
      className="space-y-4"
      model="dashboard"
      values={{ date: new Date().toISOString().split("T")[0] }}
    >
      <div className="border-gray-4 text-gray-7 border-b pb-2 font-semibold">
        {t("dashboard.stats")}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <DatePicker className="py-3! text-sm!" name="date" />
        <DashboardReport />
      </div>
      <DashboardStatistic />
    </Form>
  );
}

export default function HomePage() {
  const { t } = useI18n();
  const { permissions } = useCurrentUser();

  return (
    <Layout container title={t("dashboard.title")}>
      <div className="space-y-8">
        {permissions.canEditVfl ? (
          <div className="border-gray-4 flex justify-end border-b pb-4">
            <Button
              className="space-x-2"
              data-test="dashboard-createVflz"
              href="vflz/create"
            >
              <PlusIcon />
              <span>{t("vflz.create.title")}</span>
            </Button>
          </div>
        ) : null}

        <div className="grid grid-cols-3 gap-8">
          <Dashboard />
          <SavedSearches />
        </div>
      </div>
    </Layout>
  );
}
