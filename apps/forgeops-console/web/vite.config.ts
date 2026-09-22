import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { createHash } from "node:crypto";
import { readFileSync, globSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

// Match bundle.go's embedded inputs; omit generated assets and dependency caches.
const root = fileURLToPath(new URL("..", import.meta.url));
const inputs = ["bundle.go", "go.mod", "go.sum", "internal/*/*.go", "cmd/*/*.go", "web/src/*.ts", "web/src/*.tsx", "web/src/*.css", "web/src/plugins/*.tsx", "web/index.html", "web/package.json", "web/package-lock.json", "web/tsconfig.json", "web/tsconfig.app.json", "web/tsconfig.node.json", "web/vite.config.ts"];
const hash = createHash("sha256");
for (const path of inputs.flatMap((pattern) => globSync(pattern, { cwd: root })).map((path) => path.replaceAll("\\", "/")).sort()) hash.update(path).update("\0").update(readFileSync(resolve(root, path))).update("\0");
const identity = { protocol: "forgeops.console/v1alpha1", sourceDigest: hash.digest("hex") };

export default defineConfig({
  define: { __FORGEOPS_BUNDLE__: JSON.stringify(identity) },
  plugins: [react(), {
    name: "forgeops-bundle-identity",
    generateBundle() { this.emitFile({ type: "asset", fileName: "forgeops-bundle.json", source: JSON.stringify(identity) }); },
  }],
  build: { outDir: "dist", emptyOutDir: true },
  test: { environment: "happy-dom", restoreMocks: true },
});
