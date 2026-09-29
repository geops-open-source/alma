import { gql } from "graphql-request";

import Form from "@/components/Form";
import VflzItem from "@/components/VflzItem";

import type {
  QuerySearchArgs,
  SavedSearchFragment,
  SearchFilter,
  SearchTabularQueryVariables,
} from "@/lib/graphql";

export interface QuerySimpleSearchArgs extends QuerySearchArgs {
  beurteilung?: {
    beurteilung: {
      label: string;
      value: string;
    }[];
  };
  hGemId?: {
    bfsNummer?: number;
    gemeinde: string;
    label: string;
    value: string;
  }[];
  publiziert?: boolean;
  vftyp?: {
    label: string;
    value: string;
  }[];
}

export function makeSimpleSearchQuery(
  values: QuerySimpleSearchArgs,
): SearchTabularQueryVariables {
  const filters: SearchFilter[] = [];
  const gemeindeFilter = values.hGemId?.map((g) => {
    return g.bfsNummer ?? parseInt(g.value);
  });
  if (gemeindeFilter && gemeindeFilter.length > 0) {
    filters.push({
      field: "BFS_NR",
      value: gemeindeFilter,
    });
  }

  const beurteilungFilter = values.beurteilung?.beurteilung?.map((b) => {
    return b.value;
  });
  if (beurteilungFilter && beurteilungFilter.length > 0) {
    filters.push({
      field: "BEURTEILUNG",
      value: beurteilungFilter,
    });
  }

  const publiziertFilter = values.publiziert;
  if (publiziertFilter) {
    filters.push({
      field: "AKTUELLSTE_PUBLIKATION",
      value: publiziertFilter,
    });
  }

  const vftypFilter = values.vftyp?.map((v) => {
    return v.value;
  });
  if (vftypFilter && vftypFilter.length > 0) {
    filters.push({
      field: "STANDORTTYP",
      value: vftypFilter,
    });
  }

  return {
    advanced: values.advanced ?? false,
    fields: values.fields,
    filters: filters,
    page: values.page ?? 1,
    perPage: values.perPage ?? 10,
    query: values.query ?? "",
    sortBy: values.sortBy,
  };
}

export function makeAdvancedSearchQuery(
  values: QuerySearchArgs,
): SearchTabularQueryVariables {
  return {
    advanced: values.advanced ?? false,
    fields: values.fields,
    filters: [],
    page: values.page ?? 1,
    perPage: values.perPage ?? 10,
    query: values.query ?? "",
    sortBy: values.sortBy,
  };
}

export const savedSearchFragment = gql`
  fragment SavedSearch on SavedSearch {
    savedSearchId
    query(lang: $lang)
    fields
    isGrouped
    isShared
    name
    showOnDashboard
    sortBy {
      field
      reverse
    }
    user {
      id
      username
    }
  }
`;

export const savedSearchesQuery = gql`
  query savedSearches($lang: Language!) {
    savedSearches {
      ...SavedSearch
    }
  }
  ${savedSearchFragment}
`;

export const updateSavedSearchMutation = gql`
  mutation updateSavedSearch($data: UpdateSavedSearchInput!) {
    savedSearch: updateSavedSearch(data: $data) {
      __typename
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

export function getSearchURL(search: SavedSearchFragment): string {
  const params = new URLSearchParams({
    g: search.isGrouped ? "1" : "0",
    q: search.query,
  });
  search.sortBy?.forEach((s) => {
    params.append("sort", `${s.field}${s.reverse ? ",desc" : ""}`);
  });
  search.fields.forEach((f) => {
    params.append("field", f);
  });
  return `/search/advanced?${params.toString()}`;
}

export const querySearchGraph = gql`
  query searchGraph(
    $advanced: Boolean
    $query: String!
    $filters: [SearchFilter!]
    $page: Int
    $fields: [SearchField!]
    $perPage: Int
  ) {
    search(
      advanced: $advanced
      query: $query
      filters: $filters
      fields: $fields
      page: $page
      perPage: $perPage
    ) {
      __typename
      page
      graph {
        numPages
        numResultsTotal
        results {
          ...VflzItem
        }
      }
    }
  }
  ${VflzItem.fragment}
`;
