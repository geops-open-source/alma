import type { Point } from "geojson";

export default function removeZCoordinate(geometry?: null | Point) {
  if (geometry?.coordinates?.length === 3) {
    geometry.coordinates = geometry.coordinates.slice(0, 2);
  }
  return geometry;
}
