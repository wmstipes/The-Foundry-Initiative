# SignalForge Home

Static, browser-only landing page for the lab. Preview from this directory with `python -m http.server 8088` and open `http://127.0.0.1:8088/`. No build or external JavaScript dependencies. The time converter uses the browser's IANA time zone and accepts an ISO 8601 timestamp with an explicit UTC marker or offset; missing offsets are rejected to prevent a silent local-time interpretation. Your cluster node address is stored only in browser localStorage; the portal makes no requests to the Kubernetes API.

Workbench uses NodePort 30081 on the address you enter. Pulse and Grafana links assume port-forwards on **the same device as the browser**. The other links point to repository setup pages until their own access addresses are known. This portal is a preview, not yet a deployed service or a public gateway.
