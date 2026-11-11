import json
import time
from datetime import UTC, datetime

from alignn_scraper import collect as collector
from alignn_scraper.parsers import Page, parse_hackindia
from alignn_scraper.transport import FetchError

NOW = datetime.now(UTC)


def document(**updates):
    value = {
        "@type": "Event",
        "name": "Technology Hackathon",
        "description": "Build useful technology together.",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {"address": {"addressCountry": "IN", "addressLocality": "Noida"}},
    }
    return '<script type="application/ld+json">' + json.dumps({**value, **updates}) + "</script>"


def test_negative_or_conflicting_india_evidence_is_skipped():
    for description in [
        "This workshop is not available in India. Meet us in London.",
        "This workshop is for students across India. Meet us in London.",
    ]:
        body = document(
            description=description,
            location={"address": {"addressCountry": "GB", "addressLocality": "London"}},
        )
        assert parse_hackindia(body, "https://hackindia.org/2026/test", NOW) is None
    body = document(description="This workshop is not available in India.", location={})
    assert parse_hackindia(body, "https://hackindia.org/2026/test", NOW) is None


def test_jsonld_null_and_nullable_metadata_are_controlled():
    body = '<script type="application/ld+json">[null,{"@type":"Event","name":"Test"}]</script>'
    assert Page(body).event()["name"] == "Test"
    row = parse_hackindia(
        document(eventStatus=None, eventAttendanceMode=None),
        "https://hackindia.org/2026/test",
        NOW,
    )
    assert row.work_mode == "UNKNOWN"


def test_malformed_detail_preserves_good_rows_as_partial(monkeypatch):
    class HTTP:
        def __init__(self, source):
            self.started = time.monotonic()

        def close(self):
            pass

        def get(self, url):
            if url.endswith("/hackathons"):
                return '<a href="/2026/good">A</a><a href="/2026/bad">B</a>'
            if url.endswith("/good"):
                return document()
            return '<script type="application/ld+json">[null]</script>'

    monkeypatch.setattr(collector, "PublicHTTP", HTTP)
    result = collector.collect("hackindia")
    assert result.status == "partial" and len(result.records) == 1 and result.failed == 1


def test_all_detail_failures_are_failed_not_empty_partial(monkeypatch):
    class HTTP:
        def __init__(self, source):
            self.started = time.monotonic()

        def close(self):
            pass

        def get(self, url):
            if url.endswith("/hackathons"):
                return '<a href="/2026/missing">A</a>'
            raise FetchError("http_status", 404)

    monkeypatch.setattr(collector, "PublicHTTP", HTTP)
    result = collector.collect("hackindia")
    assert result.status == "failed" and not result.records
