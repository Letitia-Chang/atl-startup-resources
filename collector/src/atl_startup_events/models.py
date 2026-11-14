"""Normalized event model shared by every source connector."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ATLANTA_TZ = "America/New_York"
TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("funding", ("investor", "investment", "funding", "venture capital", "funder", "grant", "sbir", "sttr", "capital")),
    ("pitching", ("pitch", "demo day")),
    ("education", ("workshop", "training", "class", "educate", "learn", "webinar")),
    ("networking", ("networking", "coffee", "chowdown", "meetup", "mixer", "entrepreneur's night", "startup circle")),
    ("office-hours", ("office hours",)),
    ("ai", (" ai ", "artificial intelligence", "mond(ai)y")),
)


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value or "")).strip()


def parse_time(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\b([1-9]|1[0-2])(?::([0-5]\d))?\s*([AaPp])\.?[Mm]\.?\b", value)
    if not match:
        return None
    hour = int(match.group(1)) % 12
    if match.group(3).lower() == "p":
        hour += 12
    return f"{hour:02d}:{match.group(2) or '00'}"


def canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    netloc = host
    if parts.port and parts.port != 443:
        netloc = f"{host}:{parts.port}"
    # Drop campaign analytics but retain meaningful query keys such as event IDs.
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
    )
    return urlunsplit((parts.scheme.lower(), netloc, parts.path.rstrip("/"), urlencode(query), ""))


def infer_topics(title: str, description: str) -> list[str]:
    haystack = f" {clean_text(title + ' ' + description).casefold()} "
    return [topic for topic, needles in TOPIC_RULES if any(needle in haystack for needle in needles)]


def infer_access(text: str) -> str:
    value = clean_text(text).casefold()
    if "invite-only" in value or "invite only" in value:
        return "invite-only"
    if "member-only" in value or "member only" in value or "members only" in value:
        return "member-only"
    if "open to the public" in value or "free, open" in value:
        return "public"
    return "unknown"


def infer_format(text: str, venue: str = "") -> str:
    value = clean_text(text + " " + venue).casefold()
    if "hybrid" in value:
        return "hybrid"
    if any(word in value for word in ("virtual only", "virtual-only", "online only", "webinar", "online class")):
        return "virtual"
    if "in-person" in value or "in person" in value or venue:
        return "in-person"
    return "unknown"


@dataclass(slots=True)
class Event:
    source: str
    external_id: str
    title: str
    source_url: str
    start_date: str
    start_time: str | None = None
    end_time: str | None = None
    timezone: str = ATLANTA_TZ
    description: str = ""
    venue: str = ""
    city: str = "Atlanta"
    format: str = "unknown"
    access: str = "unknown"
    price: str | None = None
    registration_url: str | None = None
    topics: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = clean_text(self.title)
        self.description = clean_text(self.description)
        self.venue = clean_text(self.venue)
        self.source = clean_text(self.source).lower()
        self.external_id = clean_text(self.external_id)
        self.source_url = self.source_url.strip()
        if self.registration_url:
            self.registration_url = self.registration_url.strip()
        if not self.source or not self.external_id or not self.title:
            raise ValueError("source, external_id, and title are required")
        self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d").date().isoformat()
        for value, label in ((self.start_time, "start_time"), (self.end_time, "end_time")):
            if value is not None:
                # This check also rejects ambiguous timezone-less timestamps with seconds.
                parsed = datetime.strptime(value, "%H:%M").time()
                normalized = parsed.strftime("%H:%M")
                if normalized != value:
                    raise ValueError(f"{label} must be normalized HH:MM")
        if self.end_time and not self.start_time:
            raise ValueError("end_time requires start_time")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {self.timezone}") from exc
        for value, label in ((self.source_url, "source_url"), (self.registration_url, "registration_url")):
            if value and urlsplit(value).scheme != "https":
                raise ValueError(f"{label} must use HTTPS")
        self.format = infer_format(self.title + " " + self.description + " " + self.access, self.venue)
        if not self.topics:
            self.topics = infer_topics(self.title, self.description)

    @property
    def start_at(self) -> str | None:
        if not self.start_time:
            return None
        return datetime.fromisoformat(f"{self.start_date}T{self.start_time}:00").replace(
            tzinfo=ZoneInfo(self.timezone)
        ).isoformat()

    @property
    def end_at(self) -> str | None:
        if not self.start_time or not self.end_time:
            return None
        start = datetime.fromisoformat(self.start_at or "")
        end = datetime.fromisoformat(f"{self.start_date}T{self.end_time}:00").replace(
            tzinfo=ZoneInfo(self.timezone)
        )
        if end <= start:
            end += timedelta(days=1)
        return end.isoformat()

    @property
    def dedupe_key(self) -> str:
        if self.registration_url:
            # Registration URLs may be reused for recurring sessions; the local
            # date is part of the identity, so sessions never collapse by URL alone.
            return "registration:" + canonical_url(self.registration_url) + "|" + self.start_date
        venue = re.sub(r"[^\w]+", "", clean_text(self.venue).casefold(), flags=re.UNICODE)
        title = re.sub(r"[^\w]+", "", clean_text(self.title).casefold(), flags=re.UNICODE)
        raw = f"{title}|{self.start_date}|{self.start_time or ''}|{venue}"
        return "fingerprint:" + hashlib.sha256(raw.encode()).hexdigest()

    def with_details(self, **changes: Any) -> "Event":
        return replace(self, **changes)

    def to_payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "startsOn": self.start_date,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "startAt": self.start_at,
            "endAt": self.end_at,
            "timezone": self.timezone,
            "venue": self.venue or None,
            "city": self.city,
            "format": self.format,
            "access": self.access,
            "price": self.price,
            "topics": sorted(self.topics),
            "url": self.source_url,
            "registrationUrl": self.registration_url,
        }
