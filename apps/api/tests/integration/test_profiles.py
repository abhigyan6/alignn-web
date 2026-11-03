def test_anonymous_profile_is_private(api_client):
    assert api_client().get("/api/v1/me/profile").status_code == 401


def test_profile_grade_scale_and_revision(make_user, api_client):
    c = api_client(make_user(verified=True))
    first = c.put(
        "/api/v1/me/profile",
        json={
            "college": "Test Institute",
            "degree_id": "btech",
            "branch_id": "cse",
            "graduation_year": 2027,
            "current_year": 3,
            "cgpa": "8.20",
            "cgpa_scale": 10,
        },
    )
    assert first.status_code == 200, first.text
    assert first.json()["revision"] == 1
    invalid = c.put("/api/v1/me/profile", json={"cgpa": "8.2", "cgpa_scale": 4})
    assert invalid.status_code == 422
    second = c.put(
        "/api/v1/me/profile", json={"career_interests": ["design"], "discoverable": True}
    )
    assert second.status_code == 200
    assert second.json()["revision"] == 2


def test_public_teammates_are_opt_in_and_redacted(make_user, api_client):
    first = make_user(verified=True)
    second = make_user(verified=True)
    api_client(first).put(
        "/api/v1/me/profile", json={"discoverable": True, "college": "Visible Institute"}
    )
    api_client(second).put(
        "/api/v1/me/profile", json={"discoverable": False, "college": "Private Institute"}
    )
    response = api_client().get("/api/v1/people")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["college"] == "Visible Institute"
    assert "email" not in data[0]
    assert "cgpa" not in data[0]
    assert "resume" not in data[0]


def test_profile_skill_and_project_boundaries(make_user, api_client):
    c = api_client(make_user(verified=True))
    skills = c.get("/api/v1/skills")
    assert skills.status_code == 200
    added = c.put(
        "/api/v1/me/skills", json={"skills": [{"skill_id": "python", "level": "intermediate"}]}
    )
    assert added.status_code == 200
    assert added.json()[0]["skill_id"] == "python"
    duplicate = c.put(
        "/api/v1/me/skills",
        json={
            "skills": [
                {"skill_id": "python", "level": "beginner"},
                {"skill_id": "python", "level": "advanced"},
            ]
        },
    )
    assert duplicate.status_code == 422
    project = c.post(
        "/api/v1/me/projects",
        json={"title": "Campus helper", "url": "https://example.com/demo", "skill_ids": ["python"]},
    )
    assert project.status_code == 201
    other = api_client(make_user(verified=True))
    assert other.delete("/api/v1/me/projects/" + project.json()["id"]).status_code == 404


def test_skill_alias_uses_canonical_identity(make_user, api_client):
    c = api_client(make_user(verified=True))
    r = c.put("/api/v1/me/skills", json={"skills": [{"skill_id": "py", "level": "advanced"}]})
    assert r.status_code == 200, r.text
    assert r.json()[0]["skill_id"] == "python"
    r = c.put("/api/v1/me/skills", json={"skills": [{"skill_id": "p", "level": "advanced"}]})
    assert r.status_code == 422
