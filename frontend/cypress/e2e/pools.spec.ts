describe("Pools page", () => {
  it("creates and deletes a pool", () => {
    cy.intercept<{ query: string }>("POST", "/graphql", (req) => {
      if (req.body.query.includes("query filterPools")) {
        req.alias = "filterPools";
      } else if (req.body.query.includes("mutation createPool")) {
        req.alias = "createPool";
      }
    });

    cy.resetFixture("ablagerungsstandort");
    cy.resetFixture("vollzug");
    cy.setUser("bearbeiten-sachdaten");
    cy.visit("/pools");
    cy.wait("@filterPools");

    // create pool
    cy.get("button[data-test=pools-createPool]").click();
    const poolA = Math.random().toString(36).substring(2, 9);
    const poolB = Math.random().toString(36).substring(2, 9);
    cy.get("form[data-test=pools-pool] input[name=bezeichnung]").type(poolA); // prettier-ignore
    cy.get("form[data-test=pools-pool] input[name=bemerkungen]").type("Bar");
    cy.get("form[data-test=pools-pool] button[type=submit]").click();

    // add vflz to created pool
    cy.visit("/vflz/1");
    cy.get("[data-test=VflzLayout-sidebar] button[role=tab]").eq(2).click();
    cy.get("button[data-test=VflzLayout-sidebar-open-pool-dialog]").click();
    cy.get("form[data-test=AddToPoolDialog] input[name=poolId]").type(poolA); // prettier-ignore
    cy.get("div[role=listbox] div[role=option]").contains(poolA).click();
    cy.get("form[data-test=AddToPoolDialog] button[type=submit]").click(); // prettier-ignore
    cy.get("form[data-test=VflzLayout-sidebar-pools] button[name=poolId]").click(); // prettier-ignore
    cy.get("div[role=listbox] div[role=option]").contains(`${poolA} (1)`);
    cy.get("form[data-test=VflzLayout-sidebar-pools] button[name=poolId]").click(); // prettier-ignore

    // create another pool and add vflz to it
    cy.get("button[data-test=VflzLayout-sidebar-open-pool-dialog]").click();
    cy.get("form[data-test=AddToPoolDialog] button[role=tab]").contains("Neuer Pool").click(); // prettier-ignore
    cy.get("form[data-test=AddToPoolDialog] input[name=bezeichnung]").type(poolB); // prettier-ignore
    cy.get("form[data-test=AddToPoolDialog] button[type=submit]").click(); // prettier-ignore
    cy.get("form[data-test=VflzLayout-sidebar-pools] button[name=poolId]").click(); // prettier-ignore
    cy.get("div[role=listbox] div[role=option]").contains(`${poolB} (1)`);
    cy.get("form[data-test=VflzLayout-sidebar-pools] button[name=poolId]").click(); // prettier-ignore

    // remove vflz from pool and delete pool
    cy.get("div[data-test=VflzLayout-sidebar] a[href='/pools']").click();
    [poolA, poolB].forEach((pool) => {
      cy.get("form[data-test=pools-filter] input[name=filter]").clear();
      cy.get("form[data-test=pools-filter] input[name=filter]").type(pool);
      cy.get("div[data-test=pools-list] div[role=link]").first().contains(pool);
      cy.get("div[data-test=pools-list] div[role=link]").first().click();
      cy.get("table[data-test=pools-vflz] tbody tr").should("have.length", 1);
      cy.get("table[data-test=pools-vflz] tbody tr td").first().contains("A1");
      cy.get("table[data-test=pools-vflz] button[data-test=pools-removeFromPool]").click(); // prettier-ignore
      cy.get("table[data-test=pools-vflz] tbody tr").should("have.length", 0);
      cy.get("button[data-test=pools-deletePool]").click();
      cy.get("button[data-test=pools-confirmDeletePool]").click();
      cy.get("div[data-test=pools-list]").should("not.contain", pool);
    });
  });
});
