function markdownText(value) {
  return String(value ?? "")
    .replace(/[\\\`*_[\]{}<>#+.!|()-]/g, "\\$&")
    .replace(/\r?\n/g, " ");
}

function codeSpan(value) {
  const text = String(value ?? "").replace(/\r?\n/g, " ");
  const runs = text.match(/`+/g) || [];
  const fence = "`".repeat(Math.max(1, ...runs.map((run) => run.length + 1)));
  const padding = /^\s|\s$/.test(text) ? " " : "";
  return fence + padding + text + padding + fence;
}

function fencedCode(value, language = "") {
  const text = String(value ?? "").replace(/\r\n?/g, "\n").replace(/\n+$/, "");
  const runs = text.match(/`+/g) || [];
  const fence = "`".repeat(Math.max(3, ...runs.map((run) => run.length + 1)));
  return fence + language + "\n" + text + "\n" + fence;
}

function listValue(items, fallback = "None") {
  return items?.length ? items.map((item) => codeSpan(item)).join(", ") : fallback;
}

function locationText(item) {
  if (!item?.line) return null;
  return "Line " + item.line + (item.column ? ", column " + item.column : "");
}

function findingBlock(item, fallbackTitle) {
  const lines = ["### " + markdownText(String(item.level || "note").toUpperCase()) + " — " +
    markdownText(item.title || fallbackTitle || "Finding")];

  if (item.path) lines.push("- **YAML path:** " + codeSpan(item.path));
  const location = locationText(item);
  if (location) lines.push("- **Location:** " + markdownText(location));

  const explanation = item.explanation || item.detail || item.message;
  if (explanation) lines.push("", markdownText(explanation));
  if (item.suggestion) lines.push("", "**Recommended change:** " + markdownText(item.suggestion));
  if (item.example) lines.push("", "**Example YAML:**", "", fencedCode(item.example, "yaml"));
  if (item.caution) lines.push("", "**Before applying:** " + markdownText(item.caution));

  const standards = item.standards?.length ? item.standards : (item.standard ? [item.standard] : []);
  if (standards.length) {
    lines.push("", "**Security references:**");
    standards.forEach((standard) => {
      lines.push("- [" + markdownText("OWASP " + standard.id + " — " + standard.title) + "](" + standard.url + ")");
    });
  }

  return lines.join("\n");
}

function diagnosticsSection(title, items, level) {
  if (!items.length) return "";
  return [
    "## " + title,
    "",
    ...items.map((item) => findingBlock({ ...item, level }, "Document " + item.document)).join("\n\n").split("\n")
  ].join("\n");
}

function kubernetesDocument(document) {
  const lines = [
    "## Document " + document.index + " — " + markdownText(document.kind + "/" + document.name),
    "",
    "- **API version:** " + codeSpan(document.apiVersion),
    "- **Namespace:** " + codeSpan(document.namespace),
    "- **Schema:** " + markdownText(document.schema?.status || "not evaluated")
  ];

  if (document.replicas !== null) lines.push("- **Replicas:** " + document.replicas);
  if (document.serviceType) lines.push("- **Service type:** " + codeSpan(document.serviceType));
  if (document.labels?.length) lines.push("- **Labels:** " + listValue(document.labels));
  if (document.selector?.length) lines.push("- **Selector:** " + listValue(document.selector));
  if (document.containers?.length) lines.push("- **Service account:** " + codeSpan(document.serviceAccount));
  if (document.volumes?.length) {
    lines.push("- **Volumes:** " + listValue(document.volumes.map((volume) => volume.name + ": " + volume.type)));
  }
  if (document.servicePorts?.length) {
    lines.push("- **Service ports:** " + listValue(document.servicePorts.map((port) =>
      (port.name || "unnamed") + ": " + port.port + " -> " + (port.targetPort ?? port.port) +
      (port.nodePort ? " (node " + port.nodePort + ")" : ""))));
  }

  document.containers?.forEach((container) => {
    lines.push(
      "",
      "### " + markdownText(container.type + " — " + container.name),
      "",
      "- **Image:** " + codeSpan(container.image),
      "- **Ports:** " + listValue(container.ports.map((port) =>
        (port.name ? port.name + " — " : "") + port.containerPort + "/" + port.protocol)),
      "- **Probes:** " + listValue(Object.entries(container.probes)
        .filter(([, enabled]) => enabled)
        .map(([name]) => name), "None configured"),
      "- **Resource requests:** " + listValue(Object.entries(container.resources.requests || {})
        .map(([key, value]) => key + ": " + value)),
      "- **Resource limits:** " + listValue(Object.entries(container.resources.limits || {})
        .map(([key, value]) => key + ": " + value))
    );
  });

  return lines.join("\n");
}

function generalDocument(document) {
  const lines = [
    "## Document " + document.index + " — " + markdownText(document.rootType),
    "",
    "- **Root type:** " + markdownText(document.rootType)
  ];
  if (document.rootType === "mapping") {
    lines.push("- **Top-level entries:** " + document.entryCount);
    lines.push("- **Top-level keys:** " + listValue(document.keys));
  } else if (document.rootType === "sequence") {
    lines.push("- **Top-level items:** " + document.entryCount);
  } else {
    lines.push("- **Scalar value:** " + codeSpan(document.value === null ? "null" : document.value));
  }
  return lines.join("\n");
}

function operationalFindings(analysis) {
  return analysis.documents.flatMap((document) => document.findings.map((item) => ({
    ...item,
    title: document.kind + "/" + document.name + ": " + item.title
  })));
}

function schemaIssueCount(analysis) {
  if (analysis.mode !== "kubernetes") return 0;
  return analysis.documents.reduce((total, document) =>
    total + (document.schema?.status === "invalid"
      ? document.schema.errors.length
      : (document.schema?.status === "valid" ? 0 : 1)), 0);
}

export function reportFindingCount(analysis) {
  return analysis.errors.length + analysis.warnings.length + schemaIssueCount(analysis) +
    analysis.documents.reduce((total, document) => total + document.findings.length, 0);
}

export function reportFilename(sourceFilename) {
  const leaf = String(sourceFilename || "manifest.yaml").split(/[\\/]/).pop() || "manifest.yaml";
  const stem = leaf.replace(/\.ya?ml$/i, "") || "manifest";
  const safeStem = stem
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "-")
    .replace(/[. ]+$/g, "")
    .slice(0, 120) || "manifest";
  return safeStem + "-report.md";
}

export function buildMarkdownReport({ filename, analysis }) {
  if (!analysis || !Array.isArray(analysis.documents)) {
    throw new TypeError("A Workbench analysis result is required.");
  }

  const sourceName = String(filename || "manifest.yaml").split(/[\\/]/).pop() || "manifest.yaml";
  const kubernetes = analysis.mode === "kubernetes";
  const findingCount = reportFindingCount(analysis);
  const lines = [
    "# Forge YAML Workbench Analysis Report",
    "",
    "- **Source:** " + codeSpan(sourceName),
    "- **Inspection mode:** " + (kubernetes ? "Kubernetes" : "General YAML"),
    "- **Parsed documents:** " + analysis.documents.length,
    "- **Findings:** " + findingCount,
    "",
    "> Generated locally in browser memory. This report can contain resource names, namespaces, YAML paths, findings, and recommendations derived from the supplied YAML. The complete source YAML is not included.",
    "",
    "# Document Summary",
    ""
  ];

  if (!analysis.documents.length) {
    lines.push("No YAML documents were parsed.");
  } else {
    lines.push(analysis.documents.map(kubernetesDocument).join("\n\n"));
  }

  const syntaxErrors = diagnosticsSection("YAML Syntax Errors", analysis.syntaxErrors || [], "error");
  const syntaxWarnings = diagnosticsSection("YAML Syntax Warnings", analysis.syntaxWarnings || [], "warning");
  if (syntaxErrors) lines.push("", syntaxErrors);
  if (syntaxWarnings) lines.push("", syntaxWarnings);

  if (kubernetes) {
    const documentErrors = diagnosticsSection("Kubernetes Document Structure", analysis.documentErrors || [], "error");
    if (documentErrors) lines.push("", documentErrors);

    const operational = operationalFindings(analysis);
    lines.push("", "# Kubernetes Review", "");
    if (operational.length) {
      lines.push("## Deterministic Operational Findings", "",
        operational.map((item) => findingBlock(item)).join("\n\n"));
    } else {
      lines.push("## Deterministic Operational Findings", "", "No findings in the current deterministic checks.");
    }

    lines.push("", "## Kubernetes Schema Results", "");
    if (!analysis.documents.length) {
      lines.push("No parsed Kubernetes resources were available for schema evaluation.");
    } else {
      analysis.documents.forEach((document) => {
        lines.push("### " + markdownText(document.kind + "/" + document.name), "",
          "- **Status:** " + markdownText(document.schema.status),
          "- **Schema version:** " + codeSpan(document.schema.kubernetesVersion),
          "", markdownText(document.schema.message));
        document.schema.errors.forEach((item) => {
          lines.push("", findingBlock({ ...item, level: "error" }, "Schema mismatch"));
        });
        lines.push("");
      });
      while (lines.at(-1) === "") lines.pop();
    }

    lines.push("", "## OWASP Kubernetes Top 10:" +
      markdownText(analysis.owaspProfile?.[0]?.id?.split(":")[1] || "2025") + " Review Profile", "",
      "Coverage describes browser-local visibility into the supplied YAML. It is not a compliance score or pass/fail result.", "");
    (analysis.owaspProfile || []).forEach((item) => {
      lines.push("### " + markdownText(item.id + " — " + item.title), "",
        "- **Coverage:** " + markdownText(item.coverage),
        "- **Manifest-local evidence:** " + markdownText(item.evidence),
        "- **Boundary:** " + markdownText(item.boundary),
        "- **Pinned reference:** [" + markdownText("OWASP " + item.id) + "](" + item.url + ")",
        "");
    });
    while (lines.at(-1) === "") lines.pop();

    lines.push("", "# Limitations and Next Step", "",
      "- This is deterministic, browser-local file analysis—not API-server admission validation or a compliance assessment.",
      "- The Workbench does not contact Kubernetes, evaluate admission policies, apply defaulting or conversion, discover installed APIs, or retrieve CRD schemas.",
      "- Review every recommendation in workload and cluster context.",
      "- Use repository validation and Kubernetes server-side dry-run before applying a manifest.");
  } else {
    lines.push("", "# Limitations", "",
      "- General YAML mode reports syntax and document structure only.",
      "- Kubernetes operational, schema, OWASP, admission, and live-cluster checks are not performed.",
      "- The Workbench does not send the YAML or this report to a backend.");
  }

  return {
    markdown: lines.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd() + "\n",
    filename: reportFilename(sourceName),
    documentCount: analysis.documents.length,
    findingCount
  };
}
