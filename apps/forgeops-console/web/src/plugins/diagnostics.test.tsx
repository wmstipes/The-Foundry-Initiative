import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Diagnostics from "./diagnostics";
import { queryDiagnostics } from "../api";
import type { DiagnosticResult, ResourceRecord } from "../types";

vi.mock("../api", () => ({ queryDiagnostics: vi.fn() }));
const mock = vi.mocked(queryDiagnostics);
const scope = { context: "dev", namespace: "team", generation: 2 };
const pod: ResourceRecord = { kind: "Pod", name: "api", namespace: "team", status: "Running", fields: [{ label: "Containers", value: "api, sidecar" }], owners: [], related: [] };
const result: DiagnosticResult = { scope, operation: "logs", text: "<img src=x onerror=alert(1)>", events: [], warning: "sensitive", truncated: false };
let host: HTMLDivElement;
let root: Root;
function button(text: string) { return Array.from(host.querySelectorAll("button")).find((item) => item.textContent === text)!; }
async function click(text: string) { await act(async () => { button(text).click(); }); }
async function choose() {
  await act(async () => { (host.querySelector('input[type="checkbox"]') as HTMLInputElement).click();
    const select = host.querySelector("select")!; select.value = "api"; select.dispatchEvent(new Event("change", { bubbles: true })); });
}

describe("Pod diagnostics", () => {
  beforeEach(async () => {
    Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });
    mock.mockReset(); host = document.createElement("div"); document.body.append(host); root = createRoot(host);
    await act(async () => root.render(<Diagnostics key="2/api" scope={scope} pod={pod} />));
  });
  afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

  it("requires warning acknowledgement and explicit container before reading logs", async () => {
    expect(button("Read logs").disabled).toBe(true); expect(button("Read Pod Events").disabled).toBe(true);
    expect(mock).not.toHaveBeenCalled(); await choose(); expect(button("Read logs").disabled).toBe(false);
  });
  it("renders hostile content as text and sends bounded structured selections", async () => {
    mock.mockResolvedValue(result); await choose(); await click("Read logs");
    expect(mock).toHaveBeenCalledWith({ generation: 2, operation: "logs", pod: "api", container: "api", previous: false }, expect.any(AbortSignal));
    expect(host.querySelector("pre")?.textContent).toBe(result.text); expect(host.querySelector("img")).toBeNull();
  });
  it("aborts cancellation and discards a late result even if the transport ignores abort", async () => {
    let resolve!: (value: DiagnosticResult) => void; mock.mockReturnValue(new Promise((done) => { resolve = done; }));
    await choose(); await click("Read logs"); const signal = mock.mock.calls[0][1]; await click("Cancel request");
    expect(signal.aborted).toBe(true); await act(async () => resolve(result)); expect(host.querySelector("pre")).toBeNull();
  });
  it("unmounts and cancels old work when the scope generation changes", async () => {
    let resolve!: (value: DiagnosticResult) => void; mock.mockReturnValue(new Promise((done) => { resolve = done; }));
    await choose(); await click("Read logs"); const signal = mock.mock.calls[0][1];
    await act(async () => root.render(<Diagnostics key="3/api" scope={{ ...scope, generation: 3 }} pod={pod} />));
    expect(signal.aborted).toBe(true); await act(async () => resolve(result)); expect(host.querySelector("pre")).toBeNull();
    expect(button("Read logs").disabled).toBe(true);
  });
  it("rejects mismatched response scope", async () => {
    mock.mockResolvedValue({ ...result, scope: { ...scope, generation: 1 } }); await choose(); await click("Read logs");
    expect(host.querySelector("pre")).toBeNull();
  });
  it("shows bounded error, truncation, and explanatory preview states", async () => {
    mock.mockRejectedValueOnce(new Error("forbidden (403)")); await choose(); await click("Read logs");
    expect(host.querySelector('[role="alert"]')?.textContent).toBe("forbidden (403)");
    mock.mockResolvedValueOnce({ ...result, truncated: true }); await click("Read logs"); expect(host.textContent).toContain("may be incomplete");
    mock.mockResolvedValueOnce({ ...result, operation: "preview", preview: { powershell: "kubectl 'logs'", posix: "kubectl 'logs'", note: "Explanation only" } });
    await click("Preview log command"); expect(host.textContent).toContain("not executed");
    expect(mock.mock.calls.at(-1)?.[0]).toMatchObject({ operation: "preview", target: "logs" });
  });
});
