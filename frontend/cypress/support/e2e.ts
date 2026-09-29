import { gql, GraphQLClient } from "graphql-request";
import pixelmatch from "pixelmatch";

import subjekte from "../fixtures/subjekte.json";
import users from "../fixtures/users.json";
import beteiligte from "../fixtures/vflz/beteiligte.json";
import ablagerungsstandort from "../fixtures/vflz/data/ablagerungsstandort.json";
import betriebsstandort from "../fixtures/vflz/data/betriebsstandort.json";
import kinderspielplatz from "../fixtures/vflz/data/kinderspielplatz.json";
import pfasstandort from "../fixtures/vflz/data/pfasstandort.json";
import schiessanlagenstandort from "../fixtures/vflz/data/schiessanlagenstandort.json";
import unfallstandort from "../fixtures/vflz/data/unfallstandort.json";
import evaluation from "../fixtures/vflz/evaluation.json";
import vollzug from "../fixtures/vflz/vollzug.json";
import taskFormular from "../fixtures/vflz/workflow/formular.json";

import "./commands";

import type { RequestDocument, Variables } from "graphql-request";

import type { CreateVflzInput, CypressCreateVflzMutation } from "@/lib/graphql";

type Data = Record<string, unknown> | Record<string, unknown>[];

type FixtureName =
  | "ablagerungsstandort"
  | "beteiligte"
  | "betriebsstandort"
  | "evaluation"
  | "kinderspielplatz"
  | "pfasstandort"
  | "schiessanlagenstandort"
  | "subjekte"
  | "taskFormular"
  | "unfallstandort"
  | "users"
  | "vollzug";

type UserName =
  | "admin"
  | "bearbeiten-geschaefte"
  | "bearbeiten-sachdaten"
  | "lesen-geschaefte"
  | "lesen-sachdaten"
  | "unauthorized";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      createVflz: (data: Partial<CreateVflzInput>) => Cypress.Chainable<string>;
      graphql<T>(
        document: RequestDocument,
        variables?: Variables,
      ): Promise<{ data: T }>;
      pixelmatchFixture(path: string): Chainable<JQuery<HTMLCanvasElement>>;
      resetFixture: (name: FixtureName, data?: Data) => void;
      setUser: (user: UserName) => void;
      updateAdminSetting(key: string, value: unknown): void;
      updateUserSetting(user: UserName, key: string, value: unknown): void;
    }
  }
}

Cypress.Commands.add("graphql", async (document, variables) => {
  const client = new GraphQLClient("/graphql", {
    headers: { "alma-e2e-test-user": "admin" },
  });
  return { data: await client.request(document, variables) };
});

const createVflzMutation = gql`
  mutation CypressCreateVflz($data: CreateVflzInput!) {
    createVflz(data: $data) {
      __typename
      ... on Vflz {
        vflzId
      }
    }
  }
`;

const updateVflzDataMutation = gql`
  mutation cypressUpdateVflzData($data: UpdateVflzDataInput!) {
    reset: updateVflzData(data: $data) {
      __typename
    }
  }
`;

const updateVflzEvaluationMutation = gql`
  mutation cypressUpdateVflzEvaluation($data: UpdateVflzEvaluationInput!) {
    reset: updateVflzEvaluation(data: $data) {
      __typename
    }
  }
`;

const updateVflzBeteiligteMutation = gql`
  mutation cypressUpdateVflzBeteiligte($data: UpdateVflzBeteiligteInput!) {
    reset: updateVflzBeteiligte(data: $data) {
      __typename
    }
  }
`;

const updateVflzVollzugMutation = gql`
  mutation cypressUpdateVflzVollzug($data: UpdateVflzVollzugInput!) {
    reset: updateVflzVollzug(data: $data) {
      __typename
    }
  }
`;

const updateSubjektMutation = gql`
  mutation cypressUpdateSubjekt($data: UpdateSubjektInput!) {
    reset: updateSubjekt(data: $data) {
      __typename
    }
  }
`;

const updateTaskFormular = gql`
  mutation cypressUpdateTaskFormular($data: UpdateFormularInput!) {
    reset: updateFormular(data: $data) {
      __typename
    }
  }
`;

const updateUserMutation = gql`
  mutation cypressUserSubjekt($data: UpdateUserInput!) {
    reset: updateUser(data: $data) {
      __typename
    }
  }
`;

const fixtures: Record<FixtureName, [string, string, Data]> = {
  ablagerungsstandort: [updateVflzDataMutation, "Vflz", ablagerungsstandort],
  beteiligte: [updateVflzBeteiligteMutation, "Vflz", beteiligte],
  betriebsstandort: [updateVflzDataMutation, "Vflz", betriebsstandort],
  evaluation: [updateVflzEvaluationMutation, "Vflz", evaluation],
  kinderspielplatz: [updateVflzDataMutation, "Vflz", kinderspielplatz],
  pfasstandort: [updateVflzDataMutation, "Vflz", pfasstandort],
  schiessanlagenstandort: [updateVflzDataMutation, "Vflz", schiessanlagenstandort], // prettier-ignore
  subjekte: [updateSubjektMutation, "UpdateSubjektResult", subjekte],
  taskFormular: [updateTaskFormular, "Formular", taskFormular],
  unfallstandort: [updateVflzDataMutation, "Vflz", unfallstandort],
  users: [updateUserMutation, "User", users],
  vollzug: [updateVflzVollzugMutation, "Vflz", vollzug],
};

Cypress.Commands.add("resetFixture", (name: FixtureName, data: Data = {}) => {
  const [document, typename, fixtureData] = fixtures[name];
  if (Array.isArray(fixtureData)) {
    fixtureData.forEach((item) => {
      const variables = { data: { ...item, ...data } };
      cy.graphql(document, variables).then(
        (result) => {
          expect(result).to.nested.include({
            "data.reset.__typename": typename,
          });
        },
        () => {
          return null;
        },
      );
    });
  } else {
    const variables = { data: { ...fixtureData, ...data } };
    cy.graphql(document, variables).then(
      (result) => {
        expect(result).to.nested.include({ "data.reset.__typename": typename });
      },
      () => {
        return null;
      },
    );
  }
});

Cypress.Commands.add("setUser", (user) => {
  cy.intercept("/graphql", (req) => {
    req.headers["alma-e2e-test-user"] = user;
  });
  cy.intercept("/api/documents/**", (req) => {
    req.headers["alma-e2e-test-user"] = user;
  });
});

Cypress.Commands.add("updateAdminSetting", (key, value) => {
  const query = `mutation { updateInstanceSetting(data: {key: "${key}", value: ${JSON.stringify(value)}, category: ADMIN}) { ...on InstanceSetting { key } } }`;
  cy.request({
    body: JSON.stringify({ query }),
    headers: {
      "alma-e2e-test-user": "admin",
      "Content-Type": "application/json",
    },
    method: "POST",
    url: "/graphql",
  }).then((response) => {
    expect(response.status).to.equal(200);

    expect(response.body.data.updateInstanceSetting.key).to.equal(key);
  });
});

Cypress.Commands.add("updateUserSetting", (user, key, value) => {
  const query = `mutation updateUserSetting($data: UpdateUserSettingInput!) { updateUserSetting(data: $data) { ... on UserSetting { key } } }`;
  cy.request({
    body: JSON.stringify({ query, variables: { data: { key, value } } }),
    headers: {
      "alma-e2e-test-user": user,
      "Content-Type": "application/json",
    },
    method: "POST",
    url: "/graphql",
  }).then((response) => {
    expect(response.status).to.equal(200);

    expect(response.body.data.updateUserSetting.key).to.equal(key);
  });
});

Cypress.Commands.add(
  "pixelmatchFixture",
  { prevSubject: "element" },
  (subject, path) => {
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(2000); // wait for the map to finish rendering
    cy.fixture<number[]>(path, null).then((fixture) => {
      let bCanvas: HTMLCanvasElement;
      let diff: number;
      cy.wrap(subject as JQuery<HTMLCanvasElement>)
        .then((canvas) => {
          // down-scale map canvas (B) to devicePixelRatio=1
          // to support devices with different pixel ratios
          const { height: mapH, width: mapW } = canvas[0];
          bCanvas = document.createElement("canvas");
          const bContext = bCanvas.getContext("2d");
          const ratio = window.devicePixelRatio || 1;
          bCanvas.width = canvas[0].width / ratio;
          bCanvas.height = canvas[0].height / ratio;
          const { height, width } = bCanvas;
          bContext?.drawImage(canvas[0], 0, 0, mapW, mapH, 0, 0, width, height);

          // eslint-disable-next-line cypress/no-unnecessary-waiting
          cy.wait(500); // wait for bCanvas to finish rendering

          // convert binary fixture (A) to ImageData
          const aCanvas = document.createElement("canvas");
          aCanvas.width = width;
          aCanvas.height = height;
          const aContext = aCanvas.getContext("2d");
          const aImage = new Image(width, height);
          return new Promise((resolve: (data: ImageData[]) => void, reject) => {
            aImage.onload = () => {
              aContext?.drawImage(aImage, 0, 0);
              // eslint-disable-next-line cypress/no-unnecessary-waiting
              cy.wait(500); // wait for aCanvas to finish rendering
              let a, b;
              try {
                a = aContext?.getImageData(0, 0, width, height);
              } catch (e) {
                console.error("getImageData for aContext failed with", e);
                reject(new Error("getImageData for aContext failed"));
              }
              try {
                b = bContext?.getImageData(0, 0, width, height);
              } catch (e) {
                console.error("getImageData for bContext failed with", e);
                reject(new Error("getImageData for bContext failed"));
              }
              if (a && b) {
                resolve([a, b]);
              }
            };
            const data = btoa(String.fromCharCode.apply(null, fixture));
            aImage.src = `data:image/png;base64,${data}`;
          });
        })
        .then(([a, b]) => {
          diff = pixelmatch(a.data, b.data, undefined, a.width, a.height);
          if (diff > 0) {
            const brokenImage = bCanvas
              .toDataURL("image/png")
              .replace(/^data:image\/png;base64,/, "");
            cy.writeFile(
              `cypress/screenshots/${path}-${Date.now()}.png`,
              brokenImage,
              { encoding: "base64" },
            );
          }
        })
        .then(() => {
          expect(diff, `number of mismatched pixels for ${path}`).to.equal(0);
        });
    });
  },
);

Cypress.Commands.add("createVflz", (data: Partial<CreateVflzInput>) => {
  return cy.then(() => {
    return new GraphQLClient("/graphql", {
      headers: { "alma-e2e-test-user": "admin" },
    })
      .request<CypressCreateVflzMutation>(createVflzMutation, {
        data: {
          bezeichnung: "E2E Test",
          combinedId: Math.random().toString(36).substring(2, 6),
          flugplatz: null,
          gemeinde: { hGemId: "2" },
          geometry: {
            coordinates: [
              [
                [
                  [2606757, 1228616],
                  [2606761, 1228609],
                  [2606750, 1228609],
                  [2606757, 1228616],
                ],
              ],
            ],
            type: "MultiPolygon",
          },
          ktu: null,
          vftyp: "code:63:01",
          zentroid: null,
          ...data,
        },
      })
      .then((response) => {
        if (response?.createVflz.__typename !== "Vflz") {
          throw new Error("Failed to create Vflz");
        }
        expect(response).to.have.nested.property("createVflz.vflzId");
        return response.createVflz.vflzId;
      });
  });
});

export {};
