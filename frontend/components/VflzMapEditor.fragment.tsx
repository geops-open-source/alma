import { gql } from "graphql-request";

import { mutationInfoFragment } from "@/components/MutationInfo";
import VflzMapFragment from "@/components/VflzMap.fragment";

const fragment = gql`
  fragment VflzMapEditor on Vflz {
    vflzId
    vflgeo {
      erfassungMutation {
        ...MutationInfo
      }
    }
    ...VflzMap
  }
  ${mutationInfoFragment}
  ${VflzMapFragment}
`;

export default fragment;
