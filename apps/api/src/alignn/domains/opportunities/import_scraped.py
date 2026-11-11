"""Strict backend-owned artifact import. Network access is deliberately absent."""

import argparse
import json
from datetime import timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from alignn_scraper.bundle import digest, json_bytes, read_bundle
from alignn_scraper.models import SourceResult
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from alignn.db import SessionLocal, utcnow
from alignn.domains.organizations.models import Organization
from alignn.domains.profiles.models import Skill

from .ingestion import inferred_skills
from .ingestion_models import ImportReceipt
from .models import Opportunity
from .schemas import OpportunityCreate


def receipt_key(identity, source):
    return digest(json_bytes({**identity, "source": source}))


def record_hash(record):
    return digest(json_bytes(record.model_dump(mode="json", exclude={"observed_at"})))


def ensure_receipt(db, identity, source, sha):
    key = receipt_key(identity, source)
    db.execute(
        insert(ImportReceipt)
        .values(
            identity_key=key,
            identity=identity,
            source=source,
            digest=sha,
            state="DISCOVERED",
            counts={},
        )
        .on_conflict_do_nothing(index_elements=["identity_key"])
    )
    return db.scalar(
        select(ImportReceipt).where(ImportReceipt.identity_key == key).with_for_update()
    )


def apply_source(db, result, identity, sha):
    receipt = ensure_receipt(db, identity, result.source, sha)
    if receipt.digest != sha:
        return {"status": "REJECTED", "error": "identity_digest_conflict"}
    if receipt.state in {"APPLIED", "REJECTED", "FAILED"}:
        return {"status": receipt.state, **receipt.counts}
    receipt.state = "IMPORTING"
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:source))"),
        {"source": "scraper:" + result.source},
    )
    counts = dict(added=0, updated=0, expired=0, unchanged=0, skipped=0)
    catalog = db.scalars(select(Skill)).all()
    now = utcnow()
    for observed in result.records:
        values = OpportunityCreate.model_validate(
            {
                k: v
                for k, v in observed.model_dump(mode="python").items()
                if k in OpportunityCreate.model_fields
            }
        ).model_dump(mode="python")
        values["eligibility"] = OpportunityCreate(
            **{k: v for k, v in values.items() if k != "eligibility"}
        ).eligibility.model_dump(mode="json")
        values.update(
            source_name=observed.source_name,
            source_id=observed.source_id,
            source_url=observed.source_url,
            organization_name=observed.organization_name,
        )
        values["preferred_skills"] = inferred_skills(catalog, values)
        row = db.scalar(
            select(Opportunity)
            .where(
                Opportunity.source_name == observed.source_name,
                Opportunity.source_id == observed.source_id,
            )
            .with_for_update()
        )
        content_hash = record_hash(observed)
        if row and row.source_checked_at:
            if observed.observed_at < row.source_checked_at:
                counts["skipped"] += 1
                continue
            if (
                observed.observed_at == row.source_checked_at
                and row.source_content_hash
                and row.source_content_hash != content_hash
            ):
                raise ValueError("conflicting_observation")
        reason = (
            "source_cancelled"
            if observed.source_state == "CANCELLED"
            else "source_closed"
            if observed.source_state == "CLOSED"
            else "registration_elapsed"
            if observed.registration_closes_at and observed.registration_closes_at <= now
            else "event_ended"
            if observed.ends_at and observed.ends_at <= now
            else None
        )
        if row is None and (reason or observed.source_state == "UNKNOWN"):
            counts["skipped"] += 1
            continue
        status = (
            "CLOSED" if reason else ("PUBLISHED" if observed.source_state == "OPEN" else row.status)
        )
        if row is None:
            org_id = uuid5(
                NAMESPACE_URL,
                "alignn-source:" + observed.source_name + ":" + observed.organization_name,
            )
            if not db.get(Organization, org_id):
                db.add(Organization(id=org_id, name=observed.organization_name, verified=False))
                db.flush()
            row = Opportunity(organization_id=org_id, **values, status=status)
            db.add(row)
            counts["added"] += 1
        else:
            changed = any(getattr(row, k) != v for k, v in values.items()) or row.status != status
            if changed:
                if row.registration_closes_at != observed.registration_closes_at:
                    row.deadline_version += 1
                for k, v in values.items():
                    setattr(row, k, v)
                row.status = status
                row.version += 1
                counts["expired" if reason else "updated"] += 1
            else:
                counts["unchanged"] += 1
        row.source_checked_at = observed.observed_at
        row.source_imported_at = now
        row.source_content_hash = content_hash
        row.source_state = observed.source_state
        row.country_evidence = observed.country_evidence.model_dump(mode="json")
        row.closure_reason = reason
        row.next_check_at = now + timedelta(hours=6)
        row.last_attempt_at = observed.observed_at
        row.missing_since = None
        row.missing_count = 0
        row.source_error = None
    receipt.state = "APPLIED"
    receipt.counts = counts
    receipt.applied_at = now
    receipt.error = None
    db.flush()
    return {"status": "APPLIED", **counts}


def import_bundle(data, *, identity=None, local=False, dry_run=False):
    manifest, parts = read_bundle(data, utcnow())
    sha = digest(data)
    if identity is None:
        if not local:
            raise ValueError("trusted_identity_required")
        identity = {"local_artifact": sha}
    outcomes = {}
    for source, part in parts.items():
        try:
            result = SourceResult.model_validate(part)
            for row in result.records:
                if row.observed_at < utcnow() - timedelta(hours=24):
                    raise ValueError("stale_observation")
                OpportunityCreate.model_validate(
                    {
                        k: v
                        for k, v in row.model_dump().items()
                        if k in OpportunityCreate.model_fields
                    }
                )
            if result.status == "failed":
                raise ValueError("source_collection_failed")
            if dry_run:
                outcomes[source] = {"status": "VALID", "records": len(result.records)}
                continue
            with SessionLocal.begin() as db:
                outcomes[source] = apply_source(db, result, identity, sha)
        except ValueError:
            outcomes[source] = {"status": "REJECTED", "error": "source_validation_failed"}
            if not dry_run:
                with SessionLocal.begin() as db:
                    receipt = ensure_receipt(db, identity, source, sha)
                    if receipt.digest == sha and receipt.state not in {"APPLIED", "REJECTED"}:
                        receipt.state = "REJECTED"
                        receipt.error = "source_validation_failed"
    return {"schema_version": manifest["schema_version"], "sources": outcomes}


def main():
    p = argparse.ArgumentParser(description="Validate/import an approved collector bundle")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if args.file.stat().st_size > 85 * 1024 * 1024:
        raise ValueError("download_too_large")
    outcome = import_bundle(args.file.read_bytes(), local=True, dry_run=args.dry_run)
    print(json.dumps(outcome, sort_keys=True))
    return 1 if any(s["status"] == "REJECTED" for s in outcome["sources"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
