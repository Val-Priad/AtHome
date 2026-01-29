import datetime
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db import Base

if TYPE_CHECKING:
    from domain.email_verification.email_verification_model import (
        EmailVerification,
    )
    from domain.password_reset.password_reset_model import PasswordReset


class UserRole(enum.Enum):
    user = "user"
    agent = "agent"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    password_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="role_enum"),
        default=UserRole.user,
        nullable=False,
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(255))
    avatar_key: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(510))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
