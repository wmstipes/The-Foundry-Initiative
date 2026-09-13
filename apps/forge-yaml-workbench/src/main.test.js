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
    expect(document.querySelector("#results").textContent).toContain("Kubernetes operational checks are disabled");
    expect(document.querySelector("#results").textContent).not.toContain("No containers found");
  });

  it("renders an explicit null scalar in General YAML summary and tree views", () => {
    document.querySelector('[data-mode="general"]').click();
    replaceEditor("null\n");
    expect(document.querySelector("#results").textContent).toContain("null");

    document.querySelector('[data-tab="tree"]').click();
    expect(document.querySelector("#results").textContent).toContain("null");
  });

  it("reports whether formatting changed the YAML", () => {
    replaceEditor("apiVersion: v1\nkind:  Pod\nmetadata: {name: demo}\n");

    document.querySelector("#format").click();
    expect(editor.value).toContain("metadata:\n  name: demo");
    expect(document.querySelector("#action-status").textContent).toBe("YAML formatted");

    document.querySelector("#format").click();
    expect(document.querySelector("#action-status").textContent).toBe("Already formatted — no changes needed");
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

  it("supports the format keyboard shortcut", () => {
    replaceEditor("apiVersion: v1\nkind:  Pod\nmetadata: {name: demo}\n");
    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "F",
      ctrlKey: true,
      shiftKey: true,
      bubbles: true,
      cancelable: true
    }));

    expect(editor.value).toContain("metadata:\n  name: demo");
    expect(document.querySelector("#action-status").textContent).toBe("YAML formatted");
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
});
