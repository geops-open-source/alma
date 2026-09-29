import Event from "ol/events/Event";
import Feature from "ol/Feature";
import GeoJSON from "ol/format/GeoJSON";
import MultiPolygon from "ol/geom/MultiPolygon";
import oleControl from "ole/control/Control";

import type { MultiPolygon as GeoJSONMultiPolygon } from "geojson";
import type { EventsKey } from "ol/events";
import type { Polygon } from "ol/geom";
import type SelectInteraction from "ol/interaction/Select";
import type { OnSignature } from "ol/Observable";
import type VectorSource from "ol/source/Vector";

interface Options {
  operation: (geo: GeoJSONMultiPolygon) => Promise<GeoJSONMultiPolygon>;
  selectInteraction: SelectInteraction;
  source: VectorSource;
}

const geoJSON = new GeoJSON();

export class MakeValidEvent extends Event {
  features: Feature<Polygon>[];
  constructor(type: "makeValid", features: Feature<Polygon>[]) {
    super(type);
    this.features = features;
  }
}

class MakeValidControl extends oleControl {
  on!: oleControl["on"] & OnSignature<"makeValid", MakeValidEvent, EventsKey>;

  operation: Options["operation"];

  selectInteraction: SelectInteraction;

  source: VectorSource;

  un!: oleControl["un"] & OnSignature<"makeValid", MakeValidEvent, null>;

  constructor(options: Options) {
    super({ element: document.createElement("div") });
    this.element.className = "disabled ole-make-valid";
    this.operation = options.operation;
    this.selectInteraction = options.selectInteraction;
    this.source = options.source;
    this.selectInteraction.on("select", this.onSelect.bind(this));
  }

  activate() {
    const features = this.selectInteraction.getFeatures().getArray();
    const geometries = features.map((f) => {
      return f.getGeometry()?.clone();
    });
    const polygons = geometries.filter((g) => {
      return g?.getType() === "Polygon";
    });
    if (polygons.length === 0) {
      return;
    }
    const multiPolygon = new MultiPolygon(polygons as Polygon[]);
    void this.operation(
      geoJSON.writeGeometryObject(multiPolygon) as GeoJSONMultiPolygon,
    ).then((geo) => {
      const newFeatures: Feature<Polygon>[] = [];
      const geometry = geoJSON.readGeometry(geo);
      if (geometry instanceof MultiPolygon) {
        newFeatures.push(
          ...geometry.getPolygons().map((p) => {
            return new Feature(p);
          }),
        );
      }
      this.source.removeFeatures(
        this.selectInteraction.getFeatures().getArray(),
      );
      this.source.addFeatures(newFeatures);
      this.selectInteraction.getFeatures().clear();
      this.dispatchEvent(new MakeValidEvent("makeValid", newFeatures));
      this.selectInteraction.dispatchEvent(new Event("select"));
    });
  }

  private onSelect() {
    const features = this.selectInteraction
      .getFeatures()
      .getArray()
      .filter((f) => {
        return f.getGeometry()?.getType() === "Polygon";
      });
    if (features.length > 0) {
      this.element.classList.remove("disabled");
    } else {
      this.element.classList.add("disabled");
    }
  }
}

export default MakeValidControl;
