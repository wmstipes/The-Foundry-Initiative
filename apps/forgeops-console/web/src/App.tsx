import { useEffect, useRef, useState } from "react";
import { activity, bootstrap, queryResources, selectContext, selectNamespace } from "./api";
import { renderPluginCard } from "./plugin-sdk";
import ResourceBrowser from "./plugins/resources";
import Diagnostics from "./plugins/diagnostics";
import type { ActivityEntry, Bootstrap, ResourceKind, ResourceRecord, ResourceResult, Scope } from "./types";
import "./plugins/example";

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [scope, setScope] = useState<Scope>({ context: "", namespace: "", generation: 0 });
  const [contextChoice, setContextChoice] = useState("");
  const [namespaceChoice, setNamespaceChoice] = useState("");
  const [namespacesIncomplete, setNamespacesIncomplete] = useState(false);
  const pending = useRef<AbortController | null>(null);
  const serial = useRef(0);
  const [namespaces, setNamespaces] = useState<string[]>([]);
  const [kind, setKind] = useState<ResourceKind>("pods");
  const [result, setResult] = useState<ResourceResult | null>(null);
  const [selected, setSelected] = useState<ResourceRecord | null>(null);
  const [history, setHistory] = useState<ActivityEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void bootstrap().then((loaded) => {
      if (!active) return;
      setData(loaded);
      setScope(loaded.scope);
      setContextChoice(loaded.scope.context || loaded.contexts[0]?.name || "");
    }).catch((reason) => { if (active) showError(reason); });
    return () => { active = false; serial.current++; pending.current?.abort(); };
  }, []);

  function showError(reason: unknown) {
    setError(reason instanceof Error ? reason.message : "Unable to load ForgeOps Console");
  }

  function begin() {
    pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    const id = ++serial.current;
    setBusy(true); setError(""); setResult(null); setSelected(null);
    return { controller, id };
  }
  function current(id: number, controller: AbortController) { return id === serial.current && !controller.signal.aborted; }
  function sameScope(a: Scope, b: Scope) { return a.context === b.context && a.namespace === b.namespace && a.generation === b.generation; }
  function finish(id: number, controller: AbortController) { if (current(id, controller)) { setBusy(false); pending.current = null; } }

  async function activateContext() {
    if (!data || !contextChoice) return;
    const { id, controller } = begin();
    setNamespaceChoice(""); setNamespaces([]); setNamespacesIncomplete(false);
    setScope({ context: "", namespace: "", generation: 0 });
    try {
      const next = await selectContext(contextChoice);
      if (!current(id, controller)) return;
      setScope(next);
      const loaded = await queryResources("namespaces", next.generation, undefined, controller.signal);
      if (!current(id, controller)) return;
      if (!sameScope(loaded.scope, next) || loaded.resource !== "namespaces") throw new Error("stale_scope");
      setNamespaces(loaded.items.map((item) => item.name));
      setNamespacesIncomplete(loaded.truncated);
      const entries = await activity();
      if (current(id, controller)) setHistory(entries);
    } catch (reason) { if (current(id, controller)) showError(reason); }
    finally { finish(id, controller); }
  }

  async function activateNamespace() {
    if (!namespaceChoice) return;
    const { id, controller } = begin();
    try {
      const next = await selectNamespace(namespaceChoice, scope.generation);
      if (current(id, controller)) setScope(next);
    } catch (reason) { if (current(id, controller)) showError(reason); }
    finally { finish(id, controller); }
  }

  async function loadResources(nextKind: ResourceKind = kind) {
    const { id, controller } = begin(); setKind(nextKind);
    const requestedScope = scope;
    try {
      const loaded = await queryResources(nextKind, requestedScope.generation, undefined, controller.signal);
      if (!current(id, controller)) return;
      if (!sameScope(loaded.scope, requestedScope) || loaded.resource !== nextKind) throw new Error("stale_scope");
      setResult(loaded);
      const entries = await activity();
      if (current(id, controller)) setHistory(entries);
    } catch (reason) { if (current(id, controller)) { setResult(null); showError(reason); } }
    finally { finish(id, controller); }
  }

  const resourcePluginLoaded = data?.plugins.some((plugin) => plugin.id === "forge.resources") ?? false;
  return (
    <div className="app-shell">
      <header className="topbar"><div><p className="brand">FORGEOPS</p><h1>Console</h1></div><div className={`mode-pill ${data?.mode === "synthetic-demo" ? "demo" : ""}`}><span /> {data?.mode === "synthetic-demo" ? "Synthetic demo" : "Read-only C4"}</div></header>
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
              {namespacesIncomplete && <p className="warning">Namespace discovery is incomplete; some namespaces may be missing.</p>}
              <label htmlFor="namespace">Namespace</label><div className="inline-control"><select id="namespace" value={namespaceChoice} onChange={(event) => setNamespaceChoice(event.target.value)} disabled={!namespaces.length}><option value="">Choose explicitly…</option>{namespaces.map((name) => <option value={name} key={name}>{name}</option>)}</select><button type="button" onClick={() => void activateNamespace()} disabled={busy || !namespaceChoice}>Set scope</button></div>
            </div>
          </section>
          {resourcePluginLoaded && <ResourceBrowser scope={scope} kind={kind} result={result} selected={selected} busy={busy} history={history} onKind={(next) => void loadResources(next)} onRefresh={() => void loadResources()} onSelect={(record) => { if (!busy && result && sameScope(result.scope, scope) && result.resource === kind) setSelected(record); }} />}
          {selected?.kind === "Pod" && scope.namespace && data.plugins.some((plugin) => plugin.id === "forge.diagnostics") && <Diagnostics key={`${scope.generation}/${selected.namespace}/${selected.name}`} scope={scope} pod={selected} onComplete={() => { void activity().then(setHistory).catch(showError); }} />}
          <section><div className="section-heading"><p className="eyebrow">Capability broker</p><h2>First-party extensions</h2></div><div className="plugin-grid">{data.plugins.filter((plugin) => plugin.id !== "forge.resources" && plugin.id !== "forge.diagnostics").map((manifest) => <div key={manifest.id}>{renderPluginCard(manifest)}</div>)}</div></section>
        </>}
      </main>
    </div>
  );
}
