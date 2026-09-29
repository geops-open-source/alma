describe("Admin page for translations", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query translations")) {
        req.alias = "queryTranslations";
      } else if (req.body.query.includes("mutation UpdateTranslation")) {
        req.alias = "updateTranslation";
      }
    });
  });

  it("filters and updates translations", () => {
    cy.setUser("admin");
    cy.visit("/admin/translations");
    cy.wait("@queryTranslations");

    cy.get("input[name=key-filter]").type("admin.translations.title");
    cy.get("tbody tr").last().contains("admin.translations.title").click();

    const random = Math.random().toString(36).substring(2, 6);
    cy.get("input[name=de]").clear();
    cy.get("input[name=de]").type(random);
    cy.get("button[type=submit]").click();
    cy.wait("@updateTranslation");
    cy.get("tbody tr").last().contains(random);
    cy.get("main header nav a[href='/admin/translations']").contains(random);
  });

  it("shows message for missing permissions", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.visit("/admin/translations");
    cy.get("[data-test=MissingPermission]").should("exist");
  });
});
