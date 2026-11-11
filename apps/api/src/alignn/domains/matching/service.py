import re

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from alignn.domains.opportunities.models import MatchSnapshot, Opportunity
from alignn.domains.profiles.models import Profile, ProfileSkill, Project, Skill

WEIGHTS = [35, 25, 20, 10, 10]


def weighted_fit(factors):
    return round(sum(x * w / 100 for x, w in zip(factors, WEIGHTS, strict=True)), 2)


def skill_score(owned, required, preferred):
    total = 2 * len(set(required)) + len(set(preferred))
    return (
        100 * (2 * len(owned & set(required)) + len(owned & set(preferred))) / total if total else 0
    )


def tokens(value):
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def overlap(a, b):
    return 100 * len(a & b) / len(b) if b else 0


def profile_evidence(db, user_id):
    p = db.scalar(select(Profile).where(Profile.user_id == user_id))
    owned = set(
        db.scalars(select(Skill.key).join(ProfileSkill).where(ProfileSkill.user_id == user_id))
    )
    projects = db.scalars(select(Project).where(Project.user_id == user_id)).all()
    return p, owned, projects


def calculate_fit(db, user_id, opportunity, evidence=None):
    p, owned, projects = evidence if evidence is not None else profile_evidence(db, user_id)
    required = set(opportunity.required_skills + opportunity.preferred_skills)
    project_skills = {k for project in projects for k in project.skill_ids}
    factors = [
        skill_score(owned, opportunity.required_skills, opportunity.preferred_skills),
        overlap(project_skills, required),
        overlap(
            tokens(" ".join(p.career_interests if p else [])),
            tokens(" ".join(opportunity.interests)),
        ),
        100 if p and p.preferred_work_mode in {"ANY", opportunity.work_mode} else 0,
        100
        if p
        and (
            opportunity.work_mode == "REMOTE"
            or opportunity.location.lower() in p.preferred_locations
        )
        else 0,
    ]
    return {
        "score": weighted_fit(factors),
        "factors": dict(
            zip(
                ["technical", "projects", "interests", "work_mode", "location"],
                factors,
                strict=True,
            )
        ),
        "algorithm_version": "fit-1",
        "profile_revision": p.revision if p else 0,
        "opportunity_version": opportunity.version,
        "confidence": sum(x > 0 for x in factors) / 5,
        "explanation": "Evidence overlap, not a prediction of selection.",
    }


def rebuild_matches(user_id):
    from alignn.db import SessionLocal, utcnow
    from alignn.domains.opportunities.visibility import active_filters

    with SessionLocal.begin() as db:
        active = select(Opportunity).where(*active_filters(utcnow()))
        db.execute(delete(MatchSnapshot).where(
            MatchSnapshot.user_id == user_id,
            MatchSnapshot.opportunity_id.not_in(active.with_only_columns(Opportunity.id)),
        ))
        evidence = profile_evidence(db, user_id)
        for o in db.scalars(active).yield_per(100):
            result = calculate_fit(db, user_id, o, evidence)
            values = dict(
                user_id=user_id,
                opportunity_id=o.id,
                profile_revision=result["profile_revision"],
                opportunity_version=o.version,
                score=result["score"],
                evidence=result,
                algorithm_version="fit-1",
            )
            db.execute(
                insert(MatchSnapshot)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["user_id", "opportunity_id"],
                    set_={
                        k: v for k, v in values.items() if k not in {"user_id", "opportunity_id"}
                    },
                )
            )
