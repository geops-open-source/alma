describe("Dashboard", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("mutation createSavedSearch")) {
        req.alias = "createSavedSearch";
      }
    });
  });

  it("adds and removes saved searches", () => {
    const name = Math.random().toString(36).substring(2, 6);
    cy.setUser("bearbeiten-sachdaten");
    cy.visit("/");

    // make sure default saved searches exist without delete button
    cy.get("div[data-test=savedSearchCard]").should("have.length", 2);
    cy.get("div[data-test=savedSearchCard-deleteButton]").should("not.exist");

    // create a new saved search
    cy.visit("/search/advanced");
    cy.get("button[data-test=search-savedSearchDialog]").click();
    cy.get("div[role=dialog]").should("exist");
    cy.get("div[role=dialog] input[type=text][name=name]").type(name);
    cy.get("label").contains("Ergebnisse auf dem Dashboard anzeigen").click();
    cy.get("div[role=dialog] button[type=submit]").click();
    cy.wait("@createSavedSearch");

    cy.visit("/");
    cy.contains("div[data-test=savedSearchCard]", name)
      .find("button[data-test=savedSearchCard-deleteButton]")
      .click();
    cy.contains("div[data-test=savedSearchCard]", name).should("not.exist");

    // default saved searches should still exist
    cy.get("div[data-test=savedSearchCard]").should("have.length", 2);
    cy.get("div[data-test=savedSearchCard-deleteButton]").should("not.exist");
  });

  it("shows message for missing permissions", () => {
    cy.setUser("unauthorized");
    cy.visit("/");
    cy.get("[data-test=MissingPermission]").should("exist");
  });
});
