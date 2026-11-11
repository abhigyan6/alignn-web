"""Bounded public Devfolio discovery; only explicit Indian event metadata survives."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, text

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.ingestion import inferred_skills, source_is_fresh
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.opportunities.schemas import OpportunityCreate
from alignn.domains.organizations.models import Organization
from alignn.domains.profiles.models import Skill

SOURCE = "Devfolio"
INDEX = "https://devfolio.co/hackathons"
SOURCE_ORG = uuid5(NAMESPACE_URL, INDEX)
MAX_EVENTS = 100
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def event_url(slug):
    if not isinstance(slug, str) or len(slug) > 100 or not SLUG.fullmatch(slug):
        raise ValueError("Invalid event slug")
    return f"https://{slug}.devfolio.co/"


def next_data(response):
    raw = response.css("script#__NEXT_DATA__::text").get()
    if not raw:
        raise ValueError("Source page structure changed")
    return json.loads(raw)["props"]["pageProps"]


def index_events(page):
    queries = page["dehydratedState"]["queries"]
    snapshots = [
        q["state"]["data"]
        for q in queries
        if q.get("queryKey") in ("fetchAllHackathonTypes", ["fetchAllHackathonTypes"])
    ]
    if len(snapshots) != 1:
        raise ValueError("Missing catalog snapshot")
    rows = snapshots[0]["open_hackathons"]
    if not isinstance(rows, list) or not rows or len(rows) > MAX_EVENTS:
        raise ValueError("Unexpected catalog size")
    events = {}
    for row in rows:
        identity = str(UUID(row["uuid"]))
        if identity in events:
            raise ValueError("Duplicate event identity")
        events[identity] = event_url(row["slug"])
    return events


def timestamp(value):
    if value is None:
        return None
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("Source date lacks timezone")
    return date.astimezone(timezone.utc)


def normalize_event(raw, expected_id, expected_url, now):
    identity = str(UUID(raw["uuid"]))
    if identity != expected_id or event_url(raw["slug"]) != expected_url:
        raise ValueError("Event identity changed")
    # Online, English language, and Asia/Calcutta alone do not prove India eligibility.
    if str(raw.get("country", "")).strip().casefold() != "india":
        return None
    if raw.get("type") != "HACKATHON":
        return None
    settings = raw["settings"]
    deadline = timestamp(settings.get("reg_ends_at"))
    start = timestamp(raw.get("starts_at"))
    end = timestamp(raw.get("ends_at"))
    if (deadline and deadline <= now) or (end and end <= now):
        return None
    online = raw.get("is_online")
    if not isinstance(online, bool):
        raise ValueError("Unknown event format")
    location = ", ".join(part for part in [raw.get("city"), "India"] if part)
    values = OpportunityCreate(
        title=raw["name"],
        description=raw["desc"][:20000],
        kind="HACKATHON",
        apply_url=expected_url,
        location=location[:160],
        work_mode="HYBRID" if settings.get("is_hybrid") else "REMOTE" if online else "ONSITE",
        registration_closes_at=deadline,
        starts_at=start,
        ends_at=end,
    ).model_dump(mode="json", exclude={"eligibility"})
    # No participant profiles, emails, organizer contacts, logos or eligibility guesses.
    return dict(
        **values,
        source_name=SOURCE,
        source_id=identity,
        source_url=expected_url,
        organization_name="Organizer listed on Devfolio",
    )


def crawl_events():
    # A child process isolates Scrapy's reactor. No shell, arbitrary URL or user payload.
    with tempfile.TemporaryDirectory(prefix="alignn-devfolio-") as folder:
        output = Path(folder) / "events.json"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "alignn.domains.opportunities.devfolio",
                "--crawl-output",
                str(output),
            ],
            check=True,
            timeout=240,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if output.stat().st_size > 3 * 1024 * 1024:
            raise ValueError("Crawler output too large")
        result = json.loads(output.read_text())
    if not result.get("index_valid") or not result.get("rows"):
        raise ValueError("No verified Indian events; preserving catalog")
    return result


def sync_devfolio(fetch=crawl_events):
    # Release the read transaction before crawling; recheck freshness under the write lock.
    with SessionLocal() as db:
        if source_is_fresh(db, SOURCE, utcnow()):
            return {"status": "throttled", "imported": 0}
    result = fetch()
    with SessionLocal.begin() as db:
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(8134092)")):
            raise RuntimeError("source_sync_busy")
        now = utcnow()
        latest = db.scalar(
            select(Opportunity.source_checked_at)
            .where(Opportunity.source_name == SOURCE)
            .order_by(Opportunity.source_checked_at.desc())
            .limit(1)
        )
        if latest and now - latest < timedelta(hours=6):
            return {"status": "throttled", "imported": 0}
        rows = result["rows"]
        if not result.get("index_valid") or not rows or len(rows) > MAX_EVENTS:
            raise ValueError("Invalid crawler manifest")
        if len({r["source_id"] for r in rows}) != len(rows):
            raise ValueError("Duplicate source identity")
        # Revalidate the child-process boundary before any catalog writes.
        normalized = []
        for row in rows:
            UUID(row["source_id"])
            slug = row["source_url"].removeprefix("https://").removesuffix(".devfolio.co/")
            if event_url(slug) != row["source_url"] or row["apply_url"] != row["source_url"]:
                raise ValueError("Invalid source URL")
            if row["source_name"] != SOURCE or row["kind"] != "HACKATHON":
                raise ValueError("Invalid source contract")
            fields = {key: row[key] for key in OpportunityCreate.model_fields if key in row}
            values = OpportunityCreate(**fields).model_dump(mode="python", exclude={"eligibility"})
            values.update(
                source_id=row["source_id"],
                source_name=SOURCE,
                source_url=row["source_url"],
                organization_name=row["organization_name"],
            )
            normalized.append(values)
        if not db.get(Organization, SOURCE_ORG):
            db.add(
                Organization(
                    id=SOURCE_ORG,
                    name="Devfolio public opportunities",
                    website="https://devfolio.co",
                    verified=False,
                )
            )
            db.flush()
        catalog = db.scalars(select(Skill)).all()
        imported = 0
        for values in normalized:
            values["preferred_skills"] = inferred_skills(catalog, values)
            if (values["registration_closes_at"] and values["registration_closes_at"] <= now) or (
                values["ends_at"] and values["ends_at"] <= now
            ):
                continue
            row = db.scalar(
                select(Opportunity).where(
                    Opportunity.source_name == SOURCE, Opportunity.source_id == values["source_id"]
                )
            )
            if row is None:
                row = Opportunity(organization_id=SOURCE_ORG, **values)
                db.add(row)
            elif any(getattr(row, k) != v for k, v in values.items()) or row.status != "PUBLISHED":
                if row.registration_closes_at != values["registration_closes_at"]:
                    row.deadline_version += 1
                for key, value in values.items():
                    setattr(row, key, value)
                row.version += 1
            row.source_checked_at = now
            row.status = "PUBLISHED"
            imported += 1
        # The public index is curated, not a complete export: absence never means closed.
        for row in db.scalars(
            select(Opportunity).where(
                Opportunity.source_name == SOURCE, Opportunity.status == "PUBLISHED"
            )
        ):
            if (row.registration_closes_at and row.registration_closes_at <= now) or (
                row.ends_at and row.ends_at <= now
            ):
                row.status = "CLOSED"
                row.version += 1
        return {
            "status": "synced",
            "imported": imported,
            "detail_failures": result.get("detail_failures", 0),
        }


def run_crawler(output):
    import scrapy
    from scrapy.crawler import AsyncCrawlerProcess

    class IndianHackathons(scrapy.Spider):
        name = "alignn_devfolio"
        allowed_domains = ["devfolio.co"]

        def __init__(self):
            self.rows = []
            self.index_valid = False
            self.detail_failures = 0
            self.now = utcnow()

        async def start(self):
            yield scrapy.Request(INDEX, callback=self.parse_index)

        def parse_index(self, response):
            events = index_events(next_data(response))
            self.index_valid = True
            for identity, url in events.items():
                yield scrapy.Request(
                    url,
                    callback=self.parse_event,
                    errback=self.failed,
                    cb_kwargs={"identity": identity, "url": url},
                )

        def parse_event(self, response, identity, url):
            try:
                row = normalize_event(next_data(response)["hackathon"], identity, url, self.now)
                if row:
                    self.rows.append(row)
            except (ValueError, KeyError, TypeError):
                self.detail_failures += 1

        def failed(self, failure):
            self.detail_failures += 1

        def closed(self, reason):
            Path(output).write_text(
                json.dumps(
                    dict(
                        index_valid=self.index_valid,
                        rows=self.rows,
                        detail_failures=self.detail_failures,
                        finish_reason=reason,
                    )
                )
            )

    # Official settings: https://docs.scrapy.org/en/latest/topics/settings.html
    process = AsyncCrawlerProcess(
        settings={
            "ROBOTSTXT_OBEY": True,
            "USER_AGENT": "Alignn/0.1 (public opportunity discovery)",
            "CONCURRENT_REQUESTS": 1,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
            "DOWNLOAD_DELAY": 1.0,
            "DOWNLOAD_TIMEOUT": 15,
            "DOWNLOAD_MAXSIZE": 2 * 1024 * 1024,
            "DOWNLOAD_WARNSIZE": 1024 * 1024,
            "REDIRECT_ENABLED": False,
            "METAREFRESH_ENABLED": False,
            "COOKIES_ENABLED": False,
            "RETRY_TIMES": 1,
            "CLOSESPIDER_TIMEOUT": 180,
            "TELNETCONSOLE_ENABLED": False,
            "LOG_ENABLED": False,
            "ROBOTSTXT_PARSER": "scrapy.robotstxt.PythonRobotParser",
        }
    )
    process.crawl(IndianHackathons)
    process.start()


def main():
    parser = argparse.ArgumentParser(description="Sync explicit Indian Devfolio hackathons")
    parser.add_argument("--crawl-output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--preview", action="store_true", help="Fetch metadata without database writes"
    )
    args = parser.parse_args()
    if args.crawl_output:
        run_crawler(args.crawl_output)
    elif args.preview:
        result = crawl_events()
        print(json.dumps(result, indent=2))
    else:
        print(sync_devfolio())


if __name__ == "__main__":
    main()
