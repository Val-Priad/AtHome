import uuid
from datetime import datetime

from db import session

from ..models.email_verification_token import EmailVerificationToken


class EmailVerificationTokenRepository:
    @staticmethod
    def add_token(
        user_id: uuid.UUID, hashed_token: bytes, expires_at: datetime
    ):
        db = session()
        try:
            email_verification_token = EmailVerificationToken(
                user_id=user_id, token_hash=hashed_token, expires_at=expires_at
            )
            db.add(email_verification_token)
            db.commit()
            db.refresh(email_verification_token)
            return email_verification_token
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
