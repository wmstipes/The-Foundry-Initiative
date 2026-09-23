export interface ContextSummary {
  name: string;
  clusterName: string;
  authInfoName: string;
  namespace: string;
}

export interface Contribution {
  id: string;
  type: "dashboardCard" | "resourceBrowser";
  title: string;
  capability: string;
}

export interface PluginManifest {
  id: string;
  displayName: string;
  version: string;
  sdkCompatibility: string;
  capabilities: string[];
  contributions: Contribution[];
}

export interface Bootstrap {
  bundle: { protocol: string; sourceDigest: string };
  mode: "read-only-c4" | "synthetic-demo";
  sessionNonce: string;
  selectedContext: string;
  scope: Scope;
  contexts: ContextSummary[];
  plugins: PluginManifest[];
}

export interface Scope { context: string; namespace: string; generation: number }
export interface ResourceField { label: string; value: string }
export interface ResourceReference { kind: string; name: string; namespace?: string; uid?: string; relation: string }
export interface ResourceRecord { kind: string; name: string; namespace?: string; uid?: string; status: string; fields: ResourceField[]; owners: ResourceReference[]; related: ResourceReference[] }
export type ResourceKind = "namespaces" | "nodes" | "deployments" | "replicasets" | "pods" | "services" | "endpointslices";
export interface ResourceResult { resource: ResourceKind; operation: "list" | "read"; scope: Scope; items: ResourceRecord[]; truncated: boolean }
export interface ActivityEntry { sequence: number; capability: string; context: string; namespace?: string; generation: number; outcome: string; itemCount: number; truncated: boolean }

export interface PluginStatus {
  message: string;
  mode: string;
}

export interface DiagnosticQuery { generation: number; operation: "logs" | "events" | "preview"; pod: string; expectedUID?: string; container?: string; previous?: boolean; target?: "logs" | "events" }
export interface DiagnosticResult { scope: Scope; operation: string; text: string; events: Array<{ name: string; type: string; reason: string; message: string; count: number }>; truncated: boolean; warning: string; preview?: { powershell: string; posix: string; note: string } }
