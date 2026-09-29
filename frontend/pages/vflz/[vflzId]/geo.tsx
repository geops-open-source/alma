import { gql } from "graphql-request";
import dynamic from "next/dynamic";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import useSWR from "swr";

import Form from "@/components/Form";
import VflzActionMenu from "@/components/VflzActionMenu";
import VflzLayout from "@/components/VflzLayout";
import VflzMapEditorFragment from "@/components/VflzMapEditor.fragment";
import client from "@/lib/client";
import useCurrentUser from "@/lib/useCurrentUser";

import type {
  UpdateVflzGeoInput,
  UpdateVflzGeoMutation,
  VflzGeoQuery,
} from "@/lib/graphql";

const VflzMapEditor = dynamic(
  () => {
    return import("@/components/VflzMapEditor");
  },
  { ssr: false },
);

const queryVflzGeo = gql`
  query VflzGeo($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      readOnly
      ...VflzMapEditor
      ...VflzLayout
    }
  }
  ${VflzMapEditorFragment}
  ${VflzLayout.fragment}
`;

const updateVflzGeoMutation = gql`
  mutation updateVflzGeo($data: UpdateVflzGeoInput!) {
    updateVflzGeo(data: $data) {
      __typename
      ... on Vflz {
        isCurrent
        readOnly
        vflzId
        ...VflzMapEditor
        ...VflzLayout
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
  ${VflzMapEditorFragment}
  ${VflzLayout.fragment}
`;

export default function VflzGeoPage() {
  const { permissions } = useCurrentUser();
  const router = useRouter();
  const { vflzId } = router.query;
  const [mapKey, setMapKey] = useState(1);
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const { data, error, mutate } = useSWR<VflzGeoQuery>(
    vflzId && [queryVflzGeo, { vflzId }],
  );

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    setTimeout(() => {
      return document.getElementById(hash)?.scrollIntoView();
    }, 500);
  }, []);

  return (
    <VflzLayout error={error as unknown} vflz={data?.vflz}>
      <Form<Partial<UpdateVflzGeoInput>>
        disabled={data?.vflz.readOnly || !permissions.canEditVfl}
        model="Vflz"
        onSubmit={async ({ geometry, zentroid }) => {
          if (zentroid) {
            zentroid.coordinates[2] = 0;
          }
          const { updateVflzGeo } = await client.request<UpdateVflzGeoMutation>(
            updateVflzGeoMutation,
            { data: { geometry, vflzId: router.query.vflzId, zentroid } },
          );
          if (updateVflzGeo.__typename === "Vflz") {
            await mutate({ vflz: updateVflzGeo }, { revalidate: false });
            await router.push(`/vflz/${updateVflzGeo.vflzId}/geo`, undefined, {
              scroll: false,
              shallow: true,
            });
          } else {
            return updateVflzGeo; // ProblemGroup
          }
        }}
        values={{
          geometry: data?.vflz?.vflgeo?.geometry ?? undefined,
          zentroid: data?.vflz?.zentroid,
        }}
      >
        <VflzMapEditor key={mapKey} vflz={data?.vflz} />
        {permissions.canEditVfl ? (
          <VflzActionMenu
            canEditVollzug={data?.vflz.isCurrent && permissions.canEditVfl}
            mutatePage={mutate}
            onReset={() => {
              setMapKey(Date.now());
            }}
          />
        ) : null}
      </Form>
    </VflzLayout>
  );
}
