import Feature from "ol/Feature";
import Polygon from "ol/geom/Polygon";
import ImageLayer from "ol/layer/Image";
import VectorLayer from "ol/layer/Vector";
import WebGLVectorLayer from "ol/layer/WebGLVector";
import ImageWMS from "ol/source/ImageWMS";
import VectorSource from "ol/source/Vector";
import { createDefaultStyle } from "ol/style/flat";
import Layer from "react-spatial/Layer";

import Map from "@/components/Map";
import { layer as vflzLayer, source as vflzSource } from "@/components/VflzMap";

import MapFeatureInfo from "./MapFeatureInfo";

const geometry = new Polygon([
  [
    [2485000, 1064000],
    [2835000, 1064000],
    [2835000, 1300000],
    [2485000, 1300000],
    [2485000, 1064000],
  ],
]);

const vectorLayer = new VectorLayer({
  properties: { title: "Vector Layer" },
  source: new VectorSource({
    features: [new Feature({ geometry, name: "Vector Example" })],
  }),
});

const webglVectorLayer = new WebGLVectorLayer({
  properties: { title: "WebGL Vector Layer" },
  source: new VectorSource({
    features: [new Feature({ geometry, name: "WebGL Vector Example" })],
  }),
  style: createDefaultStyle(),
});

const wmsLayer = new ImageLayer({
  properties: { title: "WMS Layer" },
  source: new ImageWMS({ url: "https://test.com/wms" }),
});

const wmsGeoAdminLayer = new ImageLayer({
  properties: { title: "WMS GeoAdmin Layer" },
  source: new ImageWMS({ url: "https://wms.geo.admin.ch/" }),
});

describe("MapFeatureInfo component", () => {
  beforeEach(() => {
    cy.intercept("https://wms.geo.admin.ch/?REQUEST=GetMap**", {
      forceNetworkError: true,
    });
  });

  it("shows feature info for vector and WMS layer", () => {
    cy.intercept("GET", "https://test.com/wms**", {
      fixture: "MapLayerTree/MapFeatureInfo/feature-info.gml",
    });
    cy.intercept("GET", "https://wms.geo.admin.ch/**", {
      fixture: "MapLayerTree/MapFeatureInfo/wms-geo-admin-feature-info.gml",
    });
    cy.mount(
      <Map className="h-screen">
        <MapFeatureInfo
          active
          setActive={() => {
            return null;
          }}
        />
        <Layer layer={vectorLayer} />
        <Layer layer={webglVectorLayer} />
        <Layer layer={wmsGeoAdminLayer} />
        <Layer layer={wmsLayer} />
      </Map>,
    );
    cy.wait(1000); // wait for OpenLayers to render
    cy.get("#map").click(250, 250);
    cy.get("div[data-test=MapFeatureInfo]").should("exist");
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "Vector Layer");
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "Vector Example");
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "WebGL Vector Layer"); // prettier-ignore
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "WebGL Vector Example"); // prettier-ignore
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "WMS Layer");
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "WMS Example");
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "WMS GeoAdmin Layer"); // prettier-ignore
    cy.get("div[data-test=MapFeatureInfo]").should("contain", "7025667");
  });

  it("copies feature to vflz layer", () => {
    cy.mount(
      <Map className="h-screen">
        <MapFeatureInfo
          active
          setActive={() => {
            return null;
          }}
        />
        <Layer layer={vectorLayer} />
        <Layer layer={vflzLayer} />
      </Map>,
    );
    cy.then(() => {
      return expect(vflzSource.getFeatures().length).to.equal(0);
    });
    cy.wait(1000); // wait for OpenLayers to render
    cy.get("#map").click(250, 250);
    cy.get("button[data-test=MapFeatureInfo-copy]").click();
    cy.then(() => {
      return expect(vflzSource.getFeatures().length).to.equal(1);
    });
  });
});
