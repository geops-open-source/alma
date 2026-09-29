import { type Extent } from "ol/extent";
import { useCallback, useState } from "react";

import Map from "@/components/Map";
import MapLayerTree from "@/components/MapLayerTree";
import MapSearch from "@/components/MapSearch";
import { NoResultsInfo } from "@/components/SearchLayout/NoResultsInfo";
import VflzSearchLayer from "@/components/VflzSearchLayer";

import type { SearchFilter } from "@/lib/graphql";

export default function SearchResultsMap({
  advanced = false,
  filters = [],
  query,
}: {
  advanced?: boolean;
  filters?: SearchFilter[];
  query: string;
}) {
  const [zoomExtent, setZoomExtent] = useState<Extent>();
  const [error, setError] = useState<unknown>();

  const onError = useCallback((err: unknown) => {
    setError(err);
  }, []);

  return (
    <>
      {!!error && <NoResultsInfo />}
      <Map
        className={`h-[calc(100vh-10rem)] w-full ${error ? "hidden" : ""}`}
        settingName="search"
        zoomExtent={zoomExtent}
      >
        <MapLayerTree settingName="search">
          {(featureInfoActive) => {
            return (
              <VflzSearchLayer
                advanced={advanced}
                featureInfoActive={featureInfoActive}
                filters={filters}
                onError={onError}
                query={query}
                setZoomExtent={setZoomExtent}
              />
            );
          }}
        </MapLayerTree>
        <MapSearch />
      </Map>
    </>
  );
}
