import { writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

import metadata from "../package.json" with { type: "json" };

const __dirname = dirname(fileURLToPath(import.meta.url));
const versionFile = join(__dirname, "../out/version.txt");
writeFileSync(versionFile, process.env.NEXT_PUBLIC_VERSION ?? metadata.version);
