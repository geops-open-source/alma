import { FormProvider, useForm } from "react-hook-form";

import FieldArray from "./FieldArray";

function TestWrapper({ children }: { children: React.ReactNode }) {
  const methods = useForm({
    defaultValues: {
      items: [],
    },
  });

  return <FormProvider {...methods}>{children}</FormProvider>;
}

describe("FieldArray component", () => {
  it("hides field array when system setting is enabled", () => {
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("query useSetting")) {
        req.reply({
          data: {
            instanceSettings: [
              {
                key: "ui.fields.testModel.items.hidden",
                value: true,
              },
            ],
          },
        });
      } else {
        req.reply({});
      }
    });

    cy.mount(
      <TestWrapper>
        <FieldArray
          addLabel="Add Item"
          model="testModel"
          name="items"
          value={{ name: "" }}
        >
          {(index) => {
            return <div data-test={`item-${index}`}>Item {index}</div>;
          }}
        </FieldArray>
      </TestWrapper>,
    );

    cy.get('[data-test="FieldArrayAddButton"]').should("not.exist");
  });

  it("shows field array when system setting is disabled", () => {
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("query useSetting")) {
        req.reply({
          data: {
            instanceSettings: [
              {
                key: "ui.fields.testModel.items.hidden",
                value: false,
              },
            ],
          },
        });
      } else {
        req.reply({});
      }
    });

    cy.mount(
      <TestWrapper>
        <FieldArray
          addLabel="Add Item"
          model="testModel"
          name="items"
          value={{ name: "" }}
        >
          {(index) => {
            return <div data-test={`item-${index}`}>Item {index}</div>;
          }}
        </FieldArray>
      </TestWrapper>,
    );

    cy.get('[data-test="FieldArrayAddButton"]').should("exist");
  });
});
