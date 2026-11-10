import pytest
from sqlalchemy.engine import make_url

from alignn.config import Settings


def test_settings_import_from_shallow_container_layout(tmp_path, monkeypatch):
    import runpy
    from pathlib import Path

    import alignn.config

    source = Path(alignn.config.__file__).read_text()
    installed = tmp_path / "config.py"
    installed.write_text(source)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost/alignn_test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    loaded = runpy.run_path(str(installed))
    assert loaded["ROOT"] == tmp_path


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_database_urls_preserve_credentials_and_tls(scheme):
    config = Settings(
        _env_file=None,
        database_url=f"{scheme}://user:p%40ss@db.example:5432/alignn?sslmode=require",
    )
    parsed = make_url(config.database_url)
    assert parsed.drivername == "postgresql+psycopg"
    assert parsed.password == "p@ss"
    assert parsed.query["sslmode"] == "require"


@pytest.mark.parametrize("overrides", [
    {"database_url": "sqlite:///test.db"},
    {"database_pool_size": 0},
    {"database_max_overflow": -1},
])
def test_invalid_deployment_settings_rejected(overrides):
    values = {"database_url": "postgresql://user@localhost/alignn", **overrides}
    with pytest.raises(ValueError):
        Settings(_env_file=None, **values)
