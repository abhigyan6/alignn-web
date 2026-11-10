from unittest.mock import patch

import pytest

from alignn.adapters.objects import S3Objects
from alignn.config import Settings


def configuration(**overrides):
    return Settings(_env_file=None, **{
        "database_url": "postgresql://user@localhost/alignn_test",
        "environment": "production",
        "clerk_secret_key": "test-only-key",
        "public_origin": "https://alignn.example",
        "mail_host": "smtp.example",
        "scanner_host": "scanner",
        "object_driver": "s3",
        "object_auth_mode": "iam",
        "object_region": "ap-south-1",
        "object_endpoint": None,
        "object_access_key": None,
        "object_secret_key": None,
        **overrides,
    })


def test_native_s3_uses_sdk_role_chain_without_static_credentials():
    with patch("boto3.client") as client:
        S3Objects(configuration())
    options = client.call_args.kwargs
    assert options["region_name"] == "ap-south-1"
    assert "aws_access_key_id" not in options
    assert "aws_secret_access_key" not in options
    assert "endpoint_url" not in options
    assert options["config"].s3["addressing_style"] == "virtual"


@pytest.mark.parametrize("overrides", [
    {"object_region": None},
    {"object_endpoint": "https://untrusted.example"},
    {"object_secret_key": "test-only-secret"},
    {"object_access_key": "test-only-access"},
])
def test_iam_mode_rejects_ambiguous_or_unsafe_configuration(overrides):
    with pytest.raises(ValueError):
        configuration(**overrides)


def test_static_s3_compatible_storage_remains_explicit():
    settings = configuration(
        object_auth_mode="static", object_endpoint="https://objects.example",
        object_access_key="test-only-access", object_secret_key="test-only-secret",
    )
    assert "test-only-secret" not in repr(settings.object_secret_key)
    with patch("boto3.client") as client:
        S3Objects(settings)
    assert client.call_args.kwargs["aws_secret_access_key"] == "test-only-secret"
    assert client.call_args.kwargs["config"].s3["addressing_style"] == "path"
