from datetime import datetime, timedelta, timezone
from typing import cast

from sqlalchemy import CursorResult, delete

from api.v1.users.models.user import User
from db import session

from .jobs_logger import jobs_logger


def cleanup_unverified_users():
    db = session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        result = cast(
            CursorResult,
            db.execute(
                delete(User).where(
                    User.is_email_verified.is_(False),
                    User.created_at < cutoff,
                )
            ),
        )
        db.commit()
        jobs_logger.info(
            f"Successfully deleted {result.rowcount} unverified users"
        )
    except Exception as e:
        db.rollback()
        jobs_logger.error(
            f"Error occurred during deletion of unverified users {e}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_unverified_users()
