describe("Admin page for code lists", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query adminCodeLists")) {
        req.alias = "CodeLists";
      } else if (req.body.query.includes("query adminCodeList")) {
        req.alias = "CodeList";
      } else if (req.body.query.includes("mutation updateCodeList(")) {
        req.alias = "updateCodeList";
      } else if (req.body.query.includes("mutation createCodeListEntry")) {
        req.alias = "CreateCodeListEntry";
      } else if (req.body.query.includes("mutation updateCodeListEntry")) {
        req.alias = "UpdateCodeListEntry";
      }
    });
  });

  it("creates and updates code list entry", () => {
    const randomString = Math.random().toString(36).substring(2, 6);

    cy.setUser("admin");
    cy.visit("/admin/codelists");
    cy.wait("@CodeLists");

    cy.get("button").contains("Behörden Kürzel").click();
    cy.wait("@CodeList");

    cy.get("button").contains("Code hinzufügen").click();
    cy.get("input[name=code]").should("not.have.attr", "disabled");
    cy.get("input[name=code]").type(randomString, { force: true });
    cy.get("input[name='bezeichnung.de']").type(`De ${randomString}`);
    cy.get("input[name='bezeichnung.fr']").type(`Fr ${randomString}`);
    cy.get("input[name='bezeichnung.it']").type(`It ${randomString}`);
    cy.get("div[role=dialog] button[type=submit]").click();
    cy.wait("@CreateCodeListEntry");
    cy.get("table[data-test=admin-codelist-entries]")
      .contains(`${randomString}`)
      .should("exist");

    cy.get("table[data-test=admin-codelist-entries] tr")
      .contains(`${randomString}`)
      .click();
    cy.get("div[role=dialog] input[name='bezeichnung.de']").type("up");
    cy.get("div[role=dialog] input[name='bezeichnung.fr']").type("up");
    cy.get("div[role=dialog] input[name='bezeichnung.it']").type("up");
    cy.get("div[role=dialog] button[type=submit]").click();
    cy.wait("@UpdateCodeListEntry");
    cy.wait("@CodeList");

    cy.get("table[data-test=admin-codelist-entries]")
      .contains(`De ${randomString}up`)
      .should("exist");
  });

  it("shows message for missing permissions", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.visit("/admin/codelists");
    cy.get("[data-test=MissingPermission]").should("exist");
  });
});
