"""Public Remotive feed; no credentials, redirects, or arbitrary fetch URLs."""

import argparse
import re
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5

import httpx
from sqlalchemy import select, text

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.organizations.models import Organization
from alignn.domains.profiles.models import Skill

FEED_URL = "https://remotive.com/api/remote-jobs"
SOURCE = "Remotive"
SOURCE_ORG = uuid5(NAMESPACE_URL, FEED_URL)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "li", "div", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def inferred_skills(catalog, values):
    """Source keywords are preferences, never verified eligibility requirements."""
    content = (values["title"] + " " + values["description"]).lower()
    return [
        skill.key
        for skill in catalog
        if any(
            re.search(r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)", content)
            for alias in [skill.name, *skill.aliases]
        )
    ]


def source_is_fresh(db, source, now):
    latest = db.scalar(
        select(Opportunity.source_checked_at)
        .where(Opportunity.source_name == source)
        .order_by(Opportunity.source_checked_at.desc())
        .limit(1)
    )
    return latest is not None and now - latest < timedelta(hours=6)


def normalize(row):
    source_id = str(row["id"])
    if not source_id.isdigit() or len(source_id) > 180:
        raise ValueError("Invalid source ID")
    url = row["url"]
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "remotive.com"
        or parsed.username
        or len(url) > 1000
    ):
        raise ValueError("Invalid source URL")
    parser = PlainText()
    parser.feed(row["description"])
    description = re.sub(r"\n\s*\n+", "\n\n", "".join(parser.parts)).strip()[:20000]
    title = str(row["title"]).strip()[:180]
    company = str(row["company_name"]).strip()[:180]
    if len(title) < 3 or len(description) < 10 or not company:
        raise ValueError("Incomplete listing")
    return dict(
        source_id=source_id,
        source_name=SOURCE,
        source_url=url,
        apply_url=url,
        title=title,
        description=description,
        organization_name=company,
        kind="INTERNSHIP" if row.get("job_type") == "internship" else "JOB",
        location=str(row.get("candidate_required_location") or "Not specified")[:160],
        work_mode="REMOTE",
        mode="EXTERNAL",
    )


def fetch_feed(client):
    with client.stream("GET", FEED_URL) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 10 * 1024 * 1024:
                raise ValueError("Feed exceeds size limit")
    import json

    payload = json.loads(content)
    rows = payload.get("jobs")
    if not isinstance(rows, list) or not rows or payload.get("job-count") != len(rows):
        raise ValueError("Incomplete feed; keeping previous catalog")
    # Validate the entire snapshot before writes or closing any existing listings.
    normalized = [normalize(row) for row in rows]
    if len({row["source_id"] for row in normalized}) != len(normalized):
        raise ValueError("Duplicate source IDs")
    return normalized


def sync_remotive(client=None):
    with SessionLocal.begin() as db:
        # One source sync at a time, including fetch and the six-hour throttle.
        db.execute(text("SELECT pg_advisory_xact_lock(8134091)"))
        org = db.get(Organization, SOURCE_ORG)
        latest = db.scalar(
            select(Opportunity.source_checked_at)
            .where(Opportunity.source_name == SOURCE)
            .order_by(Opportunity.source_checked_at.desc())
            .limit(1)
        )
        now = utcnow()
        if latest and now - latest < timedelta(hours=6):
            return {"status": "throttled", "imported": 0}
        if client is None:
            with httpx.Client(
                timeout=15,
                follow_redirects=False,
                headers={"User-Agent": "Alignn/0.1 (public opportunity feed)"},
            ) as http:
                rows = fetch_feed(http)
        else:
            rows = fetch_feed(client)
        if not org:
            org = Organization(
                id=SOURCE_ORG,
                name="Remotive public feed",
                website="https://remotive.com",
                verified=False,
            )
            db.add(org)
            db.flush()
        catalog = db.scalars(select(Skill)).all()
        seen = set()
        for values in rows:
            values["preferred_skills"] = inferred_skills(catalog, values)
            source_id = values["source_id"]
            seen.add(source_id)
            row = db.scalar(
                select(Opportunity).where(
                    Opportunity.source_name == SOURCE, Opportunity.source_id == source_id
                )
            )
            if row is None:
                row = Opportunity(organization_id=SOURCE_ORG, **values)
                db.add(row)
            elif (
                any(getattr(row, key) != value for key, value in values.items())
                or row.status != "PUBLISHED"
            ):
                for key, value in values.items():
                    setattr(row, key, value)
                row.version += 1
            row.status = "PUBLISHED"
            row.source_checked_at = now
        for row in db.scalars(
            select(Opportunity).where(
                Opportunity.source_name == SOURCE, Opportunity.status == "PUBLISHED"
            )
        ):
            if row.source_id not in seen:
                row.status = "CLOSED"
                row.version += 1
        return {"status": "synced", "imported": len(rows)}


def schedule_ingestion(db, now):
    from alignn.jobs.worker import enqueue_job

    enqueue_job(
        db,
        kind="ingest_remotive",
        key=f"ingest-remotive-{now.date()}-{now.hour // 6}",
        payload={},
        run_at=now,
        expires_at=now + timedelta(hours=6),
    )
    enqueue_job(
        db,
        kind="ingest_devfolio",
        key=f"ingest-devfolio-{now.date()}-{now.hour // 6}",
        payload={},
        run_at=now,
        expires_at=now + timedelta(hours=6),
    )
    from alignn.domains.opportunities.greenhouse import BOARDS

    for board in BOARDS:
        enqueue_job(
            db,
            kind="ingest_greenhouse",
            key=f"ingest-greenhouse-{board}-{now.date()}-{now.hour // 6}",
            payload={"board": board},
            run_at=now,
            expires_at=now + timedelta(hours=6),
        )
    return 2 + len(BOARDS)


def main():
    parser = argparse.ArgumentParser(description="Sync public external opportunities")
    parser.parse_args()
    print(sync_remotive())


if __name__ == "__main__":
    main()
