import pytest
from flask import Flask

from configuration.validation import validate_required_config

COMMON_CONFIG = {
    "APP_BASE_URL": "https://athome.test",
    "DATABASE_URL": "postgresql://test",
    "JWT_SECRET_KEY": "test-secret-key-at-least-32-bytes-long",
    "MEDIA_BASE_URL": "https://media.test",
}


def _configured_app(profile: str, **config: object) -> Flask:
    app = Flask(__name__)
    app.config.update(COMMON_CONFIG)
    app.config.update(CONFIG_PROFILE=profile, **config)
    return app


def test_testing_config_requires_only_common_values() -> None:
    app = _configured_app(
        "testing",
        RESEND_API_KEY=None,
        RATELIMIT_STORAGE_URI=None,
    )

    validate_required_config(app)


@pytest.mark.parametrize("profile", ["development", "production"])
def test_non_testing_config_requires_external_infrastructure(
    profile: str,
) -> None:
    app = _configured_app(
        profile,
        RESEND_API_KEY=None,
        RATELIMIT_STORAGE_URI=None,
    )

    with pytest.raises(RuntimeError) as error:
        validate_required_config(app)

    assert "RATELIMIT_STORAGE_URI" in str(error.value)
    assert "RESEND_API_KEY" in str(error.value)
    assert "S3_BUCKET_NAME" in str(error.value)
