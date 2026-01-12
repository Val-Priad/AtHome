import uuid
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_model import (
    EmailVerificationModel,
)


class EmailVerificationRepository:
    @staticmethod
    def deactivate_previous_tokens(db: Session, user_id: uuid.UUID):
        db.execute(
            update(EmailVerificationModel)
            .where(
                EmailVerificationModel.user_id == user_id,
                EmailVerificationModel.used_at.is_(None),
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
            EmailVerificationModel(
                user_id=user_id, token_hash=hashed_token, expires_at=expires_at
            )
        )
