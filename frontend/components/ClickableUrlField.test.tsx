import { getValidUrl } from "./ClickableUrlField";

describe("getValidUrl", () => {
  it("accepts common valid URLs", () => {
    const validCases: [string, string][] = [
      [
        "https://trusted.example/path?x=1#section",
        "https://trusted.example/path?x=1#section",
      ],
      ["http://trusted.example", "http://trusted.example/"],
      ["www.trusted.example", "https://www.trusted.example/"],
      [
        "  https://sub.trusted.example:8443/path  ",
        "https://sub.trusted.example:8443/path",
      ],
    ];

    validCases.forEach(([input, expected]) => {
      cy.wrap(getValidUrl(input)).should("equal", expected);
    });
  });

  it("rejects common invalid URLs", () => {
    const invalidCases = [
      "",
      "example.com",
      "www.",
      "https://example",
      "ftp://trusted.example",
      "javascript:alert(1)",
      "https://trusted.example@evil.example",
    ];

    invalidCases.forEach((input) => {
      cy.wrap(getValidUrl(input)).should("equal", null);
    });
  });

  it("rejects URLs containing credentials", () => {
    cy.wrap(getValidUrl("https://trusted.example@evil.example")).should(
      "equal",
      null,
    );
  });

  it("accepts complete https URLs", () => {
    cy.wrap(getValidUrl("https://trusted.example/path?x=1#section")).should(
      "equal",
      "https://trusted.example/path?x=1#section",
    );
  });

  it("rejects incomplete www hostnames", () => {
    cy.wrap(getValidUrl("www.")).should("equal", null);
  });
});
