from sqlalchemy import func, select

from alignn.db import utcnow
from alignn.domains.identity.service import require_verified
from alignn.domains.organizations.service import require_membership
from alignn.domains.profiles.models import Profile
from alignn.errors import DomainError

from .models import MatchSnapshot, Opportunity
from .schemas import OpportunityOut


def lock_opportunity(db, id):
    o = db.scalar(select(Opportunity).where(Opportunity.id == id).with_for_update())
    if not o:
        raise DomainError("not_found", "Opportunity not found.", 404)
    return o


def visible(db, actor, id):
    o = db.get(Opportunity, id)
    if not o:
        raise DomainError("not_found", "Opportunity not found.", 404)
    if o.status != "PUBLISHED":
        if actor is None:
            raise DomainError("not_found", "Opportunity not found.", 404)
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
    if o.admission_started:
        if (
            o.mode != data.mode
            or o.eligibility != data.eligibility.model_dump(mode="json")
            or o.team_min != data.team_min
            or o.team_max != data.team_max
        ):
            raise DomainError(
                "policy_locked",
                "Admission policy and team size are locked after registration begins.",
                409,
            )
        if data.capacity < o.capacity_used:
            raise DomainError(
                "capacity_conflict", "Capacity cannot be below confirmed registrations.", 409
            )
        if data.registration_closes_at < o.registration_closes_at:
            raise DomainError(
                "deadline_locked",
                "Registration close cannot be brought forward after admission starts.",
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
    base = select(Opportunity).where(Opportunity.status == "PUBLISHED")
    if query.q:
        base = base.where(
            Opportunity.search_vector.op("@@")(func.websearch_to_tsquery("english", query.q))
        )
    if query.kind:
        base = base.where(Opportunity.kind == query.kind)
    if query.mode:
        base = base.where(Opportunity.mode == query.mode)
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

            enqueue_job(
                db,
                kind="rank_profile",
                key=f"rank-{actor.user_id}-{revision}-{db.scalar(select(func.max(Opportunity.created_at)))}-{db.scalar(select(func.sum(Opportunity.version)))}",
                payload={"user_id": str(actor.user_id)},
                run_at=utcnow(),
                expires_at=None,
            )
            status = "PENDING"
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
