from decimal import Decimal


def test_missing_required_evidence_is_incomplete():
    from alignn.domains.eligibility.schemas import EligibilityPolicy, ProfileEvidence
    from alignn.domains.eligibility.service import evaluate

    r = evaluate(ProfileEvidence(verified=True), EligibilityPolicy(degree_ids=["btech"]))
    assert r.status == "INCOMPLETE" and not r.can_register


def test_constraints_and_grade_scales_are_explicit():
    from alignn.domains.eligibility.schemas import EligibilityPolicy, ProfileEvidence
    from alignn.domains.eligibility.service import evaluate

    profile = ProfileEvidence(
        verified=True, degree_id="btech", branch_id="cse", cgpa=Decimal("3.5"), cgpa_scale=4
    )
    policy = EligibilityPolicy(
        degree_ids=["btech", "bca"], branch_ids=["cse"], minimum_cgpa={"10": Decimal("8")}
    )
    assert evaluate(profile, policy).status == "INCOMPLETE"
    assert evaluate(profile, EligibilityPolicy()).can_register
    assert evaluate(profile, EligibilityPolicy(branch_ids=["ece"])).status == "INELIGIBLE"


def test_fit_weights_and_required_skills():
    from alignn.domains.matching.service import skill_score, weighted_fit

    assert weighted_fit([100] * 5) == 100
    assert weighted_fit([100, 0, 0, 0, 0]) == 35
    assert skill_score({"python"}, ["python"], ["sql"]) == 200 / 3
    assert skill_score(set(), [], []) == 0
