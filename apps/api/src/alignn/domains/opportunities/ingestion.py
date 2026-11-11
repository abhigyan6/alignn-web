"""Legacy retirement and local source scheduling. Remotive never fetches."""

import argparse
import re
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.models import Opportunity

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


def sync_remotive(client=None):
    """Compatibility entry point: retire old rows and never contact the source."""
    from .visibility import expire_opportunities

    with SessionLocal.begin() as db:
        closed = expire_opportunities(db, utcnow())
    return {"status": "retired", "imported": 0, "closed": closed}


def schedule_ingestion(db, now):
    from alignn.jobs.worker import enqueue_job

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
    return 1 + len(BOARDS)


def main():
    parser = argparse.ArgumentParser(description="Sync public external opportunities")
    parser.parse_args()
    print(sync_remotive())


if __name__ == "__main__":
    main()
