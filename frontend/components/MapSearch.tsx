import { Input } from "@headlessui/react";
import DOMPurify from "dompurify";
import debounce from "lodash/debounce";
import Feature from "ol/Feature";
import GeoJSONFormat from "ol/format/GeoJSON";
import Point from "ol/geom/Point";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Fill, Icon, Stroke, Style } from "ol/style";
import React, { memo, useCallback, useMemo, useRef, useState } from "react";
import useSWR from "swr";

import ResetIcon from "@/components/icons/ResetIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import { defaultMaxExtent } from "@/components/Map";
import { useI18n } from "@/lib/i18n";
import useClickOutside from "@/lib/useClickOutside";
import useSearchCoordinates from "@/lib/useSearchCoordinates";
import useSetting from "@/lib/useSetting";
import useMap from "@/packages/react-spatial/useMap";

import type { InputProps } from "@headlessui/react";
import type { Extent } from "ol/extent";
import type MultiPolygon from "ol/geom/MultiPolygon";
import type Polygon from "ol/geom/Polygon";
import type { ButtonHTMLAttributes } from "react";
import type { Fetcher, Key, Middleware, SWRConfiguration, SWRHook } from "swr";

import type { CoordinatesResult } from "@/lib/useSearchCoordinates";

type LocationOrigin = "address" | "gg25" | "parcel";

type Location = GeoJSON.Feature<
  GeoJSON.Geometry,
  {
    [key: string]: unknown;
    label?: string;
    origin?: LocationOrigin; // only for api.ge.admin.ch coordinates hack
  }
>;

type Locations = GeoJSON.FeatureCollection<
  GeoJSON.Geometry,
  Location["properties"]
>;

const baseClassName =
  "border-gray-5 w-64 rounded-lg border px-3 py-2 pl-8 text-xs font-medium shadow-xs focus:outline-hidden";

function InputSearch({ className, onChange, ...props }: InputProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [displayValue, setDisplayValue] = useState(props.value ?? "");

  const hasResetButton = useMemo(() => {
    return !!displayValue;
  }, [displayValue]);

  return (
    <div className="relative flex h-11 w-full items-center rounded-lg">
      <div className="text-gray-6 pointer-events-none absolute inset-y-0 left-0 flex items-center rounded-lg pl-3">
        <SearchIcon className="overflow-hidden" />
      </div>
      <Input
        className={`${baseClassName} flex-1 pl-9 ${hasResetButton && "pr-9"} bg-gray-2 h-11 w-full ${className as string}`}
        data-test="map-search-input"
        onChange={(evt) => {
          setDisplayValue(evt.target.value);
          if (onChange) {
            onChange(evt);
          }
        }}
        ref={inputRef}

        type={"text"}
        {...props}
        value={displayValue}
      />
      {hasResetButton && (
        <button
          className="bg-gray-2 text-gray-6 hover:text-gray-8 disabled:bg-gray-2 disabled:text-gray-6 absolute top-1 right-1 bottom-1 flex w-8 items-center justify-center rounded-lg border-0 text-xs font-semibold hover:bg-white"
          onClick={() => {
            setDisplayValue("");
            return inputRef.current?.focus();
          }}
          type="button"
        >
          <ResetIcon />
        </button>
      )}
    </div>
  );
}

function SearchResult({
  children,
  ...props
}: { children: React.ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className="w-full px-2 py-1 text-left" {...props} type="button">
      {children}
    </button>
  );
}

// We export only for testing purposes, because it is an unmanged layers.
export const searchLayer = new VectorLayer({
  source: new VectorSource(),
  style: new Style({
    fill: new Fill({ color: "#4EE4FF77" }),
    image: new Icon({
      anchor: [0.5, 1],
      src: "/map/pin-info.svg",
    }),
    stroke: new Stroke({ color: "#277277", width: 2 }),
  }),
});

const format = new GeoJSONFormat();

const addFeature = (feature: Feature, map: ReturnType<typeof useMap>) => {
  searchLayer.getSource()?.addFeature(feature);

  if (searchLayer.getMapInternal() !== map) {
    searchLayer.setMap(map);
  }
};

const fetcherAll = async (urls: string[], signal?: AbortSignal) => {
  const results = await Promise.allSettled(
    urls.map(async (url) => {
      try {
        const res = await fetch(url, { signal });
        if (!res.ok) {
          const info = (await res.json()) as {
            error: { message: string };
          };

          const error = new Error(
            "An error occurred while fetching the data.",
            {
              cause: `Url: ${url}, Info: ${JSON.stringify(info)}`,
            },
          );
          throw error;
        }
        return res.json() as Promise<Locations>;
      } catch (error) {
        // Ignore abort error
        if (error instanceof Error && error.name === "AbortError") {
          return { features: [], type: "FeatureCollection" }; // Return empty data for aborted requests
        }

        throw error;
      }
    }),
  );

  // If all requests failed we display the error message
  if (results.every((r) => r.status === "rejected")) {
    throw new Error(results[0].reason as string);
  }
  return results.map((r) =>
    r.status === "fulfilled"
      ? r.value
      : { features: [], type: "FeatureCollection" },
  );
};

export interface SearchSetting {
  key: string;
  options?: {
    category?: {
      de?: string;
      fr?: string;
      it?: string;
    };
    labelProperty?: string;
  };
  url: string;
}

const defaultSearches: SearchSetting[] = [];

export const cancelPreviousMiddleware: Middleware = (useSWRNext: SWRHook) => {
  return <Data, Error>(
    key: Key,
    fetcher: Fetcher<Data> | null,
    config: SWRConfiguration<Data, Error>,
  ) => {
    // 1. Maintain a mutable ref for the AbortController unique to this hook instance
    const abortRef = useRef<AbortController | null>(null);

    // 2. Wrap the fetcher only if a custom fetcher function is provided
    const extendedFetcher: Fetcher<Data> | null = fetcher
      ? async (...args: unknown[]) => {
          // Cancel the previous pending request if it is still running
          if (abortRef.current) {
            abortRef.current.abort();
          }

          // Initialize a new controller for the current request
          abortRef.current = new AbortController();

          // SWR arguments can be a string, array, or object depending on your key format.
          // We extract the base arguments and append the abort signal as the final argument.
          const fetcherArgs = Array.isArray(args) ? args : [args];

          // @ts-expect-error - what?

          return fetcher(...fetcherArgs, abortRef.current.signal);
        }
      : null;

    // 3. Pass the intercepted fetcher down to the next SWR chain link
    // @ts-expect-error - what?
    return useSWRNext(key, extendedFetcher, config);
  };
};

function MapSearch({ ...props }: InputProps) {
  const [maxExtent] = useSetting<Extent>("ui.map.maxExtent", defaultMaxExtent);
  const [searches] = useSetting<SearchSetting[]>(
    "ui.map.searches",
    defaultSearches,
  );
  const { activeLocale, t } = useI18n();
  const map = useMap();
  const innerRef = useRef<HTMLDivElement>(null);
  const [value, setValue] = useState("");
  const [showResults, setShowResults] = useState(false);

  const coordinates = useSearchCoordinates(value, {
    extent: maxExtent,
    projection: map.getView()?.getProjection()?.getCode(),
  });

  // Close results panel on click outside the search
  useClickOutside(innerRef, () => {
    setShowResults(false);
  });

  const urls = useMemo(() => {
    if (!value || !activeLocale) {
      return null;
    }
    return searches.map((search) => {
      const url = search.url
        .replace("{searchText}", encodeURIComponent(value))
        .replace("{lang}", activeLocale);
      return url;
    });
  }, [searches, value, activeLocale]);

  // @ts-expect-error - what?
  const { data, error, isLoading } = useSWR<Locations[], Error>(
    urls ?? null,
    fetcherAll,
    { use: [cancelPreviousMiddleware] }, // Inject middleware
  );

  const goToCoordinates = useCallback(
    (coordinatesResult: CoordinatesResult) => {
      searchLayer.getSource()?.clear(true);
      if (coordinatesResult) {
        addFeature(new Feature(new Point(coordinatesResult.coordinates)), map);

        map?.getView()?.cancelAnimations();
        map
          ?.getView()
          .animate({ center: coordinatesResult.coordinates, zoom: 8 });
      }
    },
    [map],
  );

  const goToLocation = useCallback(
    (location: Location) => {
      searchLayer.getSource()?.clear(true);
      const { bbox } = location;
      const feature = format.readFeature(location, {
        dataProjection: "EPSG:2056",
        featureProjection:
          map.getView()?.getProjection()?.getCode() ?? "EPSG:3857",
      }) as Feature<MultiPolygon | Point | Polygon>;

      const bboxGeometry =
        location.properties.origin === "gg25"
          ? bbox
          : feature.getGeometry()?.getExtent();
      const geometry = feature?.getGeometry();

      if (geometry) {
        // SearchServer from geoadmin returns bad ordered coordinates for 2056 projection
        if (location.properties.origin && geometry instanceof Point) {
          const reversed = [...geometry.getCoordinates().reverse()];
          geometry.setCoordinates(reversed);
        }
        addFeature(feature, map);
      }

      // Zoom on bbox for gemeinde
      if (bboxGeometry) {
        map?.getView()?.cancelAnimations();
        map?.getView().fit(bboxGeometry, { duration: 500, maxZoom: 16 });
      } else if (geometry) {
        map?.getView()?.cancelAnimations();
        const zoomLevel = 16;

        map?.getView().animate({
          center: geometry?.getFirstCoordinate(),
          zoom: zoomLevel,
        });
      }
    },
    [map],
  );

  const goToFirstResult = useCallback(() => {
    if (coordinates) {
      goToCoordinates(coordinates);
      return;
    }
    const locationData = data?.flatMap((d) => d?.features)?.[0];
    if (locationData) {
      goToLocation(locationData);
    }
  }, [coordinates, data, goToCoordinates, goToLocation]);

  const showErrorMessage = useMemo(() => {
    return !!value && !coordinates && !isLoading && !!error;
  }, [value, coordinates, isLoading, error]);

  const showNoDataMessage = useMemo(() => {
    return (
      !showErrorMessage &&
      !coordinates &&
      data?.flatMap((d) => d?.features)?.length === 0 &&
      !error
    );
  }, [showErrorMessage, coordinates, data, error]);

  const debouncedOnChange = useCallback(
    (evt: React.ChangeEvent<HTMLInputElement>) => {
      return debounce(() => {
        setValue(evt.target.value);
        setShowResults(true);
      }, 300)();
    },
    [],
  );

  return (
    <div
      className="alma-map-widget text-gray-7 absolute top-4 left-40 z-20 flex w-80 flex-col space-x-px text-xs font-medium"
      ref={innerRef}
    >
      <div className={`flex w-full space-x-px p-1`}>
        <InputSearch
          onChange={debouncedOnChange}
          onFocus={() => {
            setShowResults(true);
          }}
          onKeyDown={(evt) => {
            if (evt.key === "Enter") {
              goToFirstResult();
              setShowResults(false);
            }
            if (evt.key === "Escape") {
              setShowResults(false);
            }
          }}
          placeholder={t("map.search.placeholder")}
          {...props}
        />
      </div>

      {showResults &&
        !!value &&
        (showNoDataMessage ||
          showErrorMessage ||
          !!coordinates ||
          !!data?.flatMap((d) => d?.features)?.length) && (
          <div className="w-full rounded-lg p-1">
            <div className="bg-gray-2 flex max-h-80 flex-col space-y-1 overflow-y-auto rounded-lg">
              {showNoDataMessage && (
                <div className="p-2" data-test="map-search-no-results">
                  {t("map.search.key.noresults")}
                </div>
              )}
              {showErrorMessage && (
                <div className="p-2" data-test="map-search-error">
                  {t("map.search.key.error")}
                </div>
              )}
              {/* Parse the query and find if it is a coo)rdinate and if so, show a text as result "Zoom to ..." */}
              {!!coordinates && (
                <div className="flex flex-col items-start justify-start">
                  <div
                    className="bg-gray-3 text-gray-6 sticky top-0 w-full p-2 text-xs font-semibold"
                    data-test="map-search-title-coordinates"
                  >
                    {t("map.search.key.coordinates")}:
                  </div>

                  <SearchResult
                    data-test="map-search-results-coordinates-1"
                    onClick={(evt) => {
                      goToCoordinates(coordinates);
                      evt.stopPropagation();
                    }}
                  >
                    {t("map.search.key.zoomto")}{" "}
                    {coordinates.coordinates[0].toFixed(0)},{" "}
                    {coordinates.coordinates[1].toFixed(0)}
                  </SearchResult>
                </div>
              )}
              {/* Parse the FeatureCollection results of search */}

              {searches.map((search, index) => {
                if (!data?.[index]?.features?.length) {
                  return null;
                }
                return (
                  <div
                    className="flex flex-col items-start justify-start"
                    key={search.key}
                  >
                    <div
                      className="bg-gray-3 text-gray-6 sticky top-0 w-full p-2 text-xs font-semibold"
                      data-test={`map-search-title-${search.key}`}
                    >
                      {t(`map.search.key.${search.key}`) ||
                        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing
                        search.options?.category?.[activeLocale] ||
                        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing
                        search.options?.category?.de ||
                        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing
                        search.options?.category?.fr ||
                        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing
                        search.options?.category?.it ||
                        search.key}
                      :
                    </div>
                    {data?.[index]?.features?.map(
                      (feature: Location, idx: number) => {
                        return (
                          <SearchResult
                            data-test={`map-search-results-${search.key}-${idx}`}
                            key={feature.id}
                            onClick={(evt) => {
                              goToLocation(feature);
                              evt.stopPropagation();
                            }}
                          >
                            <span
                              // eslint-disable-next-line @eslint-react/dom-no-dangerously-set-innerhtml
                              dangerouslySetInnerHTML={{
                                __html: DOMPurify.sanitize(
                                  (feature.properties[
                                    search.options?.labelProperty ?? "label"
                                  ] as string) ?? "",
                                ),
                              }}
                            />
                          </SearchResult>
                        );
                      },
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
    </div>
  );
}

export default memo(MapSearch);
