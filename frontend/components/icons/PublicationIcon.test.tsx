import PublicationIcon from "./PublicationIcon";

const status = {
  deletedPreviously: false,
  deleteNow: false,
  publishedPreviously: false,
  publishNow: false,
};

describe("PublicationIcon component", () => {
  it("renders opened and dark blue icon for: diese Version wurde publiziert", () => {
    cy.mount(
      <PublicationIcon
        vflz={{ evaluationStatus: { ...status, publishNow: true } }}
      />,
    );
    cy.get("svg path").should("have.class", "fill-blue-6");
    cy.get("svg").should("have.attr", "data-test", "PublicationIcon-open");
  });

  it("renders opened, light blue icon for: eine vorherige Version wurde publiziert", () => {
    cy.mount(
      <PublicationIcon
        vflz={{ evaluationStatus: { ...status, publishedPreviously: true } }}
      />,
    );
    cy.get("svg path").should("have.class", "fill-blue-4");
    cy.get("svg").should("have.attr", "data-test", "PublicationIcon-open");
  });

  it("renders closed, dark blue icon for: diese Version wurde gelöscht", () => {
    cy.mount(
      <PublicationIcon
        vflz={{ evaluationStatus: { ...status, deleteNow: true } }}
      />,
    );
    cy.get("svg path").should("have.class", "fill-blue-6");
    cy.get("svg").should("have.attr", "data-test", "PublicationIcon");
  });

  it("renders closed, light blue icon for: eine vorherige Version wurde gelöscht", () => {
    cy.mount(
      <PublicationIcon
        vflz={{ evaluationStatus: { ...status, deletedPreviously: true } }}
      />,
    );
    cy.get("svg path").should("have.class", "fill-blue-4");
    cy.get("svg").should("have.attr", "data-test", "PublicationIcon");
  });
});
