import type { Bootstrap, PluginManifest } from "./types";

const supported = [
  { id: "forge.example", capabilities: ["example.status"], contribution: { id: "example.card", type: "dashboardCard", capability: "example.status" } },
  { id: "forge.resources", capabilities: ["resources.read"], contribution: { id: "resources.browser", type: "resourceBrowser", capability: "resources.read" } },
  { id: "forge.diagnostics", capabilities: ["pods.logs.read", "events.read", "command.preview"], contribution: { id: "diagnostics.pod", type: "resourceBrowser", capability: "pods.logs.read" } },
];

export function validateCompatibility(data: Bootstrap): void {
  const fail = () => { throw new Error("Incompatible Console bundle. Restart with core and browser built from the same source."); };
  if (!data?.bundle || data.bundle.protocol !== __FORGEOPS_BUNDLE__.protocol || data.bundle.sourceDigest !== __FORGEOPS_BUNDLE__.sourceDigest) fail();
  if (!Array.isArray(data.plugins) || data.plugins.length !== supported.length) fail();
  for (const expected of supported) {
    const matches = data.plugins.filter((p: PluginManifest) => p?.id === expected.id);
    if (matches.length !== 1) fail();
    const plugin = matches[0];
    if (plugin.version !== "0.1.0" || plugin.sdkCompatibility !== ">=0.1.0 <0.2.0" || !Array.isArray(plugin.capabilities) || plugin.capabilities.length !== expected.capabilities.length || !expected.capabilities.every((c) => plugin.capabilities.includes(c))) fail();
    if (!Array.isArray(plugin.contributions) || plugin.contributions.length !== 1) fail();
    const contribution = plugin.contributions[0];
    if (!contribution || contribution.id !== expected.contribution.id || contribution.type !== expected.contribution.type || contribution.capability !== expected.contribution.capability) fail();
  }
}
