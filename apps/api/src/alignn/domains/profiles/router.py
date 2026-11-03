from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, select

from alignn.domains.identity.models import User
from alignn.domains.identity.service import check_csrf, get_actor
from alignn.domains.profiles.models import Profile, ProfileSkill, Project, Skill
from alignn.domains.profiles.schemas import (
    ProfileOut,
    ProfileUpdate,
    ProjectCreate,
    ProjectOut,
    SkillsUpdate,
)
from alignn.domains.profiles.service import profile_out, update_profile, validate_skills
from alignn.errors import DomainError

router = APIRouter(prefix="/api/v1", tags=["Profiles"])


@router.get("/me/profile", response_model=ProfileOut)
def profile(request: Request):
    return profile_out(request.state.db, get_actor(request))


@router.put("/me/profile", response_model=ProfileOut, dependencies=[Depends(check_csrf)])
def edit_profile(data: ProfileUpdate, request: Request):
    return update_profile(request.state.db, get_actor(request), data)


@router.get("/skills")
def catalog(request: Request):
    rows = request.state.db.scalars(select(Skill).order_by(Skill.name)).all()
    return [{"id": s.id, "key": s.key, "name": s.name, "category": s.category} for s in rows]


@router.get("/me/skills")
def list_skills(request: Request):
    actor = get_actor(request)
    rows = request.state.db.execute(
        select(ProfileSkill, Skill).join(Skill).where(ProfileSkill.user_id == actor.user_id)
    ).all()
    return [{"skill_id": s.key, "name": s.name, "level": p.level} for p, s in rows]


@router.put("/me/skills", dependencies=[Depends(check_csrf)])
def edit_skills(data: SkillsUpdate, request: Request):
    db = request.state.db
    actor = get_actor(request)
    canonical = validate_skills(db, [s.skill_id for s in data.skills])
    for entry, key in zip(data.skills, canonical, strict=True):
        entry.skill_id = key
    db.scalar(select(User).where(User.id == actor.user_id).with_for_update())
    db.execute(delete(ProfileSkill).where(ProfileSkill.user_id == actor.user_id))
    for entry in data.skills:
        skill = db.scalar(select(Skill).where(Skill.key == entry.skill_id))
        db.add(ProfileSkill(user_id=actor.user_id, skill_id=skill.id, level=entry.level))
    update_profile(db, actor, ProfileUpdate())
    db.flush()
    return list_skills(request)


@router.get("/me/projects", response_model=list[ProjectOut])
def projects(request: Request):
    actor = get_actor(request)
    return request.state.db.scalars(
        select(Project).where(Project.user_id == actor.user_id).order_by(Project.created_at.desc())
    ).all()


@router.post(
    "/me/projects", response_model=ProjectOut, status_code=201, dependencies=[Depends(check_csrf)]
)
def add_project(data: ProjectCreate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    data.skill_ids = validate_skills(db, data.skill_ids)
    project = Project(user_id=actor.user_id, **data.model_dump())
    db.add(project)
    update_profile(db, actor, ProfileUpdate())
    db.flush()
    return project


@router.delete("/me/projects/{id}", status_code=204, dependencies=[Depends(check_csrf)])
def remove_project(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    project = db.scalar(select(Project).where(Project.id == id, Project.user_id == actor.user_id))
    if not project:
        raise DomainError("not_found", "Project not found.", 404)
    db.delete(project)
    update_profile(db, actor, ProfileUpdate())


@router.get("/people")
def people(
    request: Request, search: str = Query("", max_length=100), limit: int = Query(30, ge=1, le=100)
):
    query = (
        select(Profile, User)
        .join(User, User.id == Profile.user_id)
        .where(Profile.discoverable, User.is_active, User.is_verified)
    )
    if search:
        query = query.where(User.full_name.ilike(f"%{search}%"))
    rows = request.state.db.execute(query.order_by(Profile.updated_at.desc()).limit(limit)).all()
    return {
        "items": [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "college": p.college,
                "bio": p.bio,
                "career_interests": p.career_interests,
            }
            for p, user in rows
        ]
    }
