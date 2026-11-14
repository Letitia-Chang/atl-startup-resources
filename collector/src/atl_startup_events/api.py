"""Local-first, read-only JSON API. Review changes intentionally use the CLI."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from .connectors import atlanta_today
from .store import Store, utc_now


class ApiHandler(BaseHTTPRequestHandler):
    store: Store
    server_version = "ATLStartupEvents/0.1"

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _one(self, query: dict[str, list[str]], name: str, default: str | None = None) -> str | None:
        values = query.get(name)
        if not values:
            return default
        if len(values) != 1:
            raise ValueError(f"{name} accepts only one value")
        return values[0]

    def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP handler convention
        try:
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query, keep_blank_values=True)
            if parsed.path == "/health":
                self._json(
                    200,
                    {
                        "status": "ok",
                        "time": utc_now(),
                        "events": self.store.counts(),
                        "sources": self.store.source_health(),
                    },
                )
                return
            if parsed.path == "/events":
                state = self._one(query, "state", "approved")
                from_date = self._one(query, "from", atlanta_today().isoformat())
                until_date = self._one(query, "until")
                source = self._one(query, "source")
                limit = int(self._one(query, "limit", "100") or "100")
                events = self.store.list_events(state, from_date, until_date, source, limit)
                self._json(200, {"schemaVersion": 1, "generatedAt": utc_now(), "count": len(events), "events": events})
                return
            if parsed.path.startswith("/events/"):
                event_id = unquote(parsed.path.removeprefix("/events/"))
                if not event_id or "/" in event_id:
                    self._json(404, {"error": "Event not found"})
                    return
                event = self.store.get_event(event_id)
                self._json(200 if event else 404, event or {"error": "Event not found"})
                return
            if parsed.path == "/review":
                limit = int(self._one(query, "limit", "200") or "200")
                events = self.store.list_events("pending", limit=limit)
                self._json(200, {"count": len(events), "events": events})
                return
            self._json(404, {"error": "Not found", "routes": ["/health", "/events", "/events/{id}", "/review"]})
        except (ValueError, TypeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self.log_error("Request failed: %s", exc)
            self._json(500, {"error": "Internal server error"})

    def do_POST(self) -> None:  # noqa: N802
        self.send_response(405)
        self.send_header("Allow", "GET")
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep the standard local access log, but do not log request bodies (the API has none).
        super().log_message(fmt, *args)


def make_server(store: Store, host: str = "127.0.0.1", port: int = 8787) -> HTTPServer:
    handler = type("BoundApiHandler", (ApiHandler,), {"store": store})
    return HTTPServer((host, port), handler)
