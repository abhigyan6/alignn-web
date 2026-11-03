from sqlalchemy import select

from alignn.db import utcnow
from alignn.domains.identity.models import User
from alignn.domains.opportunities.service import lock_opportunity
from alignn.errors import DomainError

from .models import Team, TeamMember


def open_event(o):
    if o.status != "PUBLISHED" or o.mode != "HOSTED" or o.registration_closes_at <= utcnow():
        raise DomainError("registration_closed", "Team changes are closed.", 409)


def lock_team(db, id):
    t = db.get(Team, id)
    if not t:
        raise DomainError("not_found", "Team not found.", 404)
    o = lock_opportunity(db, t.opportunity_id)
    db.refresh(t, with_for_update=True)
    return o, t


def team_out(db, t):
    return {
        "id": t.id,
        "opportunity_id": t.opportunity_id,
        "captain_id": t.captain_id,
        "name": t.name,
        "locked": t.locked,
        "members": [
            {"user_id": u.id, "full_name": u.full_name}
            for u in db.scalars(
                select(User).join(TeamMember).where(TeamMember.team_id == t.id).order_by(User.id)
            )
        ],
    }


def require_team_member(db, actor, t, captain=False):
    if captain and t.captain_id != actor.user_id:
        raise DomainError("forbidden", "Only the captain can do this.", 403)
    if not db.scalar(
        select(TeamMember).where(TeamMember.team_id == t.id, TeamMember.user_id == actor.user_id)
    ):
        raise DomainError("not_found", "Team not found.", 404)


def unlocked(t):
    if t.locked:
        raise DomainError("roster_locked", "This team roster is locked by registration.", 409)
