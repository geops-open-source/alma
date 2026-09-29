import geopsFlatConfig from "@geops/eslint-config-react";
import eslintNextPlugin from "@next/eslint-plugin-next";
import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  { plugins: { next: eslintNextPlugin } },
  ...geopsFlatConfig,
  globalIgnores([
    ".next/**",
    "build/**",
    "out/**",
    "lib/graphql.ts",
    "lib/generateVersionFile.mjs",
    "next-env.d.ts",
    "node_modules/**",
  ]),
  {
    rules: {
      "@next/next/google-font-display": "off",
      "@next/next/google-font-preconnect": "off",
      "@next/next/no-duplicate-head": "off",
      "@next/next/no-img-element": "off",
      "@next/next/no-page-custom-font": "off",
    },
  },
]);
