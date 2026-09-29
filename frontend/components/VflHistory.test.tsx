import { Combobox } from "@headlessui/react";

import VflHistory from "./VflHistory";

describe("VflHistory component", () => {
  beforeEach(() => {
    cy.stubCurrentUser({
      settings: [
        {
          key: "vflHistory",
          value: Array.from({ length: 31 }, (_, i) => {
            return (i + 1).toString();
          }),
        },
      ],
    });
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("query vflHistory")) {
        req.reply({
          data: {
            vflzByVflIds: (req.body.variables.vflIds as string[]).map((id) => {
              return {
                bezeichnung: `Test ${id}`,
                combinedId: id,
                evaluationStatus: {
                  deletedPreviously: false,
                  deleteNow: false,
                  publishedPreviously: false,
                  publishNow: false,
                },
                vflzId: id,
              };
            }),
          },
        });
      }
    });
  });

  it("renders list with 30 items by default", () => {
    cy.mount(<VflHistory />, { router: {} });
    cy.get("div[data-test=VflzItem]").should("have.length", 30);
    cy.get("div[data-test=VflzItem]").eq(0).contains("Test 1");
    cy.get("div[data-test=VflzItem]").eq(29).contains("Test 30");
  });

  it("renders combobox options, limits to max and skips first item on Vflz page", () => {
    cy.mount(
      <Combobox>
        <VflHistory isCombobox max={10} />
      </Combobox>,
      { router: { pathname: "/vflz/[vflzId]" } },
    );
    cy.get("div[data-test=VflzItem][role=option]").should("have.length", 10);
    cy.get("div[data-test=VflzItem][role=option]").eq(0).contains("Test 2");
    cy.get("div[data-test=VflzItem][role=option]").eq(9).contains("Test 11");
  });
});
