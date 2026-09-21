import { beforeEach, describe, expect, it, vi } from "vitest";
import { bootstrap, clearSessionForTests, exampleStatus, queryResources, selectContext, selectNamespace } from "./api";

describe("ForgeOps API client", () => {
  beforeEach(() => {
    clearSessionForTests();
    vi.unstubAllGlobals();
  });

  it("keeps the bootstrap nonce in memory for state-changing calls", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        mode: "offline-c2",
        sessionNonce: "memory-only",
        selectedContext: "",
        contexts: [],
        plugins: [],
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ selectedContext: "dev" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await bootstrap();
    await selectContext("dev");

    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/context", expect.objectContaining({
      headers: expect.objectContaining({ "X-ForgeOps-Session": "memory-only" }),
    }));
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("calls only the compiled example endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: "ready", mode: "offline-c2" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await exampleStatus();
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/plugins/forge.example/status", expect.objectContaining({ method: "POST" }));
  });

  it("sends a generation-bound resource request to the single compiled endpoint", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ mode: "synthetic-demo", sessionNonce: "memory-only", selectedContext: "", scope: { context: "", namespace: "", generation: 0 }, contexts: [], plugins: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ context: "demo", namespace: "signalforge", generation: 2 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ resource: "pods", operation: "list", scope: { context: "demo", namespace: "signalforge", generation: 2 }, items: [], truncated: false }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await bootstrap();
    await selectNamespace("signalforge", 1);
    await queryResources("pods", 2);
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/namespace", expect.objectContaining({ body: JSON.stringify({ namespace: "signalforge", generation: 1 }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/v1/plugins/forge.resources/query", expect.objectContaining({ body: JSON.stringify({ generation: 2, operation: "list", resource: "pods" }) }));
  });

  it("exposes only the server error code and status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: "stale_scope", detail: "must not escape" }), { status: 409 })));
    await expect(queryResources("pods", 1)).rejects.toThrow("stale_scope (409)");
  });
});
