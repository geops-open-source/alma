import { register as registerCypressGrep } from "@cypress/grep";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      stubSettings: (
        instanceSettings: { key: string; value: unknown }[],
      ) => void;
      triggerGarbageCollection: () => void;
    }
  }
}

registerCypressGrep();

Cypress.Commands.add("stubSettings", (instanceSettings) => {
  cy.intercept("POST", "/graphql", (req) => {
    if (req.body.query?.includes("query useSetting")) {
      req.reply({ data: { instanceSettings } });
    }
  });
});

Cypress.Commands.add("triggerGarbageCollection", () => {
  cy.window({ log: false }).then((win) => {
    // Check if the V8 flag successfully exposed the gc function
    if (typeof win.gc === "function") {
      cy.log("🧹 Running manual browser Garbage Collection...");
      win.gc();
    } else if (typeof globalThis.gc === "function") {
      cy.log("🧹 Running Node host Garbage Collection...");
      globalThis.gc();
    } else {
      cy.log(
        "⚠️ GC function not found. Verify --expose-gc flag in cypress.config.js",
      );
    }
  });
});

export {};
