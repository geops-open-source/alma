import { gql } from "graphql-request";

import Form from "@/components/Form";

const createPoolMutation = gql`
  mutation createPool($data: CreatePoolInput!) {
    createPool(data: $data) {
      __typename
      ... on Pool {
        poolId
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

export default createPoolMutation;
