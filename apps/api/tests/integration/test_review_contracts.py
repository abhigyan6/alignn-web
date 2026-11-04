from uuid import UUID


def test_registration_has_snapshot_reference(
    make_user, api_client, make_organization, make_opportunity
):
    user = make_user(verified=True)
    c = api_client(user)
    org = make_organization(user.id, verified=True)
    o = make_opportunity(org.id)
    r = c.post(
        f"/api/v1/opportunities/{o.id}/registrations",
        json={},
        headers={"Idempotency-Key": "snapshot-contract-key"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["team_id"] is None
    assert UUID(data["eligibility_snapshot_id"])
    assert data["roster_user_ids"] == [str(user.id)]
    assert data["request_id"] == r.headers["X-Request-ID"]


def test_unverified_organizer_cannot_read_participant_data(
    make_user, api_client, make_organization, make_opportunity
):
    owner = make_user(verified=True)
    c = api_client(owner)
    org = make_organization(owner.id, verified=False)
    o = make_opportunity(org.id)
    assert c.get(f"/api/v1/organizer/opportunities/{o.id}/registrations").status_code == 403


def test_organization_member_cannot_verify_their_own_organization(
    make_user, api_client, make_organization
):
    owner = make_user(verified=True, admin=True)
    c = api_client(owner)
    org = make_organization(owner.id)
    assert (
        c.post(
            f"/api/v1/admin/organizations/{org.id}/verify",
            json={"reason": "Review own organization"},
        ).status_code
        == 403
    )
