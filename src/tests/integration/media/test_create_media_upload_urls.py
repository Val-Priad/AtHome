from sqlalchemy import select

from domain.media.media_upload_model import MediaUpload
from tests.integration.conftest import MEDIA_PATH

UPLOAD_URLS_PATH = f"{MEDIA_PATH}/upload-urls"


def _payload(**overrides):
    payload = {
        "purpose": "user_avatar",
        "content_type": "image/webp",
        "size_bytes": 1024,
    }
    payload.update(overrides)
    return payload


def _batch_payload(*files):
    return {"files": list(files)}


def test_user_can_create_avatar_upload_url(
    client,
    logged_in_user,
    db_session,
) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(_payload()),
        headers=logged_in_user.headers,
    )

    assert response.status_code == 200
    uploads = response.get_json()["data"]["uploads"]
    assert len(uploads) == 1
    data = uploads[0]
    prefix, filename = data["object_key"].rsplit("/", maxsplit=1)
    assert data["upload_url"] == (
        f"https://storage.test/{prefix}/pending/{filename}"
    )
    assert data["expires_in"] == 300
    upload = db_session.scalar(
        select(MediaUpload).where(MediaUpload.object_key == data["object_key"])
    )
    assert upload is not None
    assert upload.uploader_id == logged_in_user.id


def test_user_can_create_estate_video_upload_url(
    client,
    logged_in_user,
) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(
            _payload(
                purpose="estate",
                content_type="video/mp4",
            )
        ),
        headers=logged_in_user.headers,
    )

    assert response.status_code == 200


def test_user_can_create_multiple_upload_urls_in_one_request(
    client,
    logged_in_user,
    db_session,
) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(
            _payload(
                purpose="estate",
                content_type="image/webp",
            ),
            _payload(
                purpose="estate",
                content_type="video/mp4",
            ),
        ),
        headers=logged_in_user.headers,
    )

    assert response.status_code == 200
    uploads = response.get_json()["data"]["uploads"]
    assert len(uploads) == 2
    assert uploads[0]["object_key"].endswith(".webp")
    assert uploads[1]["object_key"].endswith(".mp4")
    object_keys = [upload["object_key"] for upload in uploads]
    reservations = list(
        db_session.scalars(
            select(MediaUpload).where(MediaUpload.object_key.in_(object_keys))
        )
    )
    assert len(reservations) == 2


def test_batch_upload_rejects_more_than_twenty_files(
    client,
    logged_in_user,
) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(*[_payload(purpose="estate")] * 21),
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400


def test_avatar_upload_rejects_video(client, logged_in_user) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(_payload(content_type="video/mp4")),
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["errors"][0]["message"] == (
        "Content type is not allowed for this media purpose"
    )


def test_create_upload_urls_requires_authentication(client) -> None:
    response = client.post(
        UPLOAD_URLS_PATH,
        json=_batch_payload(_payload()),
    )

    assert response.status_code == 401
