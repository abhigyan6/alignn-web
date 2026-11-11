"""Whitelisted metadata only; never return page state, guests or contact objects."""

import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from uuid import UUID

from .models import Observation
from .registry import BOARDS


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.links = []
        self.current = None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.current = [attrs, []]
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.scripts.append(self.current)
            self.current = None

    def next_data(self):
        items = [json.loads("".join(v)) for a, v in self.scripts if a.get("id") == "__NEXT_DATA__"]
        if len(items) != 1:
            raise ValueError("page_structure_changed")
        return items[0]["props"]["pageProps"]

    def event(self):
        for attrs, parts in self.scripts:
            if attrs.get("type") == "application/ld+json":
                value = json.loads("".join(parts))
                for item in value if isinstance(value, list) else [value]:
                    if item.get("@type") == "Event":
                        return item
        raise ValueError("event_metadata_missing")


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "div", "br", "li", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(value):
    p = Text()
    p.feed(unescape(value).replace("\\n", "\n"))
    text = "".join(p.parts)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[contact omitted]", text)
    text = re.sub(
        r"https?://(?:chat\.whatsapp\.com|wa\.me|t\.me)/[^\s]+", "[contact omitted]", text
    )
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def date(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


def ld_observation(ld, source, url, identity, now, deadline=None, state=None):
    title = ld["name"]
    description = plain(ld.get("description", ""))
    if source == "luma" and not re.search(
        r"\b(hackathon|buildathon|workshop|developer|tech|coding|ai|startup|founder|engineer|career)\b",
        title,
        re.I,
    ):
        return None
    locations = ld.get("location", {})
    locations = locations if isinstance(locations, list) else [locations]
    addresses = [loc.get("address", {}) for loc in locations if isinstance(loc, dict)]
    address = next(
        (
            a
            for a in addresses
            if isinstance(a, dict) and a.get("addressCountry") in {"IN", "India"}
        ),
        None,
    )
    if address:
        evidence = {"kind": "country_metadata", "statement": "IN", "url": url}
        location = (address.get("addressLocality") or "India") + ", India"
    else:
        # Explicit audience statement, never timezone/currency/online inference.
        match = re.search(
            r"[^.\n]{0,80}\b(?:across India|in India|India[- ](?:based|wide)|Indian students)\b[^.\n]{0,80}",
            description,
            re.I,
        )
        if not match:
            return None
        evidence = {"kind": "official_audience", "statement": match.group().strip(), "url": url}
        location = "India (online audience)"
    status = ld.get("eventStatus", "")
    state = "CANCELLED" if status.endswith("EventCancelled") else state or "OPEN"
    organizer = ld.get("organizer", [])
    organizer = organizer if isinstance(organizer, list) else [organizer]
    org = next(
        (
            o.get("name")
            for o in organizer
            if isinstance(o, dict) and o.get("@type") == "Organization"
        ),
        None,
    )
    attendance = ld.get("eventAttendanceMode", "")
    mode = (
        "REMOTE"
        if attendance.endswith("/OnlineEventAttendanceMode")
        else "HYBRID"
        if attendance.endswith("/MixedEventAttendanceMode")
        else "ONSITE"
        if attendance.endswith("/OfflineEventAttendanceMode")
        else "UNKNOWN"
    )
    return Observation(
        source=source,
        source_name={"hackindia": "HackIndia", "luma": "Luma"}[source],
        source_id=identity,
        source_url=url,
        apply_url=url,
        observed_at=now,
        source_state=state,
        country_evidence=evidence,
        title=title,
        description=description,
        organization_name=org or f"Organizer listed on {source.title()}",
        kind="HACKATHON" if re.search(r"hackathon|buildathon", title, re.I) else "WORKSHOP",
        location=location,
        work_mode=mode,
        registration_closes_at=deadline,
        starts_at=date(ld.get("startDate")),
        ends_at=date(ld.get("endDate")),
    )


def parse_hackindia(body, url, now):
    # Read only the published date key, without evaluating/retaining RSC page state.
    matches = set(
        re.findall(r'"registration_end_date"\s*:\s*"([0-9TZ:.+\-]+)"', body.replace('\\"', '"'))
    )
    if len(matches) > 1:
        raise ValueError("ambiguous_deadline")
    return ld_observation(
        Page(body).event(),
        "hackindia",
        url,
        url.split("/", 3)[3],
        now,
        deadline=date(next(iter(matches))) if matches else None,
    )


def parse_luma(body, url, now):
    page = Page(body)
    data = page.next_data()["initialData"]["data"]
    event = data["event"]
    if url != "https://luma.com/" + event["url"]:
        raise ValueError("event_identity_changed")
    state = (
        "CLOSED" if data.get("registration_availability") in {"closed", "event-ended"} else "OPEN"
    )
    ld = page.event()
    description = plain(ld.get("description", ""))
    # Explicit published date only; unknown remains null. Avoid fuzzy date/LLM inference.
    match = re.search(
        r"Registration closes:\s*(\d{1,2} [A-Za-z]{3} \d{4}),?\s*(\d{1,2}:\d{2})\s*(AM|PM)\s*IST",
        description,
        re.I,
    )
    deadline = None
    if match:
        from datetime import timedelta

        deadline = datetime.strptime(" ".join(match.groups()), "%d %b %Y %I:%M %p").replace(
            tzinfo=timezone(timedelta(hours=5, minutes=30))
        )
    return ld_observation(ld, "luma", url, event["api_id"], now, deadline, state)


def parse_devfolio(body, url, now):
    raw = Page(body).next_data()["hackathon"]
    if raw.get("country", "").casefold() != "india" or raw.get("type") != "HACKATHON":
        return None
    if url != f"https://{raw['slug']}.devfolio.co/":
        raise ValueError("event_identity_changed")
    settings = raw.get("settings", {})
    return Observation(
        source="devfolio",
        source_name="Devfolio",
        source_id=str(UUID(raw["uuid"])),
        source_url=url,
        apply_url=url,
        observed_at=now,
        country_evidence={"kind": "country_metadata", "statement": "India", "url": url},
        title=raw["name"],
        description=plain(raw["desc"]),
        organization_name="Organizer listed on Devfolio",
        kind="HACKATHON",
        location=", ".join(x for x in [raw.get("city"), "India"] if x),
        work_mode="HYBRID"
        if settings.get("is_hybrid")
        else "REMOTE"
        if raw["is_online"]
        else "ONSITE",
        registration_closes_at=date(settings.get("reg_ends_at")),
        starts_at=date(raw.get("starts_at")),
        ends_at=date(raw.get("ends_at")),
    )


def parse_greenhouse(raw, board, now):
    if not re.search(r"\b(intern|internship)\b", raw["title"], re.I):
        return None
    location = raw["location"]["name"]
    if not re.search(
        r"\b(india|bengaluru|bangalore|hyderabad|gurugram|mumbai|pune|chennai)\b", location, re.I
    ):
        return None
    url = raw["absolute_url"]
    company, _ = BOARDS[board]
    return Observation(
        source="greenhouse-" + board,
        source_name="Greenhouse:" + board,
        source_id=str(raw["id"]),
        source_url=url,
        apply_url=url,
        observed_at=now,
        country_evidence={
            "kind": "official_location",
            "statement": "India: " + location,
            "url": url,
        },
        title=raw["title"],
        description=plain(raw["content"]),
        organization_name=company,
        kind="INTERNSHIP",
        location=location,
        work_mode="REMOTE"
        if re.search(r"\bremote\b", location, re.I)
        else "HYBRID"
        if re.search(r"\bhybrid\b", location, re.I)
        else "UNKNOWN",
    )
