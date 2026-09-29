import { gql } from "graphql-request";
import { useRouter } from "next/router";
import { useMemo } from "react";
import useSWR from "swr";

import VflzItem from "@/components/VflzItem";
import VflzList from "@/components/VflzList";
import useCurrentUser from "@/lib/useCurrentUser";

import type { VflHistoryQuery } from "@/lib/graphql";

const queryVflIds = gql`
  query vflHistory($vflIds: [ID!]!) {
    vflzByVflIds(vflIds: $vflIds) {
      ...VflzItem
    }
  }
  ${VflzItem.fragment}
`;

export default function VflHistory({
  isCombobox,
  max = 30,
}: {
  isCombobox?: boolean;
  max?: number;
}) {
  const { pathname } = useRouter();
  const { getSetting } = useCurrentUser();

  const vflIds = useMemo(() => {
    // vflHistory is updated in @/components/VflzLayout
    const history = getSetting("vflHistory", []);
    return pathname.startsWith("/vflz/[vflzId]")
      ? history.slice(1, max + 1) // remove current vflId from history
      : history.slice(0, max);
  }, [getSetting, max, pathname]);

  const { data } = useSWR<VflHistoryQuery>(
    vflIds.length ? [queryVflIds, { vflIds }] : null,
  );

  return <VflzList isCombobox={isCombobox} items={data?.vflzByVflIds ?? []} />;
}
