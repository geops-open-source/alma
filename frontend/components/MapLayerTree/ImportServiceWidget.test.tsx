import ImportServiceWidget from "./ImportServiceWidget";

const services = [
  {
    firstItem: "Armee- und Kriegsdenkmäler",
    fixture: "MapLayerTree/ImportServiceWidget/wms.geo.admin.ch.xml",
    url: "https://wms.geo.admin.ch/?REQUEST=GetCapabilities&SERVICE=WMS&VERSION=1.3.0",
  },
  {
    firstItem: "geodienste.ch WMS Planerischer Gewässerschutz",
    fixture:
      "MapLayerTree/ImportServiceWidget/planerischer_gewaesserschutz_v1_2_0.xml",
    url: "https://geodienste.ch/db/planerischer_gewaesserschutz_v1_2_0/deu?SERVICE=WMS&REQUEST=GetCapabilities",
  },
  {
    firstItem: "Tracer Verbindungslinien",
    fixture: "MapLayerTree/ImportServiceWidget/geoservice.apps.be.ch-wms.xml",
    url: "https://www.geoservice.apps.be.ch/geoservice3/services/a42geo/of_geoscientificinformation02_de_ms_wms/MapServer/WMSServer?&request=GetCapabilities&service=WMS",
  },
  {
    firstItem: "Naturgefahren Perimeter Gefahrenkartierung",
    fixture: "MapLayerTree/ImportServiceWidget/wfs.geo.gl.ch.xml",
    url: "https://wfs.geo.gl.ch/?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities",
  },
  {
    firstItem: "OWS Kanton Glarus",
    fixture: "MapLayerTree/ImportServiceWidget/wms.geo.gl.ch.xml",
    url: "https://wms.geo.gl.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities",
  },
];

describe("ImportServiceWidget component", () => {
  beforeEach(() => {
    cy.intercept("POST", "/graphql", (req) => {
      if (req.body.query?.includes("mutation updateInstanceSetting")) {
        req.alias = "updateInstanceSetting";
        req.reply({ data: {} });
      }
    });
  });

  it("parses OGC services", () => {
    cy.mount(<ImportServiceWidget onClose={cy.stub()} />);
    services.forEach((service) => {
      cy.get("input[name=url]").clear();
      cy.intercept("GET", service.url, { fixture: service.fixture }).as(
        "getCapabilities",
      );
      cy.get("input[name=url]").type(service.url);
      cy.wait("@getCapabilities");
      cy.contains("label", service.firstItem);
    });
  });
});
