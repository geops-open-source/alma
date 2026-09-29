describe("Admin page for field visibility", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query InstanceSettings")) {
        req.alias = "Settings";
      } else if (req.body.query.includes("mutation UpdateInstanceSetting")) {
        req.alias = "updateSetting";
      }
    });
  });

  it("reads and updates field visibility", () => {
    cy.setUser("admin");
    cy.visit("/admin/fields");
    cy.wait("@Settings");

    // read as admin user
    cy.get("td").should("contain", "mobile Stoffe");
    cy.get("input[name=fieldsFilter]").type("GENAUigkeitzeit");
    cy.get("td").should("not.contain", "mobile Stoffe");

    // Wait the checkbox is well rendered with the correct state
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(2000);

    cy.get("span[role=checkbox]")
      .eq(0)
      .invoke("attr", "aria-checked")
      .then((beforeValue) => {
        cy.get("span[role=checkbox]").eq(0).click();
        cy.wait("@updateSetting");
        cy.wait("@Settings");
        cy.get("span[role=checkbox]")
          .eq(0)
          .should("have.attr", "aria-checked", `${beforeValue !== "true"}`);
        cy.get("span[role=checkbox]").eq(0).click();
      });

    // mutate
  });

  it("shows message for missing permissions", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.visit("/admin/fields");
    cy.get("[data-test=MissingPermission]").should("exist");
  });
});
