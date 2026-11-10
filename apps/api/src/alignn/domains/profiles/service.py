from sqlalchemy import select
from sqlalchemy.orm import Session

from alignn.db import utcnow
from alignn.domains.identity.models import User
from alignn.domains.identity.schemas import Actor
from alignn.domains.profiles.models import Profile, Skill
from alignn.domains.profiles.schemas import ProfileOut, ProfileUpdate
from alignn.errors import DomainError


def get_profile(db: Session, user_id) -> Profile | None:
    return db.scalar(select(Profile).where(Profile.user_id == user_id))


def profile_out(db, actor: Actor) -> ProfileOut:
    profile = get_profile(db, actor.user_id)
    user = db.get(User, actor.user_id)
    if not profile:
        return ProfileOut(
            user_id=user.id, full_name=user.full_name, revision=0, onboarding_complete=False
        )
    fields = {key: getattr(profile, key) for key in ProfileUpdate.model_fields}
    return ProfileOut(
        id=profile.id,
        user_id=user.id,
        full_name=user.full_name,
        revision=profile.revision,
        onboarding_complete=bool(
            profile.onboarding_completed_at and profile.degree_id and profile.graduation_year
        ),
        **fields,
    )


def update_profile(db: Session, actor: Actor, data: ProfileUpdate) -> ProfileOut:
    db.scalar(select(User).where(User.id == actor.user_id).with_for_update())
    profile = get_profile(db, actor.user_id)
    updates = data.model_dump(exclude_unset=True)
    non_nullable = {
        "preferred_work_mode",
        "career_interests",
        "preferred_locations",
        "discoverable",
    }
    if any(k in updates and updates[k] is None for k in non_nullable):
        raise DomainError("invalid_input", "These profile preferences cannot be null.", 422)
    if profile is None:
        profile = Profile(user_id=actor.user_id)
        db.add(profile)
        profile.revision = 0
    grade = updates.get("cgpa", profile.cgpa)
    scale = updates.get("cgpa_scale", profile.cgpa_scale)
    if grade is not None and (scale is None or grade > scale):
        raise DomainError("invalid_input", "Provide a valid grading scale for this CGPA.", 422)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.revision += 1
    profile.updated_at = utcnow()
    db.flush()
    return profile_out(db, actor)


def validate_skills(db, keys: list[str]):
    catalog = db.scalars(select(Skill)).all()
    aliases = {alias.lower(): s.key for s in catalog for alias in [s.key, s.name, *s.aliases]}
    normalized = [aliases.get(k.strip().lower()) for k in keys]
    if any(k is None for k in normalized):
        raise DomainError("invalid_skill", "Choose skills from the catalog.", 422)
    if len(set(normalized)) != len(normalized):
        raise DomainError("duplicate_skill", "Each canonical skill can appear only once.", 422)
    return normalized
