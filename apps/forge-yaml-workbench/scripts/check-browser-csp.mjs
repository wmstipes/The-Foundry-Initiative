import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const assetsDirectory = path.resolve(scriptDirectory, "..", "dist", "assets");
const assetNames = (await readdir(assetsDirectory)).filter((name) => name.endsWith(".js"));

if (!assetNames.length) throw new Error("No production JavaScript assets found; run npm run build first.");

for (const assetName of assetNames) {
  const source = await readFile(path.join(assetsDirectory, assetName), "utf8");
  if (/\b(?:new\s+)?Function\s*\(|\beval\s*\(/.test(source)) {
    throw new Error(`${assetName} contains a Function constructor or eval call blocked by the production CSP.`);
  }
}

console.log(`Verified ${assetNames.length} production JavaScript asset(s) contain no eval or Function-constructor usage.`);
