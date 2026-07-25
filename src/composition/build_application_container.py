from flask import Flask

from application.estate.mapping.estate_response_mapper import (
    EstateResponseMapper,
)
from application.media.media_url_builder import MediaUrlBuilder
from application.users.mapping.user_response_mapper import UserResponseMapper
from composition.application_container import ApplicationContainer
from composition.dependency_overrides import DependencyOverrides
from composition.infrastructure.build_infrastructure_container import (
    build_infrastructure_container,
)
from composition.modules.admin.build_admin_container import (
    build_admin_container,
)
from composition.modules.agents.build_agents_container import (
    build_agents_container,
)
from composition.modules.auth.build_auth_container import build_auth_container
from composition.modules.estates.build_estates_container import (
    build_estates_container,
)
from composition.modules.media.build_media_container import (
    build_media_container,
)
from composition.modules.users.build_users_container import (
    build_users_container,
)
from composition.repositories.repository_container import RepositoryContainer
from composition.services.build_service_container import (
    build_service_container,
)
from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.estate.estate_media_repository import EstateMediaRepository
from domain.estate.estate_repository import EstateRepository
from domain.media.media_upload_repository import MediaUploadRepository
from domain.password_reset.password_reset_repository import (
    PasswordResetRepository,
)
from domain.user.user_repository import UserRepository


def build_application_container(
    app: Flask,
    *,
    overrides: DependencyOverrides | None = None,
) -> ApplicationContainer:
    infrastructure = build_infrastructure_container(
        app=app,
        overrides=overrides,
    )
    repositories = RepositoryContainer(
        users=UserRepository(),
        email_verifications=EmailVerificationRepository(),
        password_resets=PasswordResetRepository(),
        estates=EstateRepository(),
        estate_media=EstateMediaRepository(),
        media_uploads=MediaUploadRepository(),
    )
    services = build_service_container(
        infrastructure=infrastructure,
        repositories=repositories,
    )
    media_url_builder = MediaUrlBuilder(infrastructure.urls.media_base_url)
    user_response_mapper = UserResponseMapper(media_url_builder)
    estate_response_mapper = EstateResponseMapper(
        media_url_builder=media_url_builder,
        user_response_mapper=user_response_mapper,
    )

    return ApplicationContainer(
        auth=build_auth_container(
            infrastructure=infrastructure,
            repositories=repositories,
            services=services,
        ),
        users=build_users_container(
            infrastructure=infrastructure,
            repositories=repositories,
            services=services,
            user_response_mapper=user_response_mapper,
        ),
        admin=build_admin_container(
            infrastructure=infrastructure,
            repositories=repositories,
            services=services,
            estate_response_mapper=estate_response_mapper,
            user_response_mapper=user_response_mapper,
        ),
        agents=build_agents_container(
            infrastructure=infrastructure,
            services=services,
            estate_response_mapper=estate_response_mapper,
            user_response_mapper=user_response_mapper,
        ),
        estates=build_estates_container(
            infrastructure=infrastructure,
            repositories=repositories,
            services=services,
            estate_response_mapper=estate_response_mapper,
        ),
        media=build_media_container(
            infrastructure=infrastructure,
            repositories=repositories,
            services=services,
            presigned_url_ttl_seconds=app.config[
                "S3_PRESIGNED_URL_TTL_SECONDS"
            ],
            media_orphan_min_age_hours=app.config[
                "MEDIA_ORPHAN_MIN_AGE_HOURS"
            ],
        ),
    )
