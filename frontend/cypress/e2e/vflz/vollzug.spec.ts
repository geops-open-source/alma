describe("Vflz Vollzug", () => {
  it("updates vollzug", () => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzData")) {
        req.alias = "VflzData";
      }
    });
    cy.resetFixture("vollzug");
    cy.setUser("bearbeiten-sachdaten");
    cy.visit(`/vflz/1/data`);
    cy.wait("@VflzData");
    cy.get("[data-test=ActionMenu] button[aria-haspopup=menu]").click();
    cy.get("button[data-test=VflzActionMenu-vollzug]").click();
    cy.get("[data-test=VollzugDialog] input[name='vollzug.0.combinedId']").type("2"); // prettier-ignore
    cy.get("[data-test=VollzugDialog] [data-test=FieldArrayAddButton]").click();
    cy.get("[data-test=VollzugDialog] input[name='vollzug.1.combinedId']").type("3"); // prettier-ignore
    cy.get("[data-test=VollzugDialog] button[name='vollzug.1.behoerde']").click(); // prettier-ignore
    cy.get("div[role=listbox] div[role=option]")
      .contains("Bar Behörde")
      .click();
    cy.get("[data-test=VollzugDialog] button[type=submit]").click();
    cy.get("[data-test=VflzLayout-header]").should("contain", "A12");
  });
});
