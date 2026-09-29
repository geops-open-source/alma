import { GraphQLClient } from "graphql-request";

const headers = process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER
  ? { "alma-e2e-test-user": process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER }
  : undefined;

const client = new GraphQLClient("/graphql", { headers });

export default client;
