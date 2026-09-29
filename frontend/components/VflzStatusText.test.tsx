import VflzStatusText from "./VflzStatusText";

import type { VflzStatusTextFragment } from "@/lib/graphql";

const mountOptions = {
  translations: {
    VflzStatusText: {
      contaminated: "Aktuelle Publikation am 01.01.2025.",
      current: "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
      deleted: "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
      historized: "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
    },
  },
};

const vflz = {
  isCurrent: true,
  versionen: [],
  vflzCreatedDate: "2024-12-01",
};

const contaminated = {
  versionen: [
    {
      beurteilung: { kbsInfo: { belastet: true } },
      datPublizieren: "2025-01-01",
      publizieren: true,
      vflzId: "1",
    },
  ],
};

const notContaminated = {
  versionen: [
    {
      beurteilung: { kbsInfo: { belastet: false } },
      datPublizieren: "2025-01-01",
      publizieren: true,
      vflzId: "1",
    },
  ],
};

// content for test cases: [fixture, [expected long texts]]
const cases: [VflzStatusTextFragment, string[]][] = [
  [vflz, ["Es wird die aktuelle Version vom 01.12.2024 angezeigt."]],
  [
    { ...vflz, isCurrent: false },
    ["Es wird die historisierte Version vom 01.12.2024 angezeigt."],
  ],
  [
    { ...vflz, ...contaminated, isCurrent: true },
    [
      "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
      "Aktuelle Publikation am 01.01.2025.",
    ],
  ],
  [
    { ...vflz, ...contaminated, isCurrent: false },
    [
      "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
      "Aktuelle Publikation am 01.01.2025.",
    ],
  ],
  [
    { ...vflz, ...notContaminated, isCurrent: false },
    [
      "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
      "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
    ],
  ],
  [
    { ...vflz, ...contaminated, isCurrent: false },
    [
      "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
      "Aktuelle Publikation am 01.01.2025.",
    ],
  ],
  [
    { ...vflz, ...notContaminated },
    [
      "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
      "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
    ],
  ],
  [
    { ...vflz, ...notContaminated, isCurrent: false },
    [
      "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
      "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
    ],
  ],
  [
    { ...vflz, ...notContaminated },
    [
      "Es wird die aktuelle Version vom 01.12.2024 angezeigt.",
      "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
    ],
  ],
  [
    { ...vflz, ...notContaminated, isCurrent: false },
    [
      "Es wird die historisierte Version vom 01.12.2024 angezeigt.",
      "Am 01.01.2025 wurde der Standort aus dem KbS gelöscht.",
    ],
  ],
];

describe("VflzStatusText component", () => {
  it("renders different cases", () => {
    cases.forEach(([instance, texts]) => {
      cy.mount(<VflzStatusText vflz={instance} />, mountOptions);
      texts.forEach((text, index) => {
        cy.get("p").eq(index).should("have.text", text);
      });
    });
  });
});
