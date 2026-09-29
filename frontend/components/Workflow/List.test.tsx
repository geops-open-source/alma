import List from "@/components/Workflow/List";
import geschaefte from "@/cypress/fixtures/vflz/geschaefte.json";

import type { WorkflowItemFragment } from "@/lib/graphql";

const items = geschaefte.data.vflz.geschaefte.results as WorkflowItemFragment[];

describe("Workflow List Component", () => {
  it("renders", () => {
    cy.mount(<List items={items} />, { router: {} });
    cy.get("div[data-test^=Workflow-item]").should("have.length", "5");
  });

  it("toggles compact view", () => {
    cy.mount(<List asTree compactView items={items} />, { router: {} });
    cy.get("div[data-test^=Workflow-item]")
      .eq(0)
      .should("contain", "Test Workflow");
    cy.get("div[data-test^=Workflow-item]")
      .eq(0)
      .get("div[data-test=Task-Icon]")
      .should("have.class", "text-red-6");

    cy.get("div[data-test^=Workflow-item]").should("contain", "Test Note");
    cy.get("div[data-test^=Workflow-item] span[class=rounded-full]").should(
      "not.exist",
    );
  });
});
