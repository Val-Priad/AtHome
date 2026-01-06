import uuid
from sqlalchemy import Column, String, Enum, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum("user", "agent", "admin", name="role_enum"),
        default="user",
        nullable=False,
    )
    is_email_verified = Column(Boolean, default=False, nullable=False)
    name = Column(String(255))
    phone_number = Column(String(255))
    avatar = Column(String(255))
    description = Column(String(255))
    created_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at = Column(
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
