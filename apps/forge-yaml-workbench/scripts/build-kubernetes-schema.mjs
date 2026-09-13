import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const KUBERNETES_VERSION = "v1.36.4";
const SOURCE_URL = `https://raw.githubusercontent.com/kubernetes/kubernetes/${KUBERNETES_VERSION}/api/openapi-spec/swagger.json`;
const SOURCE_SHA256 = "dcede2063da1d7ad62ecb5af8adb6d7fabd0b52385a7fa0048afb491dac90450";
const SUPPORTED_DEFINITIONS = [
  "io.k8s.api.apps.v1.DaemonSet",
  "io.k8s.api.apps.v1.Deployment",
  "io.k8s.api.apps.v1.ReplicaSet",
  "io.k8s.api.apps.v1.StatefulSet",
  "io.k8s.api.batch.v1.CronJob",
  "io.k8s.api.batch.v1.Job",
  "io.k8s.api.core.v1.ConfigMap",
  "io.k8s.api.core.v1.Namespace",
  "io.k8s.api.core.v1.Pod",
  "io.k8s.api.core.v1.Secret",
  "io.k8s.api.core.v1.Service",
  "io.k8s.api.core.v1.ServiceAccount"
];

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const appDirectory = path.resolve(scriptDirectory, "..");
const sourcePath = process.argv[2];
const outputPath = path.join(appDirectory, "src", "schema", `kubernetes-${KUBERNETES_VERSION}.json`);

if (!sourcePath) {
  throw new Error(`Usage: npm run schema:build -- /path/to/swagger.json\nPinned source: ${SOURCE_URL}`);
}

const source = await readFile(path.resolve(sourcePath));
const actualSha256 = createHash("sha256").update(source).digest("hex");
if (actualSha256 !== SOURCE_SHA256) {
  throw new Error(`Pinned source checksum mismatch: expected ${SOURCE_SHA256}, received ${actualSha256}`);
}

const swagger = JSON.parse(source);
const definitions = swagger.definitions || {};
const selected = new Set();

function normalizeSchema(value) {
  if (Array.isArray(value)) return value.map(normalizeSchema);
  if (!value || typeof value !== "object") return value;

  const normalized = Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeSchema(item)]));
  if (normalized.format === "int-or-string") {
    delete normalized.type;
    delete normalized.format;
    normalized.anyOf = [{ type: "integer" }, { type: "string" }];
  }
  if (normalized.properties && normalized.additionalProperties === undefined && normalized["x-kubernetes-preserve-unknown-fields"] !== true) {
    normalized.additionalProperties = false;
  }
  return normalized;
}

function includeDefinition(name) {
  if (selected.has(name)) return;
  const schema = definitions[name];
  if (!schema) throw new Error(`Missing referenced definition: ${name}`);
  selected.add(name);
  const serialized = JSON.stringify(schema);
  for (const match of serialized.matchAll(/#\/definitions\/([^"\\]+)/g)) includeDefinition(match[1]);
}

SUPPORTED_DEFINITIONS.forEach(includeDefinition);

const resources = {};
for (const definitionName of SUPPORTED_DEFINITIONS) {
  const identities = definitions[definitionName]["x-kubernetes-group-version-kind"] || [];
  for (const identity of identities) {
    const apiVersion = identity.group ? `${identity.group}/${identity.version}` : identity.version;
    resources[`${apiVersion}|${identity.kind}`] = definitionName;
  }
}

const builtInGroups = new Set([""]);
for (const schema of Object.values(definitions)) {
  for (const identity of schema["x-kubernetes-group-version-kind"] || []) builtInGroups.add(identity.group || "");
}

const bundle = {
  kubernetesVersion: KUBERNETES_VERSION,
  source: SOURCE_URL,
  sourceSha256: SOURCE_SHA256,
  supportedResources: Object.fromEntries(Object.entries(resources).sort(([left], [right]) => left.localeCompare(right))),
  builtInGroups: [...builtInGroups].sort(),
  definitions: Object.fromEntries([...selected].sort().map((name) => [name, normalizeSchema(definitions[name])]))
};

await writeFile(outputPath, `${JSON.stringify(bundle)}\n`);
console.log(`Wrote ${path.relative(appDirectory, outputPath)} with ${Object.keys(resources).length} resources and ${selected.size} definitions.`);
