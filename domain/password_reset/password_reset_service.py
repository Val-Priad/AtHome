import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from domain.password_reset.password_reset_repository import (
    PasswordResetRepository,
)
from domain.user.user_repository import UserRepository
from exceptions.mailer_exceptions import EmailSendError
from exceptions.user_exceptions import (
    TokenVerificationError,
)
from infrastructure.email.Mailer import Mailer


class PasswordResetService:
    def __init__(
        self,
        password_reset_repository: PasswordResetRepository,
        user_repository: UserRepository,
        mailer: Mailer,
    ):
        self.password_reset_repository = password_reset_repository
        self.user_repository = user_repository
        self.mailer = mailer

    TOKEN_TTL = timedelta(minutes=10)

    @staticmethod
    def _get_hashed_token(raw_token: str):
        return hashlib.sha256(raw_token.encode()).digest()

    def get_user_by_email(self, db: Session, email: str):
        return self.user_repository.get_user_by_email(db, email)

    def send_reset_password_email(self, email_to: str, token: str):
        try:
            return self.mailer.send_reset_password_email(email_to, token)
        except Exception:
            raise EmailSendError()

    def get_token(
        self,
        db: Session,
        user_id: uuid.UUID,
    ):
        expires_at = datetime.now(timezone.utc) + self.TOKEN_TTL
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._get_hashed_token(raw_token)

        self.password_reset_repository.deactivate_all_user_tokens(db, user_id)
        self.password_reset_repository.add_token(
            db, user_id, token_hash, expires_at
        )
        return raw_token

    def reset_password(self, db: Session, raw_token: str, password: str):
        token = self.password_reset_repository.get_valid_token(
            db, self._get_hashed_token(raw_token)
        )
        if token is None:
            raise TokenVerificationError()

        token.used_at = datetime.now(timezone.utc)
        token.user.password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()
        )

        self.password_reset_repository.deactivate_all_user_tokens(
            db, token.user.id
        )
