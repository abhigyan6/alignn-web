from datetime import timedelta
from uuid import UUID

from alignn.db import SessionLocal, utcnow


def create_org(c):
    r = c.post(
        "/api/v1/organizations", json={"name": "Campus Collective", "description": "Student events"}
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_cross_organization_access_is_denied(make_user, api_client):
    owner = api_client(make_user(verified=True))
    organization = create_org(owner)
    assert organization["verified"] is False
    other = api_client(make_user(verified=True))
    assert other.get("/api/v1/organizations/" + organization["id"]).status_code == 404
    assert (
        other.patch(
            "/api/v1/organizations/" + organization["id"], json={"name": "Stolen"}
        ).status_code
        == 404
    )


def test_organization_requires_verified_user_and_operator(make_user, api_client):
    assert (
        api_client(make_user())
        .post("/api/v1/organizations", json={"name": "No verification"})
        .status_code
        == 403
    )
    owner = api_client(make_user(verified=True))
    org = create_org(owner)
    assert (
        owner.post(
            "/api/v1/admin/organizations/" + org["id"] + "/verify", json={"reason": "Self approval"}
        ).status_code
        == 403
    )
    admin = api_client(make_user(verified=True, admin=True))
    approved = admin.post(
        "/api/v1/admin/organizations/" + org["id"] + "/verify",
        json={"reason": "Verified local organization"},
    )
    assert approved.status_code == 200
    assert approved.json()["verified"] is True


def test_final_owner_cannot_leave(make_user, api_client):
    c = api_client(make_user(verified=True))
    org = create_org(c)
    assert c.delete("/api/v1/organizations/" + org["id"] + "/members/me").status_code == 409


def test_invitation_expires_and_only_recipient_accepts(make_user, api_client):
    from alignn.domains.organizations.models import OrganizationInvitation

    owner = api_client(make_user(verified=True))
    invited = make_user(verified=True)
    org = create_org(owner)
    admin = api_client(make_user(verified=True, admin=True))
    assert (
        admin.post(
            f"/api/v1/admin/organizations/{org['id']}/verify", json={"reason": "Verified publisher"}
        ).status_code
        == 200
    )
    invitation = owner.post(
        "/api/v1/organizations/" + org["id"] + "/invitations",
        json={"email": invited.email, "role": "REVIEWER"},
    )
    assert invitation.status_code == 201, invitation.text
    id = invitation.json()["id"]
    wrong = api_client(make_user(verified=True))
    assert wrong.post(f"/api/v1/organization-invitations/{id}/accept").status_code == 404
    with SessionLocal.begin() as db:
        row = db.get(OrganizationInvitation, UUID(id))
        assert (
            timedelta(hours=71) < row.expires_at - row.created_at <= timedelta(hours=72, seconds=1)
        )
        row.expires_at = utcnow() - timedelta(seconds=1)
    assert (
        api_client(invited).post(f"/api/v1/organization-invitations/{id}/accept").status_code == 409
    )
