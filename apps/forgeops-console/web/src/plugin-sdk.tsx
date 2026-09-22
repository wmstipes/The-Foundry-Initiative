import type { ReactNode } from "react";
import type { PluginManifest } from "./types";

export interface PluginCardProps {
  manifest: PluginManifest;
}

export interface CompiledPlugin {
  id: string;
  renderCard(props: PluginCardProps): ReactNode;
}

const compiledPlugins = new Map<string, CompiledPlugin>();

export function registerCompiledPlugin(plugin: CompiledPlugin): void {
  if (compiledPlugins.has(plugin.id)) {
    throw new Error(`Plugin ${plugin.id} is already registered`);
  }
  compiledPlugins.set(plugin.id, plugin);
}

export function renderPluginCard(manifest: PluginManifest): ReactNode {
  const plugin = compiledPlugins.get(manifest.id);
  if (!plugin) {
    return <p role="alert">Missing compiled view for {manifest.id}. Rebuild the matched Console bundle.</p>;
  }
  return plugin.renderCard({ manifest });
}
