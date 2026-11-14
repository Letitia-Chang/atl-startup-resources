"""Source-specific parsers. Network and browser I/O live in pipeline.py."""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urljoin, urlsplit
from zoneinfo import ZoneInfo

from lxml import html

from .models import ATLANTA_TZ, Event, clean_text, infer_access, parse_time

MONTH_DATE_RE = re.compile(
    r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+)?"
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?P<day>\d{1,2}),\s+(?P<year>20\d{2})",
    re.IGNORECASE,
)
DAY_FIRST_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?P<year>20\d{2})",
    re.IGNORECASE,
)


def _iso_date(match: re.Match[str]) -> str:
    return datetime.strptime(
        f"{match.group('month')} {match.group('day')} {match.group('year')}", "%B %d %Y"
    ).date().isoformat()


def _in_window(value: str, reference: date, days: int) -> bool:
    parsed = date.fromisoformat(value)
    return reference <= parsed <= reference + timedelta(days=days)


class Connector:
    key = ""
    url = ""

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def parse(self, body: bytes | str, reference: date, days: int) -> list[Event]:
        raise NotImplementedError


class AtlantaTechVillageConnector(Connector):
    key = "atlanta-tech-village"
    url = "https://atlantatechvillage.com/events"
    # Bound source traffic while covering a typical four-month listing window.
    detail_limit = 60

    def parse(self, body: bytes | str, reference: date, days: int) -> list[Event]:
        self.warnings = []
        text_body = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
        doc = html.fromstring(text_body, base_url=self.url)
        events: dict[str, Event] = {}
        for anchor in doc.xpath('//a[@href][contains(@href, "/events/")]'):
            href = urljoin(self.url, anchor.get("href") or "")
            parts = urlsplit(href)
            if parts.hostname not in {"atlantatechvillage.com", "www.atlantatechvillage.com"}:
                continue
            if not parts.path.startswith("/events/") or len(parts.path) <= len("/events/"):
                continue
            text = clean_text(" ".join(anchor.itertext()))
            date_match = MONTH_DATE_RE.search(text)
            if not date_match:
                continue
            start_date = _iso_date(date_match)
            if not _in_window(start_date, reference, days):
                continue
            candidates = [
                clean_text(node.text_content())
                for node in anchor.xpath(".//h1|.//h2|.//h3|.//h4|.//strong|.//b")
            ]
            title = next(
                (
                    value
                    for value in candidates
                    if value
                    and not MONTH_DATE_RE.search(value)
                    and value.casefold() not in {"read more", "more information"}
                ),
                "",
            )
            if not title:
                self.warnings.append(f"Skipped {href}: event title not found")
                continue
            description = text.replace(title, "", 1)
            description = description.replace(date_match.group(0), "", 1)
            description = re.sub(r"\bRead more\b", "", description, flags=re.IGNORECASE)
            description = clean_text(description)
            slug = parts.path.rstrip("/").rsplit("/", 1)[-1]
            event = Event(
                source=self.key,
                external_id=slug,
                title=title,
                source_url=f"https://atlantatechvillage.com{parts.path.rstrip('/')}",
                start_date=start_date,
                description=description,
                access=infer_access(title + " " + description),
            )
            previous = events.get(slug)
            if previous is None or len(event.description) > len(previous.description):
                events[slug] = event
        if not events:
            self.warnings.append("No dated Atlanta Tech Village event links found; inspect source markup")
        return sorted(events.values(), key=lambda event: (event.start_date, event.title))

    def enrich(self, event: Event, body: bytes | str) -> Event:
        """Fill fields available on an ATV detail page without guessing missing data."""
        text_body = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
        doc = html.fromstring(text_body, base_url=event.source_url)
        # Join text nodes explicitly: text_content() concatenates adjacent inline labels
        # (for example, "WHEN" + "Tuesday"), losing the separator parsers need.
        text = clean_text(" ".join(doc.xpath("//body//text()")))
        venue = event.venue
        location_labels = doc.xpath("//*[not(*) and normalize-space(text())='WHERE']")
        if location_labels:
            location_parts: list[str] = []
            for sibling in location_labels[0].itersiblings():
                if clean_text(sibling.text_content()).casefold() == "when":
                    break
                location_parts.append(sibling.text_content())
            candidate = clean_text(" ".join(location_parts))
            if candidate and len(candidate) <= 240:
                venue = candidate
            else:
                self.warnings.append(f"Location block was empty or too broad for {event.source_url}")
        when_match = re.search(
            r"\bWHEN\b\s+((?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+)?"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+\d{1,2},\s+20\d{2})(.{0,100})",
            text,
            re.IGNORECASE,
        )
        if not when_match:
            self.warnings.append(f"Detail date not found for {event.source_url}; kept listing-only fields")
            return event
        detail_date = MONTH_DATE_RE.search(when_match.group(1))
        if not detail_date or _iso_date(detail_date) != event.start_date:
            self.warnings.append(
                f"Detail date did not match the listing for {event.source_url}; kept listing-only fields"
            )
            return event
        times = re.findall(
            r"(?:[1-9]|1[0-2])(?::[0-5]\d)?\s*[AaPp]\.?[Mm]\.?", when_match.group(2)
        )
        start_time = parse_time(times[0]) if times else None
        end_time = parse_time(times[1]) if len(times) > 1 else None
        registration_url = event.registration_url
        for anchor in doc.xpath("//a[@href]"):
            label = clean_text(anchor.text_content()).casefold()
            href = urljoin(event.source_url, anchor.get("href") or "")
            if any(word in label for word in ("rsvp", "register", "more info", "tickets")):
                if urlsplit(href).scheme == "https" and urlsplit(href).hostname != "atlantatechvillage.com":
                    registration_url = href
                    break
        return event.with_details(
            venue=venue,
            start_time=start_time,
            end_time=end_time,
            registration_url=registration_url,
        )


class ATDCConnector(Connector):
    key = "atdc"
    url = "https://portal.atdc.org/s/events"
    detail_limit = 60

    def parse(self, body: bytes | str, reference: date, days: int) -> list[Event]:
        self.warnings = []
        text_body = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
        doc = html.fromstring(text_body, base_url=self.url)
        events: dict[str, Event] = {}
        for heading in doc.xpath("//h3"):
            title = clean_text(heading.text_content())
            if not title:
                continue
            card = None
            card_text = ""
            date_match = None
            node = heading
            for _ in range(6):
                text = clean_text(node.text_content())
                match = DAY_FIRST_DATE_RE.search(text)
                if match and len(node.xpath(".//h3")) == 1:
                    card = node
                    card_text = text
                    date_match = match
                    break
                if node.getparent() is None:
                    break
                node = node.getparent()
            if card is None or date_match is None:
                self.warnings.append(f"Skipped ATDC heading {title!r}: dated event container not found")
                continue
            start_date = _iso_date(date_match)
            if not _in_window(start_date, reference, days):
                continue
            description = card_text.replace(title, "", 1).replace(date_match.group(0), "", 1)
            description = clean_text(re.sub(r"\s+[01]\d\s+[01]\d\s+Next Page.*$", "", description))
            event_url = self.url
            record_id = ""
            routes = card.xpath(".//button[@data-url]/@data-url")
            if routes:
                route = urlsplit(urljoin(self.url, routes[0]))
                identifiers = parse_qs(route.query).get("event", [])
                if route.hostname == "portal.atdc.org" and len(identifiers) == 1 and re.fullmatch(r"[A-Za-z0-9]{15,18}", identifiers[0]):
                    record_id = identifiers[0]
                    event_url = f"https://portal.atdc.org/s/community-event?id={record_id}"
            for anchor in card.xpath(".//a[@href]"):
                if record_id:
                    break
                href = urljoin(self.url, anchor.get("href") or "")
                if urlsplit(href).hostname == "portal.atdc.org" and urlsplit(href).path != "/s/events":
                    event_url = href
                    break
            external_key = f"{title}|{start_date}"
            external_id = record_id or hashlib.sha256(external_key.encode()).hexdigest()[:24]
            combined = title + " " + description
            if re.search(r"\bAlpharetta\b", combined, re.IGNORECASE):
                city = "Alpharetta"
            elif re.search(r"\bAtlanta\b", combined, re.IGNORECASE):
                city = "Atlanta"
            else:
                city = ""
            events[external_id] = Event(
                source=self.key,
                external_id=external_id,
                title=title,
                source_url=event_url,
                start_date=start_date,
                description=description,
                city=city,
                access=infer_access(combined),
                topics=[],
            )
        if not events:
            self.warnings.append("No dated ATDC events found; the portal may require browser rendering")
        return sorted(events.values(), key=lambda event: (event.start_date, event.title))

    def enrich(self, event: Event, body: bytes | str) -> Event:
        """Enrich an ATDC occurrence from its own public community-event page."""
        text_body = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
        doc = html.fromstring(text_body, base_url=event.source_url)
        headings = [
            heading for heading in doc.xpath("//h1")
            if clean_text(heading.text_content()) == event.title
        ]
        if not headings:
            self.warnings.append(f"ATDC detail title did not match {event.source_url}")
            return event
        for anchor in doc.xpath('//a[@href][contains(@href, "google.com/calendar/render")]'):
            query = parse_qs(urlsplit(anchor.get("href") or "").query)
            calendar_dates = query.get("dates", [])
            zones = query.get("ctz", [])
            if not calendar_dates or zones != [ATLANTA_TZ]:
                continue
            fields = calendar_dates[0].split("/")
            if len(fields) != 2:
                continue
            try:
                starts = datetime.strptime(fields[0], "%Y%m%dT%H%M%S")
                ends = datetime.strptime(fields[1], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
            if starts.date().isoformat() != event.start_date or ends <= starts:
                self.warnings.append(f"ATDC detail date/time did not match {event.source_url}")
                return event
            venue = event.venue
            node = headings[0]
            for _ in range(5):
                if node.getparent() is None:
                    break
                node = node.getparent()
                detail_text = clean_text(" ".join(node.itertext()))
                match = re.search(
                    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
                    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
                    r"\s+\d{1,2}(?:st|nd|rd|th)",
                    detail_text,
                    re.IGNORECASE,
                )
                if match and event.title in detail_text[:match.start()]:
                    prefix = detail_text[:match.start()]
                    candidate = clean_text(prefix.rsplit(event.title, 1)[-1])
                    if candidate and len(candidate) <= 240:
                        venue = candidate
                    break
            if re.search(r"\bAlpharetta\b", venue, re.IGNORECASE):
                city = "Alpharetta"
            elif re.search(r"\bAtlanta\b", venue, re.IGNORECASE):
                city = "Atlanta"
            else:
                city = ""
            return event.with_details(
                start_time=starts.strftime("%H:%M"),
                end_time=ends.strftime("%H:%M"),
                city=city,
                venue=venue,
            )
        self.warnings.append(f"ATDC detail calendar data was not verified for {event.source_url}")
        return event


CONNECTORS: dict[str, Connector] = {
    "atlanta-tech-village": AtlantaTechVillageConnector(),
    "atdc": ATDCConnector(),
}


def atlanta_today() -> date:
    return datetime.now(ZoneInfo(ATLANTA_TZ)).date()
