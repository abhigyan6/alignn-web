"""Public, documented ATS GET API; curated boards, Indian internships only."""

import argparse
import json
import re
from datetime import timedelta
from html import unescape
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5

import httpx
from sqlalchemy import select, text

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.ingestion import PlainText, inferred_skills, source_is_fresh
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.opportunities.schemas import OpportunityCreate
from alignn.domains.organizations.models import Organization
from alignn.domains.profiles.models import Skill

# Curated from actual live boards, not user-provided URLs. No submission API calls.
BOARDS = {
    "stripe": ("Stripe", {"stripe.com"}),
    "figma": ("Figma", {"job-boards.greenhouse.io", "boards.greenhouse.io"}),
    "razorpaysoftwareprivatelimited": (
        "Razorpay",
        {"job-boards.greenhouse.io", "boards.greenhouse.io"},
    ),
}
INDIAN_LOCATION = re.compile(
    r"\b(?:india|bengaluru|bangalore|hyderabad|gurugram|mumbai|pune|chennai)\b", re.I
)


def normalize_intern(row, board):
    company, hosts = BOARDS[board]
    title = str(row["title"]).strip()
    if not re.search(r"\b(?:intern|internship)\b", title, re.I):
        return None
    if not isinstance(row.get("location"), dict) or not row["location"].get("name"):
        raise ValueError("Internship geography missing; preserve prior snapshot")
    location = str(row["location"]["name"]).strip()
    # Word boundary avoids matching 'Internal Systems' as an internship.
    if not re.search(r"\b(?:intern|internship)\b", title, re.I) or not INDIAN_LOCATION.search(
        location
    ):
        return None
    identity = str(row["id"])
    url = row["absolute_url"]
    parsed = urlsplit(url)
    if (
        not identity.isdigit()
        or parsed.scheme != "https"
        or parsed.hostname not in hosts
        or parsed.username
        or parsed.port not in {None, 443}
    ):
        raise ValueError("Invalid employer listing")
    parser = PlainText()
    parser.feed(unescape(row["content"]))
    description = re.sub(r"\n\s*\n+", "\n\n", "".join(parser.parts)).strip()[:20000]
    # A location is not a work-mode policy; retain unknown when no format is published.
    mode = re.search(r"(?:^|[;, (])(?:remote|hybrid)(?:$|[;, )])", location, re.I)
    work_mode = mode.group(0).strip(" ;,()").upper() if mode else "UNKNOWN"
    values = OpportunityCreate(
        title=title,
        description=description,
        kind="INTERNSHIP",
        apply_url=url,
        location=location[:160],
        work_mode=work_mode,
    )
    return dict(
        **values.model_dump(exclude={"eligibility"}),
        source_id=identity,
        source_name=f"Greenhouse:{board}",
        source_url=url,
        organization_name=company,
    )


def fetch_board(client, board):
    # Official GET contract: https://docs.greenhouse.io/job-board.html#list-jobs
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    with client.stream("GET", url) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > 20 * 1024 * 1024:
                raise ValueError("Board too large")
    payload = json.loads(data)
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or payload.get("meta", {}).get("total") != len(jobs):
        raise ValueError("Incomplete employer snapshot")
    identities = [str(row["id"]) for row in jobs]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate employer listing")
    return [item for row in jobs if (item := normalize_intern(row, board))]


def sync_board(board, client=None):
    if board not in BOARDS:
        raise ValueError("Unknown employer board")
    company, _ = BOARDS[board]
    source = f"Greenhouse:{board}"
    org_id = uuid5(NAMESPACE_URL, f"https://boards-api.greenhouse.io/v1/boards/{board}")
    with SessionLocal() as db:
        if source_is_fresh(db, source, utcnow()):
            return {"status": "throttled", "imported": 0}
    if client is None:
        with httpx.Client(
            timeout=20,
            follow_redirects=False,
            headers={"User-Agent": "Alignn/0.1 (public career discovery)"},
        ) as http:
            rows = fetch_board(http, board)
    else:
        rows = fetch_board(client, board)
    with SessionLocal.begin() as db:
        if not db.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:source))"), {"source": source}
        ):
            raise RuntimeError("source_sync_busy")
        now = utcnow()
        latest = db.scalar(
            select(Opportunity.source_checked_at)
            .where(Opportunity.source_name == source)
            .order_by(Opportunity.source_checked_at.desc())
            .limit(1)
        )
        if latest and now - latest < timedelta(hours=6):
            return {"status": "throttled", "imported": 0}
        if not db.get(Organization, org_id):
            # Source presence does not establish employer endorsement or verification.
            db.add(Organization(id=org_id, name=f"{company} public careers", verified=False))
            db.flush()
        seen = set()
        catalog = db.scalars(select(Skill)).all()
        for values in rows:
            values["preferred_skills"] = inferred_skills(catalog, values)
            seen.add(values["source_id"])
            row = db.scalar(
                select(Opportunity).where(
                    Opportunity.source_name == source, Opportunity.source_id == values["source_id"]
                )
            )
            if row is None:
                row = Opportunity(organization_id=org_id, **values)
                db.add(row)
            elif any(getattr(row, k) != v for k, v in values.items()) or row.status != "PUBLISHED":
                for key, value in values.items():
                    setattr(row, key, value)
                row.version += 1
            row.source_checked_at = now
            row.status = "PUBLISHED"
        # Complete official board snapshots can close disappeared or relocated internships.
        for row in db.scalars(
            select(Opportunity).where(
                Opportunity.source_name == source, Opportunity.status == "PUBLISHED"
            )
        ):
            if row.source_id not in seen:
                row.status = "CLOSED"
                row.source_checked_at = now
                row.version += 1
        return {"status": "synced", "imported": len(rows)}


def sync_greenhouse():
    return {board: sync_board(board) for board in BOARDS}


def main():
    argparse.ArgumentParser(description="Sync curated Indian internships").parse_args()
    print(sync_greenhouse())


if __name__ == "__main__":
    main()
