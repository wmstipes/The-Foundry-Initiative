import { LineCounter, parseAllDocuments } from "yaml";

const WORKLOADS = new Set(["Pod", "Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"]);

function object(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function podSpec(resource) {
  if (resource.kind === "Pod") return object(resource.spec);
  if (resource.kind === "CronJob") return object(resource.spec?.jobTemplate?.spec?.template?.spec);
  if (WORKLOADS.has(resource.kind)) return object(resource.spec?.template?.spec);
  return {};
}

export function splitImage(image = "") {
  const digestAt = image.indexOf("@sha256:");
  if (digestAt >= 0) {
    return { repository: image.slice(0, digestAt), reference: image.slice(digestAt + 1), type: "digest" };
  }

  const slashAt = image.lastIndexOf("/");
  const colonAt = image.lastIndexOf(":");
  if (colonAt > slashAt) {
    return { repository: image.slice(0, colonAt), reference: image.slice(colonAt + 1), type: "tag" };
  }

  return { repository: image, reference: "latest (implicit)", type: "tag" };
}

function labels(value) {
  return Object.entries(object(value)).map(([key, item]) => key + "=" + item);
}

function summarizeContainer(container, type) {
  const image = splitImage(container.image || "");
  return {
    type,
    name: container.name || "unnamed",
    image: container.image || "not set",
    imageRepository: image.repository || "not set",
    imageReference: image.reference,
    imageReferenceType: image.type,
    ports: array(container.ports).map((port) => ({
      name: port.name || "",
      containerPort: port.containerPort,
      protocol: port.protocol || "TCP"
    })),
    envCount: array(container.env).length,
    envFromCount: array(container.envFrom).length,
    mounts: array(container.volumeMounts).map((mount) => mount.name + " → " + mount.mountPath),
    resources: object(container.resources),
    probes: {
      startup: Boolean(container.startupProbe),
      readiness: Boolean(container.readinessProbe),
      liveness: Boolean(container.livenessProbe)
    },
    securityContext: object(container.securityContext)
  };
}

function findings(resource, containers, spec) {
  const items = [];
  const add = (level, title, detail) => items.push({ level, title, detail });

  if (!resource.apiVersion) add("error", "Missing apiVersion", "Kubernetes cannot identify the API group and version.");
  if (!resource.kind) add("error", "Missing kind", "Kubernetes cannot identify the resource type.");
  if (!resource.metadata?.name && !resource.metadata?.generateName) {
    add("error", "Missing metadata.name", "Set a resource name or generateName prefix.");
  }

  if (WORKLOADS.has(resource.kind) && containers.length === 0) {
    add("error", "No containers found", "This workload has no containers in its Pod template.");
  }

  for (const container of containers) {
    if (!container.image || container.imageReference === "latest" || container.imageReference === "latest (implicit)") {
      add("warning", container.name + ": mutable image reference", "Use a version tag or immutable digest for repeatable deployments.");
    }
    if (!container.probes.readiness) add("note", container.name + ": no readiness probe", "Traffic may reach the container before it is ready.");
    if (!container.probes.liveness) add("note", container.name + ": no liveness probe", "Kubernetes cannot detect every stuck process.");
    if (!container.resources.requests) add("warning", container.name + ": no resource requests", "Scheduling will not account for expected CPU and memory use.");
    if (!container.resources.limits) add("note", container.name + ": no resource limits", "The container has no explicit CPU or memory ceiling.");
    if (container.securityContext.privileged === true) add("warning", container.name + ": privileged container", "This grants broad host-level access.");
    if (container.securityContext.runAsUser === 0) add("warning", container.name + ": runs as root", "Prefer a non-root user when supported.");
  }

  if (spec.hostNetwork === true) add("warning", "Host networking enabled", "The Pod shares the node network namespace.");
  if (array(spec.volumes).some((volume) => volume.hostPath)) add("warning", "HostPath volume present", "The Pod directly accesses a node filesystem path.");
  if (WORKLOADS.has(resource.kind) && spec.automountServiceAccountToken !== false) {
    add("note", "ServiceAccount token may be mounted", "Disable token mounting when the workload does not call the Kubernetes API.");
  }

  if (resource.kind === "Service" && Object.keys(object(resource.spec?.selector)).length === 0 && resource.spec?.type !== "ExternalName") {
    add("warning", "Service has no selector", "Endpoints must be managed separately for this Service.");
  }

  return items;
}

export function summarizeResource(resource, index) {
  const spec = object(resource.spec);
  const metadata = object(resource.metadata);
  const pod = podSpec(resource);
  const containers = [
    ...array(pod.initContainers).map((container) => summarizeContainer(container, "init container")),
    ...array(pod.containers).map((container) => summarizeContainer(container, "container"))
  ];

  return {
    index,
    apiVersion: resource.apiVersion || "not set",
    kind: resource.kind || "Unknown",
    name: metadata.name || metadata.generateName || "unnamed",
    namespace: metadata.namespace || (resource.kind === "Namespace" ? "cluster-scoped" : "default / unspecified"),
    labels: labels(metadata.labels),
    annotations: labels(metadata.annotations),
    replicas: Number.isInteger(spec.replicas) ? spec.replicas : null,
    selector: labels(spec.selector?.matchLabels || spec.selector),
    serviceType: resource.kind === "Service" ? spec.type || "ClusterIP" : null,
    servicePorts: resource.kind === "Service" ? array(spec.ports) : [],
    serviceAccount: pod.serviceAccountName || "default",
    containers,
    volumes: array(pod.volumes).map((volume) => ({
      name: volume.name,
      type: Object.keys(volume).find((key) => key !== "name") || "unknown"
    })),
    findings: findings(resource, containers, pod),
    raw: resource
  };
}

export function analyzeYaml(source) {
  if (!source.trim()) return { documents: [], errors: [], warnings: [] };

  const lineCounter = new LineCounter();
  const parsed = parseAllDocuments(source, { lineCounter, prettyErrors: true, uniqueKeys: true });
  const result = { documents: [], errors: [], warnings: [] };

  const diagnostic = (item, parsedDocument, documentNumber) => {
    const position = item.linePos?.[0] || lineCounter.linePos(item.pos?.[0] ?? parsedDocument.range?.[0] ?? 0);
    return {
      document: documentNumber,
      message: item.message,
      line: position?.line,
      column: position?.col
    };
  };

  parsed.forEach((document, index) => {
    const documentNumber = index + 1;
    document.errors.forEach((error) => result.errors.push(diagnostic(error, document, documentNumber)));
    document.warnings.forEach((warning) => result.warnings.push(diagnostic(warning, document, documentNumber)));

    if (document.errors.length === 0 && document.contents !== null) {
      const value = document.toJS({ maxAliasCount: 100 });
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        const position = lineCounter.linePos(document.range?.[0] ?? 0);
        result.errors.push({
          document: documentNumber,
          message: "A Kubernetes manifest must be a YAML mapping/object at its root.",
          line: position.line,
          column: position.col
        });
      } else {
        result.documents.push(summarizeResource(value, documentNumber));
      }
    }
  });

  return result;
}

export function formatYaml(source) {
  const parsed = parseAllDocuments(source, { prettyErrors: true, uniqueKeys: true });
  const error = parsed.flatMap((document) => document.errors)[0];
  if (error) throw error;

  const output = parsed
    .filter((document) => document.contents !== null)
    .map((document) => {
      const clone = document.clone();
      clone.directives.docStart = false;
      return clone.toString({ collectionStyle: "block", indent: 2, lineWidth: 0 }).trimEnd();
    })
    .join("\n---\n");

  return output ? output + "\n" : "";
}
