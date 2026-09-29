describe("Workflow page", () => {
  it("hides menu item for missing permission", () => {
    cy.setUser("lesen-sachdaten");
    cy.visit("/");
    cy.get("header nav a[href='/']").should("exist");
    cy.get("header nav a[href='/workflow']").should("not.exist");
  });

  it("shows read-only tasks", () => {
    cy.setUser("lesen-geschaefte");
    cy.visit("/workflow");
    cy.get("header nav a[href='/workflow']").should("exist");
    cy.get("div[data-test^=Workflow-item]").should("exist");
    cy.get("form[data-test=Workflow-taskForm]")
      .find("button,fieldset,input,textarea")
      .should("be.disabled");
    cy.get("form[data-test=Workflow-taskForm] button[type=submit]").should(
      "not.exist",
    );
  });

  it("shows editable tasks", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.visit("/workflow");
    cy.get("div[data-test^=Workflow-item]").should("exist");
    cy.get("form[data-test=Workflow-taskForm]")
      .find("button,fieldset,input,textarea")
      .should("be.enabled");
    cy.get("form[data-test=Workflow-taskForm] button[type=submit]").should(
      "exist",
    );
  });

  it("filters tasks by status, type, due date, and title", () => {
    cy.setUser("bearbeiten-geschaefte");
    cy.updateUserSetting("bearbeiten-geschaefte", "workflow.filter", "");
    cy.visit("/workflow");

    cy.get("#filter input[name=status]").type("{selectall}Offen{enter}{esc}");
    cy.get("#filter input[name=taskTyp]").type(
      "{selectall}Aufgabe{enter}{esc}",
    );
    cy.get("#filter input[name=faelligkeit]").type(
      "{selectall}überfällig{enter}{esc}",
    );
    cy.get("#filter input[name=titel]").type("{selectall}Test");
    cy.get("#filter button[type=submit]").click();

    cy.get("div[data-test^=Workflow-item]").should("have.length", 1);
    cy.get("div[data-test=Workflow-item-AUFGABE]").contains("Test Task");
  });
});
