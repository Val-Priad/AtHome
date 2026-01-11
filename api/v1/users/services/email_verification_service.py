import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import resend
from flask import jsonify
from sqlalchemy.orm import Session

from infrastructure.db import session

from ..repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from ..repositories.user_repository import UserRepository


class EmailVerificationService:
    TOKEN_TTL = timedelta(hours=24)

    @staticmethod
    def get_user_by_email(email: str):
        return UserRepository.get_user_by_email(email)

    @staticmethod
    def send_verification_email(email_to: str, token: str):
        resend.api_key = os.getenv("RESEND_API_KEY")
        params = {
            "from": f"noreply@{os.getenv('RESEND_DOMAIN_NAME')}",
            "to": email_to,
            "subject": "Click on link to verify your email!",
            "html": "<strong>it works!</strong>",
        }
        r = resend.Emails.send(params)  # pyright: ignore[reportArgumentType]
        return jsonify(r)

    @staticmethod
    def add_token(
        db: Session, user_id: uuid.UUID, invalidate_previous: bool = False
    ):
        expires_at = (
            datetime.now(timezone.utc) + EmailVerificationService.TOKEN_TTL
        )
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).digest()

        if invalidate_previous:
            EmailVerificationTokenRepository.deactivate_previous_tokens(
                db, user_id
            )
        EmailVerificationTokenRepository.add_token(
            db, user_id, token_hash, expires_at
        )
        return raw_token

    @staticmethod
    def get_resend_token(user_id: uuid.UUID):
        db = session()
        try:
            raw_token = EmailVerificationService.add_token(
                db, user_id, invalidate_previous=True
            )
            db.commit()
            return raw_token
        except Exception:
            db.rollback()
            raise
        finally:
            db.close


# TODO 1. Create clickable link that will verify user
# TODO 2. Create beautiful markup for email
