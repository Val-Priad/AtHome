from flask import Flask

COMMON_REQUIRED_CONFIG = frozenset(
    {
        "APP_BASE_URL",
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "MEDIA_BASE_URL",
    }
)

DEVELOPMENT_REQUIRED_CONFIG = COMMON_REQUIRED_CONFIG | {
    "RATELIMIT_STORAGE_URI",
    "RESEND_API_KEY",
    "S3_BUCKET_NAME",
}

PRODUCTION_REQUIRED_CONFIG = COMMON_REQUIRED_CONFIG | {
    "RATELIMIT_STORAGE_URI",
    "RESEND_API_KEY",
    "S3_BUCKET_NAME",
}

TESTING_REQUIRED_CONFIG = COMMON_REQUIRED_CONFIG

REQUIRED_CONFIG_BY_PROFILE = {
    "development": DEVELOPMENT_REQUIRED_CONFIG,
    "production": PRODUCTION_REQUIRED_CONFIG,
    "testing": TESTING_REQUIRED_CONFIG,
}


def validate_required_config(app: Flask) -> None:
    profile = app.config["CONFIG_PROFILE"]
    required_config = REQUIRED_CONFIG_BY_PROFILE.get(
        profile,
        COMMON_REQUIRED_CONFIG,
    )
    missing_keys = sorted(
        key for key in required_config if not app.config.get(key)
    )

    if missing_keys:
        joined_keys = ", ".join(missing_keys)
        raise RuntimeError(
            f"Missing required application config: {joined_keys}"
        )
