describe("User settings page", () => {
  it("updates user password", () => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("mutation updateUserPassword")) {
        req.alias = "updateUserPassword";
      }
    });
    cy.setUser("lesen-sachdaten");
    cy.visit("/user");
    cy.get("input[name=password]").type("Secure1234$%");
    cy.get("input[name=passwordRepeat]").type("Secure1234$%");
    cy.get("button[type=submit]").click();
    cy.wait("@updateUserPassword");
    cy.get("input[name=password]").should("have.value", "");
    cy.get("input[name=passwordRepeat]").should("have.value", "");
    cy.get("button[type=submit]").should("be.disabled");
  });
});
