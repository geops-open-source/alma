import VflzLayout from "./VflzLayout";

describe("VflzLayout component", () => {
  beforeEach(() => {
    cy.viewport(1024, 500);
    cy.stubCurrentUser();
  });

  it("renders navigation", () => {
    cy.mount(<VflzLayout>Hello world</VflzLayout>, {
      router: { query: { vflzId: "1" } },
    });
    cy.get("main").contains("Hello world");
    [
      "#content",
      "/data#basedata",
      "/geo#map",
      "/evaluation#beurteilung",
      "/participants#sachbearbeitung",
      "/workflow#filter",
    ].forEach((path) => {
      cy.get(
        `header[data-test=VflzLayout-header] nav a[href="/vflz/1${path}"]`,
      ).should("exist");
    });
    cy.get("[data-test=VflzSummary-gemeinde]").should("not.exist");
  });

  it("renders Vflz", () => {
    cy.mount(
      <VflzLayout
        vflz={{
          bezeichnung: "TestVflz",
          combinedId: "123",
          evaluationStatus: {
            deletedPreviously: false,
            deleteNow: false,
            publishedPreviously: false,
            publishNow: false,
          },
          gemeinde: { gemeinde: "TestGemeinde" },
          isCurrent: true,
          teilstandorte: [],
          versionen: [],
          vflId: "1",
          vflzCreatedDate: "2024-12-01",
          vflzId: "1",
        }}
      />,
      {
        router: { query: { vflzId: "1" } },
        translations: {
          VflzStatusText: {
            current: "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
          },
          VflzSummary: {
            current: "aktuell, nicht publiziert",
          },
        },
      },
    );
    cy.get("[data-test=VflzLayout-header]").contains("123");
    cy.get("[data-test=VflzLayout-header]").contains("TestVflz");
    cy.get("[data-test=VflzLayout-header]").contains("aktuell, nicht publiziert"); // prettier-ignore
    cy.get("[data-test=VflzSummary-gemeinde]").contains("TestGemeinde");
    cy.get("[data-test=VflzLayout-sidebar]").contains(
      "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
    );
  });

  it("stores sidebar state", () => {
    cy.mount(<VflzLayout />, { router: {} });
    cy.get("[data-test=VflzLayout-sidebar] button[role=tab]")
      .eq(0)
      .should("have.attr", "aria-selected", "true");
    cy.get("[data-test=VflzLayout-sidebar] button[role=tab]").eq(1).click();
    cy.get("button[data-test=VflzLayout-toggleSidebar]").click();
    cy.get("[data-test=VflzLayout-sidebar]").should("not.exist");
    cy.mount(<VflzLayout />, { router: {} });
    cy.get("[data-test=VflzLayout-sidebar]").should("not.exist");
    cy.get("button[data-test=VflzLayout-toggleSidebar]").click();
    cy.get("[data-test=VflzLayout-sidebar] button[role=tab]")
      .eq(1)
      .should("have.attr", "aria-selected", "true");
  });
});
