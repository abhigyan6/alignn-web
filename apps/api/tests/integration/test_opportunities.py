from datetime import timedelta
from uuid import UUID

from alignn.db import SessionLocal, utcnow


def create_listing(c, org_id, **changes):
    r = c.post(
        "/api/v1/organizations/" + org_id + "/opportunities",
        json={
            "title": "Build for tomorrow",
            "description": "A thoughtful student hackathon.",
            "kind": "HACKATHON",
            "mode": "EXTERNAL",
            "apply_url": "https://example.com/apply",
            "registration_closes_at": (utcnow() + timedelta(days=10)).isoformat(),
            "starts_at": (utcnow() + timedelta(days=11)).isoformat(),
            "ends_at": (utcnow() + timedelta(days=12)).isoformat(),
            **changes,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_drafts_private_and_organization_verification_required(make_user, api_client):
    c = api_client(make_user(verified=True))
    anon = api_client()
    org = c.post("/api/v1/organizations", json={"name": "Builders Society"}).json()
    o = create_listing(c, org["id"])
    assert anon.get("/api/v1/opportunities/" + o["id"]).status_code == 404
    assert (
        c.post(
            "/api/v1/opportunities/" + o["id"] + "/publish", json={"expected_version": 1}
        ).status_code
        == 409
    )
    from alignn.domains.organizations.models import Organization

    with SessionLocal.begin() as db:
        db.get(Organization, UUID(org["id"])).verified = True
    assert (
        c.post(
            "/api/v1/opportunities/" + o["id"] + "/publish", json={"expected_version": 1}
        ).status_code
        == 200
    )
    assert anon.get("/api/v1/opportunities/" + o["id"]).status_code == 200
    assert len(anon.get("/api/v1/opportunities?q=tomorrow").json()["items"]) == 1
    assert anon.get("/api/v1/opportunities?limit=101").status_code == 422


def test_external_tracker_is_user_scoped(make_user, api_client):
    c = api_client(make_user(verified=True))
    other = api_client(make_user(verified=True))
    org = c.post("/api/v1/organizations", json={"name": "Builders Society"}).json()
    o = create_listing(c, org["id"], mode="EXTERNAL", apply_url="https://example.com/apply")
    from alignn.domains.organizations.models import Organization

    with SessionLocal.begin() as db:
        db.get(Organization, UUID(org["id"])).verified = True
    c.post("/api/v1/opportunities/" + o["id"] + "/publish", json={"expected_version": 1})
    a = c.post("/api/v1/applications", json={"opportunity_id": o["id"]}).json()
    assert (
        other.post(
            "/api/v1/applications/" + a["id"] + "/events", json={"status": "APPLIED", "note": ""}
        ).status_code
        == 404
    )
    assert (
        c.post(
            "/api/v1/applications/" + a["id"] + "/events",
            json={"status": "APPLIED", "note": "Applied externally"},
        ).status_code
        == 201
    )
    assert c.get("/api/v1/me/applications").json()["items"][0]["status"] == "APPLIED"


def test_match_ranking_is_global_and_profile_changes_invalidate_it(
    make_user, api_client, make_organization, make_opportunity
):
    from alignn.domains.matching.service import rebuild_matches

    user = make_user(verified=True)
    c = api_client(user)
    org = make_organization(user.id, verified=True)
    make_opportunity(org.id, required_skills=["sql"])
    best = make_opportunity(org.id, required_skills=["python"])
    c.put("/api/v1/me/skills", json={"skills": [{"skill_id": "python", "level": "advanced"}]})
    assert c.get("/api/v1/opportunities?sort=match&limit=1").json()["ranking_status"] == "PENDING"
    rebuild_matches(user.id)
    page = c.get("/api/v1/opportunities?sort=match&limit=1").json()
    assert page["ranking_status"] == "FRESH" and page["items"][0]["id"] == str(best.id)
    c.put("/api/v1/me/profile", json={"bio": "Updated evidence"})
    page = c.get("/api/v1/opportunities?sort=match&limit=1").json()
    assert page["ranking_status"] == "PENDING" and page["sort"] == "newest"
