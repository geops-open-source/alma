import { Permission } from "@/lib/graphql";

import Layout from "./Layout";

const mountOptions = {
  router: {},
  translations: { Layout: { logout: "Abmelden" } },
};

describe("Layout component", () => {
  beforeEach(() => {
    cy.viewport(1024, 500);
  });

  it("renders content and header", () => {
    cy.stubCurrentUser();
    cy.mount(
      <Layout container title="Foo">
        Hello world
      </Layout>,
      mountOptions,
    );
    ["/", "/search", "/pools", "/workflow"].forEach((href) => {
      cy.get(`header nav ul li a[href='${href}']`).should("exist");
    });
    cy.get("main").contains("Hello world");
    cy.get(`[data-test=MissingPermission]`).should("not.exist");
    cy.get("button[data-test=Layout-userMenu]").contains("Cypress");
    cy.get("button[data-test=Layout-userMenu]").click();
    ["Deutsch", "Français", "Italiano", "Abmelden"].forEach((text) => {
      cy.get(
        "div[data-test=Layout-userMenu][role=menu] button[role=menuitem]",
      ).contains(text);
    });
  });

  it("renders content and header for viewVfl permission", () => {
    cy.stubCurrentUser({ permissions: [Permission.ViewVfl] });
    cy.mount(<Layout title="Foo">Hello world</Layout>, mountOptions);
    ["/", "/search", "/pools"].forEach((href) => {
      cy.get(`header nav ul li a[href='${href}']`).should("exist");
    });
    cy.contains("Hello world");
    cy.get(`[data-test=MissingPermission]`).should("not.exist");
  });

  it("renders header for viewProcess permission", () => {
    cy.stubCurrentUser({ permissions: [Permission.ViewProcess] });
    cy.mount(<Layout title="Foo" />, mountOptions);
    cy.get(`header nav ul li a[href='/workflow']`).should("exist");
  });

  it("renders empty header and message for missing permissions", () => {
    cy.stubCurrentUser({ permissions: [] });
    cy.mount(<Layout title="Foo" />, mountOptions);
    cy.get("main").should("not.exist");
    cy.get(`header nav ul li`).should("not.exist");
    cy.get(`header ul li`).should("not.exist");
    cy.get("main").should("not.exist");
    cy.get(`[data-test=MissingPermission]`).should("exist");
  });
});
