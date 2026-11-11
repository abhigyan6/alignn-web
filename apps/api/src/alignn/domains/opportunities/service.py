from datetime import timedelta

from sqlalchemy import func, select

from alignn.db import utcnow
from alignn.domains.identity.service import require_verified
from alignn.domains.organizations.service import lock_organization, require_membership
from alignn.domains.profiles.models import Profile
from alignn.errors import DomainError
from alignn.jobs.models import Job

from .models import MatchSnapshot, Opportunity
from .schemas import OpportunityOut


def lock_opportunity(db, id):
    o = db.scalar(select(Opportunity).where(Opportunity.id == id).with_for_update())
    if not o or o.mode != "EXTERNAL":
        raise DomainError("not_found", "Opportunity not found.", 404)
    return o


def visible(db, actor, id):
    o = db.get(Opportunity, id)
    if not o or o.mode != "EXTERNAL":
        raise DomainError("not_found", "Opportunity not found.", 404)
    if o.status != "PUBLISHED":
        if actor is None:
            raise DomainError("not_found", "Opportunity not found.", 404)
        if o.status == "CLOSED":
            from alignn.domains.applications.models import Application

            from .models import SavedOpportunity

            owned_save = db.scalar(
                select(SavedOpportunity.id).where(
                    SavedOpportunity.user_id == actor.user_id, SavedOpportunity.opportunity_id == id
                )
            )
            owned_application = db.scalar(
                select(Application.id).where(
                    Application.user_id == actor.user_id, Application.opportunity_id == id
                )
            )
            if owned_save or owned_application:
                return o
        require_membership(db, actor, o.organization_id, "manage")
    return o


def validate_skills(db, data):
    from alignn.domains.profiles.service import validate_skills as canonicalize

    data.required_skills = canonicalize(db, data.required_skills)
    data.preferred_skills = canonicalize(db, data.preferred_skills)


def mutate_opportunity(db, actor, opportunity_id, expected_version, data):
    o = lock_opportunity(db, opportunity_id)
    require_verified(actor)
    require_membership(db, actor, o.organization_id, "manage")
    if o.version != expected_version:
        raise DomainError("stale_version", "Reload the latest opportunity.", 409)
    validate_skills(db, data)
    if o.status == "PUBLISHED" and not lock_organization(db, o.organization_id).verified:
        raise DomainError(
            "organization_unverified",
            "Verify your organization before editing published listings.",
            409,
        )
    if data.registration_closes_at != o.registration_closes_at:
        o.deadline_version += 1
    for k, v in data.model_dump(mode="python").items():
        setattr(o, k, data.eligibility.model_dump(mode="json") if k == "eligibility" else v)
    o.version += 1
    db.flush()
    return OpportunityOut.model_validate(o)


def search_opportunities(db, actor, query):
    from .visibility import active_filters

    base = select(Opportunity).where(*active_filters(utcnow()))
    if query.q:
        base = base.where(
            Opportunity.search_vector.op("@@")(func.websearch_to_tsquery("english", query.q))
        )
    if query.kind:
        base = base.where(Opportunity.kind == query.kind)
    status = "NOT_REQUESTED"
    sort = query.sort
    if sort == "match" and actor:
        p = db.scalar(select(Profile).where(Profile.user_id == actor.user_id))
        revision = p.revision if p else 0
        missing = db.scalar(select(func.count()).select_from(base.subquery()))
        ids = base.with_only_columns(Opportunity.id).subquery()
        count = db.scalar(
            select(func.count())
            .select_from(MatchSnapshot)
            .join(Opportunity)
            .where(
                MatchSnapshot.opportunity_id.in_(select(ids.c.id)),
                MatchSnapshot.user_id == actor.user_id,
                MatchSnapshot.profile_revision == revision,
                MatchSnapshot.opportunity_version == Opportunity.version,
            )
        )
        if count == missing:
            status = "FRESH"
            base = (
                base.join(MatchSnapshot, MatchSnapshot.opportunity_id == Opportunity.id)
                .where(MatchSnapshot.user_id == actor.user_id)
                .order_by(MatchSnapshot.score.desc(), Opportunity.id)
            )
        else:
            from alignn.jobs.worker import enqueue_job

            catalog = select(func.max(Opportunity.created_at), func.sum(Opportunity.version)).where(
                Opportunity.mode == "EXTERNAL", Opportunity.status == "PUBLISHED"
            )
            newest, version_sum = db.execute(catalog).one()
            key = f"rank-{actor.user_id}-{revision}-{newest}-{version_sum}"
            now = utcnow()
            first = db.scalar(select(Job).where(Job.key == key))
            if first is not None and first.status in {"FAILED", "SKIPPED"}:
                if first.run_at > now - timedelta(minutes=5):
                    status = "UNAVAILABLE"
                    key = None
                else:
                    key += "-retry"
            if key:
                job_id = enqueue_job(
                    db,
                    kind="rank_profile",
                    key=key,
                    payload={"user_id": str(actor.user_id)},
                    run_at=now,
                    expires_at=None,
                )
                job = db.get(Job, job_id)
                status = "PENDING" if job.status in {"QUEUED", "RUNNING"} else "UNAVAILABLE"
            sort = "newest"
    elif sort == "match":
        status = "SIGN_IN_REQUIRED"
        sort = "newest"
    if sort == "deadline":
        base = base.order_by(Opportunity.registration_closes_at, Opportunity.id)
    elif sort == "newest":
        base = base.order_by(Opportunity.created_at.desc(), Opportunity.id)
    rows = db.scalars(base.offset(query.cursor).limit(query.limit + 1)).all()
    return {
        "items": [OpportunityOut.model_validate(o) for o in rows[: query.limit]],
        "next_cursor": query.cursor + query.limit if len(rows) > query.limit else None,
        "sort": sort,
        "ranking_status": status,
    }
