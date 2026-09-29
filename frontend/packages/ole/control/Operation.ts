import Event from "ol/events/Event";
import Feature from "ol/Feature";
import GeoJSON from "ol/format/GeoJSON";
import MultiPolygon from "ol/geom/MultiPolygon";
import Polygon from "ol/geom/Polygon";
import oleControl from "ole/control/Control";

import type { MultiPolygon as GeoJSONMultiPolygon } from "geojson";
import type { EventsKey } from "ol/events";
import type SelectInteraction from "ol/interaction/Select";
import type { OnSignature } from "ol/Observable";
import type VectorSource from "ol/source/Vector";

interface Options {
  operation: (
    geoA: GeoJSONMultiPolygon,
    geoB: GeoJSONMultiPolygon,
  ) => Promise<GeoJSONMultiPolygon>;
  selectInteraction: SelectInteraction;
  source: VectorSource;
  type: "difference" | "intersection" | "makeValid" | "union";
}

const geoJSON = new GeoJSON();

export class OperationEvent extends Event {
  features: Feature<Polygon>[];
  constructor(type: "operation", features: Feature<Polygon>[]) {
    super(type);
    this.features = features;
  }
}

class OperationControl extends oleControl {
  on!: oleControl["on"] & OnSignature<"operation", OperationEvent, EventsKey>;

  operation: Options["operation"];

  selectInteraction: SelectInteraction;

  source: VectorSource;

  un!: oleControl["un"] & OnSignature<"operation", OperationEvent, null>;

  constructor(options: Options) {
    super({ element: document.createElement("div") });
    this.element.className = `disabled ole-operation ole-operation-${options.type}`;
    this.operation = options.operation;
    this.selectInteraction = options.selectInteraction;
    this.source = options.source;

    this.selectInteraction.on("select", this.onSelect.bind(this));
  }

  activate() {
    const geoA = this.selectInteraction.getFeatures().item(0)?.getGeometry();
    const geoB = this.selectInteraction.getFeatures().item(1)?.getGeometry();
    if (!geoA || !geoB) {
      return;
    }
    void this.operation(
      geoJSON.writeGeometryObject(geoA) as GeoJSONMultiPolygon,
      geoJSON.writeGeometryObject(geoB) as GeoJSONMultiPolygon,
    ).then((geo) => {
      const features: Feature<Polygon>[] = [];
      const geometry = geoJSON.readGeometry(geo);
      if (geometry instanceof MultiPolygon) {
        features.push(
          ...geometry.getPolygons().map((p) => {
            return new Feature(p);
          }),
        );
      } else if (geometry instanceof Polygon) {
        features.push(new Feature(geometry));
      }
      this.source.removeFeatures(
        this.selectInteraction.getFeatures().getArray(),
      );
      this.source.addFeatures(features);
      this.selectInteraction.getFeatures().clear();
      this.dispatchEvent(new OperationEvent("operation", features));
      this.selectInteraction.dispatchEvent(new Event("select"));
    });
  }

  private onSelect() {
    const features = this.selectInteraction.getFeatures();
    const geoAType = features.item(0)?.getGeometry()?.getType();
    const geoBType = features.item(1)?.getGeometry()?.getType();
    if (geoAType === "Polygon" && geoBType === "Polygon") {
      this.element.classList.remove("disabled");
    } else {
      this.element.classList.add("disabled");
    }
  }
}

export default OperationControl;
