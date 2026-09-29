import Button from "./Button";

describe("Button component", () => {
  it("renders button by default", () => {
    cy.mount(<Button>Hello world</Button>);
    cy.get("button[type=button]").contains("Hello world");
  });

  it("renders link for href", () => {
    cy.mount(<Button href="foo">Bar</Button>);
    cy.get("a[href=foo]").contains("Bar");
  });

  it("renders custom class name", () => {
    cy.mount(<Button className="foo">Bar</Button>);
    cy.get("button.foo");
  });
});
