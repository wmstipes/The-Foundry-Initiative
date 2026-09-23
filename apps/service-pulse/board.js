const state = document.getElementById("state");
const checks = document.getElementById("checks");
async function refresh() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Probe unavailable");
    const data = await response.json();
    checks.replaceChildren();
    for (const sample of data.samples) {
      const row = document.createElement("li");
      row.className = sample.result === "ok" ? "ok" : "failed";
      row.textContent = `${sample.observedAt} · ${sample.target} · ${sample.result} · ${sample.durationMs} ms${sample.reason ? ` · ${sample.reason}` : ""}`;
      checks.append(row);
    }
    state.textContent = !data.samples.length ? "Waiting for the first check" : !data.fresh ? `Stale: last check at ${data.samples[0].observedAt}` : `Latest: ${data.samples[0].result} (${data.samples[0].observedAt})`;
  } catch {
    state.textContent = "Probe unavailable; recent status cannot be confirmed.";
    checks.replaceChildren();
  }
}
refresh();
setInterval(refresh, 15000);
