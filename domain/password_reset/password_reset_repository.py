import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from domain.password_reset.password_reset_model import PasswordReset


class PasswordResetRepository:
    @staticmethod
    def deactivate_all_user_tokens(
        db: Session, user_id: uuid.UUID
    ):  # FIXME: rename to try_deactivate... (best effort)
        db.execute(
            update(PasswordReset)
            .where(
                PasswordReset.user_id == user_id,
                PasswordReset.used_at.is_(None),
            )
            .values(expires_at=datetime.now(timezone.utc))
        )

    @staticmethod
    def add_token(
        db: Session,
        user_id: uuid.UUID,
        hashed_token: bytes,
        expires_at: datetime,
    ):
        db.add(
            PasswordReset(
                user_id=user_id, token_hash=hashed_token, expires_at=expires_at
            )
        )

    @staticmethod
    def get_valid_token(db: Session, hashed_token):
        return db.scalar(
            select(PasswordReset).where(
                PasswordReset.token_hash == hashed_token,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > datetime.now(timezone.utc),
            )
        )
