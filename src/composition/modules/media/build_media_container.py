from datetime import timedelta

from application.media.cleanup_orphaned_media_use_case import (
    CleanupOrphanedMediaUseCase,
)
from application.media.create_media_upload_urls_use_case import (
    CreateMediaUploadUrlsUseCase,
)
from composition.infrastructure.infrastructure_container import (
    InfrastructureContainer,
)
from composition.modules.media.media_container import MediaContainer
from composition.repositories.repository_container import RepositoryContainer
from composition.services.service_container import ServiceContainer


def build_media_container(
    *,
    infrastructure: InfrastructureContainer,
    repositories: RepositoryContainer,
    services: ServiceContainer,
    presigned_url_ttl_seconds: int,
    media_orphan_min_age_hours: int,
) -> MediaContainer:
    return MediaContainer(
        create_upload_urls=CreateMediaUploadUrlsUseCase(
            transactions=infrastructure.transactions,
            media_upload_repository=repositories.media_uploads,
            object_storage=infrastructure.object_storage,
            presigned_url_ttl_seconds=presigned_url_ttl_seconds,
        ),
        cleanup_orphans=CleanupOrphanedMediaUseCase(
            transactions=infrastructure.transactions,
            media_usage_service=services.media_usage,
            media_upload_repository=repositories.media_uploads,
            object_storage=infrastructure.object_storage,
            min_object_age=timedelta(
                hours=media_orphan_min_age_hours,
            ),
        ),
    )
