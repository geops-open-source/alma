import { gql } from "graphql-request";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import { useMemo } from "react";
import useSWR from "swr";

import VflzMapFragment from "@/components/VflzMap.fragment";

import type {
  SettingItem,
  SettingWMSItem,
} from "@/components/MapLayerTree/tree";
import type { VflzMapQuery } from "@/lib/graphql";

const queryVflzMap = gql`
  query VflzMap($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      ...VflzMap
    }
  }
  ${VflzMapFragment}
`;

const loading = () => {
  return <div />;
};

// TODO: If we create a specific map component for this page,
// we should move the RenderCompleteIndicator component from VflzMap to the new one.
const VflzMap = dynamic(
  () => {
    return import("@/components/VflzMap");
  },
  { loading, ssr: false },
);

const MapLayerTree = dynamic(
  () => {
    return import("@/components/MapLayerTree");
  },
  { loading, ssr: false },
);

const MapScaleLine = dynamic(
  () => {
    return import("@/components/MapScaleLine");
  },
  { loading, ssr: false },
);

export default function MapPage() {
  const { vflzId } = useRouter().query;

  // aerial, map-color, map-grey
  const baseLayerKey = useSearchParams().get("baselayer") ?? "aerial";
  const layersKey = useSearchParams().get("layers");
  const { data } = useSWR<VflzMapQuery>(vflzId && [queryVflzMap, { vflzId }]);

  const hideZentroid = useMemo(() => {
    return data?.vflz?.vflgeo?.geometry?.type !== "Point";
  }, [data?.vflz?.vflgeo?.geometry?.type]);

  const settingItems: SettingItem[] | undefined = useMemo(() => {
    if (!layersKey) {
      return;
    }
    const items: SettingItem[] = [];
    layersKey.split(",").forEach((key) => {
      if (key === "parzellen") {
        // TODO: this infos should come from backend
        const item: SettingWMSItem = {
          id: "parzellen",
          name: "Liegenschaften",
          title: "Liegenschaften",
          type: "WMS",
          url: "https://wfs.geodienste.ch/av_0/deu",
          version: 1,
          visible: true,
        };
        items.push(item);
      }
    });
    return items?.length ? items : undefined;
  }, [layersKey]);

  return (
    <VflzMap
      baseLayerKey={baseLayerKey}
      className="h-screen w-screen"
      hideControls
      hideZentroid={hideZentroid}
      vflz={data?.vflz}
    >
      <MapLayerTree
        className="hidden"
        forceItems={settingItems}
        settingName="editor"
      />
      <MapScaleLine />
    </VflzMap>
  );
}
