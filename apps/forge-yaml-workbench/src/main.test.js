// @vitest-environment happy-dom

import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

let editor;

beforeAll(async () => {
  document.body.innerHTML = '<div id="app"></div>';
  await import("./main.js");
  editor = document.querySelector("#editor");
});

beforeEach(() => {
  document.querySelector('[data-mode="kubernetes"]').click();
  document.querySelector('[data-tab="summary"]').click();
  document.querySelector("#sample").click();
  vi.restoreAllMocks();
});

function replaceEditor(value) {
  editor.value = value;
  editor.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("Forge YAML Workbench browser interactions", () => {
  it("starts in Kubernetes mode and switches modes without changing YAML", () => {
    const source = "settings:\n  theme: dark\n";
    replaceEditor(source);

    expect(document.querySelector('[data-mode="kubernetes"]').getAttribute("aria-pressed")).toBe("true");
    document.querySelector('[data-mode="general"]').click();

    expect(editor.value).toBe(source);
    expect(document.querySelector('[data-mode="general"]').getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector("#inspection-title").textContent).toBe("General YAML inspection");
    expect(document.querySelector("#report-title").textContent).toBe("YAML report");
    expect(document.querySelector("#results").textContent).toContain("mapping");
    expect(document.querySelector("#results").textContent).toContain("settings");
  });

  it("accepts scalar input and hides Kubernetes findings in General YAML mode", () => {
    document.querySelector('[data-mode="general"]').click();
    replaceEditor("ready\n");

    expect(document.querySelector("#status").textContent).toBe("1 parsed document · no findings");
    expect(document.querySelector("#results").textContent).toContain("Scalar value");

    replaceEditor("kind: Pod\nmetadata: {name: risky}\nspec: {}\n");
    document.querySelector('[data-tab="validation"]').click();
    expect(document.querySelector("#results").textContent).toContain("Kubernetes operational and schema checks are disabled");
    expect(document.querySelector("#results").textContent).not.toContain("No containers found");
    expect(document.querySelector("#results").textContent).not.toContain("Kubernetes schema ·");
  });

  it("renders syntax, deterministic operational, and schema results as separate sections", () => {
    replaceEditor("apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: separated}\nspec:\n  replicas: three\n  mysteryField: true\n");
    document.querySelector('[data-tab="validation"]').click();

    const headings = [...document.querySelectorAll(".messages h3")].map((item) => item.textContent);
    expect(headings).toContain("Deterministic operational review");
    expect(headings).toContain("Kubernetes schema · v1.36.4");
    expect(document.querySelector("#results").textContent).toContain(".spec.replicas");
    expect(document.querySelector("#results").textContent).toContain(".spec.mysteryField");
  });

  it("filters validation results by level with accurate counts and preserved ordering", () => {
    replaceEditor([
      "apiVersion: v1",
      "kind: ConfigMap",
      "metadata: {name: valid-config}",
      "---",
      "apiVersion: networking.k8s.io/v1",
      "kind: Ingress",
      "metadata: {name: unsupported}",
      "---",
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: risky}",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: nginx:latest",
      "---",
      "apiVersion: apps/v1",
      "kind: Deployment",
      "metadata: {name: invalid}",
      "spec:",
      "  replicas: three",
      "  mysteryField: true",
      ""
    ].join("\n"));
    document.querySelector('[data-tab="validation"]').click();

    const counts = Object.fromEntries([...document.querySelectorAll("[data-validation-filter]")].map((button) => [
      button.dataset.validationFilter,
      Number(button.querySelector("span").textContent)
    ]));
    expect(counts.all).toBe(counts.error + counts.warning + counts.note + counts.valid);
    expect(counts.error).toBeGreaterThan(0);
    expect(counts.warning).toBeGreaterThan(0);
    expect(counts.note).toBeGreaterThan(0);
    expect(counts.valid).toBeGreaterThan(0);
    expect(document.querySelector('[data-validation-filter="all"]').getAttribute("aria-pressed")).toBe("true");

    for (const level of ["error", "warning", "note", "valid"]) {
      document.querySelector(`[data-validation-filter="${level}"]`).click();
      expect([...document.querySelectorAll(".message")].every((message) => message.classList.contains(level))).toBe(true);
      expect(document.querySelectorAll(".message")).toHaveLength(counts[level]);
      expect(document.querySelector(".validation-filter-summary").textContent).toBe(
        `Displaying ${counts[level]} of ${counts.all} validation results`
      );
      expect(document.querySelector(`[data-validation-filter="${level}"]`).getAttribute("aria-pressed")).toBe("true");
      expect(document.activeElement).toBe(document.querySelector(`[data-validation-filter="${level}"]`));
    }
  });

  it("keeps the OWASP profile outside validation filtering and explains filtered-empty results", () => {
    replaceEditor("apiVersion: v1\nkind: ConfigMap\nmetadata: {name: error-only}\nmysteryField: true\n");
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="note"]').click();

    expect(document.querySelectorAll(".messages")).toHaveLength(0);
    expect(document.querySelector(".filtered-empty h3").textContent).toBe("No note results in the current analysis");
    expect(document.querySelector(".filtered-empty").textContent).toContain("complete analysis still contains");
    expect(document.querySelector(".owasp-profile")).not.toBeNull();
    expect(document.querySelector("#finding-count").textContent).not.toBe("");
  });

  it("preserves a selected filter while edits recompute counts", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: risky}\nspec:\n  containers:\n    - name: app\n      image: nginx:latest\n");
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="warning"]').click();
    expect(document.querySelectorAll(".message.warning").length).toBeGreaterThan(0);

    replaceEditor("apiVersion: v1\nkind: ConfigMap\nmetadata: {name: clean}\n");

    expect(document.querySelector('[data-validation-filter="warning"]').getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector('[data-validation-filter="warning"] span').textContent).toBe("0");
    expect(document.querySelector(".filtered-empty h3").textContent).toBe("No warning results in the current analysis");
  });

  it("resets validation filtering when the mode or loaded input changes", async () => {
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="warning"]').click();
    document.querySelector('[data-mode="general"]').click();
    expect(document.querySelector('[data-validation-filter="all"]').getAttribute("aria-pressed")).toBe("true");

    document.querySelector('[data-validation-filter="warning"]').click();
    document.querySelector("#sample").click();
    expect(document.querySelector('[data-validation-filter="all"]').getAttribute("aria-pressed")).toBe("true");

    document.querySelector('[data-validation-filter="note"]').click();
    const input = document.querySelector("#file-input");
    Object.defineProperty(input, "files", {
      configurable: true,
      value: [new File(["settings:\n  theme: dark\n"], "settings.yaml", { type: "application/yaml" })]
    });
    input.dispatchEvent(new Event("change", { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(document.querySelector('[data-validation-filter="all"]').getAttribute("aria-pressed")).toBe("true");

    document.querySelector('[data-validation-filter="valid"]').click();
    document.querySelector("#clear").click();
    expect(document.querySelector('[data-validation-filter="all"]').getAttribute("aria-pressed")).toBe("true");
  });

  it("keeps Markdown reports complete when the Validation display is filtered", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: report-filter}\nspec:\n  containers:\n    - name: app\n      image: nginx:latest\n");
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="valid"]').click();
    expect(document.querySelector("#results").textContent).not.toContain("mutable image reference");

    document.querySelector("#generate-report").click();
    expect(document.querySelector("#report-markdown").textContent).toContain("mutable image reference");
    document.querySelector("#report-cancel").click();
  });

  it("scrolls the editor to a selected finding location", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: navigation}",
      "spec:",
      ...Array.from({ length: 60 }, (_, index) => `  placeholder${index}: true`),
      "  containers: []",
      ""
    ].join("\n");
    Object.defineProperties(editor, {
      clientHeight: { configurable: true, value: 200 },
      scrollHeight: { configurable: true, value: 2000 }
    });
    editor.style.fontSize = "10px";
    editor.style.lineHeight = "20px";
    editor.scrollTop = 0;

    replaceEditor(source);
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="error"]').click();
    const location = [...document.querySelectorAll(".message-location")].find((item) =>
      item.textContent.includes("Line 65"));
    expect(location).not.toBeUndefined();

    location.click();

    expect(editor.selectionStart).toBe(source.indexOf("  containers: []"));
    expect(editor.scrollTop).toBeGreaterThan(0);
  });

  it("labels unsupported resources and unavailable CRD schemas explicitly", () => {
    replaceEditor("apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata: {name: unsupported}\n---\napiVersion: database.example.com/v1\nkind: Database\nmetadata: {name: custom}\n");
    document.querySelector('[data-tab="validation"]').click();

    expect(document.querySelector("#results").textContent).toContain("No bundled v1.36.4 schema supports networking.k8s.io/v1 Ingress");
    expect(document.querySelector("#results").textContent).toContain("CRD schema unavailable for database.example.com/v1 Database");
  });

  it("renders an explicit null scalar in General YAML summary and tree views", () => {
    document.querySelector('[data-mode="general"]').click();
    replaceEditor("null\n");
    expect(document.querySelector("#results").textContent).toContain("null");

    document.querySelector('[data-tab="tree"]').click();
    expect(document.querySelector("#results").textContent).toContain("null");
  });

  it("previews formatting without changing YAML until Apply is selected", () => {
    const source = "apiVersion: v1\nkind:  Pod\nmetadata: {name: demo}\n";
    replaceEditor(source);

    document.querySelector("#format").click();
    expect(editor.value).toBe(source);
    expect(document.querySelector("#format-preview").hidden).toBe(false);
    expect(document.querySelector("#format-preview-summary").textContent).toMatch(/added.*removed/);
    expect(document.querySelectorAll(".diff-row.added").length).toBeGreaterThan(0);
    expect(document.querySelectorAll(".diff-row.removed").length).toBeGreaterThan(0);
    expect(document.activeElement).toBe(document.querySelector("#format-apply"));
    expect(document.querySelector("#action-status").textContent).toBe("Formatting preview ready");

    document.querySelector("#format-apply").click();
    expect(editor.value).toContain("metadata:\n  name: demo");
    expect(document.querySelector("#format-preview").hidden).toBe(true);
    expect(document.querySelector("#action-status").textContent).toBe("YAML formatted");

    document.querySelector("#format").click();
    expect(document.querySelector("#format-preview").hidden).toBe(true);
    expect(document.querySelector("#action-status").textContent).toBe("Already formatted — no changes needed");
  });

  it("explains a final-newline-only formatting change", () => {
    const source = "apiVersion: v1\nkind: Pod\nmetadata:\n  name: demo";
    replaceEditor(source);

    document.querySelector("#format").click();
    expect(editor.value).toBe(source);
    expect(document.querySelector("#format-preview-summary").textContent).toContain("final newline added");
    document.querySelector("#format-cancel").click();
  });

  it("cancels a formatting preview without changing the editor", () => {
    const source = "kind:  Pod\nmetadata: {name: demo}\n";
    replaceEditor(source);
    document.querySelector("#format").click();

    document.querySelector("#format-cancel").click();
    expect(editor.value).toBe(source);
    expect(document.querySelector("#format-preview").hidden).toBe(true);
    expect(document.querySelector("#action-status").textContent).toBe("Formatting cancelled");
    expect(document.activeElement).toBe(document.querySelector("#format"));
  });

  it("closes a formatting preview with Escape", () => {
    const source = "kind:  Pod\nmetadata: {name: demo}\n";
    replaceEditor(source);
    document.querySelector("#format").click();

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Escape",
      bubbles: true,
      cancelable: true
    }));

    expect(editor.value).toBe(source);
    expect(document.querySelector("#format-preview").hidden).toBe(true);
    expect(document.querySelector("#action-status").textContent).toBe("Formatting cancelled");
  });

  it("keeps keyboard focus inside the formatting preview", () => {
    replaceEditor("kind:  Pod\nmetadata: {name: demo}\n");
    document.querySelector("#format").click();
    expect(document.activeElement).toBe(document.querySelector("#format-apply"));

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true
    }));
    expect(document.activeElement).toBe(document.querySelector("#format-diff"));

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: true,
      bubbles: true,
      cancelable: true
    }));
    expect(document.activeElement).toBe(document.querySelector("#format-apply"));
    document.querySelector("#format-cancel").click();
  });

  it("switches to Validation and focuses a parser-error line", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nkind: Service\n");

    document.querySelector("#format").click();
    expect(document.querySelector('[data-tab="validation"]').classList.contains("active")).toBe(true);
    const location = document.querySelector(".message-location");
    expect(location.textContent).toBe("Line 3, column 1");

    location.click();
    expect(editor.selectionStart).toBe("apiVersion: v1\nkind: Pod\n".length);
    expect(editor.selectionEnd).toBe(editor.value.length - 1);
  });

  it("clears a stale formatting failure when editing resumes", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nkind: Service\n");
    document.querySelector("#format").click();
    expect(document.querySelector("#action-status").textContent).toBe("Formatting failed — see Validation");

    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata:\n  name: corrected\n");
    expect(document.querySelector("#action-status").textContent).toBe("Editing YAML");
    expect(document.querySelector("#status").textContent).toContain("1 parsed document");
  });

  it("protects unsaved YAML from accidental clearing", () => {
    replaceEditor(editor.value + "# local change\n");
    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn().mockReturnValue(false)
    });

    document.querySelector("#clear").click();
    expect(editor.value).toContain("# local change");
    expect(document.querySelector("#action-status").textContent).toBe("Clear cancelled");

    window.confirm.mockReturnValue(true);
    document.querySelector("#clear").click();
    expect(editor.value).toBe("");
  });

  it("opens the formatting preview with the keyboard shortcut", () => {
    const source = "apiVersion: v1\nkind:  Pod\nmetadata: {name: demo}\n";
    replaceEditor(source);
    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "F",
      ctrlKey: true,
      shiftKey: true,
      bubbles: true,
      cancelable: true
    }));

    expect(editor.value).toBe(source);
    expect(document.querySelector("#format-preview").hidden).toBe(false);
    expect(document.querySelector("#action-status").textContent).toBe("Formatting preview ready");
    document.querySelector("#format-cancel").click();
  });

  it("preserves an opened YAML filename when downloading", async () => {
    const input = document.querySelector("#file-input");
    const file = new File(["apiVersion: v1\nkind: Pod\nmetadata:\n  name: opened\n"], "opened.yml", {
      type: "application/yaml"
    });
    Object.defineProperty(input, "files", { configurable: true, value: [file] });
    input.dispatchEvent(new Event("change", { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 0));

    let downloadedAs;
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:test") });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function click() {
      downloadedAs = this.download;
    });

    document.querySelector("#download").click();
    expect(downloadedAs).toBe("opened.yml");
    expect(document.querySelector("#action-status").textContent).toBe("opened.yml downloaded");
  });

  it("renders operational YAML paths and suggested corrections", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata:\n  name: empty\nspec: {}\n");
    document.querySelector('[data-tab="validation"]').click();

    const message = [...document.querySelectorAll(".message")].find((item) =>
      item.textContent.includes("No containers found"));
    expect(message.querySelector(".message-path code").textContent).toBe(".spec.containers");
    expect(message.querySelector(".message-suggestion").textContent).toContain("Add at least one container");

    message.querySelector(".message-path").click();
    expect(editor.value.slice(editor.selectionStart, editor.selectionEnd)).toBe("spec: {}");
  });

  it("expands and copies OWASP remediation guidance", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText }
    });
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: guidance}\nspec:\n  containers: [{name: app, image: example/app:1.0.0}]\n");
    document.querySelector('[data-tab="validation"]').click();
    document.querySelector('[data-validation-filter="note"]').click();

    const message = [...document.querySelectorAll(".message")].find((item) =>
      item.textContent.includes("privilege escalation not disabled"));
    expect(message.querySelector(".fix-guidance")).not.toBeNull();
    expect(message.querySelector(".fix-guidance pre").textContent).toContain("allowPrivilegeEscalation: false");
    expect(message.querySelector(".guidance-caution").textContent).toContain("Before applying:");
    expect(message.querySelector(".guidance-standard a").textContent).toContain("OWASP K01:2025");

    message.querySelector(".copy-guidance").click();
    await vi.waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("securityContext:\n  allowPrivilegeEscalation: false");
      expect(document.querySelector("#action-status").textContent).toBe("Suggested YAML copied");
    });
  });

  it("renders the pinned OWASP review profile without implying a score", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: profile}\nspec:\n  containers: [{name: app, image: example/app:1.0.0}]\n");
    document.querySelector('[data-tab="validation"]').click();

    const profile = document.querySelector(".owasp-profile");
    expect(profile.textContent).toContain("OWASP Kubernetes Top 10:2025 review profile");
    expect(profile.querySelectorAll(".owasp-profile-item")).toHaveLength(10);
    expect(profile.textContent).toContain("Direct");
    expect(profile.textContent).toContain("Partial");
    expect(profile.textContent).toContain("Cluster context required");
    expect(profile.textContent).toContain("not a compliance score or pass/fail result");
    expect(profile.querySelector("header code").textContent).toBe("828cfa2");
  });

  it("renders multiple OWASP references for a shared finding", () => {
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: profile}\nspec:\n  containers: [{name: app, image: example/app:1.0.0}]\n");
    document.querySelector('[data-tab="validation"]').click();

    const message = [...document.querySelectorAll(".message")].find((item) =>
      item.textContent.includes("ServiceAccount token may be mounted"));
    expect([...message.querySelectorAll(".guidance-standard a")].map((item) => item.textContent)).toEqual([
      expect.stringContaining("K01:2025"),
      expect.stringContaining("K09:2025")
    ]);
  });

  it("previews a browser-local Markdown report without changing or exporting YAML", () => {
    const source = "apiVersion: v1\nkind: Pod\nmetadata: {name: report-preview}\nspec: {}\n";
    const writeText = vi.fn();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText }
    });
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:test")
    });
    replaceEditor(source);

    document.querySelector("#generate-report").click();

    expect(editor.value).toBe(source);
    expect(document.querySelector("#report-preview").hidden).toBe(false);
    expect(document.querySelector("#report-markdown").textContent).toContain(
      "# Forge YAML Workbench Analysis Report"
    );
    expect(document.querySelector("#report-markdown").textContent).not.toContain(source);
    expect(document.activeElement).toBe(document.querySelector("#report-markdown"));
    expect(writeText).not.toHaveBeenCalled();
    expect(URL.createObjectURL).not.toHaveBeenCalled();
    expect(document.querySelector("#action-status").textContent).toBe(
      "Markdown report ready for review"
    );
    expect(document.querySelector("#report-action-status").textContent).toBe(
      "No report exported yet."
    );

    document.querySelector("#report-cancel").click();
    expect(document.querySelector("#report-preview").hidden).toBe(true);
    expect(document.activeElement).toBe(document.querySelector("#generate-report"));
    expect(document.querySelector("#action-status").textContent).toBe("Report cancelled");
  });

  it("copies exactly the reviewed Markdown snapshot", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText }
    });
    replaceEditor("apiVersion: v1\nkind: Pod\nmetadata: {name: copied-report}\nspec: {}\n");
    document.querySelector("#generate-report").click();
    const reviewed = document.querySelector("#report-markdown").textContent;

    document.querySelector("#report-copy").click();

    await vi.waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(reviewed);
      expect(document.querySelector("#action-status").textContent).toBe("Markdown report copied");
      expect(document.querySelector("#report-action-status").textContent).toBe(
        "Markdown copied to the clipboard."
      );
      expect(document.querySelector("#report-copy").textContent).toBe("Copied");
      expect(document.querySelector("#report-copy").classList.contains("completed")).toBe(true);
    });
    expect(document.querySelector("#report-preview").hidden).toBe(false);
    document.querySelector("#report-cancel").click();
  });

  it("downloads the reviewed report without marking YAML as saved", () => {
    let downloadedAs;
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:report")
    });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function click() {
      downloadedAs = this.download;
    });
    const source = editor.value + "# unsaved report source\n";
    replaceEditor(source);
    document.querySelector("#generate-report").click();

    document.querySelector("#report-download").click();

    expect(downloadedAs).toBe("signalforge-sample-report.md");
    expect(document.querySelector("#action-status").textContent).toBe(
      "signalforge-sample-report.md downloaded"
    );
    expect(document.querySelector("#report-action-status").textContent).toBe(
      "signalforge-sample-report.md downloaded."
    );
    expect(document.querySelector("#report-download").textContent).toBe("Downloaded");
    expect(document.querySelector("#report-download").classList.contains("completed")).toBe(true);
    expect(editor.value).toBe(source);
    document.querySelector("#report-cancel").click();

    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn().mockReturnValue(false)
    });
    document.querySelector("#clear").click();
    expect(window.confirm).toHaveBeenCalled();
    expect(editor.value).toBe(source);
  });

  it("closes the report preview with Escape and contains keyboard focus", () => {
    document.querySelector("#generate-report").click();
    expect(document.activeElement).toBe(document.querySelector("#report-markdown"));

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true
    }));
    expect(document.activeElement).toBe(document.querySelector("#report-cancel"));

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: true,
      bubbles: true,
      cancelable: true
    }));
    expect(document.activeElement).toBe(document.querySelector("#report-markdown"));

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Escape",
      bubbles: true,
      cancelable: true
    }));
    expect(document.querySelector("#report-preview").hidden).toBe(true);
    expect(document.activeElement).toBe(document.querySelector("#generate-report"));
    expect(document.querySelector("#action-status").textContent).toBe("Report cancelled");
  });

  it("invalidates a prepared report when the source or inspection mode changes", () => {
    document.querySelector("#generate-report").click();
    expect(document.querySelector("#report-preview").hidden).toBe(false);

    replaceEditor(editor.value + "# changed\n");
    expect(document.querySelector("#report-preview").hidden).toBe(true);
    expect(document.querySelector("#report-markdown").textContent).toBe("");

    document.querySelector("#generate-report").click();
    document.querySelector('[data-mode="general"]').click();
    expect(document.querySelector("#report-preview").hidden).toBe(true);

    document.querySelector("#generate-report").click();
    const markdown = document.querySelector("#report-markdown").textContent;
    expect(markdown).toContain("**Inspection mode:** General YAML");
    expect(markdown).not.toContain("# Kubernetes Review");
    document.querySelector("#report-cancel").click();
  });

});
