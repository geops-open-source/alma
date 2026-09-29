import { Menu, MenuItem } from "./Menu";

describe("Menu component", () => {
  it("renders menu title", () => {
    cy.mount(<Menu title="Foo" />);
    cy.get("button[type=button]").contains("Foo");
  });

  it("renders button and link menu items with custom class name", () => {
    cy.mount(
      <Menu title="Foo">
        <MenuItem className="foo">Bar</MenuItem>
        <MenuItem className="foo" href="baz">
          Baz
        </MenuItem>
      </Menu>,
    );
    cy.get("div[role=menu] button[role=menuitem].foo").should("not.exist");
    cy.get("div[role=menu] a[href=baz][role=menuitem].foo").should("not.exist");
    cy.get("button[aria-haspopup=menu]").click();
    cy.get("div[role=menu] button[role=menuitem].foo").contains("Bar");
    cy.get("div[role=menu] a[href=baz][role=menuitem].foo").contains("Baz");
  });

  it("toggles menu", () => {
    cy.mount(
      <Menu title="Foo">
        <MenuItem>Bar</MenuItem>
      </Menu>,
    );
    cy.get("div[role=menu] button[role=menuitem]").should("not.exist");
    cy.get("button[aria-haspopup=menu]").click();
    cy.get("div[role=menu] button[role=menuitem]").contains("Bar");
    cy.get("button[aria-haspopup=menu]").click();
    cy.get("div[role=menu] button[role=menuitem]").should("not.exist");
  });

  it("calls menu item onClick handler", () => {
    cy.mount(
      <Menu title="Foo">
        <MenuItem onClick={cy.stub().as("onClick")}>Bar</MenuItem>
      </Menu>,
    );
    cy.get("button[aria-haspopup=menu]").click();
    cy.get("div[role=menu] button[role=menuitem]").click();
    cy.get("@onClick").should("have.been.called");
    cy.get("div[role=menu] button[role=menuitem]").should("not.exist");
  });
});
