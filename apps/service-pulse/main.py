"""Small functional check and read-only board for the SignalForge lab."""

from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Lock, Thread
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


MODE = os.environ.get("PULSE_MODE", "board")
if MODE not in ("board", "probe"):
    raise ValueError("PULSE_MODE must be board or probe")
RESTAURANT_URL = "http://restaurant-api.forge-restaurant.svc.cluster.local:8000/menu"
PROBE_URL = "http://service-pulse-probe.forge-pulse.svc.cluster.local:8080/checks"
INTERVAL_SECONDS = 30
STALE_SECONDS = 90
TIMEOUT_SECONDS = 2
MAX_RESPONSE_BYTES = 4096
SAMPLES = deque(maxlen=20)
SAMPLES_LOCK = Lock()
STOP = Event()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, **fields: object) -> None:
    print(json.dumps({"time": utc_now(), "service": f"service-pulse-{MODE}", "event": event, **fields}, separators=(",", ":")), flush=True)


def read_json(url: str, request_id: str) -> dict:
    request = Request(url, headers={"X-Request-ID": request_id})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("response_too_large")
        if response.status != 200:
            raise ValueError(f"http_{response.status}")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("invalid_response")
        return data


def check_restaurant() -> dict:
    request_id = uuid4().hex
    started = time.monotonic()
    sample: dict = {"observedAt": utc_now(), "sampleId": request_id, "target": "restaurant-api/menu"}
    try:
        data = read_json(RESTAURANT_URL, request_id)
        if not isinstance(data.get("specials"), list) or not isinstance(data.get("restaurant"), str):
            raise ValueError("invalid_menu")
        sample["result"] = "ok"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        sample["result"] = "failed"
        sample["reason"] = f"http_{exc.code}" if isinstance(exc, HTTPError) else (
            str(exc) if isinstance(exc, ValueError) else "unreachable"
        )
    sample["durationMs"] = round((time.monotonic() - started) * 1000)
    with SAMPLES_LOCK:
        SAMPLES.appendleft(sample)
    log_event("functional_check", **sample)
    return sample


def fresh_samples(samples: list) -> bool:
    if not samples:
        return False
    try:
        observed = datetime.fromisoformat(samples[0]["observedAt"])
        age = (datetime.now(timezone.utc) - observed).total_seconds()
        return observed.tzinfo is not None and 0 <= age <= STALE_SECONDS
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def poll() -> None:
    while not STOP.is_set():
        check_restaurant()
        STOP.wait(INTERVAL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        # Intentional JSON logs in handlers below, without client-supplied URLs.
        pass

    def send_body(self, status: int, body: bytes, content_type: str, *, csp: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if csp:
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, value: dict) -> None:
        self.send_body(status, json.dumps(value, separators=(",", ":")).encode(), "application/json")

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_json(200, {"status": "ok"})
        elif MODE == "probe" and self.path == "/checks":
            with SAMPLES_LOCK:
                samples = list(SAMPLES)
            request_id = self.headers.get("X-Request-ID", "missing")
            request_id = request_id if len(request_id) == 32 and all(c in "0123456789abcdef" for c in request_id) else "invalid"
            log_event("checks_read", requestId=request_id, count=len(samples))
            self.send_json(200, {"samples": samples})
        elif MODE == "board" and self.path == "/api/status":
            request_id = uuid4().hex
            started = time.monotonic()
            try:
                data = read_json(PROBE_URL, request_id)
                if not isinstance(data.get("samples"), list):
                    raise ValueError("invalid_checks")
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
                log_event("probe_read", requestId=request_id, result="failed", reason="unavailable")
                self.send_json(502, {"error": "probe_unavailable"})
                return
            data["fresh"] = fresh_samples(data["samples"])
            log_event("probe_read", requestId=request_id, result="ok" if data["fresh"] else "stale", durationMs=round((time.monotonic() - started) * 1000))
            self.send_json(200, data)
        elif MODE == "board" and self.path in ("/", "/board.js", "/board.css"):
            filename, content_type = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/board.js": ("board.js", "text/javascript; charset=utf-8"),
                "/board.css": ("board.css", "text/css; charset=utf-8"),
            }[self.path]
            self.send_body(200, Path(__file__).with_name(filename).read_bytes(), content_type, csp=self.path == "/")
        else:
            self.send_json(404, {"error": "not_found"})


if __name__ == "__main__":
    if MODE == "probe":
        Thread(target=poll, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    try:
        server.serve_forever()
    finally:
        STOP.set()
        server.server_close()
