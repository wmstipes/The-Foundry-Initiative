import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";
import { bootstrapFixture } from "./test-fixtures";
import type { ResourceRecord, ResourceResult } from "./types";

vi.mock("./api", () => ({ bootstrap: vi.fn(), selectContext: vi.fn(), selectNamespace: vi.fn(), queryResources: vi.fn(), activity: vi.fn(), exampleStatus: vi.fn(), queryDiagnostics: vi.fn() }));
let host: HTMLDivElement;
let root: Root | null;
let context: string;
const pod: ResourceRecord = { kind: "Pod", name: "old-pod", namespace: "team", status: "Running", fields: [{ label: "Containers", value: "api" }], owners: [], related: [] };
function button(text: string) { return Array.from(host.querySelectorAll("button")).find((b) => b.textContent === text)!; }
async function click(text: string) { await act(async () => { button(text).click(); }); }
async function choose(id: string, value: string) { await act(async () => { const s = host.querySelector(`#${id}`) as HTMLSelectElement; s.value = value; s.dispatchEvent(new Event("change", { bubbles: true })); }); }
async function scope() { await click("Activate"); await choose("namespace", "team"); await click("Set scope"); }
function result(resource: ResourceResult["resource"], generation = 2): ResourceResult {
 return { resource, operation: "list", scope: { context, namespace: resource === "namespaces" ? "" : "team", generation }, items: resource === "namespaces" ? [{ ...pod, kind: "Namespace", name: "team" }] : resource === "pods" ? [pod] : [], truncated: false };
}

describe("Console resource transitions", () => {
 beforeEach(async () => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });
  vi.resetAllMocks(); context = "dev";
  vi.mocked(api.bootstrap).mockResolvedValue(bootstrapFixture());
  vi.mocked(api.selectContext).mockImplementation(async (name) => { context = name; return { context, namespace: "", generation: 1 }; });
  vi.mocked(api.selectNamespace).mockResolvedValue({ context: "dev", namespace: "team", generation: 2 });
  vi.mocked(api.queryResources).mockImplementation(async (kind, generation) => result(kind, generation));
  vi.mocked(api.activity).mockResolvedValue([]);
  host = document.createElement("div"); document.body.append(host); root = createRoot(host);
  await act(async () => root!.render(<App />));
 });
 afterEach(async () => { if (root) await act(async () => root!.unmount()); host.remove(); });

 it("removes old rows and diagnostics while a different resource kind loads", async () => {
  await scope(); await click("Pods"); await act(async () => { (host.querySelector(".resource-row") as HTMLButtonElement).click(); });
  expect(host.textContent).toContain("Logs, Events");
  let resolve!: (v: ResourceResult) => void;
  vi.mocked(api.queryResources).mockReturnValueOnce(new Promise((done) => { resolve = done; }));
  await click("Services");
  expect(host.querySelector(".resource-row")).toBeNull();
  expect(host.querySelector(".diagnostics")).toBeNull();
  await act(async () => resolve(result("services")));
  expect(host.textContent).not.toContain("old-pod");
 });

 it("clears old namespace choices when new context discovery fails", async () => {
  await scope(); await choose("context", "prod");
  vi.mocked(api.queryResources).mockRejectedValueOnce(new Error("unavailable (503)"));
  await click("Activate");
  const namespaces = host.querySelector("#namespace") as HTMLSelectElement;
  expect(namespaces.options.length).toBe(1); expect(namespaces.disabled).toBe(true);
  expect(button("Set scope").disabled).toBe(true);
  expect(host.textContent).toContain("Context: prod");
 });

 it("rejects resource content for another context even with the same generation", async () => {
  await scope();
  vi.mocked(api.queryResources).mockResolvedValueOnce({ ...result("pods"), scope: { context: "prod", namespace: "team", generation: 2 } });
  await click("Pods");
  expect(host.querySelector(".resource-row")).toBeNull();
  expect(host.querySelector('[role="alert"]')?.textContent).toContain("stale_scope");
 });

 it("aborts pending resource work on unmount and ignores its late result", async () => {
  await scope(); let resolve!: (v: ResourceResult) => void;
  vi.mocked(api.queryResources).mockReturnValueOnce(new Promise((done) => { resolve = done; }));
  await click("Pods"); const signal = vi.mocked(api.queryResources).mock.calls.at(-1)![3]!;
  await act(async () => root!.unmount()); root = null;
  expect(signal.aborted).toBe(true);
  await act(async () => resolve(result("pods")));
  expect(host.textContent).toBe("");
 });

 it("shows incomplete namespace discovery and partial relationships", async () => {
  vi.mocked(api.queryResources).mockResolvedValueOnce({ ...result("namespaces", 1), truncated: true });
  await scope();
  expect(host.textContent).toContain("Namespace discovery is incomplete");
  vi.mocked(api.queryResources).mockResolvedValueOnce({ ...result("pods"), truncated: true });
  await click("Pods"); expect(host.textContent).toContain("object, relationship, or pagination limit");
 });
});
