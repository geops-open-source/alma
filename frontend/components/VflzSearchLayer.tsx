import { gql, type RequestOptions } from "graphql-request";
import { asArray } from "ol/color";
import { buffer, type Extent } from "ol/extent";
import GeoJSON from "ol/format/GeoJSON";
import Draw from "ol/interaction/Draw";
import VectorLayer from "ol/layer/Vector";
import Overlay from "ol/Overlay";
import VectorSource from "ol/source/Vector";
import Fill from "ol/style/Fill";
import Icon from "ol/style/Icon";
import Stroke from "ol/style/Stroke";
import Style from "ol/style/Style";
import ModifyControl from "ole/control/Modify";
import Toolbar from "ole/control/Toolbar";
import { useEffect, useMemo, useRef, useState } from "react";
import Layer from "react-spatial/Layer";
import useMap from "react-spatial/useMap";

import InfoCircleIcon from "@/components/icons/InfoCircleIcon";
import XIcon from "@/components/icons/XIcon";
import VflzInfo from "@/components/VflzInfo";
import { iconProps } from "@/components/VflzMap";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import isPointResolution from "@/lib/isPointResolution";

import type Feature from "ol/Feature";
import type { FeatureLike } from "ol/Feature";
import type Geometry from "ol/geom/Geometry";
import type olLayer from "ol/layer/Layer";
import type MapBrowserEvent from "ol/MapBrowserEvent";
import type { Dispatch, SetStateAction } from "react";

import type { SearchFilter, SearchMapQuery } from "@/lib/graphql";

const geoJSON = new GeoJSON();

const vflzSearchSource = new VectorSource();

export const vflzSearchLayer = new VectorLayer({
  properties: { id: "vflzSearchLayer", readonly: true },
  source: vflzSearchSource,
  style: (feature) => {
    const colorString = (feature.get("color") as string) || "#000000";
    const color = [...asArray(colorString)].splice(0, 3);
    return new Style({
      fill: new Fill({ color: [...color, 0.5] }),
      image: new Icon({ ...iconProps, color, src: "/map/pin-transparent.svg" }),
      stroke: new Stroke({ color, width: 3 }),
    });
  },
});

const searchQuery = gql`
  query searchMap(
    $advanced: Boolean!
    $extent: [Float!]
    $query: String!
    $filters: [SearchFilter!]!
    $withPoints: Boolean!
  ) {
    search(advanced: $advanced, query: $query, filters: $filters) {
      geo(extent: $extent) {
        zentroid @include(if: $withPoints)
        vflgeo @skip(if: $withPoints)
      }
    }
  }
`;

const layerFilter = {
  layerFilter: (l: olLayer) => {
    return l === vflzSearchLayer;
  },
};

const overlay = new Overlay({
  offset: [0, -8],
  positioning: "bottom-center",
});

const getFeatureVflzId = (feature: FeatureLike) => {
  const featureId = feature.get("vflzId") as unknown;
  if (typeof featureId === "string") {
    return featureId;
  }
  if (typeof featureId === "number") {
    return featureId.toString();
  }
  return undefined;
};
const ABORT_ERROR_MESSAGE = "New fetch initiated";
const UNMOUNT_ERROR_MESSAGE = "effect unmounted";

export default function VflzSearchLayer({
  advanced = false,
  featureInfoActive,
  filters = [],
  ignoreVflzId,
  onError,
  query,
  setZoomExtent,
}: {
  advanced?: boolean;
  featureInfoActive: boolean;
  filters?: SearchFilter[];
  ignoreVflzId?: string;
  onError?: (error: unknown) => void;
  query?: string;
  setZoomExtent?: Dispatch<SetStateAction<Extent | undefined>>;
}) {
  const map = useMap();
  const { activeLocale, pluralRules, t } = useI18n();
  const ref = useRef<HTMLDivElement>(null);
  const [vflzIds, setVflzIds] = useState<string[]>([]);
  const shouldResetZoomExtent = useRef(true);

  useEffect(() => {
    return overlay.panIntoView();
  }, [vflzIds]);

  useEffect(() => {
    vflzSearchLayer.set("title", t("VflzSearchLayer.title.other"));
  }, [activeLocale, t]);

  useEffect(() => {
    // fetch data on moveend
    let controller: AbortController | undefined;
    shouldResetZoomExtent.current = true;
    const fetchData = () => {
      onError?.(undefined);

      controller?.abort(ABORT_ERROR_MESSAGE);
      const resolution = map.getView().getResolution();
      if (resolution && vflzSearchLayer.getVisible()) {
        controller = new AbortController();

        client
          .request<SearchMapQuery>({
            document: searchQuery,
            signal: controller.signal as RequestOptions["signal"],
            variables: {
              advanced: advanced,
              extent: map.getView().calculateExtent(),
              filters: filters,
              query: query ?? "",
              withPoints: isPointResolution(resolution),
            },
          })
          .then((result) => {
            vflzSearchSource.clear();
            const features: Feature<Geometry>[] = geoJSON.readFeatures(
              result.search.geo.zentroid ?? result.search.geo.vflgeo,
            );
            vflzSearchSource.addFeatures(features);
            setVflzIds((current) => {
              if (!current.length) {
                return current;
              }
              const availableIds = new Set(
                features
                  .map((feature) => {
                    return getFeatureVflzId(feature);
                  })
                  .filter((id): id is string => {
                    return Boolean(id);
                  }),
              );
              const nextSelection = current.filter((id) => {
                return availableIds.has(id);
              });
              if (!nextSelection.length) {
                overlay.setPosition(undefined);
                return nextSelection;
              }
              if (nextSelection.length === current.length) {
                return current;
              }
              return nextSelection;
            });
            if (shouldResetZoomExtent.current && !vflzSearchSource.isEmpty()) {
              const extent = vflzSearchSource.getExtent();
              if (extent && setZoomExtent) {
                setZoomExtent(buffer(extent, 400));
              }
              shouldResetZoomExtent.current = false;
            }
          })
          .catch((err: Error | string) => {
            if (
              (err as Error).name !== "AbortError" &&
              err !== ABORT_ERROR_MESSAGE &&
              err !== UNMOUNT_ERROR_MESSAGE
            ) {
              onError?.(true);
            }
          });
      }
    };
    map.on("moveend", fetchData);
    fetchData();
    return () => {
      controller?.abort(UNMOUNT_ERROR_MESSAGE);
      map.un("moveend", fetchData);
    };
  }, [map, advanced, filters, query, setZoomExtent, onError]);

  useEffect(() => {
    // handle OpenLayers overlay
    function handlePointermove(event: MapBrowserEvent) {
      // change cursor on hover
      const target = map.getTarget();
      if (target instanceof HTMLElement) {
        const pixel = map.getEventPixel(event.originalEvent);
        const hasFeatureAtPixel = map.hasFeatureAtPixel(pixel, layerFilter);
        target.style.cursor = hasFeatureAtPixel ? "pointer" : "";
      }
    }

    map.on("pointermove", handlePointermove);
    map.addOverlay(overlay);
    overlay.setElement(ref.current ?? undefined);
    return () => {
      map.un("pointermove", handlePointermove);
      map.removeOverlay(overlay);
      overlay.setElement(undefined);
    };
  }, [map]);

  useEffect(() => {
    // handle click event
    if (featureInfoActive) {
      return;
    }
    function handleClick(event: MapBrowserEvent) {
      const drawActive = map
        .getInteractions()
        .getArray()
        .some((i) => {
          return i instanceof Draw && i.getActive();
        });
      const modifyFeatures = map
        .getControls()
        .getArray()
        .find((c) => {
          return c instanceof Toolbar;
        })
        ?.getControls()
        .getArray()
        .find((c) => {
          return c instanceof ModifyControl;
        })
        ?.selectInteraction.getFeatures();
      if (drawActive || (modifyFeatures?.getLength() ?? 0) > 0) {
        return;
      }
      // open and close overlay on click
      const clickedFeatures = map.getFeaturesAtPixel(event.pixel, layerFilter);
      const clickedIds = Array.from(
        new Set(
          clickedFeatures
            .map((feature) => {
              return getFeatureVflzId(feature);
            })
            .filter((id): id is string => {
              return Boolean(id);
            }),
        ),
      );
      const visibleIds = ignoreVflzId
        ? clickedIds.filter((id) => {
            return id !== ignoreVflzId;
          })
        : clickedIds;
      if (visibleIds.length > 0) {
        overlay.setPosition(event.coordinate);
        setVflzIds((current) => {
          if (
            current.length === clickedIds.length &&
            current.every((id, index) => {
              return id === clickedIds[index];
            })
          ) {
            return current;
          }
          return clickedIds;
        });
      } else {
        overlay.setPosition(undefined);
        setVflzIds([]);
      }
    }
    map.on("click", handleClick);
    return () => {
      return map.un("click", handleClick);
    };
  }, [featureInfoActive, ignoreVflzId, map]);

  useEffect(() => {
    if (featureInfoActive) {
      overlay.setPosition(undefined);
    }
  }, [featureInfoActive]);

  const displayedVflzIds = useMemo<string[]>(() => {
    if (featureInfoActive || !vflzIds.length) {
      return [];
    }
    if (!ignoreVflzId) {
      return vflzIds;
    }
    return vflzIds.filter((id) => {
      return id !== ignoreVflzId;
    });
  }, [featureInfoActive, ignoreVflzId, vflzIds]);

  useEffect(() => {
    if (!displayedVflzIds.length) {
      overlay.setPosition(undefined);
    }
  }, [displayedVflzIds]);

  const pluralRule = pluralRules.select(displayedVflzIds.length);

  return (
    <Layer layer={vflzSearchLayer}>
      <div>
        {/* This additional div is required, otherwise OpenLayers and React DOM handling will collide. */}
        <div className="alma-map-widget p-1 shadow-lg" ref={ref}>
          <div className="flex items-center justify-between px-2">
            <div className="text-gray-9 flex items-center space-x-2">
              <InfoCircleIcon className="w-4" />
              <span className="text-xs font-semibold">
                {t(`VflzSearchLayer.title.${pluralRule}`, {
                  count: displayedVflzIds.length.toString(),
                })}
              </span>
            </div>
            <button
              onClick={() => {
                setVflzIds([]);
                overlay.setPosition(undefined);
              }}
              type="button"
            >
              <XIcon className="text-gray-7 hover:text-gray-8 w-5" />
            </button>
          </div>
          <div className="max-h-96 space-y-1 overflow-auto rounded-md">
            {displayedVflzIds.map((id) => {
              return (
                <VflzInfo
                  className="rounded-md p-3 pt-2"
                  key={id}
                  vflzId={id}
                />
              );
            })}
          </div>
          <svg
            className="pointer-events-none absolute top-full left-1/2 h-2 w-4 -translate-x-1/2 fill-white/30"
            viewBox="0 0 16 8"
          >
            <path d="M0 0L8 8L16 0H0Z" />
          </svg>
        </div>
      </div>
    </Layer>
  );
}
