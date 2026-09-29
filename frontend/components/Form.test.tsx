import Form from "./Form";

describe("Form component", () => {
  it("renders form element with custom class name", () => {
    cy.mount(
      <Form className="foo" model="foo">
        Hello world
      </Form>,
    );
    cy.get("form.foo").contains("Hello world");
  });

  it("shows dialog with error message if network request fails", () => {
    cy.mount(
      <Form
        model="foo"
        onSubmit={() => {
          throw new Error("Network request failed");
        }}
      >
        <button type="submit">Submit</button>
      </Form>,
    );
    cy.get("button[type=submit]").click();
    cy.get("div[data-test=Form-networkException]").should("exist");
  });
});
