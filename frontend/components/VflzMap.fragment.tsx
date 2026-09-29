import { gql } from "graphql-request";

const fragment = gql`
  fragment VflzMap on Vflz {
    beurteilung {
      kbsInfo {
        color
      }
    }
    vflgeo {
      geometry
    }
    zentroid
  }
`;

export default fragment;
