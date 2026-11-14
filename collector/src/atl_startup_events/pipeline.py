"""Conservative HTTP collection, source refresh, and JSON export."""

from __future__ import annotations

import gzip
import logging
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .connectors import CONNECTORS, Connector, atlanta_today
from .models import Event
from .store import Store, utc_now

LOGGER = logging.getLogger(__name__)
USER_AGENT = "ATLStartupEvents/0.1"
MAX_RESPONSE_BYTES = 3_000_000
SIX_HOURS = 6 * 60 * 60


class CollectionError(RuntimeError):
    pass


@dataclass(slots=True)
class FetchResult:
    body: bytes
    from_cache: bool = False


class HttpClient:
    def __init__(self, store: Store, timeout: float = 25, retries: int = 2) -> None:
        self.store = store
        self.timeout = timeout
        self.retries = retries
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _pace(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        remaining = 1.0 - (time.monotonic() - self._last_request.get(host, 0))
        if remaining > 0:
            time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def _open(self, request: urllib.request.Request) -> tuple[bytes, Any]:
        self._pace(request.full_url)
        response = urllib.request.urlopen(request, timeout=self.timeout)
        try:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise CollectionError(f"Response exceeds {MAX_RESPONSE_BYTES} bytes")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise CollectionError(f"Response exceeds {MAX_RESPONSE_BYTES} bytes")
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            final_url = response.geturl()
            if urlsplit(final_url).scheme != "https":
                raise CollectionError(f"Refusing non-HTTPS redirect: {final_url}")
            return body, response
        finally:
            response.close()

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise CollectionError(f"Only HTTPS collection is allowed: {url}")
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            robots_url = origin + "/robots.txt"
            request = urllib.request.Request(
                robots_url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain"}
            )
            try:
                body, response = self._open(request)
                parser = urllib.robotparser.RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(body.decode("utf-8", errors="replace").splitlines())
                self._robots[origin] = parser
            except urllib.error.HTTPError as exc:
                if exc.code in {401, 403}:
                    self._robots[origin] = None
                elif exc.code == 404:
                    parser = urllib.robotparser.RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse([])
                    self._robots[origin] = parser
                else:
                    raise CollectionError(f"Could not read robots.txt ({exc.code})") from exc
        parser = self._robots[origin]
        return parser is not None and parser.can_fetch(USER_AGENT, url)

    def get(self, url: str) -> FetchResult:
        if not self.allowed(url):
            raise CollectionError(f"robots.txt does not allow collection: {url}")
        cached = self.store.cache_get(url)
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
        if cached:
            if cached["etag"]:
                headers["If-None-Match"] = cached["etag"]
            if cached["last_modified"]:
                headers["If-Modified-Since"] = cached["last_modified"]
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(self.retries + 1):
            try:
                body, response = self._open(request)
                self.store.cache_put(url, body, response.headers.get("ETag"), response.headers.get("Last-Modified"))
                return FetchResult(body)
            except urllib.error.HTTPError as exc:
                if exc.code == 304 and cached:
                    exc.close()
                    return FetchResult(cached["body"], from_cache=True)
                if exc.code not in {408, 425, 429, 500, 502, 503, 504} or attempt >= self.retries:
                    raise CollectionError(f"HTTP {exc.code} for {url}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt >= self.retries:
                    raise CollectionError(f"Request failed for {url}: {exc}") from exc
            delay = 2**attempt
            LOGGER.warning("Retrying %s in %ss", url, delay)
            time.sleep(delay)
        raise AssertionError("unreachable")


def render_page(url: str, timeout_ms: int = 45_000) -> bytes:
    """Render one public ATDC page, without signing in or interacting with controls."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CollectionError(
            "ATDC needs browser rendering for this response; install the 'browser' extra and Chromium"
        ) from exc
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # The portal has unrelated headings (for example, Change Currency).
            # Wait for a dated public event card, not merely the first h3.
            page.wait_for_function(
                r"""() => Array.from(document.querySelectorAll('h3')).some((heading) => {
                    let node = heading;
                    for (let depth = 0; depth < 6 && node; depth += 1, node = node.parentElement) {
                        if (/\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}\b/i.test(node.innerText || '') && node.querySelectorAll('h3').length === 1) return true;
                    }
                    return false;
                })""",
                timeout=timeout_ms,
            )
            return page.content().encode()
        finally:
            browser.close()


def refresh_source(
    connector: Connector,
    store: Store,
    client: HttpClient,
    reference: date,
    days: int,
    allow_browser: bool,
) -> dict[str, Any]:
    started = utc_now()
    warnings: list[str] = []
    seen_ids: list[str] = []
    try:
        raw = client.get(connector.url).body
        events = connector.parse(raw, reference, days)
        warnings.extend(connector.warnings)
        if not events and connector.key == "atdc" and allow_browser:
            LOGGER.info("ATDC returned no static events; trying public browser rendering")
            raw = render_page(connector.url)
            # Keep a distinct diagnostic snapshot; never substitute rendered bytes
            # for the conditional HTTP cache keyed by the actual request URL.
            store.cache_put(connector.url + "#rendered", raw, None, None)
            events = connector.parse(raw, reference, days)
            warnings.extend(connector.warnings)
        if not events:
            raise CollectionError("No events parsed; source changed or currently has no listed events")

        enrichable = getattr(connector, "enrich", None)
        detail_limit = getattr(connector, "detail_limit", 0)
        for index, base_event in enumerate(events):
            event = base_event
            if enrichable and index < detail_limit:
                try:
                    event = enrichable(base_event, client.get(base_event.source_url).body)
                except Exception as exc:  # Keep the useful listing event when only detail fetch fails.
                    warnings.append(f"Detail enrichment failed for {base_event.source_url}: {exc}")
            try:
                store.upsert(event, utc_now())
                seen_ids.append(event.external_id)
            except (ValueError, TypeError) as exc:
                warnings.append(f"Rejected invalid {event.source} event {event.title!r}: {exc}")
        if not seen_ids:
            raise CollectionError("Every parsed event failed validation")
        store.record_run(
            connector.key,
            started,
            "ok",
            len(seen_ids),
            warnings=warnings,
            seen_ids=seen_ids,
        )
        return {"source": connector.key, "status": "ok", "events": len(seen_ids), "warnings": warnings}
    except Exception as exc:
        LOGGER.warning("%s refresh failed: %s", connector.key, exc)
        store.record_run(connector.key, started, "error", 0, warnings=warnings, error=str(exc))
        return {"source": connector.key, "status": "error", "events": 0, "warnings": warnings, "error": str(exc)}


def refresh(
    store: Store,
    source_names: list[str] | None = None,
    reference: date | None = None,
    days: int = 120,
    allow_browser: bool = True,
) -> list[dict[str, Any]]:
    names = source_names or list(CONNECTORS)
    unknown = sorted(set(names) - set(CONNECTORS))
    if unknown:
        raise ValueError(f"Unknown sources: {', '.join(unknown)}")
    if days < 1:
        raise ValueError("days must be positive")
    client = HttpClient(store)
    return [
        refresh_source(CONNECTORS[name], store, client, reference or atlanta_today(), days, allow_browser)
        for name in names
    ]


def ingest_fixture(
    store: Store,
    source_name: str,
    body: bytes,
    reference: date,
    days: int = 120,
) -> list[str]:
    """Explicitly labelled fixture input for connector development; never a live refresh."""
    connector = CONNECTORS[source_name]
    events = connector.parse(body, reference, days)
    started = utc_now()
    ids = [store.upsert(event, utc_now())[0] for event in events]
    store.record_run(
        source_name,
        started,
        "fixture",
        len(ids),
        warnings=connector.warnings + ["Fixture input only; no network request made"],
        seen_ids=ids,
    )
    return ids
