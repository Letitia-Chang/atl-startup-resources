# ATL Startup Events MVP

Local-first event ingestion, review, storage, and read-only JSON API for Atlanta startup events.

## Status and verification boundary

Implemented:

- Atlanta Tech Village event-list and detail-page connectors
- ATDC public-portal connector, with optional Playwright rendering when static HTML has no events
- HTTPS-only HTTP client with robots.txt checks, per-host pacing, short retry/backoff, 3 MB response limits, and conditional ETag/Last-Modified caching
- Normalized Atlanta-local event fields without inventing times for date-only listings
- SQLite persistence, cross-source deduplication, distinct recurring sessions, and non-destructive stale/missed tracking
- Deterministic topic/access/format labels
- Pending, approved, and rejected review states with an audit log
- Six-hour refresh loop and atomic approved-event JSON export
- Local read-only API and source-health reporting

**Live collection is not verified yet.** This workstation's outbound allowlist DNS-refuses both required hosts. The source connectors are tested against representative saved HTML fixtures only; their selectors must be checked against raw live responses from a runtime that can reach the source sites. Fixture mode is explicitly labelled in source-health output and must not be mistaken for live ingestion.

Required outbound HTTPS destinations for live collection:

- `atlantatechvillage.com:443` (including canonical redirects)
- `portal.atdc.org:443`

No scheduler or server is left running by this project. No plugin changes or public deployment are included yet.

## Setup

Python 3.11+ is required. The only required third-party library is `lxml`; Playwright is optional and used only for ATDC rendering.

```bash
cd /path/to/atl-startup-events
python3 -m venv .venv
.venv/bin/pip install -e .

# Needed only when ATDC's static response contains no events:
.venv/bin/pip install -e '.[browser]'
.venv/bin/playwright install chromium
```

Run tests without contacting external sources:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Live refresh

```bash
# One collection pass for both configured sources.
.venv/bin/atl-events --db var/events.db refresh --export build/events.json

# ATL Tech Village only, with no browser fallback.
.venv/bin/atl-events --db var/events.db refresh --source atlanta-tech-village --no-browser

# Keep refreshing; each six-hour sleep starts after the preceding pass finishes.
.venv/bin/atl-events --db var/events.db refresh --watch --export build/events.json
```

Refresh exit status is nonzero if any source fails. Other sources still run, and previous stored events are retained. `--days 120` controls the future collection window.

Collection uses only public pages and no credentials. It does not bypass logins, CAPTCHAs, robots exclusions, or access restrictions. Confirm redistribution terms with each source before publishing descriptions or other content beyond factual event details and source links.

## Review and export

New and previously unseen events start as `pending`. They are not returned by the default `/events` query or normal export until approved.

```bash
# Inspect pending records with stable event IDs.
.venv/bin/atl-events --db var/events.db review list

# Approve selected records.
.venv/bin/atl-events --db var/events.db review approve evt_example

# Reject selected records.
.venv/bin/atl-events --db var/events.db review reject evt_example

# Bulk action is deliberate and applied only to currently pending records.
.venv/bin/atl-events --db var/events.db review approve --all-pending

# Export approved upcoming events; writes via temporary file + rename.
.venv/bin/atl-events --db var/events.db export --output build/events.json
```

## Read-only API

```bash
.venv/bin/atl-events --db var/events.db serve
# http://127.0.0.1:8787/events
```

Routes:

- `GET /events` — approved upcoming events
- `GET /events?from=2026-11-01&until=2027-03-01&source=atdc&limit=100`
- `GET /events?state=pending|approved|rejected|all` — optional review-state filter
- `GET /events/{id}` — one event and all its source identities
- `GET /review` — pending review queue
- `GET /health` — review counts and latest source result

The API accepts `GET` only; review mutations use the CLI. It binds to localhost by default and has no authentication or TLS layer. Do not expose it directly to the public internet. Put it behind an authenticated HTTPS reverse proxy if remote access is needed.

Dates and times are local to `America/New_York`. `startsOn` is always a YYYY-MM-DD date; `startTime` and `startAt` can be null when the source gives only a date. Sources carry `lastSeenAt` and `misses`; a single failed refresh never removes an event.

## Connector fixture development

Representative fixtures live in `tests/fixtures`. To test ingestion without network access:

```bash
.venv/bin/atl-events --db var/fixtures.db ingest-fixture atlanta-tech-village tests/fixtures/atv-events.html --reference-date 2026-11-13
.venv/bin/atl-events --db var/fixtures.db ingest-fixture atdc tests/fixtures/atdc-events.html --reference-date 2026-11-13
```

Fixture runs show `"status": "fixture"` from `atl-events sources` and `/health`, with an explicit warning that no network request occurred. Do not publish fixture records as real events.

## Dashboard integration next step

`build/events.json` has a versioned shape suitable for embedding into the existing plugin at build time, preserving its no-runtime-request design. A live alternative is to serve approved events from an HTTPS origin and explicitly declare that origin in the plugin's host access. Neither option should be wired up with fixture records or before live connector validation.
