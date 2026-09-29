module.exports = {
  documents: [
    "./components/**/*.{ts,tsx}",
    "./cypress/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./pages/**/*.tsx",
  ],
  extensions: {
    codegen: {
      generates: {
        "lib/graphql.ts": {
          config: {
            enumsAsConst: true,
            scalars: {
              Code: "string",
              Date: "string",
              DateTime: "string",
              FormularEingaben: "FormularEingaben",
              FormularFelder: "FormularFeld[]",
              GeoJSONFeatureCollection: "GeoJSONFeatureCollection",
              GeoJSONLineString: "GeoJSONLineString",
              GeoJSONPoint: "GeoJSONPoint",
              GeoJSONPointOrMultiPolygon: "GeoJSONPoint | GeoJSONMultiPolygon",
              JSON: "unknown",
              JSONTranslation: "JSONTranslation",
              Language: "string",
            },
            skipTypename: true,
          },
          plugins: [
            "typescript",
            "typescript-operations",
            {
              add: {
                content: `import type { FeatureCollection as GeoJSONFeatureCollection, LineString as GeoJSONLineString, Point as GeoJSONPoint, MultiPolygon as GeoJSONMultiPolygon } from "geojson";

export type FormularEingaben = Record<string, unknown>;

export type FormularFeld =
  | {
      choices?: { label: string; value: string }[];
      label?: string;
      name: string;
      type: "str";
    }
  | {
      label?: string;
      name: string;
      type: "bool" | "date" | "int" | "title";
    };

export type JSONTranslation = Record<string, string>;
`,
              },
            },
          ],
        },
      },
      hooks: { afterAllFileWrite: ["prettier --write"] },
    },
  },
  schema: "../backend/schema.graphql",
};
