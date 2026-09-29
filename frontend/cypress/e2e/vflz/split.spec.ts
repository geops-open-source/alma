describe("Vflz split page", () => {
  beforeEach(() => {
    cy.setUser("bearbeiten-sachdaten");
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("mutation createTeilstandort")) {
        req.alias = "createTeilstandort";
      }
    });
  });

  it("splits existing Standort", () => {
    cy.createVflz({ bezeichnung: "Split Test" }).then((vflzId) => {
      cy.visit(`/vflz/${vflzId}/split`);
      cy.get("[name=bezeichnung]").should("have.value", "Split Test");
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500); // wait 500ms to ensure map is loaded
      cy.get("#map").click(); // select map feature
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500); // wait 500ms for feature selection to be processed
      cy.contains(/^\s*Speichern\s*$/).click();
      cy.wait("@createTeilstandort");
      cy.get("[data-test=VflzSummary]").should("contain", ".01 Split Test");
    });
  });
});
