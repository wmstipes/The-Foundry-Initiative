export interface ContextSummary {
  name: string;
  clusterName: string;
  authInfoName: string;
  namespace: string;
}

export interface Contribution {
  id: string;
  type: "dashboardCard";
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
  mode: "offline-c2";
  sessionNonce: string;
  selectedContext: string;
  contexts: ContextSummary[];
  plugins: PluginManifest[];
}

export interface PluginStatus {
  message: string;
  mode: string;
}
