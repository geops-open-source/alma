import { gql } from "graphql-request";
import useSWR from "swr";

import VflzSachbearbeiter from "@/components/VflzSachbearbeiter";
import VflzSummary from "@/components/VflzSummary";

import type { VflzInfoQuery } from "@/lib/graphql";

const queryVflzInfo = gql`
  query VflzInfo($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      ...VflzSachbearbeiter
      ...VflzSummary
    }
  }
  ${VflzSachbearbeiter.fragment}
  ${VflzSummary.fragment}
`;

export default function VflzInfo({
  className = "",
  vflzId,
}: {
  className?: string;
  vflzId?: string;
}) {
  const { data } = useSWR<VflzInfoQuery>(vflzId && [queryVflzInfo, { vflzId }]);
  return (
    <div className={`space-y-2 bg-white ${className}`}>
      <VflzSummary vflz={data?.vflz} />
      <VflzSachbearbeiter beteiligteStandort={data?.vflz?.beteiligteStandort} />
    </div>
  );
}
