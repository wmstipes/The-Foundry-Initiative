import type { ActivityEntry, ResourceKind, ResourceRecord, ResourceResult, Scope } from "../types";

const kinds: Array<{ id: ResourceKind; label: string; namespaced: boolean }> = [
  { id: "nodes", label: "Nodes", namespaced: false }, { id: "deployments", label: "Deployments", namespaced: true },
  { id: "replicasets", label: "ReplicaSets", namespaced: true }, { id: "pods", label: "Pods", namespaced: true },
  { id: "services", label: "Services", namespaced: true }, { id: "endpointslices", label: "EndpointSlices", namespaced: true },
];

interface Props {
  scope: Scope; kind: ResourceKind; result: ResourceResult | null; selected: ResourceRecord | null;
  busy: boolean; history: ActivityEntry[]; onKind(kind: ResourceKind): void; onRefresh(): void; onSelect(record: ResourceRecord): void;
}

export default function ResourceBrowser({ scope, kind, result, selected, busy, history, onKind, onRefresh, onSelect }: Props) {
  return <section className="resource-shell">
    <nav className="resource-nav" aria-label="Kubernetes resources"><p className="eyebrow">Resources</p>{kinds.map((item) => <button type="button" className={kind === item.id ? "active" : ""} disabled={!scope.context || (item.namespaced && !scope.namespace) || busy} onClick={() => onKind(item.id)} key={item.id}>{item.label}</button>)}</nav>
    <div className="resource-main panel">
      <div className="resource-heading"><div><p className="eyebrow">Fixed projection</p><h2>{kinds.find((item) => item.id === kind)?.label}</h2></div><button type="button" disabled={busy || !scope.context || (kind !== "nodes" && !scope.namespace)} onClick={onRefresh}>{busy ? "Loading…" : "Refresh"}</button></div>
      {result?.truncated && <p className="warning">Result may be incomplete: an object, relationship, or pagination limit was reached.</p>}
      {!result && <div className="empty-state">Select a resource after setting the required scope.</div>}
      {result && !result.items.length && <div className="empty-state">No projected objects were returned.</div>}
      {result && result.items.length > 0 && <div className="resource-grid"><div className="resource-table" role="list">{result.items.map((item) => <button type="button" className={selected?.name === item.name ? "resource-row selected" : "resource-row"} disabled={busy} onClick={() => onSelect(item)} key={`${item.kind}/${item.namespace}/${item.name}`}><strong>{item.name}</strong><span>{item.status || "—"}</span></button>)}</div><aside className="detail-panel">{selected ? <><p className="eyebrow">{selected.kind}</p><h3>{selected.name}</h3><dl>{selected.fields.map((field) => <div key={field.label}><dt>{field.label}</dt><dd>{field.value || "—"}</dd></div>)}</dl>{selected.owners.length > 0 && <Relations title="Owners" records={selected.owners} />}{selected.related.length > 0 && <Relations title="Relationships" records={selected.related} />}</> : <p className="empty-state">Choose an object to inspect its bounded details.</p>}</aside></div>}
    </div>
    <aside className="activity-panel panel"><p className="eyebrow">Activity</p><h3>Session requests</h3>{history.length === 0 ? <p className="empty-state">No resource activity yet.</p> : <ol>{history.slice(-8).reverse().map((entry) => <li key={entry.sequence}><strong>{entry.outcome}</strong><span>{entry.context}/{entry.namespace || "cluster"}</span><small>gen {entry.generation} · {entry.itemCount} items</small></li>)}</ol>}</aside>
  </section>;
}

function Relations({ title, records }: { title: string; records: ResourceRecord["related"] }) {
  return <div className="relations"><h4>{title}</h4>{records.map((record) => <p key={`${record.relation}/${record.kind}/${record.name}`}><span>{record.relation}</span> {record.kind}/{record.name}</p>)}</div>;
}
