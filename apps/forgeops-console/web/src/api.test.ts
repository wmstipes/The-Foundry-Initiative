import { beforeEach, describe, expect, it, vi } from "vitest";
import { bootstrap, clearSessionForTests, exampleStatus, selectContext } from "./api";

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
});
