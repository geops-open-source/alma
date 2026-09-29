import Listbox, { useBooleanOptions } from "./Listbox";

function BooleanListbox() {
  const options = useBooleanOptions();
  return <Listbox name="foo" options={options} />;
}

describe("Listbox component", () => {
  it("renders listbox with boolean options", () => {
    cy.mount(<BooleanListbox />, {
      form: {},
      translations: { boolean: { false: "Nein", true: "Ja" } },
    });
    cy.get("button[aria-haspopup=listbox]").click();
    cy.get("div[role=listbox] div[role=option]").should("have.length", 3);
    cy.get("div[role=listbox] [role=option]").eq(0).should("contain", "-");
    cy.get("div[role=listbox] [role=option]").eq(1).should("contain", "Ja");
    cy.get("div[role=listbox] [role=option]").eq(2).should("contain", "Nein");
  });
});
