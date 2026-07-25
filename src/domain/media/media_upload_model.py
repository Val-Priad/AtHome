import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.media.media_enums import MediaPurpose, MediaType
from infrastructure.db import Base


class MediaUploadStatus(str, enum.Enum):
    available = "available"
    deleting = "deleting"


class MediaUpload(Base):
    __tablename__ = "media_uploads"
    __table_args__ = (
        Index(
            "ix_media_uploads_status_created_at",
            "status",
            "created_at",
        ),
    )

    object_key: Mapped[str] = mapped_column(Text, primary_key=True)
    upload_object_key: Mapped[str] = mapped_column(Text, unique=True)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    purpose: Mapped[MediaPurpose] = mapped_column(
        Enum(MediaPurpose, name="media_purpose_enum"),
    )
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type_enum"),
    )
    status: Mapped[MediaUploadStatus] = mapped_column(
        Enum(MediaUploadStatus, name="media_upload_status_enum"),
        default=MediaUploadStatus.available,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
