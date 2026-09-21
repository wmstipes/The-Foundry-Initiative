import { useEffect, useState } from "react";
import { bootstrap, selectContext } from "./api";
import { renderPluginCard } from "./plugin-sdk";
import type { Bootstrap } from "./types";
import "./plugins/example";

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [choice, setChoice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void bootstrap()
      .then((result) => {
        setData(result);
        setChoice(result.selectedContext || result.contexts[0]?.name || "");
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load ForgeOps Console"));
  }, []);

  async function activateContext() {
    if (!data || !choice) return;
    try {
      const result = await selectContext(choice);
      setData({ ...data, selectedContext: result.selectedContext });
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to select context");
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="brand">FORGEOPS</p>
          <h1>Console</h1>
        </div>
        <div className="mode-pill"><span /> Offline C2</div>
      </header>

      <div className="scope-banner" role="status">
        <strong>Offline walking skeleton</strong>
        <span>Active context: {data?.selectedContext || "none selected"}</span>
        <span>No cluster connections or Kubernetes operations are available.</span>
      </div>

      <main>
        {error && <p className="error" role="alert">{error}</p>}
        {!data && !error && <p className="loading">Loading local configuration…</p>}
        {data && (
          <>
            <section className="panel context-panel">
              <div>
                <p className="eyebrow">Explicit local configuration</p>
                <h2>Choose a context label</h2>
                <p>This selection stays in memory. C2 does not contact the cluster or persist your choice.</p>
              </div>
              <div className="context-control">
                <label htmlFor="context">Kubernetes context</label>
                <select id="context" value={choice} onChange={(event) => setChoice(event.target.value)}>
                  {data.contexts.map((context) => (
                    <option value={context.name} key={context.name}>{context.name}</option>
                  ))}
                </select>
                <button type="button" onClick={activateContext} disabled={!choice}>Activate locally</button>
              </div>
            </section>

            <section>
              <div className="section-heading">
                <p className="eyebrow">Capability broker</p>
                <h2>First-party extensions</h2>
              </div>
              <div className="plugin-grid">
                {data.plugins.map((manifest) => <div key={manifest.id}>{renderPluginCard(manifest)}</div>)}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
