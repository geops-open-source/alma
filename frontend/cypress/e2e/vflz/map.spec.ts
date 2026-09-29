/* eslint-disable cypress/no-unnecessary-waiting */
describe("Vflz map page", () => {
  before(() => {
    cy.resetFixture("evaluation");
  });

  beforeEach(() => {
    cy.setUser("lesen-sachdaten");
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzMap")) {
        req.alias = "VflzMap";
      }
    });
    // reject all requests for baselayer tiles to avoid cross-origin issues with pixelmatchFixture
    cy.intercept("https://wms.geo.admin.ch/**", { forceNetworkError: true });
  });

  it("renders polygon for Ablagerungsstandort", () => {
    cy.visit("/vflz/1/map?baselayer=map-color");
    cy.wait("@VflzMap");
    cy.wait(5000); // wait for the map to render
    cy.get(".ol-layer:last canvas").pixelmatchFixture(
      "vflz/map/ablagerungsstandort",
    );
    cy.get(".ol-scale-bar").should("exist");
  });

  it("renders point for Betriebsstandort", () => {
    cy.visit("/vflz/2/map?baselayer=map-color");
    cy.wait("@VflzMap");
    cy.wait(5000); // wait for the map to render
    cy.get(".ol-layer:last canvas").pixelmatchFixture(
      "vflz/map/betriebsstandort",
    );
    cy.get(".ol-scale-bar").should("exist");
  });
});
