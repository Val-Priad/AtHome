import uuid
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_model import (
    EmailVerification,
)


class EmailVerificationRepository:
    @staticmethod
    def deactivate_all_user_tokens(db: Session, user_id: uuid.UUID):
        db.execute(
            update(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.used_at.is_(None),
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
            EmailVerification(
                user_id=user_id, token_hash=hashed_token, expires_at=expires_at
            )
        )
