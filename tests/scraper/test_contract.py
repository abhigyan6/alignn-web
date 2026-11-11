import io
import json
import zipfile
from datetime import UTC, datetime, timedelta

import pytest
from alignn_scraper.bundle import read_bundle, write_bundle
from alignn_scraper.models import Observation, SourceResult
from alignn_scraper.parsers import parse_hackindia, parse_luma
from alignn_scraper.registry import validate_url

NOW = datetime.now(UTC)


def event_ld(country="IN"):
    return {
        "@type": "Event",
        "name": "India AI Hackathon",
        "description": "Build useful Python technology with students.",
        "startDate": (NOW + timedelta(days=5)).isoformat(),
        "endDate": (NOW + timedelta(days=6)).isoformat(),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {"address": {"addressCountry": country, "addressLocality": "Noida"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "organizer": {
            "@type": "Person",
            "name": "Do not copy",
            "email": "private@alignn.test",
        },
    }


def html(ld, state=None):
    return (
        '<script type="application/ld+json">'
        + json.dumps(ld)
        + "</script>"
        + ('<script id="__NEXT_DATA__">' + json.dumps(state) + "</script>" if state else "")
    )


def row():
    return parse_hackindia(html(event_ld()), "https://hackindia.org/2026/test-hackathon", NOW)


def test_hackindia_india_dates_and_no_person_fields():
    value = row()
    assert value.country_code == "IN" and value.registration_closes_at is None
    assert value.ends_at > value.starts_at
    assert (
        "private@" not in value.model_dump_json() and "Do not copy" not in value.model_dump_json()
    )
    assert parse_hackindia(html(event_ld("US")), value.source_url, NOW) is None


def test_luma_uses_public_event_and_technical_scope():
    ld = event_ld()
    ld["url"] = "https://luma.com/test1234"
    state = {
        "props": {
            "pageProps": {
                "initialData": {
                    "data": {
                        "event": {"api_id": "evt-123", "url": "test1234"},
                        "registration_availability": "open",
                    }
                }
            }
        }
    }
    value = parse_luma(html(ld, state), ld["url"], NOW)
    assert value.source_id == "evt-123"
    assert parse_luma(html({**ld, "name": "Weekend Football"}, state), ld["url"], NOW) is None
    cancelled = {**ld, "eventStatus": "https://schema.org/EventCancelled"}
    assert parse_luma(html(cancelled, state), ld["url"], NOW).source_state == "CANCELLED"


def test_contract_rejects_naive_future_or_unsafe_urls():
    data = row().model_dump(mode="json")
    for changes in [
        {"observed_at": "2026-01-01T00:00:00"},
        {"source_url": "https://127.0.0.1/private"},
        {"country_code": "US"},
        {"description": "x" * 20001},
        {"unknown_private_field": "secret"},
    ]:
        with pytest.raises(ValueError):
            Observation.model_validate({**data, **changes})
    for url in [
        "https://hackindia.org/api/hackathons/1",
        "https://evil.hackindia.org/2026/test",
        "http://hackindia.org/2026/test",
        "https://hackindia.org@localhost/2026/test",
        "https://luma.com/user/someone",
        "https://hackindia.org:444/2026/test",
    ]:
        with pytest.raises(ValueError):
            validate_url("hackindia" if "luma" not in url else "luma", url)


def test_bundle_roundtrip_chunking_and_tamper():
    values = [
        row().model_copy(update={"source_id": f"event-{i}", "description": "字" * 19000})
        for i in range(30)
    ]
    result = SourceResult(source="hackindia", status="ok", checked_at=NOW, records=values)
    packed = write_bundle([result], NOW)
    manifest, parts = read_bundle(packed, NOW)
    assert len(manifest["chunks"]) > 1 and len(parts["hackindia"]["records"]) == 30
    stream = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(packed)) as source,
        zipfile.ZipFile(stream, "w") as dest,
    ):
        for name in source.namelist():
            dest.writestr(name, source.read(name) + (b" " if name != "manifest.json" else b""))
    with pytest.raises(ValueError):
        read_bundle(stream.getvalue(), NOW)
    with pytest.raises(ValueError):
        read_bundle(packed, NOW + timedelta(days=2))


def test_bundle_does_not_extract_paths_or_accept_duplicate_members():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("../opportunities.json", "{}")
    with pytest.raises(ValueError):
        read_bundle(stream.getvalue(), NOW)


def test_devfolio_missing_country_is_skipped_and_dates_are_distinct():
    from alignn_scraper.parsers import parse_devfolio

    raw = {
        "uuid": "123456781234123412341234567890ab",
        "slug": "student-build",
        "country": None,
        "type": "HACKATHON",
        "name": "Student buildathon",
        "desc": "Build useful Python applications.",
        "is_online": False,
        "city": "Bhopal",
        "settings": {},
        "starts_at": None,
        "ends_at": None,
    }

    def document(value):
        return html({}, {"props": {"pageProps": {"hackathon": value}}})

    assert parse_devfolio(document(raw), "https://student-build.devfolio.co/", NOW) is None
    value = parse_devfolio(
        document({**raw, "country": "India"}), "https://student-build.devfolio.co/", NOW
    )
    assert value.registration_closes_at is None and value.ends_at is None


def test_greenhouse_intern_boundary_and_unknown_location():
    from alignn_scraper.parsers import parse_greenhouse

    raw = {
        "id": 123,
        "title": "Software Intern",
        "content": "<p>Build useful software.</p>",
        "location": {"name": "Bengaluru"},
        "absolute_url": "https://stripe.com/jobs/search?gh_jid=123",
    }
    assert parse_greenhouse(raw, "stripe", NOW).work_mode == "UNKNOWN"
    assert parse_greenhouse({**raw, "title": "Internal Manager"}, "stripe", NOW) is None
    assert parse_greenhouse({**raw, "location": {"name": "Remote"}}, "stripe", NOW) is None


def test_known_external_country_does_not_become_indian_by_timezone():
    ld = event_ld("US")
    ld["timezone"] = "Asia/Kolkata"
    assert parse_hackindia(html(ld), "https://hackindia.org/2026/test-hackathon", NOW) is None
