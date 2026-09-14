import { analyzeYaml, formatYaml } from "./analyze.js";
import { buildLineDiff } from "./format-diff.js";
import { SAMPLE_YAML } from "./sample.js";
import { KUBERNETES_SCHEMA_VERSION } from "./schema-validation.js";
import { OWASP_PROFILE_VERSION, OWASP_SOURCE_COMMIT } from "./owasp-profile.js";
import { buildMarkdownReport } from "./report.js";
import "./styles.css";

const app = document.querySelector("#app");
let activeTab = "summary";
let inspectionMode = "kubernetes";
let currentFilename = "signalforge-sample.yaml";
let cleanSnapshot = SAMPLE_YAML;
let formatPreview = null;
let formatPreviewReturnFocus = null;
let reportPreview = null;
let reportPreviewReturnFocus = null;

app.innerHTML = [
  '<header class="topbar">',
  '  <div class="brand"><span class="brand-mark">F</span><div><strong>Forge YAML Workbench</strong><small>SignalForge · local analysis</small></div></div>',
  '  <div class="privacy"><span></span>Input stays inside the lab</div>',
  '</header>',
  '<main>',
  '  <section class="toolbar">',
  '    <div><h1 id="inspection-title">Kubernetes manifest inspection</h1><p id="inspection-description">Parse structure and review important fields before deployment.</p></div>',
  '    <div class="toolbar-controls">',
  '    <div class="mode-selector" role="group" aria-label="YAML inspection mode"><button class="mode active" data-mode="kubernetes" aria-pressed="true">Kubernetes</button><button class="mode" data-mode="general" aria-pressed="false">General YAML</button></div>',
  '    <div class="actions">',
  '      <input id="file-input" type="file" accept=".yaml,.yml,text/yaml,application/yaml" hidden />',
  '      <button id="upload" aria-keyshortcuts="Control+O Meta+O" title="Open file (Ctrl+O)">Open file</button><button id="sample">Load sample</button><button id="format" aria-keyshortcuts="Control+Shift+F Meta+Shift+F" title="Format (Ctrl+Shift+F)">Format</button><button id="generate-report">Generate report</button><button id="download" aria-keyshortcuts="Control+S Meta+S" title="Download YAML (Ctrl+S)">Download YAML</button><button id="clear" class="quiet">Clear</button>',
  '    </div>',
  '    <div id="action-status" class="action-status" role="status" aria-live="polite" aria-atomic="true">Ready</div>',
  '    </div>',
  '  </section>',
  '  <section class="workspace">',
  '    <div class="pane editor-pane">',
  '      <div class="pane-heading"><div><span class="eyebrow">INPUT</span><h2>YAML editor</h2></div><span id="line-count" class="muted"></span></div>',
  '      <textarea id="editor" spellcheck="false" aria-label="YAML editor"></textarea>',
  '    </div>',
  '    <div class="pane results-pane">',
  '      <div class="pane-heading"><div><span class="eyebrow">ANALYSIS</span><h2 id="report-title">Manifest report</h2></div><div id="status" class="status neutral"></div></div>',
  '      <div class="tabs" role="tablist"><button class="tab active" role="tab" aria-selected="true" data-tab="summary">Summary</button><button class="tab" role="tab" aria-selected="false" data-tab="validation">Validation <span id="finding-count"></span></button><button class="tab" role="tab" aria-selected="false" data-tab="tree">Tree</button></div>',
  '      <div id="results" class="results" aria-live="polite"></div>',
  '    </div>',
  '  </section>',
  '  <footer><span id="review-boundary">Syntax and bounded operational guidance</span><span id="next-step">Use server-side dry-run before applying.</span></footer>',
  '</main>',
  '<div id="format-preview" class="format-preview" hidden>',
  '  <section class="format-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="format-preview-title" aria-describedby="format-preview-description">',
  '    <header><div><span class="eyebrow">FORMAT PREVIEW</span><h2 id="format-preview-title">Review formatting changes</h2><p id="format-preview-description">The editor will not change until you apply this preview.</p></div><div id="format-preview-summary" class="format-preview-summary"></div></header>',
  '    <div class="diff-heading" aria-hidden="true"><span></span><span>Before</span><span>After</span><span>YAML</span></div>',
  '    <div id="format-diff" class="format-diff" tabindex="0"></div>',
  '    <footer><button id="format-cancel" class="quiet">Cancel</button><button id="format-apply">Apply formatting</button></footer>',
  '  </section>',
  '</div>',
  '<div id="report-preview" class="report-preview" hidden>',
  '  <section class="report-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="report-preview-title" aria-describedby="report-preview-description">',
  '    <header><div><span class="eyebrow">MARKDOWN REPORT</span><h2 id="report-preview-title">Review analysis report</h2><p id="report-preview-description">The report stays in browser memory until you explicitly copy or download it.</p></div><div id="report-preview-summary" class="report-preview-summary"></div></header>',
  '    <p class="report-export-boundary">Exported reports can contain resource names, namespaces, YAML paths, findings, and recommendations derived from your YAML. The complete source YAML is not included.</p>',
  '    <pre id="report-markdown" class="report-markdown" tabindex="0" aria-label="Generated Markdown report"></pre>',
  '    <footer><button id="report-cancel" class="quiet">Cancel</button><button id="report-copy">Copy Markdown</button><button id="report-download">Download .md</button></footer>',
  '  </section>',
  '</div>'
].join("");

const editor = document.querySelector("#editor");
editor.value = SAMPLE_YAML;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

function scalarText(value) {
  return value === null ? "null" : String(value);
}

function pills(items, emptyText = "None") {
  if (!items?.length) return '<span class="muted">' + emptyText + "</span>";
  return '<div class="pills">' + items.map((item) => "<span>" + escapeHtml(item) + "</span>").join("") + "</div>";
}

function field(label, value) {
  return '<div class="field"><dt>' + escapeHtml(label) + "</dt><dd>" + (value ?? '<span class="muted">Not set</span>') + "</dd></div>";
}

function containerCard(container) {
  const ports = container.ports.map((port) => (port.name ? port.name + " · " : "") + port.containerPort + "/" + port.protocol);
  const probeNames = Object.entries(container.probes).filter(([, enabled]) => enabled).map(([name]) => name);
  const requests = Object.entries(container.resources.requests || {}).map(([key, value]) => key + ": " + value);
  const limits = Object.entries(container.resources.limits || {}).map(([key, value]) => key + ": " + value);

  return [
    '<div class="container-card">',
    '  <div class="container-title"><span>' + escapeHtml(container.type) + "</span><strong>" + escapeHtml(container.name) + "</strong></div>",
    '  <dl class="field-grid">',
    field("Image", "<code>" + escapeHtml(container.imageRepository) + "</code>"),
    field(container.imageReferenceType === "digest" ? "Digest" : "Tag", "<code>" + escapeHtml(container.imageReference) + "</code>"),
    field("Ports", pills(ports)),
    field("Environment", container.envCount + " direct · " + container.envFromCount + " sources"),
    field("Probes", pills(probeNames, "None configured")),
    field("Requests", pills(requests)),
    field("Limits", pills(limits)),
    field("Mounts", pills(container.mounts)),
    "  </dl>",
    "</div>"
  ].join("");
}

function schemaBadge(schema) {
  const labels = {
    valid: "Schema valid",
    invalid: "Schema invalid",
    unsupported: "Schema unsupported",
    "schema-unavailable": "CRD schema unavailable",
    "not-evaluated": "Schema not evaluated"
  };
  return '<span class="schema-badge ' + escapeHtml(schema.status) + '">' +
    escapeHtml(labels[schema.status] || schema.status) + " · " + escapeHtml(schema.kubernetesVersion) + "</span>";
}

function fixGuidance(item) {
  if (!item.example && !item.caution && !item.standard) return "";
  const example = item.example ? [
    '<div class="guidance-heading"><b>Recommended YAML</b><button class="copy-guidance" data-example="' +
      escapeHtml(encodeURIComponent(item.example)) + '">Copy YAML</button></div>',
    '<pre><code>' + escapeHtml(item.example) + "</code></pre>"
  ].join("") : "";
  const caution = item.caution ? '<p class="guidance-caution"><b>Before applying:</b> ' + escapeHtml(item.caution) + "</p>" : "";
  const standards = item.standards?.length ? item.standards : (item.standard ? [item.standard] : []);
  const standard = standards.length ? '<p class="guidance-standard"><b>Security reference' +
    (standards.length === 1 ? ":</b> " : "s:</b> ") + standards.map((entry) => '<a href="' +
      escapeHtml(entry.url) + '" target="_blank" rel="noopener noreferrer">OWASP ' +
      escapeHtml(entry.id) + " · " + escapeHtml(entry.title) + "</a>").join(" · ") + "</p>" : "";
  return '<details class="fix-guidance"><summary>Fix guidance</summary><div>' + example + caution + standard + "</div></details>";
}

function owaspProfileView(items) {
  const labels = {
    direct: "Direct",
    partial: "Partial",
    "cluster-context-required": "Cluster context required"
  };
  return [
    '<section class="owasp-profile">',
    '<header><div><h3>OWASP Kubernetes Top 10:' + escapeHtml(OWASP_PROFILE_VERSION) + ' review profile</h3>',
    '<p>Coverage describes what this browser-local file review can observe. It is not a compliance score or pass/fail result.</p></div>',
    '<code title="Pinned OWASP source commit">' + escapeHtml(OWASP_SOURCE_COMMIT.slice(0, 7)) + '</code></header>',
    '<div class="owasp-profile-list">',
    items.map((item) => [
      '<article class="owasp-profile-item">',
      '<div><a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(item.id) + '</a>',
      '<strong>' + escapeHtml(item.title) + '</strong></div>',
      '<span class="coverage ' + escapeHtml(item.coverage) + '">' + escapeHtml(labels[item.coverage]) + '</span>',
      '<p>' + escapeHtml(item.evidence) + '</p>',
      '<small>' + escapeHtml(item.boundary) + '</small>',
      '</article>'
    ].join("")).join(""),
    '</div></section>'
  ].join("");
}

function messages(title, items, fallbackLevel) {
  return '<section class="messages"><h3>' + escapeHtml(title) + "</h3>" + items.map((item) => {
    const level = item.level || fallbackLevel;
    const path = item.path ? (item.line
      ? '<button class="message-path" data-line="' + item.line + '" data-column="' + (item.column || 1) +
        '" aria-label="Go to ' + escapeHtml(item.path) + ' in the YAML editor"><span>YAML path</span><code>' + escapeHtml(item.path) + "</code></button>"
      : '<div class="message-path"><span>YAML path</span><code>' + escapeHtml(item.path) + "</code></div>") : "";
    const suggestion = item.suggestion ? '<p class="message-suggestion"><b>Recommended change:</b> ' +
      escapeHtml(item.suggestion) + "</p>" : "";
    const location = item.line ? '<button class="message-location" data-line="' + item.line + '" data-column="' +
      (item.column || 1) + '">Line ' + item.line + (item.column ? ", column " + item.column : "") + "</button>" : "";
    return '<div class="message ' + level + '"><span>' + escapeHtml(level) + "</span><div><strong>" +
      escapeHtml(item.title || "Document " + item.document) + "</strong><p>" +
      escapeHtml(item.explanation || item.detail || item.message) + "</p>" + path + suggestion + fixGuidance(item) + location + "</div></div>";
  }).join("") + "</section>";
}

function announce(message, tone = "neutral") {
  const status = document.querySelector("#action-status");
  status.className = "action-status " + tone;
  status.textContent = message;
}

function diffRows(rows) {
  return rows.map((row) => {
    const marker = row.type === "added" ? "+" : (row.type === "removed" ? "−" : "");
    const label = row.type === "added" ? "Added line" : (row.type === "removed" ? "Removed line" : "Unchanged line");
    return '<div class="diff-row ' + row.type + '" aria-label="' + label + '">' +
      '<span class="diff-marker" aria-hidden="true">' + marker + "</span>" +
      '<span class="diff-line-number">' + (row.beforeNumber ?? "") + "</span>" +
      '<span class="diff-line-number">' + (row.afterNumber ?? "") + "</span>" +
      "<code>" + escapeHtml(row.text || " ") + "</code></div>";
  }).join("");
}

function openFormatPreview(before, after) {
  const diff = buildLineDiff(before, after);
  formatPreview = { before, after };
  formatPreviewReturnFocus = document.querySelector("#format");
  const summary = [diff.added + " added", diff.removed + " removed"];
  if (diff.newlineChange) summary.push("final newline " + diff.newlineChange);
  if (diff.lineEndingsChanged) summary.push("line endings normalized");
  if (diff.simplified) summary.push("simplified alignment");
  document.querySelector("#format-preview-summary").textContent = summary.join(" · ");
  document.querySelector("#format-diff").innerHTML = diffRows(diff.rows);
  document.querySelector("#format-preview").hidden = false;
  document.querySelector("#format-apply").focus();
  announce("Formatting preview ready");
}

function closeFormatPreview(message) {
  document.querySelector("#format-preview").hidden = true;
  document.querySelector("#format-diff").innerHTML = "";
  formatPreview = null;
  const returnFocus = formatPreviewReturnFocus;
  formatPreviewReturnFocus = null;
  if (returnFocus?.focus) returnFocus.focus();
  if (message) announce(message);
}

function openReportPreview(report) {
  reportPreview = report;
  reportPreviewReturnFocus = document.querySelector("#generate-report");
  document.querySelector("#report-preview-summary").textContent =
    report.documentCount + " document" + (report.documentCount === 1 ? "" : "s") + " · " +
    report.findingCount + " finding" + (report.findingCount === 1 ? "" : "s");
  document.querySelector("#report-markdown").textContent = report.markdown;
  document.querySelector("#report-preview").hidden = false;
  document.querySelector("#report-markdown").focus();
  announce("Markdown report ready for review");
}

function closeReportPreview(message, restoreFocus = true) {
  document.querySelector("#report-preview").hidden = true;
  document.querySelector("#report-markdown").textContent = "";
  reportPreview = null;
  const returnFocus = reportPreviewReturnFocus;
  reportPreviewReturnFocus = null;
  if (restoreFocus && returnFocus?.focus) returnFocus.focus();
  if (message) announce(message);
}

function invalidateReportPreview() {
  if (reportPreview) closeReportPreview(null, false);
}

function setActiveTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll(".tab").forEach((item) => {
    const selected = item.dataset.tab === activeTab;
    item.classList.toggle("active", selected);
    item.setAttribute("aria-selected", String(selected));
  });
}

function normalizedFilename(filename) {
  const safeName = String(filename || "manifest.yaml").split(/[\\/]/).pop() || "manifest.yaml";
  return /\.ya?ml$/i.test(safeName) ? safeName : safeName + ".yaml";
}

function focusEditorLocation(line, column = 1) {
  const lines = editor.value.split("\n");
  const lineIndex = Math.max(0, Math.min(Number(line) - 1, lines.length - 1));
  const lineStart = lines.slice(0, lineIndex).reduce((total, value) => total + value.length + 1, 0);
  const start = lineStart + Math.max(0, Math.min(Number(column) - 1, lines[lineIndex]?.length || 0));
  const end = lineStart + (lines[lineIndex]?.length || 0);
  editor.focus();
  editor.setSelectionRange(start, Math.max(start, end));

  const styles = window.getComputedStyle(editor);
  const fontSize = Number.parseFloat(styles.fontSize) || 16;
  const parsedLineHeight = Number.parseFloat(styles.lineHeight);
  const lineHeight = Number.isFinite(parsedLineHeight)
    ? (styles.lineHeight.endsWith("px") ? parsedLineHeight : parsedLineHeight * fontSize)
    : fontSize * 1.62;
  const centeredOffset = (editor.clientHeight - lineHeight) / 2;
  const maximumScroll = Math.max(0, editor.scrollHeight - editor.clientHeight);
  editor.scrollTop = Math.min(maximumScroll, Math.max(0, lineIndex * lineHeight - centeredOffset));
}

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const temporary = document.createElement("textarea");
  temporary.value = value;
  temporary.setAttribute("readonly", "");
  temporary.style.position = "fixed";
  temporary.style.opacity = "0";
  document.body.appendChild(temporary);
  temporary.select();
  document.execCommand("copy");
  temporary.remove();
}

function loadEditor(value, filename, message) {
  invalidateReportPreview();
  editor.value = value;
  currentFilename = normalizedFilename(filename);
  cleanSnapshot = value;
  render();
  announce(message, "success");
}

function summaryView(analysis) {
  if (analysis.errors.length) return messages("YAML could not be parsed", analysis.errors, "error");
  if (!analysis.documents.length) return '<div class="empty"><div>{ }</div><h3>Paste or open YAML</h3><p>The report updates as you type and supports multi-document files.</p></div>';

  if (analysis.mode === "general") {
    return analysis.documents.map((document) => {
      const shape = document.rootType === "mapping"
        ? document.entryCount + " top-level " + (document.entryCount === 1 ? "entry" : "entries")
        : (document.rootType === "sequence"
          ? document.entryCount + " top-level " + (document.entryCount === 1 ? "item" : "items")
          : "Scalar value");
      return [
        '<article class="resource-card general-card">',
        '  <header><span class="kind">' + escapeHtml(document.rootType) + '</span><div><h3>Document ' + document.index + '</h3><p>' + escapeHtml(shape) + '</p></div></header>',
        '  <dl class="field-grid">',
        document.rootType === "mapping" ? field("Top-level keys", pills(document.keys)) : "",
        document.rootType === "scalar" ? field("Value", "<code>" + escapeHtml(scalarText(document.value)) + "</code>") : "",
        '  </dl>',
        '</article>'
      ].join("");
    }).join("");
  }

  return analysis.documents.map((resource) => [
    '<article class="resource-card">',
    '  <header><span class="kind">' + escapeHtml(resource.kind) + '</span><div><h3>' + escapeHtml(resource.name) + '</h3><p>' + escapeHtml(resource.apiVersion) + " · " + escapeHtml(resource.namespace) + '</p></div><div class="resource-status">' + schemaBadge(resource.schema) + '<small>Document ' + resource.index + "</small></div></header>",
    '  <dl class="field-grid">',
    resource.replicas !== null ? field("Replicas", escapeHtml(resource.replicas)) : "",
    resource.serviceType ? field("Service type", escapeHtml(resource.serviceType)) : "",
    field("Labels", pills(resource.labels)),
    resource.selector.length ? field("Selector", pills(resource.selector)) : "",
    resource.containers.length ? field("Service account", escapeHtml(resource.serviceAccount)) : "",
    resource.volumes.length ? field("Volumes", pills(resource.volumes.map((volume) => volume.name + ": " + volume.type))) : "",
    resource.servicePorts.length ? field("Service ports", pills(resource.servicePorts.map((port) => (port.name || "unnamed") + ": " + port.port + " → " + (port.targetPort ?? port.port) + (port.nodePort ? " · node " + port.nodePort : "")))) : "",
    "  </dl>",
    resource.containers.map(containerCard).join(""),
    "</article>"
  ].join("")).join("");
}

function validationView(analysis) {
  const syntaxItems = [
    ...analysis.syntaxErrors.map((item) => ({ ...item, level: "error" })),
    ...analysis.syntaxWarnings.map((item) => ({ ...item, level: "warning" }))
  ];
  const documentItems = analysis.documentErrors.map((item) => ({ ...item, level: "error" }));
  const operational = analysis.documents.flatMap((resource) => resource.findings.map((item) => ({
    ...item,
    title: resource.kind + "/" + resource.name + ": " + item.title
  })));

  const schemaItems = analysis.mode === "kubernetes" ? analysis.documents.flatMap((resource) => {
    const identity = resource.kind + "/" + resource.name;
    if (resource.schema.status === "invalid") {
      return resource.schema.errors.map((item) => ({ ...item, title: identity + ": " + item.title }));
    }
    const levels = {
      valid: "valid",
      unsupported: "note",
      "schema-unavailable": "warning",
      "not-evaluated": "warning"
    };
    return [{
      level: levels[resource.schema.status] || "note",
      title: identity,
      explanation: resource.schema.message
    }];
  }) : [];

  if (!syntaxItems.length && !documentItems.length && !operational.length && !schemaItems.length) {
    const detail = analysis.mode === "general"
      ? "The YAML parsed successfully. Kubernetes operational and schema checks are disabled in General YAML mode."
      : "The YAML parsed and passed the Workbench's bounded review.";
    return '<div class="empty success"><div>✓</div><h3>No findings in the current checks</h3><p>' + escapeHtml(detail) + '</p></div>';
  }

  return (syntaxItems.length ? messages("YAML syntax", syntaxItems, "error") : "") +
    (documentItems.length ? messages("Kubernetes document structure", documentItems, "error") : "") +
    (operational.length ? messages("Deterministic operational review", operational, "warning") : "") +
    (schemaItems.length ? messages("Kubernetes schema · " + KUBERNETES_SCHEMA_VERSION, schemaItems, "note") : "") +
    (analysis.mode === "kubernetes" && analysis.owaspProfile.length ? owaspProfileView(analysis.owaspProfile) : "");
}

function treeNode(value, name = "root", depth = 0) {
  if (value === null || typeof value !== "object") {
    return '<div class="tree-leaf"><span>' + escapeHtml(name) + "</span><code>" + escapeHtml(scalarText(value)) + "</code></div>";
  }

  const entries = Object.entries(value);
  return '<details class="tree-node" ' + (depth < 2 ? "open" : "") + '><summary><span>' +
    escapeHtml(name) + "</span><em>" + (Array.isArray(value) ? "[" + entries.length + "]" : "{" + entries.length + "}") +
    "</em></summary><div>" + entries.map(([key, item]) => treeNode(item, key, depth + 1)).join("") + "</div></details>";
}

function treeView(analysis) {
  if (analysis.errors.length) return messages("YAML could not be parsed", analysis.errors, "error");
  if (!analysis.documents.length) return '<div class="empty"><div>⌘</div><h3>No document tree yet</h3></div>';
  return analysis.documents.map((document) => {
    const identity = analysis.mode === "kubernetes" ? document.kind + "/" + document.name : document.rootType;
    return '<article class="tree-card"><h3>Document ' + document.index + " · " + escapeHtml(identity) + "</h3>" +
      treeNode(document.raw) + "</article>";
  }).join("");
}

function render() {
  const source = editor.value;
  const analysis = analyzeYaml(source, inspectionMode);
  const schemaIssueCount = analysis.mode === "kubernetes" ? analysis.documents.reduce((total, document) =>
    total + (document.schema.status === "invalid" ? document.schema.errors.length : (document.schema.status === "valid" ? 0 : 1)), 0) : 0;
  const invalidSchemaCount = analysis.mode === "kubernetes" ? analysis.documents.reduce((total, document) =>
    total + (document.schema.status === "invalid" ? document.schema.errors.length : 0), 0) : 0;
  const findingCount = analysis.errors.length + analysis.warnings.length + schemaIssueCount +
    analysis.documents.reduce((total, document) => total + document.findings.length, 0);

  document.querySelector("#line-count").textContent = source ? source.split("\n").length + " lines" : "0 lines";
  document.querySelector("#finding-count").textContent = findingCount || "";

  const general = inspectionMode === "general";
  document.querySelector("#inspection-title").textContent = general ? "General YAML inspection" : "Kubernetes manifest inspection";
  document.querySelector("#inspection-description").textContent = general
    ? "Inspect mappings, sequences, and scalar YAML without Kubernetes-specific findings."
    : "Review syntax, deterministic operations, the pinned Kubernetes " + KUBERNETES_SCHEMA_VERSION + " schema, and OWASP Top 10:" + OWASP_PROFILE_VERSION + " coverage.";
  document.querySelector("#report-title").textContent = general ? "YAML report" : "Manifest report";
  document.querySelector("#review-boundary").textContent = general ? "Syntax and document structure" : "Syntax · operations · schema " + KUBERNETES_SCHEMA_VERSION + " · OWASP profile " + OWASP_PROFILE_VERSION;
  document.querySelector("#next-step").textContent = general ? "No Kubernetes checks in this mode." : "No admission or live-cluster checks. Use server-side dry-run before applying.";

  const status = document.querySelector("#status");
  if (!source.trim()) {
    status.className = "status neutral";
    status.textContent = "Waiting for YAML";
  } else if (analysis.errors.length || invalidSchemaCount) {
    status.className = "status error";
    status.textContent = analysis.errors.length
      ? analysis.errors.length + " YAML error" + (analysis.errors.length === 1 ? "" : "s")
      : invalidSchemaCount + " schema error" + (invalidSchemaCount === 1 ? "" : "s");
  } else {
    status.className = "status " + (findingCount ? "warning" : "valid");
    status.textContent = analysis.documents.length + " parsed document" + (analysis.documents.length === 1 ? "" : "s") +
      (findingCount ? " · " + findingCount + " finding" + (findingCount === 1 ? "" : "s") : " · no findings");
  }

  const views = { summary: summaryView, validation: validationView, tree: treeView };
  document.querySelector("#results").innerHTML = views[activeTab](analysis);
}

editor.addEventListener("input", () => {
  invalidateReportPreview();
  announce("Editing YAML");
  render();
});
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  setActiveTab(tab.dataset.tab);
  render();
}));
document.querySelectorAll(".mode").forEach((button) => button.addEventListener("click", () => {
  invalidateReportPreview();
  inspectionMode = button.dataset.mode;
  document.querySelectorAll(".mode").forEach((item) => {
    const selected = item.dataset.mode === inspectionMode;
    item.classList.toggle("active", selected);
    item.setAttribute("aria-pressed", String(selected));
  });
  render();
  announce((inspectionMode === "general" ? "General YAML" : "Kubernetes") + " mode selected", "success");
}));
document.querySelector("#sample").addEventListener("click", () => loadEditor(SAMPLE_YAML, "signalforge-sample.yaml", "Sample loaded"));
document.querySelector("#clear").addEventListener("click", () => {
  if (editor.value !== cleanSnapshot && !window.confirm("Discard your unsaved YAML changes?")) {
    announce("Clear cancelled");
    return;
  }
  invalidateReportPreview();
  editor.value = "";
  currentFilename = "manifest.yaml";
  cleanSnapshot = "";
  render();
  editor.focus();
  announce("Editor cleared", "success");
});
document.querySelector("#upload").addEventListener("click", () => document.querySelector("#file-input").click());
document.querySelector("#file-input").addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (file) loadEditor(await file.text(), file.name, file.name + " opened");
  event.target.value = "";
});
document.querySelector("#format").addEventListener("click", () => {
  const before = editor.value;
  if (!before.trim()) {
    announce("Nothing to format");
    return;
  }
  try {
    const after = formatYaml(before);
    if (after === before) {
      announce("Already formatted — no changes needed", "success");
    } else {
      openFormatPreview(before, after);
    }
  } catch {
    setActiveTab("validation");
    announce("Formatting failed — see Validation", "error");
  }
  render();
});
document.querySelector("#format-cancel").addEventListener("click", () => closeFormatPreview("Formatting cancelled"));
document.querySelector("#format-apply").addEventListener("click", () => {
  if (!formatPreview) return;
  editor.value = formatPreview.after;
  closeFormatPreview();
  render();
  editor.focus();
  announce("YAML formatted", "success");
});
function downloadText(value, type, filename) {
  const blob = new Blob([value], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

document.querySelector("#download").addEventListener("click", () => {
  if (!editor.value) {
    announce("Nothing to download");
    return;
  }
  downloadText(editor.value, "application/yaml", currentFilename);
  cleanSnapshot = editor.value;
  announce(currentFilename + " downloaded", "success");
});
document.querySelector("#generate-report").addEventListener("click", () => {
  const analysis = analyzeYaml(editor.value, inspectionMode);
  openReportPreview(buildMarkdownReport({ filename: currentFilename, analysis }));
});
document.querySelector("#report-cancel").addEventListener("click", () => closeReportPreview("Report cancelled"));
document.querySelector("#report-copy").addEventListener("click", async () => {
  if (!reportPreview) return;
  try {
    await copyText(reportPreview.markdown);
    announce("Markdown report copied", "success");
  } catch {
    announce("Could not copy automatically — use the preview to select the report", "error");
  }
});
document.querySelector("#report-download").addEventListener("click", () => {
  if (!reportPreview) return;
  downloadText(reportPreview.markdown, "text/markdown;charset=utf-8", reportPreview.filename);
  announce(reportPreview.filename + " downloaded", "success");
});
document.querySelector("#results").addEventListener("click", async (event) => {
  const copy = event.target.closest(".copy-guidance");
  if (copy) {
    try {
      await copyText(decodeURIComponent(copy.dataset.example));
      announce("Suggested YAML copied", "success");
    } catch {
      announce("Could not copy automatically — select the example manually", "error");
    }
    return;
  }
  const location = event.target.closest(".message-location, .message-path[data-line]");
  if (location) focusEditorLocation(location.dataset.line, location.dataset.column);
});
document.addEventListener("keydown", (event) => {
  if (reportPreview && event.key === "Escape") {
    event.preventDefault();
    closeReportPreview("Report cancelled");
    return;
  }
  if (reportPreview && event.key === "Tab") {
    const focusable = [...document.querySelectorAll("#report-preview [tabindex='0'], #report-preview button")];
    const current = focusable.indexOf(document.activeElement);
    const next = event.shiftKey
      ? (current <= 0 ? focusable.length - 1 : current - 1)
      : (current === focusable.length - 1 ? 0 : current + 1);
    event.preventDefault();
    focusable[next].focus();
    return;
  }
  if (reportPreview && (event.ctrlKey || event.metaKey)) {
    if (["o", "s", "f"].includes(event.key.toLowerCase())) event.preventDefault();
    return;
  }
  if (formatPreview && event.key === "Escape") {
    event.preventDefault();
    closeFormatPreview("Formatting cancelled");
    return;
  }
  if (formatPreview && event.key === "Tab") {
    const focusable = [...document.querySelectorAll("#format-preview [tabindex='0'], #format-preview button")];
    const current = focusable.indexOf(document.activeElement);
    const next = event.shiftKey
      ? (current <= 0 ? focusable.length - 1 : current - 1)
      : (current === focusable.length - 1 ? 0 : current + 1);
    event.preventDefault();
    focusable[next].focus();
    return;
  }
  if (formatPreview && (event.ctrlKey || event.metaKey)) {
    if (["o", "s", "f"].includes(event.key.toLowerCase())) event.preventDefault();
    return;
  }
  if (!(event.ctrlKey || event.metaKey)) return;
  if (event.key.toLowerCase() === "o") {
    event.preventDefault();
    document.querySelector("#upload").click();
  } else if (event.key.toLowerCase() === "s") {
    event.preventDefault();
    document.querySelector("#download").click();
  } else if (event.shiftKey && event.key.toLowerCase() === "f") {
    event.preventDefault();
    document.querySelector("#format").click();
  }
});

render();
