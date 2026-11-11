"""Register table metadata for non-HTTP processes before their first ORM flush."""

from importlib import import_module


def load_models():
    for module in (
        "alignn.audit",
        "alignn.domains.identity.models",
        "alignn.domains.profiles.models",
        "alignn.domains.organizations.models",
        "alignn.domains.opportunities.models",
        "alignn.domains.opportunities.ingestion_models",
        "alignn.domains.applications.models",
        "alignn.domains.files.models",
        "alignn.domains.teams.models",
        "alignn.domains.participation.models",
        "alignn.jobs.models",
    ):
        import_module(module)
