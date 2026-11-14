"""Command-line entry point for refresh, review, export, and local API serving."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

from .api import make_server
from .connectors import CONNECTORS, atlanta_today
from .pipeline import SIX_HOURS, ingest_fixture, refresh
from .store import Store, utc_now


def export_events(store: Store, output: Path, state: str = "approved") -> int:
    events = store.list_events(state=state, from_date=atlanta_today().isoformat(), limit=200)
    payload = {
        "schemaVersion": 1,
        "generatedAt": utc_now(),
        "count": len(events),
        "events": events,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return len(events)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atl-events", description=__doc__)
    parser.add_argument("--db", default="var/events.db", help="SQLite path (default: var/events.db)")
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    refresh_parser = sub.add_parser("refresh", help="Collect public sources now or on a six-hour schedule")
    refresh_parser.add_argument("--source", action="append", choices=sorted(CONNECTORS))
    refresh_parser.add_argument("--days", type=int, default=120, help="Future collection window")
    refresh_parser.add_argument("--no-browser", action="store_true", help="Disable ATDC browser fallback")
    refresh_parser.add_argument("--watch", action="store_true", help="Repeat every six hours")
    refresh_parser.add_argument("--export", type=Path, help="Atomically export approved upcoming events after each run")

    ingest = sub.add_parser("ingest-fixture", help="Development only: parse saved HTML without making requests")
    ingest.add_argument("source", choices=sorted(CONNECTORS))
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--reference-date", type=date.fromisoformat, default=atlanta_today())
    ingest.add_argument("--days", type=int, default=120)

    review = sub.add_parser("review", help="Inspect or change event review state")
    review.add_argument("action", choices=("list", "approve", "reject", "pending"))
    review.add_argument("event_ids", nargs="*", metavar="event-id")
    review.add_argument("--all-pending", action="store_true", help="Apply action to every pending event")

    export = sub.add_parser("export", help="Write an API-compatible events JSON snapshot")
    export.add_argument("--output", type=Path, default=Path("build/events.json"))
    export.add_argument("--state", choices=("approved", "pending", "rejected", "all"), default="approved")

    serve = sub.add_parser("serve", help="Serve the read-only API (binds to localhost by default)")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)

    sub.add_parser("sources", help="Show the latest source health run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    with Store(args.db) as store:
        if args.command == "refresh":
            def run_once() -> list[dict[str, object]]:
                results = refresh(
                    store,
                    source_names=args.source,
                    days=args.days,
                    allow_browser=not args.no_browser,
                )
                for result in results:
                    print(json.dumps(result, ensure_ascii=False))
                if args.export:
                    print(json.dumps({"exported": export_events(store, args.export), "output": str(args.export)}))
                return results

            if not args.watch:
                results = run_once()
                return 1 if any(result["status"] == "error" for result in results) else 0
            while True:
                run_once()
                time.sleep(SIX_HOURS)
        if args.command == "ingest-fixture":
            ids = ingest_fixture(store, args.source, args.file.read_bytes(), args.reference_date, args.days)
            print(json.dumps({"mode": "fixture", "eventIds": ids, "count": len(ids)}, indent=2))
            return 0 if ids else 1
        if args.command == "review":
            if args.action == "list":
                events = store.list_events("pending", limit=200)
                print(json.dumps({"count": len(events), "events": events}, indent=2))
                return 0
            if args.all_pending == bool(args.event_ids):
                raise SystemExit("Provide event IDs or --all-pending, not both")
            state = {"approve": "approved", "reject": "rejected", "pending": "pending"}[args.action]
            if args.all_pending:
                count = store.review_all_pending(state)
            else:
                count = sum(store.review(event_id, state) for event_id in args.event_ids)
                if count != len(args.event_ids):
                    raise SystemExit("One or more event IDs were not found")
            print(json.dumps({"action": args.action, "updated": count}))
            return 0
        if args.command == "export":
            count = export_events(store, args.output, args.state)
            print(json.dumps({"output": str(args.output), "count": count}))
            return 0
        if args.command == "serve":
            server = make_server(store, args.host, args.port)
            print(f"Read-only events API: http://{args.host}:{args.port}/events", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return 0
        if args.command == "sources":
            print(json.dumps(store.source_health(), indent=2))
            return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
