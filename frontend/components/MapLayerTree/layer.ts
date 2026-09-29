import GML from "ol/format/GML";
import WebGLVectorLayer from "ol/layer/WebGLVector";
import { bbox as bboxStrategy } from "ol/loadingstrategy";
import VectorSource from "ol/source/Vector";
import { createDefaultStyle } from "ol/style/flat";

import { SCALE_RANGE_MAX_RESOLUTION, type SettingWFSItem } from "./tree";

import type { Extent } from "ol/extent";
import type RBush from "ol/structs/RBush";

export function createWFSLayer(item: SettingWFSItem) {
  const source = new VectorSource({
    format: new GML(),
    strategy: bboxStrategy,
    url: (extent: Extent) => {
      return `${item.url}&bbox=${extent.join(",")}&maxFeatures=10000`;
    },
  });
  source.on("featuresloadend", () => {
    setTimeout(() => {
      // @ts-expect-error we want to access the private property loadedExtentsRtree_ to fetch new data when zooming in
      const loadedExtents = source.loadedExtentsRtree_ as RBush<unknown>;
      loadedExtents.clear();
    }, 1000);
  });
  const layer = new WebGLVectorLayer({
    properties: {
      id: item.id,
      title: item.title,
      url: item.url,
    },
    source,
    style: createDefaultStyle(),
    visible: item.visible,
  });
  if (item.scaleRange) {
    layer.setMaxResolution(SCALE_RANGE_MAX_RESOLUTION[item.scaleRange]);
  }
  return layer;
}
