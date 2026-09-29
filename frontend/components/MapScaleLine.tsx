import ScaleLine from "ol/control/ScaleLine";
import { useEffect } from "react";
import useMap from "react-spatial/useMap";

const scaleLine = new ScaleLine({
  bar: true,
  minWidth: 128,
  text: false,
});

function MapScaleLine() {
  const map = useMap();

  useEffect(() => {
    map.addControl(scaleLine);
    return () => {
      map.removeControl(scaleLine);
    };
  }, [map]);

  return null;
}

export default MapScaleLine;
