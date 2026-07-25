from dataclasses import dataclass

from application.media.cleanup_orphaned_media_use_case import (
    CleanupOrphanedMediaUseCase,
)
from application.media.create_media_upload_urls_use_case import (
    CreateMediaUploadUrlsUseCase,
)


@dataclass(frozen=True, slots=True)
class MediaContainer:
    create_upload_urls: CreateMediaUploadUrlsUseCase
    cleanup_orphans: CleanupOrphanedMediaUseCase
