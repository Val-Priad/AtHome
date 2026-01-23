import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from domain.password_reset.password_reset_repository import (
    PasswordResetRepository,
)
from domain.user.user_repository import UserRepository
from exceptions import EmailSendError, TokenVerificationError
from infrastructure.email.Mailer import Mailer
from security import PasswordCrypto, TokenCrypto


class PasswordResetService:
    def __init__(
        self,
        password_reset_repository: PasswordResetRepository,
        user_repository: UserRepository,
        mailer: Mailer,
        token_hasher: TokenCrypto,
        password_hasher: PasswordCrypto,
    ):
        self.password_reset_repository = password_reset_repository
        self.user_repository = user_repository
        self.mailer = mailer
        self.token_hasher = token_hasher
        self.password_hasher = password_hasher

    TOKEN_TTL = timedelta(minutes=10)

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
        raw_token = self.token_hasher.generate_token()
        token_hash = self.token_hasher.hash_token(raw_token)

        self.password_reset_repository.deactivate_all_user_tokens(db, user_id)
        self.password_reset_repository.add_token(
            db, user_id, token_hash, expires_at
        )
        return raw_token

    def reset_password(self, db: Session, raw_token: str, password: str):
        token = self.password_reset_repository.get_valid_token(
            db, self.token_hasher.hash_token(raw_token)
        )
        if token is None:
            raise TokenVerificationError()

        token.used_at = datetime.now(timezone.utc)
        token.user.password_hash = self.password_hasher.hash_password(password)

        self.password_reset_repository.deactivate_all_user_tokens(
            db, token.user.id
        )
