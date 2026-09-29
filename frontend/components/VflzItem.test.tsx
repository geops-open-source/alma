import VflzItem from "./VflzItem";

const vflz = {
  bezeichnung: "TestVflz",
  combinedId: "123",
  evaluationStatus: {
    deletedPreviously: false,
    deleteNow: false,
    publishedPreviously: false,
    publishNow: false,
  },
  vflzId: "456",
};

describe("VflzItem component", () => {
  it("renders VflzItem component", () => {
    cy.mount(<VflzItem vflz={vflz} />, { router: {} });
    cy.contains("123");
    cy.contains("TestVflz");
    cy.get("a[href^='/vflz/456']").should("exist");
  });
});
