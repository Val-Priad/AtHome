import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from application.ports.object_storage import (
    ObjectStorageError,
    ObjectStorageProtocol,
)
from application.ports.transaction_manager import TransactionManagerProtocol
from domain.media.media_config import MEDIA_CONFIG_BY_PURPOSE
from domain.media.media_enums import MediaPurpose
from domain.media.media_upload_repository import MediaUploadRepository
from domain.media.media_usage_service import MediaUsageService

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrphanCleanupResult:
    scanned: int
    eligible: int
    used: int
    deleted: int
    failed: int
    expired_reservations_deleted: int = 0


@dataclass(frozen=True, slots=True)
class _BatchCleanupResult:
    used: int
    deleted: int
    failed: int


class CleanupOrphanedMediaUseCase:
    def __init__(
        self,
        *,
        transactions: TransactionManagerProtocol,
        media_usage_service: MediaUsageService,
        media_upload_repository: MediaUploadRepository,
        object_storage: ObjectStorageProtocol,
        min_object_age: timedelta,
        batch_size: int = 500,
    ) -> None:
        if min_object_age <= timedelta(0):
            raise ValueError("Minimum object age must be greater than zero")
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than zero")

        self._transactions = transactions
        self._media_usage_service = media_usage_service
        self._media_upload_repository = media_upload_repository
        self._object_storage = object_storage
        self._min_object_age = min_object_age
        self._batch_size = batch_size

    def execute(self) -> OrphanCleanupResult:
        cutoff = datetime.now(timezone.utc) - self._min_object_age
        with self._transactions.session() as session:
            expired_reservations_deleted = (
                self._media_upload_repository.delete_expired_available(
                    session,
                    cutoff,
                )
            )

        scanned = 0
        eligible = 0
        used = 0
        deleted = 0
        failed = 0

        for purpose, config in MEDIA_CONFIG_BY_PURPOSE.items():
            purpose_result = self._process_purpose(
                purpose=purpose,
                prefix=f"{config.prefix}/",
                cutoff=cutoff,
            )

            scanned += purpose_result.scanned
            eligible += purpose_result.eligible
            used += purpose_result.used
            deleted += purpose_result.deleted
            failed += purpose_result.failed

        result = OrphanCleanupResult(
            scanned=scanned,
            eligible=eligible,
            used=used,
            deleted=deleted,
            failed=failed,
            expired_reservations_deleted=expired_reservations_deleted,
        )

        _logger.info(
            "Orphaned media cleanup completed",
            extra={
                "scanned": result.scanned,
                "eligible": result.eligible,
                "used": result.used,
                "deleted": result.deleted,
                "failed": result.failed,
                "expired_reservations_deleted": (
                    result.expired_reservations_deleted
                ),
            },
        )
        return result

    def _process_purpose(
        self,
        *,
        purpose: MediaPurpose,
        prefix: str,
        cutoff: datetime,
    ) -> OrphanCleanupResult:
        scanned = 0
        eligible = 0
        used = 0
        deleted = 0
        failed = 0
        batch: list[str] = []

        for stored_object in self._object_storage.iter_objects(prefix=prefix):
            scanned += 1
            if stored_object.last_modified > cutoff:
                continue

            eligible += 1
            batch.append(stored_object.object_key)
            if len(batch) < self._batch_size:
                continue

            batch_result = self._process_batch(purpose, batch)
            used += batch_result.used
            deleted += batch_result.deleted
            failed += batch_result.failed
            batch = []

        if batch:
            batch_result = self._process_batch(purpose, batch)
            used += batch_result.used
            deleted += batch_result.deleted
            failed += batch_result.failed

        return OrphanCleanupResult(
            scanned=scanned,
            eligible=eligible,
            used=used,
            deleted=deleted,
            failed=failed,
        )

    def _process_batch(
        self,
        purpose: MediaPurpose,
        object_keys: list[str],
    ) -> _BatchCleanupResult:
        with self._transactions.session() as session:
            uploads = self._media_upload_repository.lock_for_cleanup(
                session,
                object_keys,
            )
            used_keys = self._media_usage_service.get_used_object_keys(
                session=session,
                purpose=purpose,
                object_keys=object_keys,
            )

            orphan_keys = [
                object_key
                for object_key in object_keys
                if object_key not in used_keys
            ]
            self._media_upload_repository.mark_deleting(
                [
                    uploads[object_key]
                    for object_key in orphan_keys
                    if object_key in uploads
                ]
            )
        if not orphan_keys:
            return _BatchCleanupResult(
                used=len(used_keys),
                deleted=0,
                failed=0,
            )

        try:
            delete_result = self._object_storage.delete_objects(orphan_keys)
        except ObjectStorageError:
            _logger.exception(
                "Failed to delete orphaned media objects",
                extra={
                    "purpose": purpose.value,
                    "object_key_count": len(orphan_keys),
                    "object_keys_sample": orphan_keys[:10],
                },
            )
            with self._transactions.session() as session:
                self._media_upload_repository.restore_available(
                    session,
                    orphan_keys,
                )
            return _BatchCleanupResult(
                used=len(used_keys),
                deleted=0,
                failed=len(orphan_keys),
            )

        with self._transactions.session() as session:
            self._media_upload_repository.delete_by_object_keys(
                session,
                delete_result.deleted_keys,
            )
            self._media_upload_repository.restore_available(
                session,
                delete_result.failed_keys,
            )

        return _BatchCleanupResult(
            used=len(used_keys),
            deleted=len(delete_result.deleted_keys),
            failed=len(delete_result.failed_keys),
        )
