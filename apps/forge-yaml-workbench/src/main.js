import { analyzeYaml, formatYaml } from "./analyze.js";
import { SAMPLE_YAML } from "./sample.js";
import "./styles.css";

const app = document.querySelector("#app");
let activeTab = "summary";

app.innerHTML = [
  '<header class="topbar">',
  '  <div class="brand"><span class="brand-mark">F</span><div><strong>Forge YAML Workbench</strong><small>SignalForge · local analysis</small></div></div>',
  '  <div class="privacy"><span></span>Input stays inside the lab</div>',
  '</header>',
  '<main>',
  '  <section class="toolbar">',
  '    <div><h1>Kubernetes manifest inspection</h1><p>Parse structure and review important fields before deployment.</p></div>',
  '    <div class="actions">',
  '      <input id="file-input" type="file" accept=".yaml,.yml,text/yaml,application/yaml" hidden />',
  '      <button id="upload">Open file</button><button id="sample">Load sample</button><button id="format">Format</button><button id="download">Download</button><button id="clear" class="quiet">Clear</button>',
  '    </div>',
  '  </section>',
  '  <section class="workspace">',
  '    <div class="pane editor-pane">',
  '      <div class="pane-heading"><div><span class="eyebrow">INPUT</span><h2>YAML editor</h2></div><span id="line-count" class="muted"></span></div>',
  '      <textarea id="editor" spellcheck="false" aria-label="YAML editor"></textarea>',
  '    </div>',
  '    <div class="pane results-pane">',
  '      <div class="pane-heading"><div><span class="eyebrow">ANALYSIS</span><h2>Manifest report</h2></div><div id="status" class="status neutral"></div></div>',
  '      <div class="tabs" role="tablist"><button class="tab active" data-tab="summary">Summary</button><button class="tab" data-tab="validation">Validation <span id="finding-count"></span></button><button class="tab" data-tab="tree">Tree</button></div>',
  '      <div id="results" class="results" aria-live="polite"></div>',
  '    </div>',
  '  </section>',
  '  <footer><span>Syntax and bounded operational guidance</span><span>Use server-side dry-run before applying.</span></footer>',
  '</main>'
].join("");

const editor = document.querySelector("#editor");
editor.value = SAMPLE_YAML;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
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

function messages(title, items, fallbackLevel) {
  return '<section class="messages"><h3>' + escapeHtml(title) + "</h3>" + items.map((item) => {
    const level = item.level || fallbackLevel;
    return '<div class="message ' + level + '"><span>' + escapeHtml(level) + "</span><div><strong>" +
      escapeHtml(item.title || "Document " + item.document) + "</strong><p>" +
      escapeHtml(item.detail || item.message) + "</p></div></div>";
  }).join("") + "</section>";
}

function summaryView(analysis) {
  if (analysis.errors.length) return messages("YAML could not be parsed", analysis.errors, "error");
  if (!analysis.documents.length) return '<div class="empty"><div>{ }</div><h3>Paste or open a YAML manifest</h3><p>The report updates as you type and supports multi-document files.</p></div>';

  return analysis.documents.map((resource) => [
    '<article class="resource-card">',
    '  <header><span class="kind">' + escapeHtml(resource.kind) + '</span><div><h3>' + escapeHtml(resource.name) + '</h3><p>' + escapeHtml(resource.apiVersion) + " · " + escapeHtml(resource.namespace) + '</p></div><small>Document ' + resource.index + "</small></header>",
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
  const parserItems = [
    ...analysis.errors.map((item) => ({ ...item, level: "error" })),
    ...analysis.warnings.map((item) => ({ ...item, level: "warning" }))
  ];
  const operational = analysis.documents.flatMap((resource) => resource.findings.map((item) => ({
    ...item,
    title: resource.kind + "/" + resource.name + ": " + item.title
  })));

  if (!parserItems.length && !operational.length) {
    return '<div class="empty success"><div>✓</div><h3>No findings in the current checks</h3><p>The YAML parsed and passed the Workbench\'s bounded review.</p></div>';
  }

  return (parserItems.length ? messages("Parser findings", parserItems, "error") : "") +
    (operational.length ? messages("Operational review", operational, "warning") : "");
}

function treeNode(value, name = "root", depth = 0) {
  if (value === null || typeof value !== "object") {
    return '<div class="tree-leaf"><span>' + escapeHtml(name) + "</span><code>" + escapeHtml(value) + "</code></div>";
  }

  const entries = Object.entries(value);
  return '<details class="tree-node" ' + (depth < 2 ? "open" : "") + '><summary><span>' +
    escapeHtml(name) + "</span><em>" + (Array.isArray(value) ? "[" + entries.length + "]" : "{" + entries.length + "}") +
    "</em></summary><div>" + entries.map(([key, item]) => treeNode(item, key, depth + 1)).join("") + "</div></details>";
}

function treeView(analysis) {
  if (analysis.errors.length) return messages("YAML could not be parsed", analysis.errors, "error");
  if (!analysis.documents.length) return '<div class="empty"><div>⌘</div><h3>No document tree yet</h3></div>';
  return analysis.documents.map((resource) => '<article class="tree-card"><h3>Document ' + resource.index + " · " +
    escapeHtml(resource.kind) + "/" + escapeHtml(resource.name) + "</h3>" + treeNode(resource.raw) + "</article>").join("");
}

function render() {
  const source = editor.value;
  const analysis = analyzeYaml(source);
  const findingCount = analysis.errors.length + analysis.warnings.length +
    analysis.documents.reduce((total, document) => total + document.findings.length, 0);

  document.querySelector("#line-count").textContent = source ? source.split("\n").length + " lines" : "0 lines";
  document.querySelector("#finding-count").textContent = findingCount || "";

  const status = document.querySelector("#status");
  if (!source.trim()) {
    status.className = "status neutral";
    status.textContent = "Waiting for YAML";
  } else if (analysis.errors.length) {
    status.className = "status error";
    status.textContent = analysis.errors.length + " parse error" + (analysis.errors.length === 1 ? "" : "s");
  } else {
    status.className = "status " + (findingCount ? "warning" : "valid");
    status.textContent = analysis.documents.length + " valid document" + (analysis.documents.length === 1 ? "" : "s");
  }

  const views = { summary: summaryView, validation: validationView, tree: treeView };
  document.querySelector("#results").innerHTML = views[activeTab](analysis);
}

editor.addEventListener("input", render);
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  activeTab = tab.dataset.tab;
  document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
  render();
}));
document.querySelector("#sample").addEventListener("click", () => { editor.value = SAMPLE_YAML; render(); });
document.querySelector("#clear").addEventListener("click", () => { editor.value = ""; render(); editor.focus(); });
document.querySelector("#upload").addEventListener("click", () => document.querySelector("#file-input").click());
document.querySelector("#file-input").addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (file) editor.value = await file.text();
  event.target.value = "";
  render();
});
document.querySelector("#format").addEventListener("click", () => {
  try {
    editor.value = formatYaml(editor.value);
  } catch {
    activeTab = "validation";
    document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item.dataset.tab === activeTab));
  }
  render();
});
document.querySelector("#download").addEventListener("click", () => {
  const blob = new Blob([editor.value], { type: "application/yaml" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "manifest.yaml";
  link.click();
  URL.revokeObjectURL(url);
});

render();
