describe("Vflz historization", () => {
  it("historizes current vflz and disables form fields for historized vflz", () => {
    cy.setUser("bearbeiten-sachdaten");
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzData")) {
        req.alias = "VflzData";
      }
    });

    cy.createVflz({ bezeichnung: "Historize Test" }).then((vflzId) => {
      cy.visit(`/vflz/${vflzId}/data`);
      cy.wait("@VflzData");
      cy.get("form[data-test=vflzDataForm] input[name=bezeichnung]").should(
        "not.be.disabled",
      );
      cy.get("[data-test=ActionMenu] button[aria-haspopup=menu]").click();
      cy.get("button[data-test=VflzActionMenu-historize]").click();

      const random = Math.random().toString(36).substring(2, 6);
      cy.get("[data-test=HistorizeDialog] input[name=message").type(random);
      cy.get("[data-test=HistorizeDialog] button[type=submit]").click();

      cy.get("[data-test=VflzLayout-sidebar-versionen] tr")
        .eq(0)
        .and("contain", random);

      cy.visit(`/vflz/${vflzId}/data`);
      cy.wait("@VflzData");
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(1000); // wait for potential async state updates
      cy.get("form[data-test=vflzDataForm]")
        .find("button[type=submit],fieldset,input,textarea")
        .each((element) => {
          // log form field names for easier debugging
          cy.wrap(element)
            .invoke("attr", "name")
            .then((name) => {
              cy.log(`Checking if field ${name} is disabled`);
            });
          cy.wrap(element).should("have.attr", "disabled");
        });
    });
  });
});
