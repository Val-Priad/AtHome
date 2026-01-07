import uuid
import datetime
from sqlalchemy import (
    String,
    Enum,
    DateTime,
    func,
    Boolean,
    LargeBinary,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from db import Base
import enum


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
    is_email_verified: Mapped[Boolean] = mapped_column(
        Boolean, default=False, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(255))
    avatar: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "name": self.name,
            "phone_number": self.phone_number,
            "avatar": self.avatar,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
