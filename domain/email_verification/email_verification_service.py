import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import resend  # TODO create MAILER class to handle emails
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.user.user_repository import UserRepository


class EmailVerificationService:
    def __init__(
        self,
        email_verification_repository: EmailVerificationRepository,
        user_repository: UserRepository,
    ):
        self.email_verification_repository = email_verification_repository
        self.user_repository = user_repository

    TOKEN_TTL = timedelta(hours=24)

    def get_user_by_email(self, db: Session, email: str):
        return self.user_repository.get_user_by_email(db, email)

    @staticmethod
    def send_verification_email(email_to: str, token: str):
        resend.api_key = os.getenv("RESEND_API_KEY")
        params = {
            "from": f"noreply@{os.getenv('RESEND_DOMAIN_NAME')}",
            "to": email_to,
            "subject": "Click on link to verify your email!",
            "html": "<strong>it works!</strong>",
        }
        resend.Emails.send(params)  # pyright: ignore[reportArgumentType]

    def add_token(
        self,
        db: Session,
        user_id: uuid.UUID,
        invalidate_previous: bool = False,
    ):
        expires_at = datetime.now(timezone.utc) + self.TOKEN_TTL
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).digest()

        if invalidate_previous:
            self.email_verification_repository.deactivate_previous_tokens(
                db, user_id
            )
        self.email_verification_repository.add_token(
            db, user_id, token_hash, expires_at
        )
        return raw_token

    def get_resend_token(self, db: Session, user_id: uuid.UUID):
        return self.add_token(db, user_id, invalidate_previous=True)


# TODO 1. Create clickable link that will verify user
# TODO 2. Create beautiful markup for email
