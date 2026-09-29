import Workflow from "@/components/Workflow/index";
import i18n from "@/cypress/fixtures/i18n.json";
import geschaefte from "@/cypress/fixtures/vflz/geschaefte.json";

import type {
  UpdateUserSettingMutationVariables,
  UserSetting,
  VflzLayoutFragment,
} from "@/lib/graphql";

function buildWorkflowItem(index: number) {
  return {
    ...geschaefte.data.vflz.geschaefte.results[0],
    parentId: null,
    taskId: `${index}`,
    title: `Task ${index}`,
    vflz: {
      ...geschaefte.data.vflz.geschaefte.results[0].vflz,
      vflzId: "1",
    },
  };
}

function buildWorkflowResponse(resultsPerPage: number[]) {
  const allItems = Array.from({ length: 12 }, (_, index) => {
    return buildWorkflowItem(index + 1);
  });

  return (page: number) => {
    const start = (page - 1) * resultsPerPage[0];
    const end = start + (resultsPerPage[page - 1] ?? 0);

    return {
      data: {
        vflz: {
          ...geschaefte.data.vflz,
          geschaefte: {
            ...geschaefte.data.vflz.geschaefte,
            numPages: resultsPerPage.length,
            numResultsTotal: allItems.length,
            page,
            results: allItems.slice(start, end),
          },
          prozesse: [],
          teilstandorte: [],
        },
      },
    };
  };
}

describe("Workflow", () => {
  let userSettings: UserSetting[] = [];

  describe("default", () => {
    beforeEach(() => {
      cy.intercept("POST", "/graphql", (req) => {
        if (req.body.query?.includes("query VflzWorkflow")) {
          req.reply(geschaefte);
        } else if (req.body.query?.includes("query I18n")) {
          req.reply(i18n);
        } else if (req.body.query?.includes("query useCurrentUser")) {
          req.reply({
            data: {
              currentUser: {
                settings: userSettings,
              },
            },
          });
        } else if (req.body.query?.includes("mutation updateUserSetting")) {
          req.alias = "updateUserSetting";
          req.reply({
            data: {
              updateUserSetting: req.body.variables.data,
            },
          });
        } else if (req.body.query?.includes("query useSetting")) {
          req.reply({
            data: {
              instanceSettings: [],
            },
          });
        }
      });
    });

    it("toggles grouping and sorting", () => {
      cy.mount(
        <Workflow
          vflz={{ combinedId: "A1" } as VflzLayoutFragment}
          vflzId="1"
        />,
        {
          router: {},
          translations: {
            workflow: {
              asTree: { false: "Chronologisch", true: "Gruppiert" },
              sortBy: { due: "Fälligkeit" },
            },
          },
        },
      );
      cy.get("div[data-test^=Workflow-item]").siblings().should("not.exist");
      cy.get("button").contains("Gruppiert").click();
      cy.get("div[data-test^=Workflow-item]").siblings().should("exist");
    });

    it("keeps the workflow list vertically scrollable for infinite loading", () => {
      cy.mount(
        <Workflow
          vflz={{ combinedId: "A1" } as VflzLayoutFragment}
          vflzId="1"
        />,
        {
          router: {},
          translations: {
            workflow: {
              asTree: { false: "Chronologisch", true: "Gruppiert" },
              sortBy: { due: "Fälligkeit" },
            },
          },
        },
      );

      cy.get('[data-test="Workflow-list"]').should(
        "have.class",
        "overflow-y-auto",
      );
    });
  });

  it("loads additional compact-view items after user scrolls on a short list", () => {
    const workflowResponse = buildWorkflowResponse([10, 2]);

    userSettings = [
      { key: "workflow.compactView", value: true },
      {
        key: "workflow.filter",
        value: {
          eigene: null,
          faelligkeit: [],
          status: [],
          taskTyp: [],
          teilflaechen: null,
          titel: null,
        },
      },
    ];

    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("query VflzWorkflow")) {
        const page = req.body.variables.page as number;
        req.reply(workflowResponse(page));
      } else if (req.body.query?.includes("query I18n")) {
        req.reply(i18n);
      } else if (req.body.query?.includes("query useCurrentUser")) {
        req.reply({
          data: {
            currentUser: {
              settings: userSettings,
            },
          },
        });
      } else if (req.body.query?.includes("mutation updateUserSetting")) {
        req.alias = "updateUserSetting";
        req.reply({
          data: {
            updateUserSetting: req.body.variables.data,
          },
        });
      } else if (req.body.query?.includes("query useSetting")) {
        req.reply({
          data: {
            instanceSettings: [],
          },
        });
      }
    });

    cy.mount(
      <Workflow vflz={{ combinedId: "A1" } as VflzLayoutFragment} vflzId="1" />,
      {
        router: {},
        translations: {
          workflow: {
            asTree: { false: "Chronologisch", true: "Gruppiert" },
            compactView: "Kompakt",
            sortBy: { due: "Fälligkeit" },
          },
        },
      },
    );

    cy.get("div[data-test^=Workflow-item]").should("have.length", "10");
    cy.get('[data-test="Workflow-list"]').scrollTo("bottom");
    cy.get("div[data-test^=Workflow-item]").should("have.length", "12");
  });
});
