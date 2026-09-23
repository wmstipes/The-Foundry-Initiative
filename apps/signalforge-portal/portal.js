const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || "your device time zone";
const fullTime = new Intl.DateTimeFormat(undefined, { dateStyle: "full", timeStyle: "long" });
const utcTime = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "long", timeZone: "UTC" });
const byId = id => document.getElementById(id);
byId("zone").textContent = `Your device reports ${zone}.`;

function tick() {
  const now = new Date();
  byId("utc-now").textContent = `${utcTime.format(now)} UTC`;
  byId("local-now").textContent = fullTime.format(now);
}
tick();
setInterval(tick, 1000);

// Require an explicit offset: JavaScript interprets offset-free ISO strings in the browser's local zone.
function parseTimestamp(value) {
  const normalized = value.trim();
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$/i.test(normalized)) return null;
  const timestamp = new Date(normalized);
  return Number.isNaN(timestamp.getTime()) ? null : timestamp;
}
function convert() {
  const parsed = parseTimestamp(byId("utc-input").value);
  const result = byId("converted");
  if (!parsed) {
    result.textContent = "Use an ISO timestamp with an explicit zone, such as 2026-09-23T22:15:58Z.";
    return;
  }
  result.textContent = `${fullTime.format(parsed)} (${zone}) · ${utcTime.format(parsed)} UTC`;
}
byId("convert").addEventListener("click", convert);
byId("utc-input").addEventListener("keydown", event => { if (event.key === "Enter") convert(); });

const hostInput = byId("host");
const storedHost = localStorage.getItem("signalforge-host") || "";
hostInput.value = storedHost;
function updateWorkbench(host) {
  const link = byId("workbench");
  if (host) link.href = `http://${host}:30081/`;
  else link.href = "https://github.com/wmstipes/The-Foundry-Initiative/tree/main/apps/forge-yaml-workbench";
}
updateWorkbench(storedHost);
byId("save-host").addEventListener("click", () => {
  const host = hostInput.value.trim();
  // A hostname or IPv4 address only; never accept URL punctuation in an authority.
  if (host && !/^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/i.test(host)) {
    hostInput.setCustomValidity("Enter a hostname or IPv4 address without a scheme, port, or path.");
    hostInput.reportValidity();
    return;
  }
  hostInput.setCustomValidity("");
  localStorage.setItem("signalforge-host", host);
  updateWorkbench(host);
});
