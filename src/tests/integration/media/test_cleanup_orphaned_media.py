from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from application.ports.object_storage import StoredObject
from domain.estate.enums.estate_listing_enums import ListingStatus
from domain.estate.models.estate_media_model import EstateMedia
from domain.media.media_enums import MediaPurpose, MediaType
from domain.media.media_upload_model import MediaUpload
from tests.integration.estate.test_filter_estate import create_filter_estate


def _object_key(uploader_id) -> str:
    return f"estate-media/{uploader_id}/{uuid4()}.webp"


def _avatar_key(uploader_id) -> str:
    return f"user-avatars/{uploader_id}/{uuid4()}.webp"


def test_orphan_cleanup_preserves_real_database_references(
    application_container,
    db_session,
    any_user,
    fake_object_storage,
    reserve_media_upload,
):
    used_estate_key = _object_key(any_user.id)
    orphan_estate_key = _object_key(any_user.id)
    used_avatar_key = _avatar_key(any_user.id)
    orphan_avatar_key = _avatar_key(any_user.id)
    reserve_media_upload(
        orphan_estate_key,
        any_user.id,
        purpose=MediaPurpose.estate,
    )
    reserve_media_upload(
        orphan_avatar_key,
        any_user.id,
        purpose=MediaPurpose.user_avatar,
    )

    create_filter_estate(
        db_session,
        title="Orphan cleanup protected estate",
        status=ListingStatus.draft,
        media=[
            EstateMedia(
                object_key=used_estate_key,
                media_type=MediaType.image,
                position=0,
            )
        ],
    )
    any_user.avatar_key = used_avatar_key
    db_session.flush()

    old = datetime.now(timezone.utc) - timedelta(days=2)
    fake_object_storage.stored_objects = [
        StoredObject(used_estate_key, old),
        StoredObject(orphan_estate_key, old),
        StoredObject(used_avatar_key, old),
        StoredObject(orphan_avatar_key, old),
    ]

    result = application_container.media.cleanup_orphans.execute()

    assert fake_object_storage.deleted_object_keys == [
        orphan_estate_key,
        orphan_avatar_key,
    ]
    assert result.used == 2
    assert result.deleted == 2


def test_cleanup_removes_expired_but_preserves_fresh_reservations(
    application_container,
    db_session,
    any_user,
    reserve_media_upload,
):
    old = datetime.now(timezone.utc) - timedelta(days=2)
    expired_key = _object_key(any_user.id)
    fresh_key = _object_key(any_user.id)

    expired = reserve_media_upload(
        expired_key,
        any_user.id,
        purpose=MediaPurpose.estate,
    )
    reserve_media_upload(
        fresh_key,
        any_user.id,
        purpose=MediaPurpose.estate,
    )
    expired.created_at = old
    db_session.flush()

    result = application_container.media.cleanup_orphans.execute()

    remaining_keys = set(
        db_session.scalars(
            select(MediaUpload.object_key).where(
                MediaUpload.object_key.in_([expired_key, fresh_key])
            )
        )
    )
    assert remaining_keys == {fresh_key}
    assert result.expired_reservations_deleted == 1
