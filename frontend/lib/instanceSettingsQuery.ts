import { gql } from "graphql-request";

const queryInstanceSettings = gql`
  query InstanceSettings {
    instanceSettings {
      category
      key
      value
      valueSchema
    }
  }
`;

export default queryInstanceSettings;
