import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import resend
from flask import jsonify

from ..repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)


class EmailVerificationService:
    TOKEN_TTL = timedelta(hours=24)

    @staticmethod
    def generate_verification_token(user_id: uuid.UUID) -> str:
        expires_at = (
            datetime.now(timezone.utc) + EmailVerificationService.TOKEN_TTL
        )
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).digest()
        EmailVerificationTokenRepository.add_token(
            user_id, token_hash, expires_at
        )
        return raw_token

    @staticmethod
    def send_verification_email(email_to: str, token: str):
        resend.api_key = os.getenv("RESEND_API_KEY")
        params = {
            "from": f"noreply@{os.getenv('RESEND_DOMAIN_NAME')}",
            "to": email_to,
            "subject": "Click on link to verify your email!",
            "html": "<strong>it works!</strong>",
        }

        # TODO 1. Create clickable link that will verify user
        # TODO 2. Create beautiful markup for email

        r = resend.Emails.send(params)  # pyright: ignore[reportArgumentType]
        return jsonify(r)
