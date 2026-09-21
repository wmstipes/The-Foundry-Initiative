import { useEffect, useRef, useState } from "react";
import { queryDiagnostics } from "../api";
import type { DiagnosticQuery, DiagnosticResult, ResourceRecord, Scope } from "../types";

export default function Diagnostics({ scope, pod, onComplete }: { scope: Scope; pod: ResourceRecord; onComplete?: () => void }) {
  const containers = pod.fields.find((field) => field.label === "Containers")?.value.split(", ").filter(Boolean) ?? [];
  const [container, setContainer] = useState("");
  const [previous, setPrevious] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef<AbortController | null>(null);
  const serial = useRef(0);

  function cancel() {
    serial.current++;
    pending.current?.abort(); pending.current = null;
    setBusy(false); setResult(null); setError("");
  }
  useEffect(() => () => { serial.current++; pending.current?.abort(); }, []);

  async function run(operation: DiagnosticQuery["operation"], target?: "logs" | "events") {
    cancel();
    const id = serial.current;
    const controller = new AbortController(); pending.current = controller;
    setBusy(true);
    const logRequest = operation === "logs" || target === "logs";
    try {
      const loaded = await queryDiagnostics({ generation: scope.generation, operation, pod: pod.name,
        ...(logRequest ? { container, previous } : {}), ...(target ? { target } : {}),
      }, controller.signal);
      if (id === serial.current && !controller.signal.aborted && loaded.scope.generation === scope.generation && loaded.scope.context === scope.context && loaded.scope.namespace === scope.namespace) setResult(loaded);
    } catch (reason) {
      if (id === serial.current && !controller.signal.aborted) setError(reason instanceof Error ? reason.message : "request_failed");
    } finally {
      if (id === serial.current) { setBusy(false); pending.current = null; onComplete?.(); }
    }
  }

  return <section className="panel diagnostics" aria-label="Pod diagnostics">
    <p className="eyebrow">First-party diagnostics · {pod.name}</p><h2>Logs, Events & command explanation</h2>
    <p className="warning">Logs and Events may contain credentials or personal data. Text is not guaranteed redacted. No export or execution is provided.</p>
    <label><input type="checkbox" checked={acknowledged} onChange={(e) => { cancel(); setAcknowledged(e.target.checked); }} /> I understand the sensitive-data warning.</label>
    <div className="diagnostic-controls">
      <label>Container <select value={container} onChange={(e) => { cancel(); setContainer(e.target.value); }}><option value="">Choose explicitly…</option>{containers.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
      <label><input type="checkbox" checked={previous} onChange={(e) => { cancel(); setPrevious(e.target.checked); }} /> Previous container instance</label>
      <button disabled={busy || !acknowledged || !container} onClick={() => void run("logs")}>Read logs</button>
      <button disabled={busy || !acknowledged} onClick={() => void run("events")}>Read Pod Events</button>
      <button disabled={busy || !container} onClick={() => void run("preview", "logs")}>Preview log command</button>
      <button disabled={busy} onClick={() => void run("preview", "events")}>Preview Events command</button>
      <button onClick={cancel}>{busy ? "Cancel request" : "Clear diagnostics"}</button>
    </div>
    <p>Snapshots only: 5 seconds, 64 KiB / 500 log lines, 100 Events. No follow or automatic refresh. Scope or Pod changes clear diagnostics.</p>
    {busy && <p role="status">Reading bounded diagnostics…</p>}
    {error && <p role="alert" className="error">{error}</p>}
    {result && <div aria-live="polite">
      {result.truncated && <p className="warning">A safety limit was reached; this result may be incomplete.</p>}
      {result.operation === "logs" && <pre className="diagnostic-text">{result.text || "No log text returned."}</pre>}
      {result.operation === "events" && (result.events.length ? <ul>{result.events.map((event) => <li key={event.name}><strong>{event.type} · {event.reason} · count {event.count}</strong><pre className="diagnostic-text">{event.message}</pre></li>)}</ul> : <p>No matching Events returned; this is not proof that no Events occurred.</p>)}
      {result.preview && <><h3>Explanation only — not executed</h3><p>{result.preview.note}</p><h4>PowerShell</h4><pre className="diagnostic-text">{result.preview.powershell}</pre><h4>POSIX shell</h4><pre className="diagnostic-text">{result.preview.posix}</pre></>}
    </div>}
  </section>;
}
