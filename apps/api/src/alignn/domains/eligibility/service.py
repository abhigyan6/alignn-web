from sqlalchemy import select

from alignn.domains.profiles.models import Profile

from .schemas import EligibilityPolicy, EligibilityResult, ProfileEvidence


def evaluate(profile: ProfileEvidence, rules: EligibilityPolicy) -> EligibilityResult:
    missing = []
    failed = []
    if not profile.verified:
        missing.append("Verify your email")
    for field, allowed in [
        ("degree_id", rules.degree_ids),
        ("branch_id", rules.branch_ids),
        ("graduation_year", rules.graduation_years),
        ("current_year", rules.current_years),
    ]:
        if not allowed:
            continue
        value = getattr(profile, field)
        if value is None:
            missing.append("Add " + field.replace("_", " "))
        elif value not in allowed:
            failed.append(field.replace("_", " ") + " does not meet this policy")
    if rules.minimum_cgpa:
        threshold = rules.minimum_cgpa.get(str(profile.cgpa_scale))
        if profile.cgpa is None or threshold is None:
            missing.append("A grade and a published threshold for your grading scale are required")
        elif profile.cgpa < threshold:
            failed.append("Grade is below the published threshold")
    status = "INELIGIBLE" if failed else "INCOMPLETE" if missing else "ELIGIBLE"
    return EligibilityResult(
        status=status, can_register=status == "ELIGIBLE", reasons=failed + missing
    )


def profile_evidence(db, actor):
    p = db.scalar(select(Profile).where(Profile.user_id == actor.user_id))
    return ProfileEvidence(
        verified=actor.verified,
        **(
            {k: getattr(p, k) for k in ProfileEvidence.model_fields if k != "verified"} if p else {}
        ),
    )
