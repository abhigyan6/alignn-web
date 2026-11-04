import hashlib
import json
from datetime import timedelta

from sqlalchemy import select

from alignn.domains.eligibility.schemas import EligibilityPolicy
from alignn.domains.eligibility.service import evaluate, profile_evidence
from alignn.domains.files.models import ConsentGrant, PrivateFile
from alignn.domains.identity.models import User
from alignn.domains.identity.schemas import Actor
from alignn.domains.identity.service import require_verified
from alignn.domains.opportunities.service import lock_opportunity
from alignn.domains.profiles.models import Profile
from alignn.domains.teams.models import Team, TeamInvitation, TeamMember
from alignn.domains.teams.service import open_event, unlocked
from alignn.errors import DomainError
from alignn.jobs.worker import enqueue_job

from .models import (
    EligibilitySnapshot,
    EventConsent,
    IdempotencyRecord,
    Registration,
    RegistrationMember,
)


def registration_out(db, r):
    return {
        "id": str(r.id),
        "opportunity_id": str(r.opportunity_id),
        "team_id": str(r.team_id) if r.team_id else None,
        "eligibility_snapshot_id": str(r.eligibility_snapshot_id),
        "roster_user_ids": [
            str(id)
            for id in db.scalars(
                select(RegistrationMember.user_id)
                .where(RegistrationMember.registration_id == r.id)
                .order_by(RegistrationMember.user_id)
            )
        ],
        "captain_id": str(r.captain_id),
        "status": r.status,
        "policy_version": r.policy_version,
        "created_at": r.created_at.isoformat(),
        "roster": [
            {
                "user_id": str(m.user_id),
                "full_name": m.full_name,
                "profile_revision": m.profile_revision,
            }
            for m in db.scalars(
                select(RegistrationMember)
                .where(RegistrationMember.registration_id == r.id)
                .order_by(RegistrationMember.user_id)
            )
        ],
    }


def register(db, actor, opportunity_id, data, idempotency_key, clock):
    require_verified(actor)
    o = lock_opportunity(db, opportunity_id)
    operation = "register:" + str(o.id)
    now = clock.now()
    request_hash = hashlib.sha256(
        json.dumps(data.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()
    previous = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == actor.user_id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.key == idempotency_key,
        )
    )
    if previous and previous.expires_at > now:
        if previous.request_hash != request_hash:
            raise DomainError(
                "idempotency_conflict", "This key was already used for different input.", 409
            )
        return previous.response
    if previous:
        db.delete(previous)
        db.flush()
    open_event(o)
    t = None
    if data.team_id:
        t = db.scalar(
            select(Team)
            .where(Team.id == data.team_id, Team.opportunity_id == o.id)
            .with_for_update()
        )
        if not t:
            raise DomainError("not_found", "Team not found.", 404)
        if t.captain_id != actor.user_id:
            raise DomainError("forbidden", "Only the captain can register this team.", 403)
        unlocked(t)
        if db.scalar(
            select(TeamInvitation).where(
                TeamInvitation.team_id == t.id,
                TeamInvitation.status == "PENDING",
                TeamInvitation.expires_at > now,
            )
        ):
            raise DomainError(
                "pending_invitations", "Resolve pending invitations before registration.", 409
            )
        roster = list(
            db.scalars(
                select(TeamMember.user_id)
                .where(TeamMember.team_id == t.id)
                .order_by(TeamMember.user_id)
            )
        )
    else:
        if o.team_min > 1:
            raise DomainError("team_required", "Register with an accepted team roster.", 409)
        roster = [actor.user_id]
    if not o.team_min <= len(roster) <= o.team_max:
        raise DomainError("team_size", "Your team does not meet the event size requirement.", 409)
    if db.scalar(
        select(RegistrationMember).where(
            RegistrationMember.opportunity_id == o.id,
            RegistrationMember.user_id.in_(roster),
            RegistrationMember.active,
        )
    ):
        raise DomainError("already_registered", "A roster member is already registered.", 409)
    if o.capacity_used >= o.capacity:
        raise DomainError("event_full", "This event has reached capacity.", 409)
    users = db.scalars(
        select(User).where(User.id.in_(roster)).order_by(User.id).with_for_update()
    ).all()
    evidence = []
    for u in users:
        a = Actor(u.id, u.is_verified, u.is_admin)
        p = profile_evidence(db, a)
        result = evaluate(p, EligibilityPolicy.model_validate(o.eligibility))
        if not u.is_active or not result.can_register:
            raise DomainError(
                "eligibility_failed",
                "Every roster member must meet the current eligibility policy.",
                409,
            )
        profile = db.scalar(select(Profile).where(Profile.user_id == u.id))
        evidence.append((u, p, profile.revision if profile else 0))
    # Check the acceptance instant after every lock/evidence read, never a client timestamp.
    if clock.now() >= o.registration_closes_at:
        raise DomainError("registration_closed", "Registration has closed.", 409)
    snapshot = EligibilitySnapshot(
        opportunity_id=o.id,
        policy_version=o.version,
        policy=o.eligibility,
        evidence=[
            {"user_id": str(u.id), "profile_revision": rev, "evidence": p.model_dump(mode="json")}
            for u, p, rev in evidence
        ],
    )
    db.add(snapshot)
    db.flush()
    r = Registration(
        opportunity_id=o.id,
        eligibility_snapshot_id=snapshot.id,
        status="PENDING",
        captain_id=actor.user_id,
        team_id=t.id if t else None,
        policy_version=o.version,
        policy_snapshot=o.eligibility,
    )
    db.add(r)
    db.flush()
    for u, p, rev in evidence:
        db.add(
            RegistrationMember(
                registration_id=r.id,
                opportunity_id=o.id,
                user_id=u.id,
                full_name=u.full_name,
                profile_revision=rev,
                admission_evidence=p.model_dump(mode="json"),
            )
        )
    r.status = "CONFIRMED"
    o.capacity_used += 1
    o.admission_started = True
    if t:
        t.locked = True
    set_consent(db, actor, o.id, data.contact_consent)
    if data.resume_file_id:
        file = db.get(PrivateFile, data.resume_file_id)
        if (
            not file
            or file.owner_id != actor.user_id
            or file.purpose != "resume"
            or file.scan_status != "CLEAN"
        ):
            raise DomainError("invalid_resume", "Choose your own safety-checked resume.", 422)
        grant = db.scalar(
            select(ConsentGrant).where(
                ConsentGrant.owner_id == actor.user_id,
                ConsentGrant.opportunity_id == o.id,
                ConsentGrant.file_id == file.id,
            )
        )
        if grant:
            grant.revoked = False
        else:
            db.add(
                ConsentGrant(
                    file_id=file.id,
                    owner_id=actor.user_id,
                    organization_id=o.organization_id,
                    opportunity_id=o.id,
                )
            )
    db.flush()
    response = registration_out(db, r)
    db.add(
        IdempotencyRecord(
            actor_id=actor.user_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response=response,
            expires_at=now + timedelta(hours=24),
        )
    )
    for u, _, _ in evidence:
        enqueue_job(
            db,
            kind="registration_notice",
            key=f"registered-{r.id}-{u.id}",
            payload={
                "user_id": str(u.id),
                "registration_id": str(r.id),
                "opportunity_id": str(o.id),
                "title": o.title,
            },
            run_at=clock.now(),
            expires_at=None,
        )
    return response


def set_consent(db, actor, opportunity_id, contact):
    consent = db.scalar(
        select(EventConsent)
        .where(EventConsent.user_id == actor.user_id, EventConsent.opportunity_id == opportunity_id)
        .with_for_update()
    )
    if consent:
        consent.contact = contact
    else:
        db.add(EventConsent(user_id=actor.user_id, opportunity_id=opportunity_id, contact=contact))


def withdraw(db, actor, registration_id, clock):
    r = db.get(Registration, registration_id)
    if not r:
        raise DomainError("not_found", "Registration not found.", 404)
    o = lock_opportunity(db, r.opportunity_id)
    db.refresh(r, with_for_update=True)
    is_member = db.scalar(
        select(RegistrationMember).where(
            RegistrationMember.registration_id == r.id, RegistrationMember.user_id == actor.user_id
        )
    )
    if not is_member:
        raise DomainError("not_found", "Registration not found.", 404)
    if r.captain_id != actor.user_id:
        raise DomainError("forbidden", "Only the captain can withdraw this registration.", 403)
    if clock.now() >= o.registration_closes_at:
        raise DomainError("withdrawal_closed", "Withdrawal closed with registration.", 409)
    if r.status == "CONFIRMED":
        r.status = "WITHDRAWN"
        r.withdrawn_at = clock.now()
        o.capacity_used -= 1
        for member in db.scalars(
            select(RegistrationMember).where(RegistrationMember.registration_id == r.id)
        ):
            member.active = False
        if r.team_id:
            t = db.scalar(select(Team).where(Team.id == r.team_id).with_for_update())
            t.locked = False
    db.flush()
    return registration_out(db, r)
