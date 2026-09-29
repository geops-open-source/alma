describe("Admin page for Users", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query Users")) {
        req.alias = "Users";
      } else if (req.body.query.includes("mutation updateUser")) {
        req.alias = "updateUser";
      } else if (req.body.query.includes("mutation createUser")) {
        req.alias = "createUser";
      }
    });
  });

  it("reads, updates and creates user", () => {
    cy.setUser("admin");
    cy.resetFixture("users");
    cy.visit("/admin/users");
    cy.wait("@Users");

    // read admin user
    cy.get("div[data-test=admin-users-List] button")
      .contains("admin@example.test")
      .click();
    cy.get("form h2").contains("admin@example.test");
    cy.get("form input[name=firstName]").should("have.value", "admin");
    cy.get("form input[name=lastName]").should("have.value", "admin");
    cy.get("form input[name=email]").should("have.value", "admin@example.test");
    cy.get("form button[name=roleName]").contains("Administration");
    cy.get("form span[role=checkbox]").should(
      "have.attr",
      "aria-checked",
      "true",
    );

    // read unauthorized user
    cy.get("div[data-test=admin-users-List] button")
      .contains("unauthorized@example.test")
      .click();
    cy.get("div[data-test=admin-users-List] button")
      .contains("unauthorized@example.test")
      .parent()
      .find("svg[data-test=LockedIcon]")
      .should("exist");
    cy.get("form input[name=firstName]").should("have.value", "unauthorized");
    cy.get("form input[name=lastName]").should("have.value", "unauthorized");
    cy.get("form input[name=email]").should(
      "have.value",
      "unauthorized@example.test",
    );
    cy.get("form button[name=roleName]").contains("-");
    cy.get("form span[role=checkbox]").should(
      "have.attr",
      "aria-checked",
      "false",
    );

    // update unauthorized user
    cy.get("form input[name=email]").type("ing");
    cy.get("form button[type=submit]").click();
    cy.wait("@updateUser").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.user.email",
        "unauthorized@example.testing",
      );
    });
    cy.get("form h2").contains("unauthorized@example.testing");
    cy.get("div[data-test=admin-users-List] button").contains(
      "unauthorized@example.testing",
    );

    // create new user
    const random = Math.random().toString(36).substring(2, 6);
    cy.get("button[data-test=admin-users-create]").click();
    cy.get("form h2").contains("Neuer User");
    cy.get("form input[name=firstName]").type("x");
    cy.get("form input[name=lastName]").type("y");
    cy.get("form input[name=email]").type(`${random}@test.com`);
    cy.get("form input[name=password]").type("asdfASDF12$%");
    cy.get("form button[type=submit]").click();
    cy.wait("@createUser").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.user.email",
        `${random}@test.com`,
      );
    });
  });

  it("shows message for missing permissions", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.visit("/admin/users");
    cy.get("[data-test=MissingPermission]").should("exist");
  });
});
