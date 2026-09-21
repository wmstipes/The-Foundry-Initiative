import { useEffect, useState } from "react";
import { activity, bootstrap, queryResources, selectContext, selectNamespace } from "./api";
import { renderPluginCard } from "./plugin-sdk";
import ResourceBrowser from "./plugins/resources";
import type { ActivityEntry, Bootstrap, ResourceKind, ResourceRecord, ResourceResult, Scope } from "./types";
import "./plugins/example";

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [scope, setScope] = useState<Scope>({ context: "", namespace: "", generation: 0 });
  const [contextChoice, setContextChoice] = useState("");
  const [namespaceChoice, setNamespaceChoice] = useState("");
  const [namespaces, setNamespaces] = useState<string[]>([]);
  const [kind, setKind] = useState<ResourceKind>("pods");
  const [result, setResult] = useState<ResourceResult | null>(null);
  const [selected, setSelected] = useState<ResourceRecord | null>(null);
  const [history, setHistory] = useState<ActivityEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void bootstrap().then((loaded) => {
      setData(loaded);
      setScope(loaded.scope);
      setContextChoice(loaded.scope.context || loaded.contexts[0]?.name || "");
    }).catch(showError);
  }, []);

  function showError(reason: unknown) {
    setError(reason instanceof Error ? reason.message : "Unable to load ForgeOps Console");
  }

  async function activateContext() {
    if (!data || !contextChoice) return;
    setBusy(true); setError(""); setResult(null); setSelected(null); setNamespaceChoice("");
    try {
      const next = await selectContext(contextChoice);
      setScope(next);
      const namespaceResult = await queryResources("namespaces", next.generation);
      setNamespaces(namespaceResult.items.map((item) => item.name));
      setHistory(await activity());
    } catch (reason) { showError(reason); } finally { setBusy(false); }
  }

  async function activateNamespace() {
    if (!namespaceChoice) return;
    setBusy(true); setError(""); setResult(null); setSelected(null);
    try { setScope(await selectNamespace(namespaceChoice, scope.generation)); }
    catch (reason) { showError(reason); } finally { setBusy(false); }
  }

  async function loadResources(nextKind: ResourceKind = kind) {
    setBusy(true); setError(""); setSelected(null); setKind(nextKind);
    try {
      const loaded = await queryResources(nextKind, scope.generation);
      setResult(loaded);
      setHistory(await activity());
    } catch (reason) { setResult(null); showError(reason); } finally { setBusy(false); }
  }

  const resourcePluginLoaded = data?.plugins.some((plugin) => plugin.id === "forge.resources") ?? false;
  return (
    <div className="app-shell">
      <header className="topbar"><div><p className="brand">FORGEOPS</p><h1>Console</h1></div><div className={`mode-pill ${data?.mode === "synthetic-demo" ? "demo" : ""}`}><span /> {data?.mode === "synthetic-demo" ? "Synthetic demo" : "Read-only C3"}</div></header>
      <div className="scope-banner" role="status">
        <strong>{data?.mode === "synthetic-demo" ? "SYNTHETIC DATA — NO CLUSTER CONNECTION" : "Read-only cluster access"}</strong>
        <span>Context: {scope.context || "none"}</span><span>Namespace: {scope.namespace || "none"}</span><span>Generation: {scope.generation || "—"}</span>
      </div>
      <main>
        {error && <p className="error" role="alert">{error}</p>}
        {!data && !error && <p className="loading">Loading local configuration…</p>}
        {data && <>
          <section className="panel context-panel">
            <div><p className="eyebrow">Explicit session scope</p><h2>Choose context and namespace</h2><p>Each change creates a new generation and cancels older work.</p></div>
            <div className="scope-controls">
              <label htmlFor="context">Kubernetes context</label><div className="inline-control"><select id="context" value={contextChoice} onChange={(event) => setContextChoice(event.target.value)}>{data.contexts.map((item) => <option value={item.name} key={item.name}>{item.name}</option>)}</select><button type="button" onClick={() => void activateContext()} disabled={busy || !contextChoice}>Activate</button></div>
              <label htmlFor="namespace">Namespace</label><div className="inline-control"><select id="namespace" value={namespaceChoice} onChange={(event) => setNamespaceChoice(event.target.value)} disabled={!namespaces.length}><option value="">Choose explicitly…</option>{namespaces.map((name) => <option value={name} key={name}>{name}</option>)}</select><button type="button" onClick={() => void activateNamespace()} disabled={busy || !namespaceChoice}>Set scope</button></div>
            </div>
          </section>
          {resourcePluginLoaded && <ResourceBrowser scope={scope} kind={kind} result={result} selected={selected} busy={busy} history={history} onKind={(next) => void loadResources(next)} onRefresh={() => void loadResources()} onSelect={setSelected} />}
          <section><div className="section-heading"><p className="eyebrow">Capability broker</p><h2>First-party extensions</h2></div><div className="plugin-grid">{data.plugins.filter((plugin) => plugin.id !== "forge.resources").map((manifest) => <div key={manifest.id}>{renderPluginCard(manifest)}</div>)}</div></section>
        </>}
      </main>
    </div>
  );
}
