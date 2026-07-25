from dataclasses import dataclass

from domain.media.media_enums import (
    MediaContentType,
    MediaPurpose,
    MediaType,
)


@dataclass(frozen=True, slots=True)
class MediaPurposeConfig:
    prefix: str
    extensions_by_media_type: dict[MediaType, frozenset[str]]


@dataclass(frozen=True, slots=True)
class MediaFormatConfig:
    extension: str
    media_type: MediaType
    max_size_bytes: int


MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024

MEDIA_FORMAT_BY_CONTENT_TYPE = {
    MediaContentType.jpeg: MediaFormatConfig(
        extension="jpg",
        media_type=MediaType.image,
        max_size_bytes=MAX_IMAGE_SIZE_BYTES,
    ),
    MediaContentType.png: MediaFormatConfig(
        extension="png",
        media_type=MediaType.image,
        max_size_bytes=MAX_IMAGE_SIZE_BYTES,
    ),
    MediaContentType.webp: MediaFormatConfig(
        extension="webp",
        media_type=MediaType.image,
        max_size_bytes=MAX_IMAGE_SIZE_BYTES,
    ),
    MediaContentType.mp4: MediaFormatConfig(
        extension="mp4",
        media_type=MediaType.video,
        max_size_bytes=MAX_VIDEO_SIZE_BYTES,
    ),
}

MEDIA_FORMAT_BY_EXTENSION = {
    config.extension: (content_type, config)
    for content_type, config in MEDIA_FORMAT_BY_CONTENT_TYPE.items()
}


MEDIA_CONFIG_BY_PURPOSE = {
    MediaPurpose.estate: MediaPurposeConfig(
        prefix="estate-media",
        extensions_by_media_type={
            MediaType.image: frozenset({"jpg", "png", "webp"}),
            MediaType.video: frozenset({"mp4"}),
        },
    ),
    MediaPurpose.user_avatar: MediaPurposeConfig(
        prefix="user-avatars",
        extensions_by_media_type={
            MediaType.image: frozenset({"jpg", "png", "webp"}),
        },
    ),
}
