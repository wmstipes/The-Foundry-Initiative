import type { ActivityEntry, ResourceKind, ResourceRecord, ResourceResult, Scope } from "../types";

const kinds: Array<{ id: ResourceKind; label: string; namespaced: boolean }> = [
  { id: "nodes", label: "Nodes", namespaced: false }, { id: "deployments", label: "Deployments", namespaced: true },
  { id: "replicasets", label: "ReplicaSets", namespaced: true }, { id: "pods", label: "Pods", namespaced: true },
  { id: "services", label: "Services", namespaced: true }, { id: "endpointslices", label: "EndpointSlices", namespaced: true },
];

interface Props {
  scope: Scope; kind: ResourceKind; result: ResourceResult | null; selected: ResourceRecord | null;
  busy: boolean; history: ActivityEntry[]; onKind(kind: ResourceKind): void; onRefresh(): void; onSelect(record: ResourceRecord): void; onPodTarget(name: string, uid?: string): void;
}

export default function ResourceBrowser({ scope, kind, result, selected, busy, history, onKind, onRefresh, onSelect, onPodTarget }: Props) {
  return <section className="resource-shell">
    <nav className="resource-nav" aria-label="Kubernetes resources"><p className="eyebrow">Resources</p>{kinds.map((item) => <button type="button" className={kind === item.id ? "active" : ""} aria-current={kind === item.id ? "page" : undefined} disabled={!scope.context || (item.namespaced && !scope.namespace) || busy} onClick={() => onKind(item.id)} key={item.id}>{item.label}</button>)}</nav>
    <div className="resource-main panel">
      <div className="resource-heading"><div><p className="eyebrow">Fixed projection</p><h2>{kinds.find((item) => item.id === kind)?.label}</h2></div><button type="button" disabled={busy || !scope.context || (kind !== "nodes" && !scope.namespace)} onClick={onRefresh}>{busy ? "Loading…" : "Refresh"}</button></div>
      {result?.truncated && <p className="warning">Result may be incomplete: an object, relationship, or pagination limit was reached.</p>}
      {!result && <div className="empty-state">Select a resource after setting the required scope.</div>}
      {result && !result.items.length && <div className="empty-state">No projected objects were returned.</div>}
      {result && result.items.length > 0 && <div className="resource-grid"><ul className="resource-table" aria-label="Resource objects">{result.items.map((item) => <li key={`${item.kind}/${item.namespace}/${item.name}`}><button type="button" className={selected?.name === item.name ? "resource-row selected" : "resource-row"} disabled={busy} onClick={() => onSelect(item)} aria-pressed={selected?.name === item.name}><strong>{item.name}</strong><span>{item.status || "—"}</span></button></li>)}</ul><aside className="detail-panel">{selected ? <><p className="eyebrow">{selected.kind}</p><h3>{selected.name}</h3><dl>{selected.fields.map((field) => <div key={field.label}><dt>{field.label}</dt><dd>{field.value || "—"}</dd></div>)}</dl>{selected.owners.length > 0 && <Relations title="Owners" records={selected.owners} />}{selected.related.length > 0 && <Relations title="Relationships" records={selected.related} onPodTarget={selected.kind === "EndpointSlice" ? onPodTarget : undefined} busy={busy} />}{selected.kind === "EndpointSlice" && <><p className="warning">Next check: inspect the Pod target of any endpoint with ready=false, then review its Ready condition, Events, and bounded logs. Endpoint readiness does not establish Pod failure or an outage start time.</p>{selected.related.some((ref) => ref.relation === "endpoint-target" && !ref.uid) && <p className="warning">Some endpoint targets have no UID. A name-only Pod read cannot verify that the Pod is the same object.</p>}</>}</> : <p className="empty-state">Choose an object to inspect its bounded details.</p>}</aside></div>}
    </div>
    <aside className="activity-panel panel"><details><summary>Activity · Session requests <span>({history.length > 8 ? `latest 8 of ${history.length}` : history.length})</span></summary>{history.length === 0 ? <p className="empty-state">No resource activity yet.</p> : <ol>{history.slice(-8).reverse().map((entry) => <li key={entry.sequence}><strong>{entry.outcome}</strong><span>{entry.context}/{entry.namespace || "cluster"}</span><small>gen {entry.generation} · {entry.itemCount} items</small></li>)}</ol>}</details></aside>
  </section>;
}

function Relations({ title, records, onPodTarget, busy }: { title: string; records: ResourceRecord["related"]; onPodTarget?: (name: string, uid?: string) => void; busy?: boolean }) {
  return <div className="relations"><h4>{title}</h4>{records.map((record, index) => <p key={`${record.relation}/${record.kind}/${record.name}/${index}`}><span>{record.relation}</span> {record.kind}/{record.name}{record.kind === "Pod" && record.relation === "endpoint-target" && onPodTarget && <button type="button" disabled={busy} onClick={() => onPodTarget(record.name, record.uid)} aria-label={`Inspect Pod ${record.name}${record.uid ? "" : " by name only"}`}>Inspect Pod{record.uid ? "" : " (name only)"}</button>}</p>)}</div>;
}
