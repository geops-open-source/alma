const force = { force: true };

describe("Vflz Participants Page", () => {
  beforeEach(() => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query VflzParticipantsLayout")) {
        req.alias = "VflzParticipantsLayout";
      } else if (req.body.query.includes("mutation deleteSubjekt")) {
        req.alias = "deleteSubjekt";
      } else if (req.body.query.includes("mutation updateVflzBeteiligte")) {
        req.alias = "updateVflzBeteiligte";
      }
    });
  });

  it("reads and updates values for Beteiligte", () => {
    cy.setUser("bearbeiten-sachdaten");
    cy.resetFixture("beteiligte");
    cy.resetFixture("subjekte");
    cy.updateAdminSetting(
      "ui.display.gemeindenUndNummerierungsbereiche",
      "gemeinde",
    );
    cy.visit("/vflz/1/participants");
    cy.wait("@VflzParticipantsLayout");

    /* Sachbearbeitung */
    cy.get(
      'button[name="sachbearbeitung.0.beteiligter.subjekt.subjId"]',
    ).contains("Bearbeiten Sachdaten");
    cy.get(
      'button[name="sachbearbeitung.0.beteiligter.subjekt.subjId"]',
    ).click();
    cy.get("div[role='listbox']").contains("Bearbeiten Geschäfte").click();
    cy.get("button").contains("Sachbearbeitung hinzufügen").click();
    cy.get(
      'button[name="sachbearbeitung.1.beteiligter.subjekt.subjId"]',
    ).click();
    cy.get("div[role='listbox']").should("not.contain", "Bearbeiten Geschäfte");
    cy.get("div[role='listbox']").contains("Bearbeiten Sachdaten").click();

    /* Sonstige Beteiligte */
    cy.get('input[name="sonstigeBeteiligte.0.beteiligter.subjekt"]').should(
      "have.value",
      "Foo Bar",
    );
    cy.get("button[name='sonstigeBeteiligte.0.beziehungsart']").contains("Foo");
    /* add Sonstigen Beteiligten */
    cy.get("button").contains("Beteiligte hinzufügen").click();
    cy.get('input[name="sonstigeBeteiligte.1.beteiligter.subjekt"]').click();
    cy.get("div[role='listbox']").contains("neue Adresse").click();
    /* create Subjekt */
    cy.get("div[role='dialog']").within(() => {
      cy.get("h2").contains("Neue Adresse");
      cy.get("input[name=kuerzel]").type("ab", force);
      cy.get("input[name=vorname]").type("a", force);
      cy.get("input[name=name][type=text]").type("b", force);
      cy.get("textarea[name=taetigkeit]").type("t", force);
      cy.get("input[name=strasse]").type("s 1", force);
      cy.get("input[name=postleitzahl]").type("1", force);
      cy.get("input[name=ort]").type("o", force);
      cy.get("button").contains("Adresse speichern").click();
    });
    cy.get('input[name="sonstigeBeteiligte.1.beteiligter.subjekt"]').should(
      "have.value",
      "a b, t",
    );
    /* update Subjekt */
    cy.get(
      "button[name='sonstigeBeteiligte.1.beteiligter.subjekt.SubjektDialog']",
    ).click(force);
    cy.get("div[role='dialog']").within(() => {
      cy.get("h2").contains("Adresse bearbeiten");
      cy.get("input[name=vorname]").should("have.value", "a");
      cy.get("input[name=vorname]").type("1", force);
      cy.get("input[name=name][type=text]").type("1", force);
      cy.get("textarea[name=taetigkeit]").type("1", force);
      cy.get("button").contains("Adresse speichern").click();
    });
    cy.get('input[name="sonstigeBeteiligte.1.beteiligter.subjekt"]').should(
      "have.value",
      "a1 b1, t1",
    );
    cy.get("button[name='sonstigeBeteiligte.1.beziehungsart']").click();
    cy.get("div[role='listbox']").contains("Bar").click();

    /* Eigentum */
    /* first row */
    cy.get('input[name="eigentum.0.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.0.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.0.gemeinde.hGemId']").contains("Foo (0001)");
    cy.get("input[name='eigentum.0.parzellen']").should("have.value", "1");
    /* second row */
    cy.get('input[name="eigentum.1.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.1.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.1.gemeinde.hGemId']").contains("Foo (0001)");
    cy.get("input[name='eigentum.1.parzellen']").should("have.value", "4");
    /* third row */
    cy.get('input[name="eigentum.2.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.2.gemeinde.hGemId']").contains("Foo (0001)");
    cy.get("input[name='eigentum.2.parzellen']").should("have.value", "2");
    /* fourth row */
    cy.get('input[name="eigentum.3.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.3.gemeinde.hGemId']").contains("Bar (0002)");
    cy.get("input[name='eigentum.3.parzellen']").should("have.value", "3");

    cy.get("form button").contains("Speichern").click();
    cy.wait("@updateVflzBeteiligte").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.updateVflzBeteiligte.__typename",
        "Vflz",
      );
    });
    cy.get(
      'button[name="sachbearbeitung.0.beteiligter.subjekt.subjId"]',
    ).contains("Bearbeiten Geschäfte");
    cy.get(
      'button[name="sachbearbeitung.1.beteiligter.subjekt.subjId"]',
    ).contains("Bearbeiten Sachdaten");
    cy.get("button[name='sonstigeBeteiligte.0.beziehungsart']").contains("Foo");
    cy.get("button[name='sonstigeBeteiligte.1.beziehungsart']").contains("Bar");

    /* delete */
    cy.get('button[name="sachbearbeitung.1.remove"]').click();
    cy.get("form button").contains("Speichern").click();
    cy.wait("@updateVflzBeteiligte").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.updateVflzBeteiligte.__typename",
        "Vflz",
      );
    });
    cy.get(
      'button[name="sonstigeBeteiligte.1.beteiligter.subjekt.SubjektDialog"]',
    ).click();
    cy.get("div[role='dialog'] button").contains("Adresse löschen").click();
    cy.wait("@deleteSubjekt").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.deleteSubjekt",

        interception.request.body.variables.subjId,
      );
    });

    cy.get(
      'button[name="sachbearbeitung.0.beteiligter.subjekt.subjId"]',
    ).contains("Bearbeiten Geschäfte");
    cy.get(
      'button[name="sachbearbeitung.1.beteiligter.subjekt.subjId"]',
    ).should("not.exist");
    cy.get('input[name="sonstigeBeteiligte.0.beteiligter.subjekt"]').should(
      "have.value",
      "Foo Bar",
    );
    cy.get("button[name='sonstigeBeteiligte.0.beziehungsart']").contains("Foo");
    cy.get('input[name="sonstigeBeteiligte.1.beteiligter.subjekt"]').should(
      "not.exist",
    );

    // should automatically select current user if no other user is selected
    cy.get("button[name='sachbearbeitung.0.remove']").click();
    cy.get("button").contains("Sachbearbeitung hinzufügen").click();
    cy.get(
      'button[name="sachbearbeitung.0.beteiligter.subjekt.subjId"]',
    ).contains("Bearbeiten Sachdaten");
  });

  it("displays and uses nummerierungsbereich for eigentum", () => {
    cy.setUser("bearbeiten-sachdaten");
    cy.resetFixture("beteiligte");
    cy.updateAdminSetting(
      "ui.display.gemeindenUndNummerierungsbereiche",
      "nummerierungsbereich",
    );
    cy.visit("/vflz/1/participants");
    cy.wait("@VflzParticipantsLayout");

    /* first row */
    cy.get('input[name="eigentum.0.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.0.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.0.nummerierungsbereich.hNbId']").contains(
      "Test A",
    );

    cy.get("input[name='eigentum.0.parzellen']").should("have.value", "1");
    /* second row */
    cy.get('input[name="eigentum.1.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.1.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.1.nummerierungsbereich.hNbId']").contains(
      "Test A",
    );

    cy.get("input[name='eigentum.1.parzellen']").should("have.value", "4");
    /* third row */
    cy.get('input[name="eigentum.2.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.2.nummerierungsbereich.hNbId']").contains(
      "Test A",
    );
    cy.get("input[name='eigentum.2.parzellen']").should("have.value", "2");
    /* fourth row */
    cy.get('input[name="eigentum.3.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.3.nummerierungsbereich.hNbId']").should(
      "have.value",
      "",
    );
    cy.get("input[name='eigentum.3.parzellen']").should("have.value", "3");

    /* UPDATE first row to nummerierungsbereich B */
    cy.get("button[name='eigentum.0.nummerierungsbereich.hNbId']").click();
    cy.get("div[role='listbox']").contains("Test B").click();

    cy.get("form button").contains("Speichern").click();
    cy.wait("@updateVflzBeteiligte").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.updateVflzBeteiligte.__typename",
        "Vflz",
      );
    });
    cy.get("button[name='eigentum.1.nummerierungsbereich.hNbId']").contains(
      "Test B",
    );
  });

  it("displays and uses gemeinde and nummerierungsbereich for eigentum", () => {
    cy.setUser("bearbeiten-sachdaten");
    cy.resetFixture("beteiligte");
    cy.updateAdminSetting(
      "ui.display.gemeindenUndNummerierungsbereiche",
      "both",
    );
    cy.visit("/vflz/1/participants");
    cy.wait("@VflzParticipantsLayout");

    /* first row */
    cy.get('input[name="eigentum.0.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.0.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.0.gemeinde.hGemId']").contains(
      "Test A / Foo (0001)",
    );

    cy.get("input[name='eigentum.0.parzellen']").should("have.value", "1");
    /* second row */
    cy.get('input[name="eigentum.1.subjekt"]').should(
      "have.value",
      "Lesen Sachdaten",
    );
    cy.get("button[name='eigentum.1.beziehungsart']").contains("Eigentum");
    cy.get("button[name='eigentum.1.gemeinde.hGemId']").contains(
      "Test A / Foo (0001)",
    );

    cy.get("input[name='eigentum.1.parzellen']").should("have.value", "4");
    /* third row */
    cy.get('input[name="eigentum.2.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.2.gemeinde.hGemId']").contains(
      "Test A / Foo (0001)",
    );
    cy.get("input[name='eigentum.2.parzellen']").should("have.value", "2");
    /* fourth row */
    cy.get('input[name="eigentum.3.subjekt"]').should("have.value", "");
    cy.get("button[name='eigentum.3.gemeinde.hGemId']").contains(
      "Test A / Bar (0002)",
    );
    cy.get("input[name='eigentum.3.parzellen']").should("have.value", "3");

    /* UPDATE first row */
    cy.get("button[name='eigentum.0.gemeinde.hGemId']").click();
    cy.get("div[role='listbox']").contains("Test A / Bar (0002)").click();

    cy.get("form button").contains("Speichern").click();
    cy.wait("@updateVflzBeteiligte").then((interception) => {
      expect(interception.response?.body).to.have.nested.property(
        "data.updateVflzBeteiligte.__typename",
        "Vflz",
      );
    });
    cy.get("button[name='eigentum.1.gemeinde.hGemId']").contains(
      "Test A / Bar (0002)",
    );
  });
});
