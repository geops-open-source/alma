import { useEffect, useState } from "react";
import useMap from "react-spatial/useMap";

import Map from "./Map";
import MapSearch from "./MapSearch";
import { defaultMapSearchesSetting } from "./MapSearch.test";

import type { Extent } from "ol/extent";

const mountOptions = {
  translations: {
    Map: { BaseLayer: { aerial: "Luftbild" } },
  },
};

/* helper component to display current map extent */
function MapExtent() {
  const map = useMap();
  const [extent, setExtent] = useState<Extent | null>();

  useEffect(() => {
    const view = map.getView();
    const updateExtent = () => {
      if (view.getCenter() === undefined) {
        return;
      }
      setExtent(view.calculateExtent());
    };
    setTimeout(updateExtent, 100);
    view.on("change:resolution", updateExtent);
    return () => {
      return view.un("change:resolution", updateExtent);
    };
  }, [map]);

  return (
    <div className="text-red-5 absolute z-20" data-test="extent">
      {extent?.join()}
    </div>
  );
}

describe("Map component", () => {
  beforeEach(() => {
    cy.clearAllLocalStorage();
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("mutation updateUserSetting")) {
        req.alias = "updateUserSetting";
        req.reply({ data: {} });
      }
    });
  });

  it("renders small map with small controls and base layer switcher", () => {
    cy.mount(
      <Map className="h-screen">
        <MapExtent />
      </Map>,
    );
    cy.get(".ol-zoom-in, .ol-zoom-out").should("be.visible");
    cy.get(".ol-zoomslider").should("be.hidden");
    cy.get("button.alma-map-base-layer-toggle")
      .find("img")
      .should("have.attr", "src", "/map/baselayer-aerial.png");
    cy.get("button.alma-map-base-layer-toggle").click();
    cy.get(".alma-map-base-layer span").should("be.hidden");
    cy.get("button[data-test=BaseLayer-map-color]").click();
    cy.get("button.alma-map-base-layer-toggle")
      .find("img")
      .should("have.attr", "src", "/map/baselayer-aerial.png");
    cy.get(".ol-zoom-in").click();
    cy.contains("[data-test=extent]", "2601000,1123000,2719000,1241000");
    cy.get(".ol-zoom-extent").click();
    cy.contains("[data-test=extent]", "2542000,1064000,2778000,1300000");
  });

  it("renders large map with large controls and custom zoom extent", () => {
    cy.viewport(768, 512);
    cy.mount(
      <Map
        className="h-screen"
        zoomExtent={[2485000, 1007000, 2486000, 1008000]}
      >
        <MapExtent />
      </Map>,
      mountOptions,
    );
    cy.get("button.alma-map-base-layer-toggle").click();
    cy.get(".alma-map-base-layer span").should("be.visible");
    cy.get(".ol-zoomslider").should("be.visible");
    cy.get(".ol-zoom-in").click();
    cy.contains("[data-test=extent]", "2485375,1064250,2486125,1064750");
    cy.get(".ol-zoom-extent").click();
    cy.contains("[data-test=extent]", "2485000,1064000,2486500,1065000");
  });

  it("supports custom base layers and max extent", () => {
    cy.stubSettings([
      { key: "ui.map.baseLayers", value: [{ key: "foo" }] },
      { key: "ui.map.maxExtent", value: [2485000, 1007000, 2486000, 1008000] },
    ]);
    cy.mount(
      <Map className="h-screen">
        <MapExtent />
      </Map>,
    );
    cy.contains("[data-test=extent]", "2485000,1007000,2486000,1008000");
    cy.get("button.alma-map-base-layer-toggle")
      .find("img")
      .should("have.attr", "src", "/map/baselayer-foo.png");
  });

  it("renders small map with map search", () => {
    cy.stubSettings([defaultMapSearchesSetting]);
    cy.intercept("*origins=address*", {
      fixture: "search/search-address-bern.json",
    });
    cy.intercept("*origins=gg25*", {
      fixture: "search/search-municipality-bern.json",
    });
    cy.intercept("*origins=parcel*", {
      fixture: "search/search-parcel-bern.json",
    });
    cy.mount(
      <Map>
        <MapSearch />
      </Map>,
    );
    cy.get("[data-test=map-search-input]").should("be.visible");
    cy.get("[data-test=map-search-input]").type("Bern");
    cy.get("[data-test=map-search-title-parcel]").should("contain", "Parcel:");
    cy.get("[data-test=map-search-title-address]").should(
      "contain",
      "Address:",
    );
    cy.get("[data-test=map-search-title-municipality]").should(
      "contain",
      "Municipality:",
    );
  });
});
