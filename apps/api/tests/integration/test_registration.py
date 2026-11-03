from uuid import UUID

from sqlalchemy import func, select

from alignn.db import SessionLocal


def test_registration_idempotency_and_admission_history(
    make_user, api_client, make_organization, make_opportunity
):
    user = make_user(verified=True)
    c = api_client(user)
    org = make_organization(user.id, verified=True)
    o = make_opportunity(org.id, capacity=1)
    path = "/api/v1/opportunities/" + str(o.id) + "/registrations"
    headers = {"Idempotency-Key": "register-first-key"}
    first = c.post(path, json={}, headers=headers)
    assert first.status_code == 201, first.text
    second = c.post(path, json={}, headers=headers)
    assert second.json()["id"] == first.json()["id"]
    assert c.post(path, json={"contact_consent": True}, headers=headers).status_code == 409
    c.put("/api/v1/me/profile", json={"degree_id": "btech"})
    snapshot = c.get("/api/v1/me/registrations").json()["items"][0]
    assert snapshot["roster"][0]["profile_revision"] == 0
    assert c.post(path, json={}, headers={"Idempotency-Key": "register-new-key"}).status_code == 409
    assert c.post("/api/v1/registrations/" + first.json()["id"] + "/withdraw").status_code == 200
    from alignn.domains.opportunities.models import Opportunity

    with SessionLocal() as db:
        assert db.get(Opportunity, o.id).capacity_used == 0


def test_team_pending_invitation_and_roster_freeze(
    make_user, api_client, make_organization, make_opportunity
):
    captain = make_user(verified=True)
    member = make_user(verified=True)
    c = api_client(captain)
    m = api_client(member)
    org = make_organization(captain.id, verified=True)
    o = make_opportunity(org.id, team_min=2, team_max=3)
    t = c.post("/api/v1/opportunities/" + str(o.id) + "/teams", json={"name": "Loop makers"})
    assert t.status_code == 201, t.text
    t = t.json()
    invite = c.post("/api/v1/teams/" + t["id"] + "/invitations", json={"email": member.email})
    assert invite.status_code == 201, invite.text
    route = "/api/v1/opportunities/" + str(o.id) + "/registrations"
    assert (
        c.post(
            route, json={"team_id": t["id"]}, headers={"Idempotency-Key": "team-register-key"}
        ).status_code
        == 409
    )
    assert m.post("/api/v1/team-invitations/" + invite.json()["id"] + "/accept").status_code == 200
    r = c.post(route, json={"team_id": t["id"]}, headers={"Idempotency-Key": "team-register-key"})
    assert r.status_code == 201, r.text
    assert len(r.json()["roster"]) == 2
    assert m.delete("/api/v1/teams/" + t["id"] + "/members/me").status_code == 409
    assert m.post("/api/v1/registrations/" + r.json()["id"] + "/withdraw").status_code == 403
    assert c.get("/api/v1/organizer/opportunities/" + str(o.id) + "/registrations").json()["items"][
        0
    ]["roster"][0].keys() == {"user_id", "full_name", "contact", "resume_file_id"}


def test_last_seat_race(make_user, api_client, make_organization, make_opportunity):
    from concurrent.futures import ThreadPoolExecutor

    owner = make_user(verified=True)
    org = make_organization(owner.id, verified=True)
    o = make_opportunity(org.id, capacity=1)
    clients = [api_client(make_user(verified=True)) for _ in range(100)]

    def attempt(pair):
        i, c = pair
        return c.post(
            "/api/v1/opportunities/" + str(o.id) + "/registrations",
            json={},
            headers={"Idempotency-Key": f"race-participant-{i}"},
        )

    with ThreadPoolExecutor(max_workers=100) as pool:
        responses = list(pool.map(attempt, enumerate(clients)))
    assert sum(r.status_code == 201 for r in responses) == 1, [
        r.text for r in responses if r.status_code not in {201, 409}
    ]
    assert sum(r.status_code == 409 for r in responses) == 99
    from alignn.domains.opportunities.models import Opportunity
    from alignn.domains.participation.models import Registration

    with SessionLocal() as db:
        assert db.get(Opportunity, o.id).capacity_used == 1
        assert (
            db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(Registration.status == "CONFIRMED")
            )
            == 1
        )


def test_admission_locks_policy_and_expired_keys_do_not_duplicate(
    make_user, api_client, make_organization, make_opportunity
):
    from datetime import timedelta

    from alignn.db import utcnow
    from alignn.domains.opportunities.models import Opportunity
    from alignn.domains.opportunities.schemas import OpportunityCreate
    from alignn.domains.participation.models import IdempotencyRecord
    from alignn.jobs.models import Job

    user = make_user(verified=True)
    c = api_client(user)
    org = make_organization(user.id, verified=True)
    o = make_opportunity(org.id)
    route = "/api/v1/opportunities/" + str(o.id)
    r = c.post(route + "/registrations", json={}, headers={"Idempotency-Key": "admission-lock-key"})
    assert r.status_code == 201, r.text
    full = c.get(route).json()
    data = {k: v for k, v in full.items() if k in OpportunityCreate.model_fields}
    data["eligibility"] = {"degree_ids": ["btech"]}
    assert (
        c.put(route, json={"expected_version": full["version"], "opportunity": data}).status_code
        == 409
    )
    data["eligibility"] = {}
    data["registration_closes_at"] = (o.registration_closes_at - timedelta(days=1)).isoformat()
    assert (
        c.put(route, json={"expected_version": full["version"], "opportunity": data}).status_code
        == 409
    )
    with SessionLocal.begin() as db:
        db.scalar(select(IdempotencyRecord)).expires_at = utcnow() - timedelta(seconds=1)
        assert (
            db.scalar(
                select(func.count()).select_from(Job).where(Job.kind == "registration_notice")
            )
            == 1
        )
    assert (
        c.post(
            route + "/registrations", json={}, headers={"Idempotency-Key": "admission-lock-key"}
        ).status_code
        == 409
    )
    with SessionLocal.begin() as db:
        db.get(Opportunity, o.id).registration_closes_at = utcnow() - timedelta(seconds=1)
    assert c.post("/api/v1/registrations/" + r.json()["id"] + "/withdraw").status_code == 409


def test_missing_roster_evidence_and_expired_team_invite(
    make_user, api_client, make_organization, make_opportunity
):
    from datetime import timedelta

    from alignn.db import utcnow
    from alignn.domains.teams.models import TeamInvitation

    captain = make_user(verified=True)
    member = make_user(verified=True)
    c = api_client(captain)
    m = api_client(member)
    org = make_organization(captain.id, verified=True)
    o = make_opportunity(org.id, team_min=2, team_max=2, eligibility={"degree_ids": ["btech"]})
    t = c.post("/api/v1/opportunities/" + str(o.id) + "/teams", json={"name": "Together"}).json()
    invitation = c.post(
        "/api/v1/teams/" + t["id"] + "/invitations", json={"email": member.email}
    ).json()
    with SessionLocal.begin() as db:
        i = db.get(TeamInvitation, UUID(invitation["id"]))
        i.expires_at = utcnow() - timedelta(seconds=1)
    assert m.post("/api/v1/team-invitations/" + invitation["id"] + "/accept").status_code == 409
    with SessionLocal.begin() as db:
        db.get(TeamInvitation, UUID(invitation["id"])).expires_at = utcnow() + timedelta(hours=1)
    assert m.post("/api/v1/team-invitations/" + invitation["id"] + "/accept").status_code == 200
    c.put("/api/v1/me/profile", json={"degree_id": "btech"})
    assert (
        c.post(
            "/api/v1/opportunities/" + str(o.id) + "/registrations",
            json={"team_id": t["id"]},
            headers={"Idempotency-Key": "missing-evidence-key"},
        ).status_code
        == 409
    )
    m.put("/api/v1/me/profile", json={"degree_id": "btech"})
    assert (
        c.post(
            "/api/v1/opportunities/" + str(o.id) + "/registrations",
            json={"team_id": t["id"]},
            headers={"Idempotency-Key": "missing-evidence-key"},
        ).status_code
        == 201
    )


def test_invitation_and_registration_serialize_on_event(
    make_user, api_client, make_organization, make_opportunity
):
    from concurrent.futures import ThreadPoolExecutor

    captain = make_user(verified=True)
    member = make_user(verified=True)
    c = api_client(captain)
    other = api_client(captain)
    org = make_organization(captain.id, verified=True)
    o = make_opportunity(org.id, team_min=1, team_max=3)
    t = c.post("/api/v1/opportunities/" + str(o.id) + "/teams", json={"name": "Race team"}).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        invite = pool.submit(
            c.post, "/api/v1/teams/" + t["id"] + "/invitations", json={"email": member.email}
        )
        registration = pool.submit(
            other.post,
            "/api/v1/opportunities/" + str(o.id) + "/registrations",
            json={"team_id": t["id"]},
            headers={"Idempotency-Key": "invitation-race-key"},
        )
        responses = [invite.result(), registration.result()]
    assert sorted(r.status_code for r in responses) == [201, 409]
