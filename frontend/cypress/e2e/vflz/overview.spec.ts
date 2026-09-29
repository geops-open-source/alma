import ablagerungsstandort from "../../fixtures/vflz/data/ablagerungsstandort.json";

describe("Vflz overview page", () => {
  beforeEach(() => {
    cy.resetFixture("ablagerungsstandort");
    cy.resetFixture("beteiligte");
    cy.resetFixture("evaluation");
    cy.resetFixture("subjekte");
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzOverview")) {
        req.alias = "VflzOverview";
      }
    });
    // reject all requests for baselayer tiles to avoid cross-origin issues with pixelmatchFixture
    cy.intercept("https://wms.geo.admin.ch/**", { forceNetworkError: true });
  });

  it("renders overview for Ablagerungsstandort", () => {
    cy.setUser("lesen-sachdaten");
    cy.visit("/vflz/1");
    cy.wait("@VflzOverview");
    cy.get("[data-test=VflzOverview] [data-test=VflzSummary]").contains(
      ablagerungsstandort.bezeichnung,
    );
    cy.get("[data-test=VflzOverview-beurteilung]").contains(
      "Definitiver Katastereintrag rechtskräftig",
    );
    cy.get("[data-test=VflzOverview-beurteilung]").contains(
      "Überwachung läuft",
    );
    cy.get("[data-test=VflzSachbearbeiter-beteiligter]").eq(0).contains("Bearbeiten Sachdaten"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-mit-eigentum]").eq(0).contains("Foo"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-mit-eigentum]").eq(0).contains("1"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-mit-eigentum]").eq(0).contains("4"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-ohne-eigentum]").eq(0).contains("2"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-ohne-eigentum]").eq(0).contains("Bar"); // prettier-ignore
    cy.get("[data-test=VflzOverview-parzellen-ohne-eigentum]").eq(0).contains("3"); // prettier-ignore
    cy.get(".ol-layer:last canvas").pixelmatchFixture("vflz/overview-map");

    cy.get("[data-test=VflzOverview] dl").should("not.contain", "Offene Tasks");
  });

  it("renders Tasks for users with permission", () => {
    cy.setUser("lesen-geschaefte");
    cy.visit("/vflz/1");
    cy.wait("@VflzOverview");
    cy.get("[data-test=VflzOverview] dl").should("contain", "Offene Tasks");
  });
});
