import DatePicker from "./DatePicker";

const mountOptions = {
  form: { model: "DatePicker" },
  translations: {
    DatePicker: { invalidDate: "Datum ungültig" },
    fields: { DatePicker: { foo: "Foo" } },
    zeitraum: { bisheute: "bis heute" },
  },
};

function isValid(value: string, expectedValue = value) {
  cy.get("input[name=foo]").type(value);
  cy.get("button[type='submit']").click();
  cy.get("input[name=foo]").should("have.value", expectedValue);
  cy.get("[data-test=ValidationPopover-button]").should("not.exist");
  cy.get("input[name=foo]").clear();
}

function isInvalid(value: string) {
  cy.get("input[name=foo]").type(value);
  cy.get("button[type='submit']").click();
  cy.get("input[name=foo]").should("have.value", "");

  cy.get("[data-test=ValidationPopover-button]").click();
  cy.get("[data-test=ValidationPopover-panel]").contains("Datum ungültig");
  cy.get("[data-test=ValidationPopover-button]").click();
  cy.get("input[name=foo]").clear();
}

describe("DatePicker component", () => {
  it("should type a date into the input field and verify the value", () => {
    cy.mount(<DatePicker name="foo" />, mountOptions);

    // should type a date into the input field
    cy.get('input[name="foo"]').type("28.09.2022");
    cy.get('input[name="foo"]').should("have.value", "28.09.2022");

    // should type a year into the input field
    cy.get('input[name="foo"]').clear();
    cy.get('input[name="foo"]').type("2021");
    cy.get('input[name="foo"]').should("have.value", "2021");

    // should select a date from the date picker
    cy.get("button").first().click();
    cy.get(".react-datepicker").should("be.visible");
    cy.contains(/^17$/).click(); // Select 17th
    cy.get('input[name="foo"]')
      .invoke("val")
      .then((t) => {
        return expect(t).to.match(new RegExp(/^17/));
      });
  });

  it("hasJahr: shows checkbox and switches to year", () => {
    cy.mount(<DatePicker hasJahr name="von" />, mountOptions);
    cy.get('input[name="von"]').type("28.09.2022");
    cy.get("button").click();
    cy.get('span[role="checkbox"]').click();
    cy.get('input[name="von"]').should("have.value", "2022");
  });

  it("hasHeute: shows checkbox and switches to 'bis heute'", () => {
    cy.mount(<DatePicker hasHeute name="bis" />, mountOptions);
    cy.get('input[name="bis"]').type("28.09.2022");
    cy.get("button").click();
    cy.get('span[role="checkbox"]').click();
    cy.get('input[name="bis"]').should("have.value", "bis heute");
  });

  it("validates input correctly", () => {
    cy.mount(
      <>
        <DatePicker hasHeute name="foo" />
        <button type="submit">Submit</button>
      </>,
      mountOptions,
    );
    isValid("1.1.1000", "01.01.1000");
    isValid("31.12.9999");
    isValid("2020-01-01", "01.01.2020");
    isInvalid("foo");
    isInvalid("1");
    isInvalid("12345678");
    isInvalid("32.01.2020");
    isInvalid("01.13.2020");
    isInvalid("01.01.20201");
    isInvalid("02-03-2022");
  });
});
