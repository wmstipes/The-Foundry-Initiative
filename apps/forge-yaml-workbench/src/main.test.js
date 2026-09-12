// @vitest-environment happy-dom

import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

let editor;

beforeAll(async () => {
  document.body.innerHTML = '<div id="app"></div>';
  await import("./main.js");
  editor = document.querySelector("#editor");
});

beforeEach(() => {
  document.querySelector("#sample").click();
  vi.restoreAllMocks();
});

function replaceEditor(value) {
  editor.value = value;
  editor.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("Forge YAML Workbench browser interactions", () => {
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
});
