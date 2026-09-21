import { useState } from "react";
import { exampleStatus } from "../api";
import { registerCompiledPlugin, type PluginCardProps } from "../plugin-sdk";

function ExampleCard({ manifest }: PluginCardProps) {
  const [status, setStatus] = useState("Not checked");
  const [busy, setBusy] = useState(false);

  async function checkStatus() {
    setBusy(true);
    try {
      const response = await exampleStatus();
      setStatus(response.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Status check failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="plugin-card">
      <div>
        <p className="eyebrow">Compiled-in plugin · v{manifest.version}</p>
        <h3>{manifest.displayName}</h3>
        <p>{status}</p>
      </div>
      <button type="button" onClick={checkStatus} disabled={busy}>
        {busy ? "Checking…" : "Check inert status"}
      </button>
    </article>
  );
}

registerCompiledPlugin({
  id: "forge.example",
  renderCard: (props) => <ExampleCard {...props} />,
});
