import { gql } from "graphql-request";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import useSWR from "swr";
import useSWRInfinite from "swr/infinite";

import { NoResultsInfo } from "@/components/SearchLayout/NoResultsInfo";
import Spinner from "@/components/Spinner";
import VflzItem from "@/components/VflzItem";
import VflzOverview from "@/components/VflzOverview";
import VflzSummary from "@/components/VflzSummary";
import { useI18n } from "@/lib/i18n";
import {
  makeAdvancedSearchQuery,
  makeSimpleSearchQuery,
  querySearchGraph,
  type QuerySimpleSearchArgs,
} from "@/lib/search";
import useCurrentUser from "@/lib/useCurrentUser";
import useInfiniteScroll from "@/lib/useInfiniteScroll";

import type {
  QuerySearchArgs,
  SearchGraphQuery,
  VflzPreviewDataQuery,
} from "@/lib/graphql";

const queryVflzPreviewData = gql`
  query VflzPreviewData($vflzId: ID!, $withGeschaefte: Boolean!) {
    vflz(vflzId: $vflzId) {
      ...VflzSummary
      ...VflzOverview
    }
  }
  ${VflzSummary.fragment}
  ${VflzOverview.fragment}
`;

export function SearchResultsPreview({
  filters,
}: {
  filters?: QuerySearchArgs | QuerySimpleSearchArgs;
}) {
  const { pluralRules, t } = useI18n();
  const router = useRouter();
  const [selectedVflzId, setSelectedVflzId] = useState<string>();
  const { permissions } = useCurrentUser();
  const getKey = (pageIndex: number, previousPageData: SearchGraphQuery) => {
    // If previous page has no results, we reached the end
    if (previousPageData && !previousPageData.search.graph.results.length) {
      return null;
    }
    const baseQuery = {
      ...filters,
      page: pageIndex + 1, // SWR Infinite pages are 0-indexed
      perPage: 10,
      query: filters?.query ?? "",
    };
    return filters?.advanced
      ? [querySearchGraph, makeAdvancedSearchQuery(baseQuery)]
      : [querySearchGraph, makeSimpleSearchQuery(baseQuery)];
  };

  const {
    data: pages,
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    error,
    isLoading: searchResultsLoading,
    isValidating,
    setSize,
    size,
  } = useSWRInfinite<SearchGraphQuery>(getKey, { initialSize: 2 });

  const searchResultsData = useMemo(() => {
    return pages
      ? pages.flatMap((page) => {
          return page.search.graph.results;
        })
      : [];
  }, [pages]);

  const previewVflzId = useMemo(() => {
    if (selectedVflzId) {
      return selectedVflzId;
    }
    return searchResultsData[0]?.vflzId;
  }, [searchResultsData, selectedVflzId]);

  const { data: previewItemData } = useSWR<VflzPreviewDataQuery>(
    previewVflzId && [
      queryVflzPreviewData,
      {
        vflzId: previewVflzId,
        withGeschaefte: permissions.canViewProcess ?? false,
      },
    ],
  );

  const isLoading =
    (!pages && !isValidating) ||
    (searchResultsData.length < 1 && searchResultsLoading);
  const numResultsTotal = pages?.[0]?.search.graph.numResultsTotal ?? 0;

  const scrollContainerRef = useInfiniteScroll(() => {
    if (!isValidating && searchResultsData.length < numResultsTotal) {
      void setSize(size + 1);
    }
  });

  if (error) {
    return <NoResultsInfo />;
  }

  return (
    <div className="mt-4 flex gap-4">
      <div className="shrink-0 basis-96">
        <div
          className="border-gray-4 flex max-h-[calc(100dvh-300px)] flex-col overflow-hidden rounded-xl border-2"
          data-test="resultsPreviewList"
        >
          <div className="bg-gray-4 p-2 text-xs font-bold">
            {isLoading ? (
              <Spinner className="size-4" />
            ) : (
              (() => {
                return t(
                  `search.results.${pluralRules.select(numResultsTotal)}`,
                  {
                    count: numResultsTotal.toString(),
                  },
                );
              })()
            )}
          </div>
          <div className="grow overflow-y-auto" ref={scrollContainerRef}>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Spinner className="size-8" />
              </div>
            )}
            {searchResultsData?.map((r) => {
              return (
                <div
                  className={`border-gray-4 bg-gray-5/20 text-gray-6 hover:bg-gray-5/10 border-b text-sm hover:cursor-pointer ${
                    r.vflzId && r.vflzId === previewVflzId
                      ? "ring-blue-6 ring-2 ring-inset"
                      : ""
                  }`}
                  key={r.combinedId}
                  onClick={() => {
                    if (r.vflzId) {
                      setSelectedVflzId(r.vflzId);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      if (r.vflzId) {
                        setSelectedVflzId(r.vflzId);
                      }
                    }
                  }}
                  role="link"
                  tabIndex={0}
                >
                  <VflzItem className="px-4 py-2" link={false} vflz={r} />
                </div>
              );
            })}
            {numResultsTotal < 1 && !isLoading ? <NoResultsInfo /> : null}
          </div>
        </div>
      </div>
      {numResultsTotal > 0 && (
        <div
          className="grow cursor-pointer"
          data-test="resultsPreviewItem"
          onClick={() => {
            if (previewVflzId) {
              void router.push(`/vflz/${previewVflzId}`);
            }
          }}
          onKeyDown={() => {
            if (previewVflzId) {
              void router.push(`/vflz/${previewVflzId}`);
            }
          }}
          role="link"
          tabIndex={0}
        >
          <VflzOverview
            className="hover:border-gray-5 hover:shadow-md"
            hideMapControls={true}
            vflz={previewItemData?.vflz}
          />
        </div>
      )}
    </div>
  );
}
