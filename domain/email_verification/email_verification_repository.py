import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_model import (
    EmailVerification,
)
from exceptions.custom_exceptions.user_exceptions import TokenVerificationError


# TODO: add type annotations for returns to split best effort from strict
class EmailVerificationRepository:
    @staticmethod
    def try_deactivate_all_user_tokens(
        db: Session, user_id: uuid.UUID
    ) -> None:
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
    ) -> None:
        db.add(
            EmailVerification(
                user_id=user_id, token_hash=hashed_token, expires_at=expires_at
            )
        )

    @staticmethod
    def get_valid_token(db: Session, hashed_token: bytes) -> EmailVerification:
        token = db.scalar(
            select(EmailVerification).where(
                EmailVerification.token_hash == hashed_token,
                EmailVerification.used_at.is_(None),
                EmailVerification.expires_at > datetime.now(timezone.utc),
            )
        )
        if token is None:
            raise TokenVerificationError()
        return token
