import Event from "ol/events/Event";
import Feature from "ol/Feature";
import GeoJSON from "ol/format/GeoJSON";
import MultiPolygon from "ol/geom/MultiPolygon";
import DrawInteraction, { type DrawEvent } from "ol/interaction/Draw";
import oleControl from "ole/control/Control";

import type { EventsKey } from "ol/events";
import type { GeoJSONLineString, GeoJSONMultiPolygon } from "ol/format/GeoJSON";
import type { Polygon } from "ol/geom";
import type SelectInteraction from "ol/interaction/Select";
import type { OnSignature } from "ol/Observable";
import type VectorSource from "ol/source/Vector";

interface Options {
  operation: (
    geo: GeoJSONMultiPolygon,
    blade: GeoJSONLineString,
  ) => Promise<GeoJSONMultiPolygon>;
  selectInteraction: SelectInteraction;
  source: VectorSource;
}

const geoJSON = new GeoJSON();

export class SplitEvent extends Event {
  features: Feature<Polygon>[];
  constructor(type: "split", features: Feature<Polygon>[]) {
    super(type);
    this.features = features;
  }
}

class SplitControl extends oleControl {
  drawInteraction: DrawInteraction;

  on!: oleControl["on"] & OnSignature<"split", SplitEvent, EventsKey>;

  operation: Options["operation"];

  selectInteraction: SelectInteraction;

  source: VectorSource;

  un!: oleControl["un"] & OnSignature<"split", SplitEvent, null>;

  constructor(options: Options) {
    super({ element: document.createElement("div") });
    this.element.className = "disabled ole-split";
    this.operation = options.operation;
    this.selectInteraction = options.selectInteraction;
    this.source = options.source;
    this.selectInteraction.on("select", this.onSelect.bind(this));
    this.drawInteraction = new DrawInteraction({
      type: "LineString",
    });
    this.drawInteraction.on("drawend", this.onDrawend.bind(this));
  }

  activate() {
    super.activate();
    this.getMap()?.addInteraction(this.drawInteraction);
    this.getMap()?.addInteraction(this.selectInteraction);
    this.selectInteraction.setActive(false);
  }

  deactivate() {
    super.deactivate();
    this.getMap()?.removeInteraction(this.drawInteraction);
    this.getMap()?.removeInteraction(this.selectInteraction);
    this.selectInteraction.setActive(true);
  }

  onDrawend(event: DrawEvent) {
    const geometry = event.feature.getGeometry();
    const features = this.selectInteraction.getFeatures().getArray();
    const geometries = features.map((f) => {
      return f.getGeometry()?.clone();
    });
    const polygons = geometries.filter((g) => {
      return g?.getType() === "Polygon";
    });
    if (polygons.length === 0 || !geometry) {
      return;
    }
    const mp = new MultiPolygon(polygons as Polygon[]);
    const geo = geoJSON.writeGeometryObject(mp) as GeoJSONMultiPolygon;
    const blade = geoJSON.writeGeometryObject(geometry) as GeoJSONLineString;
    void this.operation(geo, blade).then((result) => {
      const newFeatures: Feature<Polygon>[] = [];
      const newGeo = geoJSON.readGeometry(result);
      if (newGeo instanceof MultiPolygon) {
        newFeatures.push(
          ...newGeo.getPolygons().map((p) => {
            return new Feature(p);
          }),
        );
      }
      this.source.removeFeatures(
        this.selectInteraction.getFeatures().getArray(),
      );
      this.source.addFeatures(newFeatures);
      this.dispatchEvent(new SplitEvent("split", newFeatures));
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

export default SplitControl;
