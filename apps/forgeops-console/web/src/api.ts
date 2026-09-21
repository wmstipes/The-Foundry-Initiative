import type { Bootstrap, PluginStatus } from "./types";

let sessionNonce = "";

async function expectJSON<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`ForgeOps request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function bootstrap(): Promise<Bootstrap> {
  const result = await expectJSON<Bootstrap>(await fetch("/api/v1/bootstrap", { credentials: "same-origin" }));
  sessionNonce = result.sessionNonce;
  return result;
}

export async function selectContext(context: string): Promise<{ selectedContext: string }> {
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
