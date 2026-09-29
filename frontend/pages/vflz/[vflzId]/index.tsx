import { gql } from "graphql-request";
import { useRouter } from "next/router";
import useSWR from "swr";

import VflzLayout from "@/components/VflzLayout";
import VflzOverview from "@/components/VflzOverview";
import useCurrentUser from "@/lib/useCurrentUser";

import type { VflzOverviewQuery } from "@/lib/graphql";

const queryVflzOverview = gql`
  query VflzOverview($vflzId: ID!, $withGeschaefte: Boolean!) {
    vflz(vflzId: $vflzId) {
      ...VflzLayout
      ...VflzOverview
    }
  }
  ${VflzLayout.fragment}
  ${VflzOverview.fragment}
`;

export default function VflzOverviewPage() {
  const { vflzId } = useRouter().query;
  const { permissions } = useCurrentUser();
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const { data, error, isLoading } = useSWR<VflzOverviewQuery>(
    vflzId && [
      queryVflzOverview,
      { vflzId, withGeschaefte: permissions.canViewProcess ?? false },
    ],
  );
  return (
    <VflzLayout
      error={error as unknown}
      isLoading={isLoading}
      vflz={data?.vflz}
    >
      {!error && !isLoading && (
        <VflzOverview showReport={true} vflz={data?.vflz} />
      )}
    </VflzLayout>
  );
}
