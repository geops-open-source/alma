import { Feature } from "ol";
import WMSGetFeatureInfo from "ol/format/WMSGetFeatureInfo";
import MultiPolygon from "ol/geom/MultiPolygon";
import Point from "ol/geom/Point";
import ImageLayer from "ol/layer/Image";
import VectorLayer from "ol/layer/Vector";
import WebGLVectorLayer from "ol/layer/WebGLVector";
import ImageWMS from "ol/source/ImageWMS";
import VectorSource from "ol/source/Vector";
import Icon from "ol/style/Icon";
import Style from "ol/style/Style";
import Toolbar from "ole/control/Toolbar";
import { useEffect, useState } from "react";
import Layer from "react-spatial/Layer";
import useMap from "react-spatial/useMap";

import InfoCircleIcon from "@/components/icons/InfoCircleIcon";
import VflzInfo from "@/components/VflzInfo";
import { layer as vflzLayer, source as vflzSource } from "@/components/VflzMap";
import { useI18n } from "@/lib/i18n";

import Widget from "./Widget";

import type Geometry from "ol/geom/Geometry";
import type MapBrowserEvent from "ol/MapBrowserEvent";

type InfosType = (
  | [string, Record<string, unknown>, Geometry]
  | [string, Record<string, unknown>]
)[];

const wmsGetFeatureInfo = new WMSGetFeatureInfo();

const featureInfoSource = new VectorSource();
const featureInfoLayer = new VectorLayer({
  source: featureInfoSource,
  style: new Style({
    image: new Icon({
      displacement: [0, 18],
      scale: 0.75,
      src: "/map/pin-info.svg",
    }),
  }),
  zIndex: 100,
});

function CopyGeometryIcon() {
  return (
    <svg
      fill="none"
      height="32"
      viewBox="0 0 32 32"
      width="32"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect fill="#0086C9" height="28" rx="14" width="28" x="2" y="1" />
      <rect height="27" rx="13.5" stroke="#0086C9" width="27" x="2.5" y="1.5" />
      <path
        d="m12 20-4.5 1.667V12L12 9.333M12 20l3.667 1.667M12 20V9.333m3.667 12.334 4-1.667v-1.5m-4 3.167V12m0 0 4-2.667V12m-4 0L12 9.333"
        stroke="#fff"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
      <path
        d="m21 15 2.5-2.5M21 15l2.5 2.5M21 15h5"
        stroke="#fff"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function CopyGeometryButton({
  className,
  geometry,
}: {
  className?: string;
  geometry?: Geometry;
}) {
  const { t } = useI18n();
  const map = useMap();
  return geometry && map.getAllLayers().includes(vflzLayer) ? (
    <button
      className={className}
      data-test="MapFeatureInfo-copy"
      onClick={() => {
        if (geometry instanceof MultiPolygon) {
          geometry.getPolygons().forEach((polygon) => {
            vflzSource.addFeature(new Feature({ geometry: polygon }));
          });
        } else {
          vflzSource.addFeature(new Feature({ geometry }));
        }
      }}
      title={t("CopyGeometryButton")}
      type="button"
    >
      <CopyGeometryIcon />
    </button>
  ) : null;
}

const supportedGeometryTypes = ["MultiPolygon", "Point", "Polygon"];

export default function MapFeatureInfo({
  active,
  setActive,
}: {
  active: boolean;
  setActive: (active: boolean) => void;
}) {
  const { t } = useI18n();
  const [infos, setInfos] = useState<InfosType>([]);
  const map = useMap();

  useEffect(() => {
    const toolbarControls = map
      .getControls()
      .getArray()
      .find((c) => {
        return c instanceof Toolbar;
      })
      ?.getControls();
    if (active) {
      toolbarControls?.forEach((control) => {
        control.once("change:active", () => {
          return setActive(false);
        });
        control.deactivate();
      });
      const onClick = (event: MapBrowserEvent) => {
        const newInfos: InfosType = [];
        featureInfoSource.clear();
        featureInfoSource.addFeature(
          new Feature({ geometry: new Point(event.coordinate) }),
        );
        map?.getAllLayers().forEach((layer) => {
          const title = layer.get("title") as string | undefined;
          if (title === undefined || layer.getVisible() === false) {
            return;
          }
          if (layer instanceof ImageLayer) {
            const resolution = map.getView().getResolution();
            const source = layer.getSource() as unknown;
            if (resolution && source instanceof ImageWMS) {
              const url = source.getFeatureInfoUrl(
                event.coordinate,
                resolution,
                "EPSG:2056",
                { INFO_FORMAT: "application/vnd.ogc.gml" },
              );
              if (url) {
                fetch(url)
                  .then((response) => {
                    return response.text();
                  })
                  .then((text) => {
                    const features = wmsGetFeatureInfo.readFeatures(text);
                    requestAnimationFrame(() => {
                      setInfos((prevInfos) => {
                        return [
                          ...prevInfos,
                          ...(features.map((feature) => {
                            return [title, feature.getProperties()];
                          }) as InfosType),
                        ];
                      });
                    });
                  })
                  .catch((error) => {
                    return console.error(error);
                  });
              }
            }
          } else if (
            layer instanceof VectorLayer ||
            layer instanceof WebGLVectorLayer
          ) {
            const renderer = layer.getRenderer();
            if (renderer && event.frameState) {
              renderer.forEachFeatureAtCoordinate(
                event.coordinate,
                event.frameState,
                10,
                (feature) => {
                  const geom = feature.getGeometry();
                  const properties = feature.getProperties();
                  if (geom && supportedGeometryTypes.includes(geom.getType())) {
                    newInfos.push([title, properties, geom as Geometry]);
                  } else {
                    newInfos.push([title, properties]);
                  }
                },
                [],
              );
            }
          }
        });
        requestAnimationFrame(() => {
          setInfos(newInfos);
        });
      };
      map?.on("click", onClick);
      return () => {
        return map?.un("click", onClick);
      };
    } else {
      featureInfoSource.clear();
      requestAnimationFrame(() => {
        setInfos([]);
      });
      if (
        toolbarControls?.getArray().every((c) => {
          return !c.active;
        })
      ) {
        toolbarControls?.item(0)?.activate();
      }
    }
  }, [active, map, setActive]);

  const infoChildren = infos
    .map(([title, { vflzId, ...properties }, geometry]) => {
      if (typeof vflzId === "number") {
        return (
          <div className="relative" key={title}>
            <VflzInfo
              className="rounded-lg p-2"
              key={title}
              vflzId={vflzId.toString()}
            />
            <CopyGeometryButton
              className="absolute top-2 right-2"
              geometry={geometry}
            />
          </div>
        );
      }
      return (
        <div
          className="divide-gray-4 divide-y overflow-hidden rounded-lg bg-white"
          key={title}
        >
          <div className="bg-gray-2 flex items-center justify-between p-2 text-xs font-semibold">
            {title}
            <CopyGeometryButton geometry={geometry} />
          </div>
          {Object.entries(properties)
            .filter(([, value]) => {
              return typeof value === "string" || typeof value === "number";
            })
            .map(([key, value]) => {
              return (
                <div className="grid grid-cols-2 p-2 text-xs" key={key}>
                  <div className="font-medium">{key}</div>
                  <div>{value as number | string}</div>
                </div>
              );
            })}
        </div>
      );
    })
    .filter(Boolean);

  return (
    <>
      {infoChildren.length === 0 ? null : (
        <Widget
          className="absolute top-4 right-18 z-20 max-h-[calc(100vh-11rem)] overflow-y-auto"
          data-test="MapFeatureInfo"
          icon={<InfoCircleIcon className="w-4" />}
          onClose={() => {
            return [featureInfoSource.clear(), setInfos([])];
          }}
          title={t("MapLayerTree.featureInfo.title")}
        >
          {infoChildren}
        </Widget>
      )}
      <Layer layer={featureInfoLayer} />
    </>
  );
}
