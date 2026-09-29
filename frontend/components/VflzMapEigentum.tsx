import ImageLayer from "ol/layer/Image";
import ImageWMS from "ol/source/ImageWMS";

import VflzMap from "@/components/VflzMap";
import Layer from "@/packages/react-spatial/Layer";

import type { VflzMapFragment } from "@/lib/graphql";

const liegenschaften = new ImageLayer({
  source: new ImageWMS({
    params: { LAYERS: "Liegenschaften" },
    url: "https://wfs.geodienste.ch/av_0/deu",
  }),
});

export default function VflzMapEigentum({ vflz }: { vflz?: VflzMapFragment }) {
  return (
    <VflzMap className="mb-4 h-96" vflz={vflz}>
      <Layer layer={liegenschaften} />
    </VflzMap>
  );
}
