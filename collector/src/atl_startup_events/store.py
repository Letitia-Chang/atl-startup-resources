"""SQLite persistence, source health, review workflow, and read models."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import Event

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    dedupe_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    start_date TEXT NOT NULL,
    start_time TEXT,
    review_state TEXT NOT NULL CHECK (review_state IN ('pending', 'approved', 'rejected')),
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_start ON events(start_date, start_time);
CREATE INDEX IF NOT EXISTS events_review ON events(review_state, start_date);
CREATE TABLE IF NOT EXISTS event_sources (
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    misses INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (source, external_id)
);
CREATE INDEX IF NOT EXISTS event_sources_event ON event_sources(event_id);
CREATE TABLE IF NOT EXISTS review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL,
    event_count INTEGER NOT NULL,
    warnings TEXT NOT NULL DEFAULT '[]',
    error TEXT
);
CREATE TABLE IF NOT EXISTS http_cache (
    url TEXT PRIMARY KEY,
    etag TEXT,
    last_modified TEXT,
    body BLOB NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # API integration tests and embedders may serve in a dedicated thread.
        # The default HTTPServer is serial; callers using threaded servers must
        # provide their own connection-per-thread or request serialization.
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert(self, event: Event, seen_at: str) -> tuple[str, str]:
        payload = json.dumps(event.to_payload(), sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(payload.encode()).hexdigest()
        with self.conn:
            source_row = self.conn.execute(
                "SELECT event_id FROM event_sources WHERE source=? AND external_id=?",
                (event.source, event.external_id),
            ).fetchone()
            dedupe_row = self.conn.execute(
                "SELECT id FROM events WHERE dedupe_key=?", (event.dedupe_key,)
            ).fetchone()
            own_id = source_row["event_id"] if source_row else None
            match_id = dedupe_row["id"] if dedupe_row else None

            # Enrichment can discover a shared registration URL after two rows exist.
            if own_id and match_id and own_id != match_id:
                states = [
                    row[0]
                    for row in self.conn.execute(
                        "SELECT review_state FROM events WHERE id IN (?, ?)", (own_id, match_id)
                    )
                ]
                state = "pending" if "pending" in states else "rejected" if "rejected" in states else "approved"
                self.conn.execute("UPDATE events SET review_state=? WHERE id=?", (state, match_id))
                self.conn.execute("UPDATE event_sources SET event_id=? WHERE event_id=?", (match_id, own_id))
                self.conn.execute("DELETE FROM events WHERE id=?", (own_id,))
                own_id = match_id

            event_id = own_id or match_id
            if not event_id:
                digest = hashlib.sha256(f"{event.source}:{event.external_id}".encode()).hexdigest()[:20]
                event_id = f"evt_{digest}"
                self.conn.execute(
                    """INSERT INTO events
                    (id,dedupe_key,title,start_date,start_time,review_state,payload,created_at,updated_at,last_seen_at)
                    VALUES (?,?,?,?,?,'pending',?,?,?,?)""",
                    (
                        event_id,
                        event.dedupe_key,
                        event.title,
                        event.start_date,
                        event.start_time,
                        payload,
                        seen_at,
                        seen_at,
                        seen_at,
                    ),
                )
            else:
                existing = self.conn.execute("SELECT payload FROM events WHERE id=?", (event_id,)).fetchone()
                changed_at = seen_at if not existing or existing["payload"] != payload else None
                self.conn.execute(
                    """UPDATE events SET dedupe_key=?,title=?,start_date=?,start_time=?,payload=?,
                    updated_at=COALESCE(?,updated_at),last_seen_at=? WHERE id=?""",
                    (
                        event.dedupe_key,
                        event.title,
                        event.start_date,
                        event.start_time,
                        payload,
                        changed_at,
                        seen_at,
                        event_id,
                    ),
                )
            self.conn.execute(
                """INSERT INTO event_sources
                (source,external_id,event_id,url,content_hash,last_seen_at,misses)
                VALUES (?,?,?,?,?,?,0)
                ON CONFLICT(source,external_id) DO UPDATE SET event_id=excluded.event_id,
                url=excluded.url,content_hash=excluded.content_hash,
                last_seen_at=excluded.last_seen_at,misses=0""",
                (
                    event.source,
                    event.external_id,
                    event_id,
                    event.source_url,
                    content_hash,
                    seen_at,
                ),
            )
        state = self.conn.execute("SELECT review_state FROM events WHERE id=?", (event_id,)).fetchone()[0]
        return event_id, state

    def review(self, event_id: str, action: str) -> bool:
        if action not in {"pending", "approved", "rejected"}:
            raise ValueError("Review action must be pending, approved, or rejected")
        now = utc_now()
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE events SET review_state=? WHERE id=?", (action, event_id)
            )
            if cursor.rowcount:
                self.conn.execute(
                    "INSERT INTO review_log(event_id,action,created_at) VALUES(?,?,?)",
                    (event_id, action, now),
                )
        return bool(cursor.rowcount)

    def review_all_pending(self, action: str) -> int:
        ids = [row["id"] for row in self.conn.execute("SELECT id FROM events WHERE review_state='pending'")]
        for event_id in ids:
            self.review(event_id, action)
        return len(ids)

    def list_events(
        self,
        state: str = "approved",
        from_date: str | None = None,
        until_date: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if state not in {"pending", "approved", "rejected", "all"}:
            raise ValueError("Unknown review state")
        if not 1 <= limit <= 200:
            raise ValueError("Limit must be between 1 and 200")
        for value, label in ((from_date, "from"), (until_date, "until")):
            if value:
                datetime.strptime(value, "%Y-%m-%d")
        clauses: list[str] = []
        args: list[Any] = []
        if state != "all":
            clauses.append("e.review_state=?")
            args.append(state)
        if from_date:
            clauses.append("e.start_date>=?")
            args.append(from_date)
        if until_date:
            clauses.append("e.start_date<=?")
            args.append(until_date)
        if source:
            clauses.append(
                "EXISTS (SELECT 1 FROM event_sources sf WHERE sf.event_id=e.id AND sf.source=?)"
            )
            args.append(source)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        args.append(limit)
        rows = self.conn.execute(
            """SELECT e.*,s.source,s.external_id,s.url AS source_last_url,s.last_seen_at AS source_seen_at,s.misses
            FROM (SELECT * FROM events e"""
            + where
            + (
                " ORDER BY e.start_date,COALESCE(e.start_time,'99:99'),e.title,e.id LIMIT ?) e"
                " JOIN event_sources s ON s.event_id=e.id"
                " ORDER BY e.start_date,COALESCE(e.start_time,'99:99'),e.title,e.id,s.source"
            ),

            args,
        ).fetchall()
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            event_id = row["id"]
            if event_id not in grouped:
                grouped[event_id] = {
                    "id": event_id,
                    **json.loads(row["payload"]),
                    "reviewState": row["review_state"],
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                    "lastCheckedAt": row["last_seen_at"],
                    "sources": [],
                }
            grouped[event_id]["sources"].append(
                {
                    "source": row["source"],
                    "externalId": row["external_id"],
                    "url": row["source_last_url"],
                    "lastSeenAt": row["source_seen_at"],
                    "misses": row["misses"],
                }
            )
        for event in grouped.values():
            event["source"] = event["sources"][0]["source"]
        return list(grouped.values())

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        # Read the requested ID directly; public list pagination must never hide it.
        event_rows = self.conn.execute(
            """SELECT e.*,s.source,s.external_id,s.url AS source_last_url,s.last_seen_at AS source_seen_at,s.misses
            FROM events e JOIN event_sources s ON s.event_id=e.id WHERE e.id=?""",
            (event_id,),
        ).fetchall()
        if not event_rows:
            return None
        first = event_rows[0]
        return {
            "id": first["id"],
            **json.loads(first["payload"]),
            "reviewState": first["review_state"],
            "createdAt": first["created_at"],
            "updatedAt": first["updated_at"],
            "lastCheckedAt": first["last_seen_at"],
            "source": first["source"],
            "sources": [
                {
                    "source": row["source"],
                    "externalId": row["external_id"],
                    "url": row["source_last_url"],
                    "lastSeenAt": row["source_seen_at"],
                    "misses": row["misses"],
                }
                for row in event_rows
            ],
        }

    def record_run(
        self,
        source: str,
        started_at: str,
        status: str,
        event_count: int,
        warnings: Iterable[str] = (),
        error: str | None = None,
        seen_ids: Iterable[str] = (),
    ) -> None:
        finished = utc_now()
        seen = list(seen_ids)
        with self.conn:
            self.conn.execute(
                """INSERT INTO source_runs
                (source,started_at,finished_at,status,event_count,warnings,error)
                VALUES (?,?,?,?,?,?,?)""",
                (source, started_at, finished, status, event_count, json.dumps(list(warnings)), error),
            )
            if status == "ok":
                if seen:
                    placeholders = ",".join("?" for _ in seen)
                    self.conn.execute(
                        f"UPDATE event_sources SET misses=misses+1 WHERE source=? AND external_id NOT IN ({placeholders})",
                        [source, *seen],
                    )
                else:
                    self.conn.execute("UPDATE event_sources SET misses=misses+1 WHERE source=?", (source,))

    def source_health(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT r.* FROM source_runs r
            JOIN (SELECT source,MAX(id) AS latest_id FROM source_runs GROUP BY source) latest
            ON latest.latest_id=r.id ORDER BY r.source"""
        ).fetchall()
        return [
            {
                "source": row["source"],
                "startedAt": row["started_at"],
                "finishedAt": row["finished_at"],
                "status": row["status"],
                "eventCount": row["event_count"],
                "warnings": json.loads(row["warnings"]),
                "error": row["error"],
            }
            for row in rows
        ]

    def counts(self) -> dict[str, int]:
        return {
            row["review_state"]: row["count"]
            for row in self.conn.execute(
                "SELECT review_state,COUNT(*) AS count FROM events GROUP BY review_state"
            )
        }

    def cache_get(self, url: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT url,etag,last_modified,body,fetched_at FROM http_cache WHERE url=?", (url,)
        ).fetchone()

    def cache_put(self, url: str, body: bytes, etag: str | None, last_modified: str | None) -> None:
        with self.conn:
            self.conn.execute(
                """INSERT INTO http_cache(url,etag,last_modified,body,fetched_at) VALUES(?,?,?,?,?)
                ON CONFLICT(url) DO UPDATE SET etag=excluded.etag,last_modified=excluded.last_modified,
                body=excluded.body,fetched_at=excluded.fetched_at""",
                (url, etag, last_modified, body, utc_now()),
            )
        return None
