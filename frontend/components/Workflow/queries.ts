import { gql } from "graphql-request";

export const workflowItemFragment = gql`
  fragment WorkflowItem on Task {
    sachbearbeitung {
      subjekt {
        name
        vorname
      }
    }
    deletable
    taskId
    parentId
    type
    title
    status
    startDatum
    endDatum
    faelligkeitsDatum
    faelligkeitsStatus
    notiz
    vflz {
      vflzId
      combinedId
      bezeichnung
    }
    ... on Dokument {
      dokument
    }
  }
`;

export const queryGlobal = gql`
  query GlobalWorkflow(
    $asTree: Boolean!
    $page: Int!
    $perPage: Int!
    $reverse: Boolean!
    $sortBy: SortTasks!
    $taskId: ID
    $filter: GeschaefteFilter
  ) {
    geschaefte(
      asTree: $asTree
      page: $page
      perPage: $perPage
      sortBy: $sortBy
      reverse: $reverse
      taskId: $taskId
      filter: $filter
    ) {
      numPages
      numResultsTotal
      page
      results {
        ...WorkflowItem
      }
    }
  }
  ${workflowItemFragment}
`;

const workflowFilterFragment = gql`
  fragment WorkflowFilter on Vflz {
    teilstandorte {
      combinedId
    }
  }
`;

export const queryVflz = gql`
  query VflzWorkflow(
    $asTree: Boolean!
    $page: Int
    $perPage: Int!
    $reverse: Boolean!
    $sortBy: SortTasks!
    $taskId: ID
    $vflzId: ID!
    $filter: GeschaefteFilter
  ) {
    vflz(vflzId: $vflzId) {
      geschaefte(
        asTree: $asTree
        page: $page
        perPage: $perPage
        sortBy: $sortBy
        reverse: $reverse
        taskId: $taskId
        filter: $filter
      ) {
        numPages
        numResultsTotal
        page
        results {
          ...WorkflowItem
        }
      }
      ...WorkflowFilter
      prozesse {
        optionId
        title
        type
      }
    }
  }
  ${workflowItemFragment}
  ${workflowFilterFragment}
`;
