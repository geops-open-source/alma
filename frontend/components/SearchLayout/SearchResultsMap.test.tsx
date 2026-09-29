import SearchResultsMap from "./SearchResultsMap";

const vflz = {
  beteiligteStandort: [],
  beurteilung: {
    beurteilung: "code:103:01",
    kbsInfo: { belastet: false, color: "#00FF00" },
  },
  bezeichnung: "Test",
  combinedId: "T1",
  evaluationStatus: {
    deletedPreviously: false,
    deleteNow: false,
    publishedPreviously: false,
    publishNow: false,
    vflPublished: false,
  },
  gemeinde: { kanton: "code:15:ZH" },
  ort: "TestOrt",
  vflzId: "1",
};

const zentroid = {
  features: [
    {
      geometry: { coordinates: [2588478, 1222978], type: "Point" },
      properties: { color: "#00FF00", vflzId: 1 },
      type: "Feature",
    },
  ],
  type: "FeatureCollection",
};

describe("SearchResultsMap component", () => {
  beforeEach(() => {
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("query searchMap")) {
        req.reply({ data: { search: { geo: { zentroid } } } });
        req.alias = "searchMapQuery";
      } else if (req.body.query?.includes("query VflzInfo")) {
        req.reply({ data: { vflz } });
      }
    });
    cy.intercept("https://wms.geo.admin.ch/**", { forceNetworkError: true });
  });

  it("zooms to single search result and opens overlay on click", () => {
    cy.mount(<SearchResultsMap filters={[]} query="" />, { router: {} });
    cy.wait("@searchMapQuery");
    cy.wait(2000); // wait for map to render
    cy.get(".ol-viewport").then((viewport) => {
      const { height, width } = viewport[0].getBoundingClientRect();
      cy.get(".ol-viewport").click(width / 2, height / 2 - 10, { force: true });
      cy.get("[data-test=VflzSummary]").contains("T1 Test");
    });
  });
});
