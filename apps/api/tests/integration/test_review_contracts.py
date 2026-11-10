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
