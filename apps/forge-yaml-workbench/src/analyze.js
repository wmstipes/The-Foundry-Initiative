import { LineCounter, parseAllDocuments } from "yaml";

const WORKLOADS = new Set(["Pod", "Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"]);
const SELECTOR_WORKLOADS = new Set(["Deployment", "StatefulSet", "DaemonSet", "ReplicaSet"]);

function object(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function podContext(resource) {
  if (resource.kind === "Pod") {
    return { spec: object(resource.spec), path: ".spec", labels: object(resource.metadata?.labels) };
  }
  if (resource.kind === "CronJob") {
    return {
      spec: object(resource.spec?.jobTemplate?.spec?.template?.spec),
      path: ".spec.jobTemplate.spec.template.spec",
      labels: object(resource.spec?.jobTemplate?.spec?.template?.metadata?.labels)
    };
  }
  if (WORKLOADS.has(resource.kind)) {
    return {
      spec: object(resource.spec?.template?.spec),
      path: ".spec.template.spec",
      labels: object(resource.spec?.template?.metadata?.labels)
    };
  }
  return { spec: {}, path: ".spec", labels: {} };
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

function finding(level, title, path, explanation, suggestion) {
  return { level, title, path, detail: explanation, explanation, suggestion };
}

function summarizeContainer(container, type, path) {
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
    securityContext: object(container.securityContext),
    path
  };
}

function findings(resource, containers, pod) {
  const items = [];
  const add = (...arguments_) => items.push(finding(...arguments_));

  if (!resource.apiVersion) add("error", "Missing apiVersion", ".apiVersion", "Kubernetes cannot identify the API group and version.", "Add the API version supported by the target cluster, such as apiVersion: v1.");
  if (!resource.kind) add("error", "Missing kind", ".kind", "Kubernetes cannot identify the resource type.", "Add the Kubernetes resource kind, such as kind: Deployment.");
  if (!resource.metadata?.name && !resource.metadata?.generateName) {
    add("error", "Missing metadata.name", ".metadata.name", "The resource has neither a fixed name nor a generated-name prefix.", "Set metadata.name or metadata.generateName.");
  }

  if (WORKLOADS.has(resource.kind) && containers.length === 0) {
    add("error", "No containers found", pod.path + ".containers", "This workload has no containers in its Pod template.", "Add at least one container under " + pod.path + ".containers.");
  }

  for (const container of containers) {
    if (!container.image || container.imageReference === "latest" || container.imageReference === "latest (implicit)") {
      add("warning", container.name + ": mutable image reference", container.path + ".image", "A missing or latest image reference can resolve to different content over time.", "Use a version tag or immutable digest for repeatable deployments.");
    }
    if (container.type === "container" && !container.probes.readiness) add("note", container.name + ": no readiness probe", container.path + ".readinessProbe", "Traffic may reach the container before it is ready.", "Add a readinessProbe that represents whether this container can receive traffic.");
    if (container.type === "container" && !container.probes.liveness) add("note", container.name + ": no liveness probe", container.path + ".livenessProbe", "Kubernetes cannot detect every stuck process.", "Add a livenessProbe only when the application has a reliable self-health signal.");
    if (Object.keys(object(container.resources.requests)).length === 0) add("warning", container.name + ": no resource requests", container.path + ".resources.requests", "Scheduling will not account for expected CPU and memory use.", "Set measured CPU and memory requests.");
    if (Object.keys(object(container.resources.limits)).length === 0) add("note", container.name + ": no resource limits", container.path + ".resources.limits", "The container has no explicit CPU or memory ceiling.", "Set an appropriate memory limit and evaluate whether a CPU limit fits the workload.");
    if (container.securityContext.privileged === true) add("warning", container.name + ": privileged container", container.path + ".securityContext.privileged", "Privileged mode grants broad host-level access.", "Remove privileged: true unless the workload has a documented host-level requirement.");
    if (container.securityContext.runAsUser === 0) add("warning", container.name + ": runs as root", container.path + ".securityContext.runAsUser", "UID 0 runs the container process as root.", "Use a non-zero runAsUser and set runAsNonRoot: true when the image supports it.");
    if (container.securityContext.allowPrivilegeEscalation !== false) add("note", container.name + ": privilege escalation not disabled", container.path + ".securityContext.allowPrivilegeEscalation", "The container does not explicitly prevent gaining additional process privileges.", "Set securityContext.allowPrivilegeEscalation: false.");
    if (container.securityContext.readOnlyRootFilesystem !== true) add("note", container.name + ": root filesystem is writable", container.path + ".securityContext.readOnlyRootFilesystem", "A writable image filesystem increases the container's mutation surface.", "Set readOnlyRootFilesystem: true and mount bounded writable volumes where required.");
    if (!array(container.securityContext.capabilities?.drop).includes("ALL")) add("note", container.name + ": Linux capabilities not fully dropped", container.path + ".securityContext.capabilities.drop", "The container does not explicitly drop every inherited Linux capability.", "Set securityContext.capabilities.drop to [ALL], then add back only documented requirements.");
    if (pod.spec.securityContext?.runAsNonRoot !== true && container.securityContext.runAsNonRoot !== true && container.securityContext.runAsUser == null) {
      add("note", container.name + ": non-root execution not required", container.path + ".securityContext.runAsNonRoot", "Neither the Pod nor container security context explicitly requires non-root execution.", "Set runAsNonRoot: true at the Pod or container level when the image supports it.");
    }
  }

  if (pod.spec.hostNetwork === true) add("warning", "Host networking enabled", pod.path + ".hostNetwork", "The Pod shares the node network namespace.", "Remove hostNetwork: true unless direct node networking is required and reviewed.");
  if (pod.spec.hostPID === true) add("warning", "Host PID namespace enabled", pod.path + ".hostPID", "The Pod can observe processes in the node PID namespace.", "Remove hostPID: true unless host process visibility is explicitly required.");
  if (pod.spec.hostIPC === true) add("warning", "Host IPC namespace enabled", pod.path + ".hostIPC", "The Pod shares the node IPC namespace.", "Remove hostIPC: true unless host IPC access is explicitly required.");
  array(pod.spec.volumes).forEach((volume, index) => {
    if (volume.hostPath) add("warning", "HostPath volume present", pod.path + ".volumes[" + index + "].hostPath", "The Pod directly accesses a node filesystem path.", "Prefer a PVC, ConfigMap, Secret, or bounded emptyDir when possible.");
  });
  if (WORKLOADS.has(resource.kind) && pod.spec.automountServiceAccountToken !== false) {
    add("note", "ServiceAccount token may be mounted", pod.path + ".automountServiceAccountToken", "The default token mount may provide Kubernetes API credentials the workload does not need.", "Set automountServiceAccountToken: false when the workload does not call the Kubernetes API.");
  }

  if (resource.kind === "Service" && Object.keys(object(resource.spec?.selector)).length === 0 && resource.spec?.type !== "ExternalName") {
    add("warning", "Service has no selector", ".spec.selector", "Kubernetes will not automatically select Pods for this Service.", "Add a selector or document how EndpointSlices are managed separately.");
  }

  if (SELECTOR_WORKLOADS.has(resource.kind)) {
    const selector = object(resource.spec?.selector?.matchLabels);
    const expressions = array(resource.spec?.selector?.matchExpressions);
    const templateLabels = pod.labels;
    if (Object.keys(selector).length === 0 && expressions.length === 0) {
      add("error", "Workload has no selector terms", ".spec.selector", "The controller needs a stable selector for its Pod template.", "Set matchLabels or matchExpressions so the selector matches the labels under .spec.template.metadata.labels.");
    } else if (!selectorMatches(selector, templateLabels)) {
      add("error", "Selector does not match Pod template labels", ".spec.selector.matchLabels", "At least one selector label differs from or is absent in the Pod template.", "Make every matchLabels entry identical to a label under .spec.template.metadata.labels.");
    }
  }

  return items;
}

function selectorMatches(selector, candidateLabels) {
  return Object.entries(object(selector)).every(([key, value]) => candidateLabels[key] === value);
}

function addBundleFindings(documents) {
  const workloads = documents.filter((document) => WORKLOADS.has(document.kind));

  documents.forEach((document, documentIndex) => {
    const duplicate = document.raw.metadata?.name ? documents.findIndex((candidate, candidateIndex) => candidateIndex < documentIndex &&
      candidate.raw.metadata?.name &&
      candidate.apiVersion === document.apiVersion && candidate.kind === document.kind &&
      candidate.namespace === document.namespace && candidate.name === document.name) : -1;
    if (duplicate >= 0) {
      document.findings.unshift(finding(
        "error",
        "Duplicate resource identity",
        ".metadata.name",
        "Document " + documents[duplicate].index + " already defines the same apiVersion, kind, namespace, and name.",
        "Remove one definition or give the resources distinct identities."
      ));
    }

    if (document.kind !== "Service" || document.serviceType === "ExternalName") return;
    const selector = object(document.raw.spec?.selector);
    if (Object.keys(selector).length === 0) return;
    const sameNamespace = workloads.filter((workload) => workload.namespace === document.namespace);
    if (sameNamespace.length === 0) return;
    const matches = sameNamespace.filter((workload) => selectorMatches(selector, workload.podLabels));
    if (matches.length === 0) {
      document.findings.push(finding(
        "warning",
        "Service selector matches no workload in this file",
        ".spec.selector",
        "None of the included workload Pod labels satisfy this Service selector.",
        "Align the Service selector with the intended workload's Pod-template labels."
      ));
      return;
    }

    const portNames = new Set(matches.flatMap((workload) => workload.containers.flatMap((container) =>
      container.ports.map((port) => port.name).filter(Boolean))));
    document.servicePorts.forEach((port, index) => {
      if (typeof port.targetPort === "string" && !portNames.has(port.targetPort)) {
        document.findings.push(finding(
          "warning",
          "Named targetPort is not exposed by the selected workload",
          ".spec.ports[" + index + "].targetPort",
          "No selected container declares a port named " + port.targetPort + ".",
          "Use an existing container port name or a numeric targetPort."
        ));
      }
    });
  });
}

export function summarizeResource(resource, index) {
  const spec = object(resource.spec);
  const metadata = object(resource.metadata);
  const pod = podContext(resource);
  const containers = [
    ...array(pod.spec.initContainers).map((container, index) => summarizeContainer(container, "init container", pod.path + ".initContainers[" + index + "]")),
    ...array(pod.spec.containers).map((container, index) => summarizeContainer(container, "container", pod.path + ".containers[" + index + "]"))
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
    serviceAccount: pod.spec.serviceAccountName || "default",
    containers,
    volumes: array(pod.spec.volumes).map((volume) => ({
      name: volume.name,
      type: Object.keys(volume).find((key) => key !== "name") || "unknown"
    })),
    findings: findings(resource, containers, pod),
    podLabels: pod.labels,
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

  addBundleFindings(result.documents);

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
