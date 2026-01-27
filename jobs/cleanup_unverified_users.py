from datetime import datetime, timedelta, timezone
from typing import cast

from sqlalchemy import CursorResult, delete

from domain.user.user_model import User
from infrastructure.db import db_session

from .jobs_logger import jobs_logger


def cleanup_unverified_users():
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        with db_session() as session:
            result = cast(
                CursorResult,
                session.execute(
                    delete(User).where(
                        User.is_email_verified.is_(False),
                        User.created_at < cutoff,
                    )
                ),
            )
        jobs_logger.info(
            f"Successfully deleted {result.rowcount} unverified users"
        )
    except Exception as e:
        jobs_logger.error(
            f"Error occurred during deletion of unverified users {e}"
        )


if __name__ == "__main__":
    cleanup_unverified_users()
