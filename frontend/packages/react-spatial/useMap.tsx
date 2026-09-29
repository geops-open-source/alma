import { useContext } from "react";

import { MapContext } from "./Map";

export default function useMap() {
  return useContext(MapContext);
}
