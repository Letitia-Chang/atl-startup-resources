from __future__ import annotations

import contextlib
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from atl_startup_events.api import make_server
from atl_startup_events.cli import main as cli_main
from atl_startup_events.connectors import ATDCConnector, AtlantaTechVillageConnector
from atl_startup_events.models import Event, canonical_url, infer_access, parse_time
from atl_startup_events.pipeline import FetchResult, HttpClient, CollectionError, ingest_fixture, refresh_source
from atl_startup_events.store import Store

FIXTURES = Path(__file__).parent / "fixtures"
REFERENCE = date(2026, 11, 13)


def event(**changes: object) -> Event:
    values: dict[str, object] = {
        "source": "atlanta-tech-village",
        "external_id": "founder-night-2026-11-20",
        "title": "Founder Night",
        "source_url": "https://atlantatechvillage.com/events/founder-night",
        "start_date": "2026-11-20",
        "venue": "Terminus Hub",
        "registration_url": "https://www.eventbrite.com/e/founder-night-123?utm_source=test",
    }
    values.update(changes)
    return Event(**values)  # type: ignore[arg-type]


class ModelTests(unittest.TestCase):
    def test_timezone_and_date_only_precision(self) -> None:
        value = event(start_time="17:30", end_time="19:00")
        self.assertEqual(value.start_at, "2026-11-20T17:30:00-05:00")
        self.assertEqual(value.end_at, "2026-11-20T19:00:00-05:00")
        self.assertIsNone(event().start_at)

    def test_urls_topics_and_access_are_normalized(self) -> None:
        value = event(title="SBIR Grant Workshop", registration_url="https://www.eventbrite.com/e/test/?utm_source=x#top")
        self.assertEqual(canonical_url(value.registration_url or ""), "https://eventbrite.com/e/test")
        self.assertIn("funding", value.topics)
        self.assertIn("education", value.topics)
        self.assertEqual(infer_access("Invite-only founder session"), "invite-only")
        self.assertEqual(parse_time("2:00 PM"), "14:00")
        self.assertEqual(canonical_url("https://example.com/register?b=2&utm_source=x&a=1"), "https://example.com/register?a=1&b=2")

    def test_invalid_or_ambiguous_fields_fail(self) -> None:
        with self.assertRaises(ValueError):
            event(start_time="6:00 PM")
        with self.assertRaises(ValueError):
            event(start_date="Next Friday")
        with self.assertRaises(ValueError):
            event(source_url="http://not-encrypted.example/events/1")
        with self.assertRaises(ValueError):
            event(end_time="18:00")


class ConnectorTests(unittest.TestCase):
    def test_atv_list_and_detail(self) -> None:
        connector = AtlantaTechVillageConnector()
        events = connector.parse((FIXTURES / "atv-events.html").read_bytes(), REFERENCE, 120)
        self.assertEqual(len(events), 2)
        first = events[0]
        self.assertEqual(first.external_id, "r-e-p-s-podcasts-20261117")
        self.assertEqual(first.start_date, "2026-11-17")
        self.assertIsNone(first.start_time)
        enriched = connector.enrich(first, (FIXTURES / "atv-detail.html").read_bytes())
        self.assertEqual(enriched.start_time, "14:00")
        self.assertEqual(enriched.end_time, "16:00")
        self.assertIn("Terminus Hub", enriched.venue)
        self.assertEqual(enriched.registration_url, "https://www.eventbrite.com/e/reps-podcasts-tickets-2002658757253?utm_source=calendar")
        self.assertEqual(enriched.format, "in-person")

    def test_atv_reused_detail_date_never_enriches_another_occurrence(self) -> None:
        connector = AtlantaTechVillageConnector()
        event = connector.parse((FIXTURES / "atv-events.html").read_bytes(), REFERENCE, 120)[0]
        detail = (FIXTURES / "atv-detail.html").read_text().replace(
            "Tuesday, November 17, 2026", "Tuesday, November 24, 2026"
        )
        enriched = connector.enrich(event, detail)
        self.assertEqual(enriched.start_date, event.start_date)
        self.assertIsNone(enriched.start_time)
        self.assertIsNone(enriched.registration_url)
        self.assertEqual(enriched.venue, "")
        self.assertTrue(any("did not match" in warning for warning in connector.warnings))

    def test_atdc_access_format_and_source_urls(self) -> None:
        connector = ATDCConnector()
        events = connector.parse((FIXTURES / "atdc-events.html").read_bytes(), REFERENCE, 120)
        self.assertEqual(len(events), 3)
        self.assertIn("ai", events[0].topics)
        self.assertEqual(events[0].format, "in-person")
        self.assertEqual(events[1].format, "virtual")
        self.assertEqual(events[2].access, "invite-only")
        self.assertTrue(events[0].source_url.startswith("https://portal.atdc.org/s/events/"))

    def test_empty_markup_is_a_source_warning_not_an_empty_success(self) -> None:
        connector = ATDCConnector()
        self.assertEqual(connector.parse(b"<html><body>Loading</body></html>", REFERENCE, 120), [])
        self.assertTrue(connector.warnings)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "events.db")

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_review_dedupe_update_and_recurring_instances(self) -> None:
        first_id, state = self.store.upsert(event(), "2026-11-13T18:00:00+00:00")
        self.assertEqual(state, "pending")
        self.assertTrue(self.store.review(first_id, "approved"))
        updated = event(description="Newly enriched description")
        self.assertEqual(self.store.upsert(updated, "2026-11-13T19:00:00+00:00")[0], first_id)
        self.assertEqual(self.store.get_event(first_id)["reviewState"], "approved")

        same_other_source = event(source="atdc", external_id="atdc-founder-night-456", source_url="https://portal.atdc.org/s/events/founder-night")
        self.assertEqual(self.store.upsert(same_other_source, "2026-11-13T19:00:00+00:00")[0], first_id)
        self.assertEqual(len(self.store.get_event(first_id)["sources"]), 2)

        # Even an identical registration URL must not merge recurring sessions.
        recurring = event(external_id="founder-night-2026-11-27", start_date="2026-11-27")
        recurring_id, _ = self.store.upsert(recurring, "2026-11-13T19:00:00+00:00")
        self.assertNotEqual(recurring_id, first_id)
        self.store.record_run("atlanta-tech-village", "2026-11-14T00:00:00+00:00", "ok", 1, seen_ids=[event().external_id])
        missed = self.store.get_event(recurring_id)
        self.assertEqual(missed["sources"][0]["misses"], 1)
        self.assertIsNotNone(missed)

    def test_cli_approve_maps_to_approved_state(self) -> None:
        event_id, _ = self.store.upsert(event(), "2026-11-13T18:00:00+00:00")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = cli_main(["--db", str(self.store.path), "review", "approve", "--all-pending"])
        self.assertEqual(result, 0)
        self.assertIn('"updated": 1', output.getvalue())
        self.assertEqual(self.store.get_event(event_id)["reviewState"], "approved")

    def test_approved_and_pending_are_separated(self) -> None:
        approved_id, _ = self.store.upsert(event(), "2026-11-13T18:00:00+00:00")
        self.store.review(approved_id, "approved")
        self.store.upsert(event(external_id="pending-event", title="Pending Event", start_date="2026-11-21", registration_url=None), "2026-11-13T18:00:00+00:00")
        self.assertEqual(len(self.store.list_events("approved", from_date="2026-11-01")), 1)
        self.assertEqual(len(self.store.list_events("pending", from_date="2026-11-01")), 1)
        self.assertEqual(len(self.store.list_events("all", from_date="2026-11-01")), 2)


class PipelineAndApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "events.db")

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_fixture_refresh_is_labelled_and_http_failure_preserves_data(self) -> None:
        ids = ingest_fixture(self.store, "atdc", (FIXTURES / "atdc-events.html").read_bytes(), REFERENCE)
        self.assertEqual(len(ids), 3)
        health = self.store.source_health()[0]
        self.assertEqual(health["status"], "fixture")

        class FailingClient:
            def get(self, url: str) -> object:
                raise RuntimeError("network unavailable")

        result = refresh_source(ATDCConnector(), self.store, FailingClient(), REFERENCE, 120, False)  # type: ignore[arg-type]
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(self.store.list_events("all", from_date="2026-11-01")), 3)

    def test_detail_failure_keeps_listing_events(self) -> None:
        connector = AtlantaTechVillageConnector()

        class ListingOnlyClient:
            def get(self, url: str) -> FetchResult:
                if url == connector.url:
                    return FetchResult((FIXTURES / "atv-events.html").read_bytes())
                raise CollectionError("detail unavailable")

        result = refresh_source(connector, self.store, ListingOnlyClient(), REFERENCE, 120, False)  # type: ignore[arg-type]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["events"], 2)
        self.assertEqual(len(result["warnings"]), 2)
        self.assertEqual(len(self.store.list_events("all", from_date="2026-11-01")), 2)

    def test_conditional_http_304_reuses_cached_body(self) -> None:
        client = HttpClient(self.store, retries=0)
        url = "https://example.com/events"
        client.allowed = lambda _url: True  # type: ignore[method-assign]

        class Response:
            headers = {"ETag": "version-1"}

            def geturl(self) -> str:
                return url

        client._open = lambda _request: (b"event-page", Response())  # type: ignore[method-assign]
        self.assertEqual(client.get(url).body, b"event-page")

        def not_modified(_request: object) -> object:
            raise urllib.error.HTTPError(url, 304, "Not Modified", {}, None)

        client._open = not_modified  # type: ignore[method-assign]
        second = client.get(url)
        self.assertEqual(second.body, b"event-page")
        self.assertTrue(second.from_cache)

    def test_api_readonly_event_filters_and_review_queue(self) -> None:
        approved_id, _ = self.store.upsert(event(), "2026-11-13T18:00:00+00:00")
        self.store.review(approved_id, "approved")
        self.store.upsert(event(external_id="pending-event", title="Pending Event", registration_url=None), "2026-11-13T18:00:00+00:00")
        server = make_server(self.store, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(base + "/events?from=2026-11-01&state=approved") as response:
                payload = json.load(response)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["events"][0]["id"], approved_id)
            with urllib.request.urlopen(base + "/review") as response:
                review = json.load(response)
            self.assertEqual(review["count"], 1)
            with urllib.request.urlopen(base + f"/events/{approved_id}") as response:
                self.assertEqual(json.load(response)["id"], approved_id)
            with self.assertRaises(urllib.error.HTTPError) as bad_state:
                urllib.request.urlopen(base + "/events?state=nonsense")
            self.assertEqual(bad_state.exception.code, 400)
            bad_state.exception.close()
            request = urllib.request.Request(base + "/events", data=b"{}", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as post:
                urllib.request.urlopen(request)
            self.assertEqual(post.exception.code, 405)
            post.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
