from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from domain.media.media_config import (
    MEDIA_CONFIG_BY_PURPOSE,
    MEDIA_FORMAT_BY_CONTENT_TYPE,
)
from domain.media.media_enums import MediaContentType, MediaPurpose
from schemas.parent_types import RequestValidation


class MediaUploadUrlRequest(RequestValidation):
    model_config = ConfigDict(extra="forbid")

    purpose: MediaPurpose
    content_type: MediaContentType
    size_bytes: int = Field(gt=0)

    @field_validator("content_type")
    @classmethod
    def _validate_content_type_for_purpose(
        cls,
        content_type: MediaContentType,
        info: ValidationInfo,
    ) -> MediaContentType:
        purpose = info.data.get("purpose")
        if not isinstance(purpose, MediaPurpose):
            return content_type

        media_format = MEDIA_FORMAT_BY_CONTENT_TYPE[content_type]
        purpose_config = MEDIA_CONFIG_BY_PURPOSE[purpose]
        allowed_extensions = purpose_config.extensions_by_media_type.get(
            media_format.media_type,
            frozenset(),
        )
        if media_format.extension not in allowed_extensions:
            raise ValueError(
                "Content type is not allowed for this media purpose"
            )

        return content_type

    @field_validator("size_bytes")
    @classmethod
    def _validate_max_size(
        cls,
        size_bytes: int,
        info: ValidationInfo,
    ) -> int:
        content_type = info.data.get("content_type")
        if not isinstance(content_type, MediaContentType):
            return size_bytes

        media_format = MEDIA_FORMAT_BY_CONTENT_TYPE[content_type]
        if size_bytes > media_format.max_size_bytes:
            media_kind = media_format.media_type.value.capitalize()
            raise ValueError(
                f"{media_kind} size must not exceed "
                f"{media_format.max_size_bytes} bytes"
            )

        return size_bytes


class MediaUploadUrlsRequest(RequestValidation):
    model_config = ConfigDict(extra="forbid")

    files: list[MediaUploadUrlRequest] = Field(
        min_length=1,
        max_length=20,
    )
