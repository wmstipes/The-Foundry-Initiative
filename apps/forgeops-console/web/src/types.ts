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
  mode: "read-only-c3" | "synthetic-demo";
  sessionNonce: string;
  selectedContext: string;
  scope: Scope;
  contexts: ContextSummary[];
  plugins: PluginManifest[];
}

export interface Scope { context: string; namespace: string; generation: number }
export interface ResourceField { label: string; value: string }
export interface ResourceReference { kind: string; name: string; namespace?: string; relation: string }
export interface ResourceRecord { kind: string; name: string; namespace?: string; status: string; fields: ResourceField[]; owners: ResourceReference[]; related: ResourceReference[] }
export type ResourceKind = "namespaces" | "nodes" | "deployments" | "replicasets" | "pods" | "services" | "endpointslices";
export interface ResourceResult { resource: ResourceKind; operation: "list" | "read"; scope: Scope; items: ResourceRecord[]; truncated: boolean }
export interface ActivityEntry { sequence: number; capability: string; context: string; namespace?: string; generation: number; outcome: string; itemCount: number; truncated: boolean }

export interface PluginStatus {
  message: string;
  mode: string;
}
