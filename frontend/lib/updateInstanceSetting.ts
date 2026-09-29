import { gql } from "graphql-request";

import Form from "@/components/Form";

const updateInstanceSettingMutation = gql`
  mutation UpdateInstanceSetting($data: UpdateInstanceSettingInput!) {
    updateInstanceSetting(data: $data) {
      __typename
      ... on InstanceSetting {
        category
        key
        value
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

export default updateInstanceSettingMutation;
