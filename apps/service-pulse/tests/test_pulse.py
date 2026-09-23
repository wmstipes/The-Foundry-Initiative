import io
import importlib.util
import json
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen
from urllib.parse import urlsplit
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("pulse_main", Path(__file__).resolve().parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)


class Response:
    status = 200

    def __init__(self, data):
        self.body = io.BytesIO(json.dumps(data).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self, count):
        return self.body.read(count)


class PulseTests(unittest.TestCase):
    def setUp(self):
        main.SAMPLES.clear()

    def test_restaurant_check_uses_clusterip_service_port(self):
        # The tracked Restaurant ClusterIP Service exposes port 80; its container uses 8000.
        url = urlsplit(main.RESTAURANT_URL)
        self.assertEqual(url.hostname, "restaurant-api.forge-restaurant.svc.cluster.local")
        self.assertEqual(url.port, 80)
        self.assertEqual(url.path, "/menu")

    def test_functional_check_records_bounded_success_and_request_identity(self):
        with patch.object(main, "urlopen", return_value=Response({"restaurant": "SignalForge Grill", "specials": ["Soup"]})) as fetch, patch.object(main, "log_event"):
            result = main.check_restaurant()
        self.assertEqual(result["result"], "ok")
        self.assertEqual(result["target"], "restaurant-api/menu")
        self.assertEqual(fetch.call_args.args[0].headers["X-request-id"], result["sampleId"])
        self.assertEqual(len(main.SAMPLES), 1)

    def test_http_failure_is_a_sample_without_response_body(self):
        from urllib.error import HTTPError
        with patch.object(main, "urlopen", side_effect=HTTPError(main.RESTAURANT_URL, 503, "unavailable", {}, None)), patch.object(main, "log_event"):
            result = main.check_restaurant()
        self.assertEqual((result["result"], result["reason"]), ("failed", "http_503"))

    def test_unexpected_menu_shape_fails_and_history_has_fixed_limit(self):
        with patch.object(main, "urlopen", side_effect=lambda *_args, **_kwargs: Response({"specials": "wrong"})), patch.object(main, "log_event"):
            for _ in range(25):
                result = main.check_restaurant()
        self.assertEqual((result["result"], result["reason"]), ("failed", "invalid_menu"))
        self.assertEqual(len(main.SAMPLES), 20)

    def test_old_success_cannot_be_presented_as_current_health(self):
        self.assertFalse(main.fresh_samples([{"observedAt": "2020-01-01T00:00:00+00:00", "result": "ok"}]))
        self.assertFalse(main.fresh_samples([]))

    def test_board_fetches_probe_with_request_identity_and_freshness(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), main.Handler)
        worker = Thread(target=server.serve_forever)
        worker.start()
        sample = {"observedAt": datetime.now(timezone.utc).isoformat(), "result": "ok"}
        try:
            with patch.object(main, "read_json", return_value={"samples": [sample]}) as fetch, patch.object(main, "log_event"):
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/status") as response:
                    data = json.load(response)
            self.assertTrue(data["fresh"])
            self.assertEqual(data["samples"], [sample])
            self.assertEqual(fetch.call_args.args[0], main.PROBE_URL)
            self.assertEqual(len(fetch.call_args.args[1]), 32)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_board_reports_probe_failure_without_claiming_restaurant_outage(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), main.Handler)
        worker = Thread(target=server.serve_forever)
        worker.start()
        try:
            from urllib.error import HTTPError
            with patch.object(main, "read_json", side_effect=TimeoutError()), patch.object(main, "log_event"):
                with self.assertRaises(HTTPError) as error:
                    urlopen(f"http://127.0.0.1:{server.server_port}/api/status")
            self.assertEqual(error.exception.code, 502)
            self.assertEqual(json.load(error.exception)["error"], "probe_unavailable")
        finally:
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == "__main__":
    unittest.main()
