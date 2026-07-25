from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from application.media.cleanup_orphaned_media_use_case import (
    CleanupOrphanedMediaUseCase,
    OrphanCleanupResult,
)
from application.ports.object_storage import (
    DeleteObjectsResult,
    StoredObject,
)

OLD = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _use_case(
    *,
    objects: list[StoredObject],
    used_keys: set[str] | None = None,
    failed_keys: set[str] | None = None,
) -> tuple[CleanupOrphanedMediaUseCase, Mock]:
    transactions = Mock()

    @contextmanager
    def session() -> Iterator[Mock]:
        yield Mock()

    transactions.session.side_effect = session

    storage = Mock()
    storage.iter_objects.side_effect = lambda *, prefix: iter(
        item for item in objects if item.object_key.startswith(prefix)
    )
    failed_keys = failed_keys or set()

    def delete_objects(object_keys: list[str]) -> DeleteObjectsResult:
        return DeleteObjectsResult(
            deleted_keys=tuple(
                key for key in object_keys if key not in failed_keys
            ),
            failed_keys=tuple(
                key for key in object_keys if key in failed_keys
            ),
        )

    storage.delete_objects.side_effect = delete_objects

    usage = Mock()
    usage.get_used_object_keys.side_effect = lambda **kwargs: (
        set(kwargs["object_keys"]) & (used_keys or set())
    )

    uploads = Mock()
    uploads.lock_for_cleanup.return_value = {}
    uploads.delete_expired_available.return_value = 0

    return (
        CleanupOrphanedMediaUseCase(
            transactions=transactions,
            media_usage_service=usage,
            media_upload_repository=uploads,
            object_storage=storage,
            min_object_age=timedelta(hours=24),
        ),
        storage,
    )


def test_cleanup_preserves_used_objects_and_deletes_orphans() -> None:
    used = "estate-media/user/used.webp"
    orphan = "estate-media/user/orphan.webp"
    use_case, storage = _use_case(
        objects=[StoredObject(used, OLD), StoredObject(orphan, OLD)],
        used_keys={used},
    )

    result = use_case.execute()

    assert result == OrphanCleanupResult(
        scanned=2,
        eligible=2,
        used=1,
        deleted=1,
        failed=0,
    )
    assert storage.delete_objects.call_args.args[0] == [orphan]


def test_cleanup_reports_partial_storage_failure_accurately() -> None:
    deleted = "estate-media/user/deleted.webp"
    failed = "estate-media/user/failed.webp"
    use_case, _ = _use_case(
        objects=[StoredObject(deleted, OLD), StoredObject(failed, OLD)],
        failed_keys={failed},
    )

    result = use_case.execute()

    assert result.deleted == 1
    assert result.failed == 1


def test_cleanup_skips_fresh_objects() -> None:
    fresh = StoredObject(
        "estate-media/user/fresh.webp",
        datetime.now(timezone.utc),
    )
    use_case, storage = _use_case(objects=[fresh])

    result = use_case.execute()

    assert result.scanned == 1
    assert result.eligible == 0
    storage.delete_objects.assert_not_called()
