"""Bounded known-listing checks. Absence, access failures and expiry stay distinct."""

import json
from datetime import timedelta
from uuid import uuid4

from alignn_scraper.models import SourceResult
from alignn_scraper.parsers import parse_devfolio, parse_greenhouse, parse_hackindia, parse_luma
from alignn_scraper.registry import SOURCES
from alignn_scraper.transport import FetchError, PublicHTTP
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert

from alignn.db import SessionLocal, utcnow

from .import_scraped import apply_source
from .ingestion_models import ScraperCursor
from .models import Opportunity


def apply_check(db, identity, expected_observation, now, *, status, error=None, retry_after=None):
    row = db.scalar(select(Opportunity).where(Opportunity.id == identity).with_for_update())
    if not row or row.source_checked_at != expected_observation:
        return "superseded"
    row.last_attempt_at = now
    row.next_check_at = now + timedelta(hours=6)
    row.source_error = error or ("not_found" if status == 404 else None)
    close = status == 410
    if status == 404:
        if row.missing_since is None:
            row.missing_since = now
            row.missing_count = 1
        elif now - row.missing_since >= timedelta(minutes=30):
            row.missing_count += 1
            close = row.missing_count >= 2
        row.next_check_at = now + timedelta(minutes=30)
    elif status == 429:
        row.next_check_at = now + timedelta(seconds=max(6 * 3600, min(retry_after or 0, 24 * 3600)))
    if close:
        if row.status != "CLOSED":
            row.version += 1
        row.status = "CLOSED"
        row.closure_reason = "source_removed"
        row.source_state = "CLOSED"
        row.source_checked_at = now
        row.source_content_hash = None
        return "removed"
    return "unknown"


def recheck_source(source):
    if source not in SOURCES or SOURCES[source].status != "enabled":
        raise ValueError("unsupported_source")
    now = utcnow()
    token = uuid4().hex
    key = "recheck-lease:" + source
    # Persist a source lease without holding a transaction over public network I/O.
    with SessionLocal.begin() as db:
        db.execute(
            insert(ScraperCursor)
            .values(key=key, value={})
            .on_conflict_do_nothing(index_elements=["key"])
        )
        cursor = db.scalar(select(ScraperCursor).where(ScraperCursor.key == key).with_for_update())
        if cursor.value.get("until", "") > now.isoformat():
            return {"status": "busy"}
        cursor.value = {"token": token, "until": (now + timedelta(seconds=240)).isoformat()}
        rows = [
            (r.id, r.source_checked_at, r.source_url, r.source_id)
            for r in db.scalars(
                select(Opportunity)
                .where(
                    Opportunity.source_name == SOURCES[source].name,
                    Opportunity.status == "PUBLISHED",
                    or_(Opportunity.next_check_at.is_(None), Opportunity.next_check_at <= now),
                )
                .order_by(Opportunity.next_check_at.nullsfirst(), Opportunity.id)
                .limit(20)
            )
        ]
    http = PublicHTTP(source)
    checked = failed = 0
    try:
        board_data = None
        for identity, stamp, url, source_id in rows:
            observed = None
            error = None
            status = 200
            retry_after = None
            try:
                if source.startswith("greenhouse-"):
                    if board_data is None:
                        payload = json.loads(http.get(SOURCES[source].indexes[0]))
                        candidate = payload["jobs"]
                        if (
                            not isinstance(candidate, list)
                            or payload["meta"]["total"] != len(candidate)
                            or len({str(item["id"]) for item in candidate}) != len(candidate)
                        ):
                            raise ValueError("incomplete_board")
                        board_data = candidate
                    raw = next((r for r in board_data if str(r["id"]) == source_id), None)
                    # A complete documented ATS snapshot can explicitly report absence.
                    if raw is None:
                        status = 410
                    else:
                        observed = parse_greenhouse(
                            raw, source.removeprefix("greenhouse-"), utcnow()
                        )
                else:
                    body = http.get(url)
                    observed = {
                        "hackindia": parse_hackindia,
                        "luma": parse_luma,
                        "devfolio": parse_devfolio,
                    }[source](body, url, utcnow())
                if status == 200 and (observed is None or observed.source_id != source_id):
                    raise ValueError("source_identity_or_geography_changed")
            except (ValueError, KeyError, TypeError) as e:
                failed += 1
                status = e.status if isinstance(e, FetchError) else None
                retry_after = e.retry_after if isinstance(e, FetchError) else None
                error = e.code if isinstance(e, FetchError) else "recheck_validation_failed"
            with SessionLocal.begin() as db:
                cursor = db.scalar(
                    select(ScraperCursor).where(ScraperCursor.key == key).with_for_update()
                )
                if (
                    cursor.value.get("token") != token
                    or cursor.value["until"] < utcnow().isoformat()
                ):
                    return {"status": "lease_lost", "checked": checked}
                if observed is not None and error is None:
                    # The importer serializes source observations and fences older data.
                    result = SourceResult(
                        source=source, status="partial", checked_at=utcnow(), records=[observed]
                    )
                    apply_source(
                        db,
                        result,
                        {"recheck": str(identity), "observed_at": observed.observed_at.isoformat()},
                        __import__("hashlib")
                        .sha256(observed.model_dump_json().encode())
                        .hexdigest(),
                    )
                else:
                    apply_check(
                        db,
                        identity,
                        stamp,
                        utcnow(),
                        status=status,
                        error=error,
                        retry_after=retry_after,
                    )
            checked += 1
            if status in {403, 429} or error in {"robots_disallowed", "source_budget_exhausted"}:
                break
        return {
            "status": "checked",
            "checked": checked,
            "failed": failed,
            "remaining": len(rows) - checked,
        }
    finally:
        http.close()
        with SessionLocal.begin() as db:
            cursor = db.scalar(
                select(ScraperCursor).where(ScraperCursor.key == key).with_for_update()
            )
            if cursor and cursor.value.get("token") == token:
                cursor.value = {**cursor.value, "until": utcnow().isoformat()}
