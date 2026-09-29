import olTileLayer from "ol/layer/Tile";
import olOSM from "ol/source/OSM";
import olView from "ol/View";

import Layer from "./Layer";
import Map from "./Map";

const mapStyle = { height: "100vh", width: "100vw" };

const osmTileLayer = new olTileLayer({
  source: new olOSM(),
});

const view = new olView({
  center: [0, 0],
  zoom: 2,
});

describe("Layer", () => {
  it("renders a tile layer with an OSM source", () => {
    cy.mount(
      <Map style={mapStyle} view={view}>
        <Layer layer={osmTileLayer} />
      </Map>,
    );
    cy.get(".ol-layer canvas").should("exist");
  });
});
