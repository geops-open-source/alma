import Form from "./Form";
import ZeitraumFields from "./ZeitraumFields";

describe("ZeitraumFields component", () => {
  it("validates zeitraum", () => {
    cy.mount(
      <Form model="Ablagerung">
        <ZeitraumFields name="foo" />
        <button type="submit">Submit</button>
      </Form>,
    );
    cy.get("input[name='foo.von']").type("2022");
    cy.get("input[name='foo.bis']").type("2021");
    cy.get("button[type=submit]").click();
    cy.get("[data-test=ValidationPopover-button]").should("have.length", 2);
    cy.get("input[name='foo.bis']").clear();
    cy.get("input[name='foo.bis']").type("2023");
    cy.get("button[type=submit]").click();
    cy.get("[data-test=ValidationPopover-button]").should("not.exist");
  });
});
