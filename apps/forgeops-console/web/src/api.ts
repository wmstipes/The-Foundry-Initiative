import type { ActivityEntry, Bootstrap, PluginStatus, ResourceKind, ResourceResult, Scope } from "./types";

let sessionNonce = "";

async function expectJSON<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let code = "request_failed";
    try { code = ((await response.json()) as { error?: string }).error || code; } catch { /* intentionally generic */ }
    throw new Error(`${code} (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function bootstrap(): Promise<Bootstrap> {
  const result = await expectJSON<Bootstrap>(await fetch("/api/v1/bootstrap", { credentials: "same-origin" }));
  sessionNonce = result.sessionNonce;
  return result;
}

export async function selectContext(context: string): Promise<Scope> {
  return expectJSON(
    await fetch("/api/v1/context", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-ForgeOps-Session": sessionNonce,
      },
      body: JSON.stringify({ context }),
    }),
  );
}

export async function selectNamespace(namespace: string, generation: number): Promise<Scope> {
  return expectJSON(await fetch("/api/v1/namespace", {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-ForgeOps-Session": sessionNonce },
    body: JSON.stringify({ namespace, generation }),
  }));
}

export async function queryResources(resource: ResourceKind, generation: number, name?: string): Promise<ResourceResult> {
  return expectJSON(await fetch("/api/v1/plugins/forge.resources/query", {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-ForgeOps-Session": sessionNonce },
    body: JSON.stringify({ generation, operation: name ? "read" : "list", resource, ...(name ? { name } : {}) }),
  }));
}

export async function activity(): Promise<ActivityEntry[]> {
  const result = await expectJSON<{ activity: ActivityEntry[] }>(await fetch("/api/v1/activity", {
    method: "POST", credentials: "same-origin", headers: { "X-ForgeOps-Session": sessionNonce },
  }));
  return result.activity;
}

export async function exampleStatus(): Promise<PluginStatus> {
  return expectJSON(
    await fetch("/api/v1/plugins/forge.example/status", {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-ForgeOps-Session": sessionNonce },
    }),
  );
}

export function clearSessionForTests(): void {
  sessionNonce = "";
}
