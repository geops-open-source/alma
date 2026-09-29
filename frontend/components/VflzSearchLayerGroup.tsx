import GroupLayer from "ol/layer/Group";
import VectorLayer from "ol/layer/Vector";
import { useEffect, useState } from "react";
import Layer from "react-spatial/Layer";
import useMap from "react-spatial/useMap";

import VflzSearchLayer, { vflzSearchLayer } from "@/components/VflzSearchLayer";
import { useI18n } from "@/lib/i18n";

const published = new VectorLayer({
  properties: { id: "vflzSearchLayerGroup.published" },
});
const notPublished = new VectorLayer({
  properties: { id: "vflzSearchLayerGroup.notPublished" },
});

const groupLayer = new GroupLayer({
  layers: [notPublished, published, vflzSearchLayer],
  properties: {
    collapsed: false,
    hiddenLayers: ["vflzSearchLayer"],
    id: "vflzSearchLayerGroup",
    readonly: true,
  },
});

export default function VflzSearchLayerGroup(props: {
  featureInfoActive: boolean;
  ignoreVflzId?: string;
}) {
  const { activeLocale, t } = useI18n();
  const map = useMap();
  const [query, setQuery] = useState("");

  useEffect(() => {
    groupLayer.set("title", t("VflzSearchLayer.title.other"));
    published.set("title", t("published"));
    notPublished.set("title", t("notPublished"));
  }, [activeLocale, t]);

  useEffect(() => {
    const onChangeVisible = () => {
      const publishedVisible = published.getVisible();
      const notPublishedVisible = notPublished.getVisible();
      let searchLayerVisible = true;
      if (publishedVisible && !notPublishedVisible) {
        setQuery("Aktuellste-Publikation-im-KbS = TRUE");
      } else if (!publishedVisible && notPublishedVisible) {
        setQuery("Aktuellste-Publikation-im-KbS = FALSE");
      } else if (!publishedVisible && !notPublishedVisible) {
        searchLayerVisible = false;
      } else {
        setQuery("");
      }
      vflzSearchLayer.setVisible(searchLayerVisible);
    };

    published.on("change:visible", onChangeVisible);
    notPublished.on("change:visible", onChangeVisible);

    map.removeLayer(vflzSearchLayer);

    return () => {
      published.un("change:visible", onChangeVisible);
      notPublished.un("change:visible", onChangeVisible);
    };
  }, [map]);

  return (
    <>
      <VflzSearchLayer advanced query={query} {...props} />
      <Layer layer={groupLayer} />
    </>
  );
}
