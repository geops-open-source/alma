import { gql } from "graphql-request";
import { useRouter } from "next/router";
import useSWR from "swr";

import VflzLayout from "@/components/VflzLayout";
import Workflow from "@/components/Workflow";

import type { VflzWorkflowLayoutQuery } from "@/lib/graphql";

const queryVflzWorkflow = gql`
  query VflzWorkflowLayout($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      ...VflzLayout
    }
  }
  ${VflzLayout.fragment}
`;

export default function VflzWorkflowPage() {
  const router = useRouter();
  const { vflzId } = router.query as { vflzId: string };
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const { data, error, mutate } = useSWR<VflzWorkflowLayoutQuery>(
    vflzId && [queryVflzWorkflow, { vflzId }],
  );
  return (
    <VflzLayout error={error as unknown} vflz={data?.vflz}>
      <Workflow mutatePage={mutate} vflz={data?.vflz} vflzId={vflzId} />
    </VflzLayout>
  );
}
