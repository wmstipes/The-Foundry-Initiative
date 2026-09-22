import type { Bootstrap } from "./types";

export function bootstrapFixture(): Bootstrap {
 return { bundle: { ...__FORGEOPS_BUNDLE__ }, mode: "synthetic-demo", sessionNonce: "memory-only", selectedContext: "", scope: { context: "", namespace: "", generation: 0 },
  contexts: ["dev", "prod"].map((name) => ({ name, clusterName: name, authInfoName: "synthetic", namespace: "" })),
  plugins: [
   { id: "forge.example", displayName: "Example", version: "0.1.0", sdkCompatibility: ">=0.1.0 <0.2.0", capabilities: ["example.status"], contributions: [{ id: "example.card", type: "dashboardCard", title: "Example", capability: "example.status" }] },
   { id: "forge.resources", displayName: "Resources", version: "0.1.0", sdkCompatibility: ">=0.1.0 <0.2.0", capabilities: ["resources.read"], contributions: [{ id: "resources.browser", type: "resourceBrowser", title: "Resources", capability: "resources.read" }] },
   { id: "forge.diagnostics", displayName: "Diagnostics", version: "0.1.0", sdkCompatibility: ">=0.1.0 <0.2.0", capabilities: ["pods.logs.read", "events.read", "command.preview"], contributions: [{ id: "diagnostics.pod", type: "resourceBrowser", title: "Diagnostics", capability: "pods.logs.read" }] },
  ],
 };
}
