import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from domain.email_verification import (
    EmailVerificationRepository,
)
from domain.user import User, UserRepository
from exceptions import (
    EmailSendError,
    TokenVerificationError,
    UserAlreadyVerifiedError,
)
from infrastructure.email.Mailer import Mailer
from security import TokenHasher


class EmailVerificationService:
    def __init__(
        self,
        email_verification_repository: EmailVerificationRepository,
        user_repository: UserRepository,
        mailer: Mailer,
        token_hasher: TokenHasher,
    ):
        self.email_verification_repository = email_verification_repository
        self.user_repository = user_repository
        self.mailer = mailer
        self.token_hasher = token_hasher

    TOKEN_TTL = timedelta(hours=24)

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
            raise UserAlreadyVerifiedError()

    def add_token(
        self,
        db: Session,
        user_id: uuid.UUID,
        invalidate_previous: bool = False,
    ):
        expires_at = datetime.now(timezone.utc) + self.TOKEN_TTL
        raw_token = self.token_hasher.generate_token()
        token_hash = self.token_hasher.hash_token(raw_token)

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
            db, self.token_hasher.hash_token(raw_token)
        )
        if token is None:
            raise TokenVerificationError()

        token.used_at = datetime.now(timezone.utc)

        token.user.is_email_verified = True

        self.email_verification_repository.deactivate_all_user_tokens(
            db, token.user.id
        )
