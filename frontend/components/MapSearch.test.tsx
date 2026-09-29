/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-call */
import { unByKey } from "ol/Observable";
import { useEffect, useState } from "react";
import useMap from "react-spatial/useMap";

import Map from "./Map";
import MapSearch from "./MapSearch";

import type { Extent } from "ol/extent";

export const defaultMapSearchesSetting: {
  key: string;
  value: {
    key: string;
    url: string;
  }[];
} = {
  key: "ui.map.searches",
  value: [
    {
      key: "parcel",
      url: "https://api3.geo.admin.ch/rest/services/api/SearchServer?origins=parcel&geometryFormat=geojson&lang={lang}&limit=10&returnGeometry=true&searchText={searchText}&sr=2056&type=locations",
    },
    {
      key: "municipality",
      url: "https://api3.geo.admin.ch/rest/services/api/SearchServer?origins=gg25&geometryFormat=geojson&lang={lang}&limit=10&returnGeometry=true&searchText={searchText}&sr=2056&type=locations",
    },
    {
      key: "address",
      url: "https://api3.geo.admin.ch/rest/services/api/SearchServer?origins=address&geometryFormat=geojson&lang={lang}&limit=10&returnGeometry=true&searchText={searchText}&sr=2056&type=locations",
    },
  ],
};

const mountOptions = {
  translations: {
    map: {
      search: {
        key: {
          address: "Address:",
          coordinates: "Coordinates:",
          error: "Error",
          municipality: "Municipality:",
          noresults: "No results found",
          parcel: "Parcel:",
        },
      },
    },
  },
};

/* helper component to display current map extent */
function MapExtent() {
  const map = useMap();
  const [extent, setExtent] = useState<Extent | null>();
  const [zoom, setZoom] = useState<null | number>(null);
  const [center, setCenter] = useState<[number, number] | null | undefined>(
    null,
  );

  useEffect(() => {
    const view = map.getView();
    const updateExtent = () => {
      if (view.getCenter() === undefined) {
        return;
      }
      setExtent(view.calculateExtent());
      setZoom(view.getZoom() ?? null);
      setCenter(view.getCenter() as [number, number]);
    };
    const timeo = setTimeout(updateExtent, 100);
    const key = map.on("moveend", updateExtent);
    return () => {
      unByKey(key);
      clearTimeout(timeo);
    };
  }, [map]);

  return (
    <>
      <div className="text-red-5 absolute z-20" data-test="extent">
        {extent?.join()}
      </div>
      <div className="text-red-5 absolute z-20" data-test="zoom">
        {zoom}
      </div>
      <div className="text-red-5 absolute z-20" data-test="center">
        {center?.join()}
      </div>
    </>
  );
}

describe("MapSearch component", () => {
  beforeEach(() => {
    cy.stubSettings([defaultMapSearchesSetting]);
  });

  describe("should get datas from search api", () => {
    beforeEach(() => {
      cy.viewport(768, 512);
      cy.intercept("POST", "/graphql", (req) => {
        if (req.body.query?.includes("mutation updateUserSetting")) {
          req.alias = "updateUserSetting";
          req.reply({ data: {} });
        }
      });
      cy.intercept("*origins=address*", {
        fixture: "search/search-address-bern.json",
      });
      cy.intercept("*origins=gg25*", {
        fixture: "search/search-municipality-bern.json",
      });
      cy.intercept("*origins=parcel*", {
        fixture: "search/search-parcel-bern.json",
      });
      cy.intercept("*categories=ImmeublesCanton*", {
        fixture: "search/search-sitennech-1157.json",
      });
    });

    it("renders separate list of results", () => {
      cy.mount(
        <Map className="h-screen">
          <MapSearch />
        </Map>,
        mountOptions,
      );
      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("Bern");

      // Results should be have translated titles
      cy.get("[data-test=map-search-title-parcel]").should(
        "contain",
        "Parcel:",
      );
      cy.get("[data-test=map-search-title-address]").should(
        "contain",
        "Address:",
      );
      cy.get("[data-test=map-search-title-municipality]").should(
        "contain",
        "Municipality:",
      );

      // Results should be there
      cy.get("[data-test^=map-search-results-parcel-]").should(
        "have.length",
        10,
      );
      cy.get("[data-test^=map-search-results-address-]").should(
        "have.length",
        10,
      );
      cy.get("[data-test^=map-search-results-municipality-]").should(
        "have.length",
        8,
      );
    });

    it("zooms on address, municipality and parcel", () => {
      cy.mount(
        <Map className="h-screen">
          <MapExtent />
          <MapSearch />
        </Map>,
      );

      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("Bern");

      cy.get("[data-test=center]").should("contain", "2660000,1182000");

      cy.get("[data-test=map-search-results-address-1]").click({ force: true });
      cy.get("[data-test=center]")
        .invoke("text")
        .should("match", /2612910(\.[0-9]*)?,1219349(\.[0-9]*)?/);

      cy.get("[data-test=map-search-results-municipality-1]").click({
        force: true,
      });
      cy.get("[data-test=center]")
        .invoke("text")
        .should("match", /2596671(\.[0-9]*)?,1200393(\.[0-9]*)?/);

      cy.get("[data-test=map-search-results-parcel-1]").click({ force: true });
      cy.get("[data-test=center]")
        .invoke("text")
        .should("match", /2603416(\.[0-9]*)?,1198063(\.[0-9]*)?/);
    });

    it("zooms on coordinates", () => {
      cy.mount(
        <Map className="h-screen">
          <MapExtent />
          <MapSearch />
        </Map>,
      );

      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("2660019.11/1184616.17");

      cy.get("[data-test=center]").should("contain", "2660000,1182000");
      cy.get("[data-test=map-search-title-coordinates]").should(
        "contain",
        "Coordinates:",
      );

      cy.get("[data-test=map-search-results-coordinates-1]").click({
        force: true,
      });
      cy.get("[data-test=center]")
        .invoke("text")
        .should("match", /2660019(\.[0-9]*)?,1184616(\.[0-9]*)?/);
    });

    it("supports custom search", () => {
      cy.stubSettings([
        {
          key: "ui.map.searches",
          value: [
            {
              key: "nech",
              options: {
                category: {
                  de: "Parzelle (NeCH)",
                  fr: "Parcelle (NeCH)",
                  it: "Particella (NeCH)",
                },
                labelProperty: "label",
              },
              url: "https://sitn.ne.ch/search?categories=ImmeublesCanton&limit=10&partitionlimit=10&query={searchText}",
            },
          ],
        },
      ]);
      cy.mount(
        <Map className="h-screen">
          <MapExtent />
          <MapSearch />
        </Map>,
      );

      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("1157");

      cy.get("[data-test=center]").should("contain", "2660000,1182000");
      cy.get("[data-test=map-search-title-nech]").should(
        "contain",
        "Parzelle (NeCH):",
      );

      cy.get("[data-test=map-search-results-nech-1]").click({
        force: true,
      });
      cy.get("[data-test=center]")
        .invoke("text")
        .should("match", /2544105(\.[0-9]*)?,1207188(\.[0-9]*)?/);
    });
  });
  describe("should handle error from search apis", () => {
    beforeEach(() => {
      cy.viewport(768, 512);
      cy.intercept("POST", "/graphql", (req) => {
        if (req.body.query?.includes("mutation updateUserSetting")) {
          req.alias = "updateUserSetting";
          req.reply({ data: {} });
        }
      });
    });

    it("renders error message", () => {
      cy.intercept("*origins=address*", {
        statusCode: 500,
      });
      cy.intercept("*origins=gg25*", {
        statusCode: 500,
      });
      cy.intercept("*origins=parcel*", {
        statusCode: 500,
      });
      cy.mount(
        <Map className="h-screen">
          <MapSearch />
        </Map>,
        mountOptions,
      );
      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("Bern");

      // Results should be have translated titles
      cy.get("[data-test=map-search-error]").should("be.visible");
    });

    it("renders no results message", () => {
      cy.intercept("*origins=address*", {
        body: { features: [], type: "FeatureCollection" },
      });
      cy.intercept("*origins=gg25*", {
        body: { features: [], type: "FeatureCollection" },
      });
      cy.intercept("*origins=parcel*", {
        body: { features: [], type: "FeatureCollection" },
      });
      cy.mount(
        <Map className="h-screen">
          <MapSearch />
        </Map>,
        mountOptions,
      );
      cy.get("[data-test=map-search-input]").should("be.visible");
      cy.get("[data-test=map-search-input]").type("Bern");

      // Results should be have translated titles
      cy.get("[data-test=map-search-no-results]").should("be.visible");
    });
  });
});
