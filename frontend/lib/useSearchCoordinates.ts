import proj4 from "proj4";
import { useMemo } from "react";

import type { Extent } from "ol/extent";

export type CoordinateProjection =
  "EPSG:2056" | "EPSG:21781" | "EPSG:3857" | "EPSG:4326";

export interface UseCoordinatesOptions {
  /**
   * Allowed `[minX, minY, maxX, maxY]` bounds in `projection`.
   * Coordinates outside these bounds are treated as unparseable.
   */
  extent?: Extent;
  /** Projection of the returned coordinates. */
  projection?: string;
}

export interface CoordinatesResult {
  /** Coordinates transformed to `projection`. */
  coordinates: [number, number];
  /** Projection used for `coordinates`. */
  projection: string;
  /** Projection inferred from the input value. */
  sourceProjection: CoordinateProjection;
}

const DEFAULT_PROJECTION = "EPSG:2056";

const coordinatePattern =
  /^\s*[[()]?\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:[,;/]|\s+)\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[\])]?\s*$/;

// Swiss coordinate reference systems are not included in proj4's default set.
proj4.defs(
  "EPSG:2056",
  "+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=2600000 +y_0=1200000 +ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0 +units=m +no_defs",
);
proj4.defs(
  "EPSG:21781",
  "+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=600000 +y_0=200000 +ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0 +units=m +no_defs",
);

function isBetween(value: number, min: number, max: number) {
  return value >= min && value <= max;
}

function getProjection(x: number, y: number): CoordinateProjection | undefined {
  // EPSG:4326 is longitude, latitude (x, y).
  if (isBetween(x, -180, 180) && isBetween(y, -90, 90)) {
    return "EPSG:4326";
  }

  // Bounding boxes cover Switzerland with a small margin. Checking these before
  // Web Mercator avoids classifying Swiss coordinates as generic EPSG:3857.
  if (isBetween(x, 2_400_000, 2_900_000) && isBetween(y, 900_000, 1_400_000)) {
    return "EPSG:2056";
  }

  if (isBetween(x, 400_000, 900_000) && isBetween(y, 0, 400_000)) {
    return "EPSG:21781";
  }

  if (
    isBetween(x, -20_037_508.342789244, 20_037_508.342789244) &&
    isBetween(y, -20_037_508.342789244, 20_037_508.342789244)
  ) {
    return "EPSG:3857";
  }
}

function parseCoordinates(value: string):
  | {
      coordinates: [number, number];
      projection: CoordinateProjection;
    }
  | undefined {
  const match = coordinatePattern.exec(value);
  if (!match) return;

  const coordinates: [number, number] = [Number(match[1]), Number(match[2])];
  if (!coordinates.every(Number.isFinite)) return;

  const projection = getProjection(...coordinates);
  return projection ? { coordinates, projection } : undefined;
}

function isInExtent(
  coordinates: [number, number],
  extent: UseCoordinatesOptions["extent"],
) {
  if (!extent) return true;

  const [minX, minY, maxX, maxY] = extent;
  const [x, y] = coordinates;
  return x >= minX && x <= maxX && y >= minY && y <= maxY;
}

/**
 * Parses a coordinate pair and transforms it to the requested projection.
 *
 * Accepted input examples: `8.54, 47.37`, `2600000 1200000`, and
 * `(600000; 200000)`. Inputs must be ordered as x, y (longitude, latitude
 * for EPSG:4326).
 */
export default function useCoordinates(
  value: string,
  { extent, projection = DEFAULT_PROJECTION }: UseCoordinatesOptions = {},
): CoordinatesResult | undefined {
  return useMemo(() => {
    const parsed = parseCoordinates(value);
    if (!parsed) return;

    const coordinates = proj4(
      parsed.projection,
      projection,
      parsed.coordinates,
    );
    if (!isInExtent(coordinates, extent)) return;

    return {
      coordinates,
      projection,
      sourceProjection: parsed.projection,
    };
  }, [value, extent, projection]);
}
