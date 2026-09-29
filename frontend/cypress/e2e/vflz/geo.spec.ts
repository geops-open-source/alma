/* eslint-disable cypress/no-unnecessary-waiting */
describe("Vflz geo page", () => {
  before(() => {
    cy.resetFixture("evaluation");
  });

  beforeEach(() => {
    cy.setUser("bearbeiten-sachdaten");
    cy.updateUserSetting("bearbeiten-sachdaten", "mapLayerTree.editor", [
      {
        collapsed: false,
        id: "vflzSearchLayerGroup",
        items: [
          {
            id: "vflzSearchLayerGroup.notPublished",
            type: "Layer",
            version: 1,
            visible: false,
          },
          {
            id: "vflzSearchLayerGroup.published",
            type: "Layer",
            version: 1,
            visible: false,
          },
          {
            id: "vflzSearchLayer",
            type: "Layer",
            version: 1,
            visible: false,
          },
        ],
        title: " Standorte",
        type: "Group",
        version: 1,
        visible: false,
      },
    ]);
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzGeo")) {
        req.alias = "VflzGeo";
      }
    });
    // reject all requests for baselayer tiles to avoid cross-origin issues with pixelmatchFixture
    cy.intercept("https://wms.geo.admin.ch/**", { forceNetworkError: true });
  });

  it("renders polygon for Ablagerungsstandort", () => {
    cy.visit("/vflz/1/geo");
    cy.wait("@VflzGeo");
    cy.get(".ol-layer:last canvas").pixelmatchFixture(
      "vflz/geo/ablagerungsstandort",
    );
    for (let i = 0; i < 5; i++) {
      cy.wait(2000); // wait for the map to render
      cy.get("button.ol-zoom-out").click();
    }
    cy.wait(5000); // wait for the map to render
    cy.get(".ol-layer:last canvas").pixelmatchFixture(
      "vflz/geo/ablagerungsstandort-zoomed-out",
    );
  });

  it("renders point for Betriebsstandort", () => {
    cy.visit("/vflz/2/geo");
    cy.wait("@VflzGeo");
    cy.wait(5000); // wait for the map to render
    cy.get(".ol-layer:last canvas").pixelmatchFixture(
      "vflz/geo/betriebsstandort",
    );
  });
});
