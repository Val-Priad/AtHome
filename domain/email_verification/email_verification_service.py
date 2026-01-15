import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.user.user_model import User
from domain.user.user_repository import UserRepository
from exceptions.user import (
    EmailSendError,
    TokenVerificationError,
    UserAlreadyVerifiedError,
)
from infrastructure.email.Mailer import Mailer


class EmailVerificationService:
    def __init__(
        self,
        email_verification_repository: EmailVerificationRepository,
        user_repository: UserRepository,
        mailer: Mailer,
    ):
        self.email_verification_repository = email_verification_repository
        self.user_repository = user_repository
        self.mailer = mailer

    TOKEN_TTL = timedelta(hours=24)

    @staticmethod
    def _get_hashed_token(raw_token: str):
        return hashlib.sha256(raw_token.encode()).digest()

    def get_user_by_email(self, db: Session, email: str):
        return self.user_repository.get_user_by_email(db, email)

    def send_verification_email(self, email_to: str, token: str):
        try:
            return self.mailer.send_verification_email(email_to, token)
        except Exception:
            raise EmailSendError()

    @staticmethod
    def check_user_is_not_verified(user: User):
        if user.is_email_verified:
            raise UserAlreadyVerifiedError(user.email)

    def add_token(
        self,
        db: Session,
        user_id: uuid.UUID,
        invalidate_previous: bool = False,
    ):
        expires_at = datetime.now(timezone.utc) + self.TOKEN_TTL
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._get_hashed_token(raw_token)

        if invalidate_previous:
            self.email_verification_repository.deactivate_all_user_tokens(
                db, user_id
            )
        self.email_verification_repository.add_token(
            db, user_id, token_hash, expires_at
        )
        return raw_token

    def get_resend_token(self, db: Session, user_id: uuid.UUID):
        return self.add_token(db, user_id, invalidate_previous=True)

    def verify_token(self, db: Session, raw_token):
        token = self.email_verification_repository.get_valid_token(
            db, self._get_hashed_token(raw_token)
        )
        if token is None:
            raise TokenVerificationError

        token.used_at = datetime.now(timezone.utc)

        token.user.is_email_verified = True

        self.email_verification_repository.deactivate_all_user_tokens(
            db, token.user.id
        )
