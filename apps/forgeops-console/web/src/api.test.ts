import { bootstrapFixture } from "./test-fixtures";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { bootstrap, clearSessionForTests, exampleStatus, queryResources, queryDiagnostics, selectContext, selectNamespace } from "./api";

describe("ForgeOps API client", () => {
  beforeEach(() => {
    clearSessionForTests();
    vi.unstubAllGlobals();
  });

  it("keeps the bootstrap nonce in memory for state-changing calls", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(bootstrapFixture()), { status: 200 }))
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
      .mockResolvedValueOnce(new Response(JSON.stringify(bootstrapFixture()), { status: 200 }))
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

  it("sends diagnostics through the nonce-protected fixed endpoint with cancellation", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(bootstrapFixture())))
      .mockResolvedValueOnce(new Response(JSON.stringify({ scope: { generation: 2 } })));
    vi.stubGlobal("fetch", fetchMock); await bootstrap();
    const controller = new AbortController();
    const query = { generation: 2, operation: "events" as const, pod: "api" };
    await queryDiagnostics(query, controller.signal);
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/plugins/forge.diagnostics/query", expect.objectContaining({
      method: "POST", signal: controller.signal, body: JSON.stringify(query), headers: expect.objectContaining({ "X-ForgeOps-Session": "memory-only" }),
    }));
  });

  it("rejects diagnostic results with a stale generation or aborted signal", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => new Response(JSON.stringify({ scope: { generation: 1 } }))));
    const controller = new AbortController();
    await expect(queryDiagnostics({ generation: 2, operation: "events", pod: "api" }, controller.signal)).rejects.toThrow("stale_scope");
    controller.abort();
    await expect(queryDiagnostics({ generation: 1, operation: "events", pod: "api" }, controller.signal)).rejects.toThrow("stale_scope");
  });
  it("rejects mismatched resource identity and cancellation", async () => {
    const valid = { resource: "pods", operation: "list", scope: { generation: 2 }, items: [], truncated: false };
    const controller = new AbortController();
    for (const result of [{ ...valid, scope: { generation: 1 } }, { ...valid, resource: "services" }, { ...valid, operation: "read" }]) {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(result))));
      await expect(queryResources("pods", 2, undefined, controller.signal)).rejects.toThrow();
    }
    controller.abort();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(valid))));
    await expect(queryResources("pods", 2, undefined, controller.signal)).rejects.toThrow("stale_scope");
  });

  it("rejects incompatible bootstrap before retaining its nonce", async () => {
    for (const mode of ["digest", "protocol", "missing-plugin", "missing-contribution", "wrong-version"]) {
      const fixture = bootstrapFixture();
      if (mode === "digest") fixture.bundle.sourceDigest = "old-build";
      if (mode === "protocol") fixture.bundle.protocol = "unsupported";
      if (mode === "missing-plugin") fixture.plugins.pop();
      if (mode === "missing-contribution") fixture.plugins[0].contributions = [];
      if (mode === "wrong-version") fixture.plugins[0].version = "99.0.0";
      const fetchMock = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(fixture))).mockResolvedValueOnce(new Response("{}"));
      vi.stubGlobal("fetch", fetchMock);
      await expect(bootstrap()).rejects.toThrow("Incompatible Console bundle");
      await selectContext("dev");
      expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/context", expect.objectContaining({ headers: expect.objectContaining({ "X-ForgeOps-Session": "" }) }));
    }
  });

});
