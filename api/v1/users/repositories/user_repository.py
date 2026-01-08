from sqlalchemy import select
from sqlalchemy.orm import Session

from db import session
from exceptions.user import UserNotFoundError

from ..models.user import User


class UserRepository:
    @staticmethod
    def add_user(db: Session, email: str, hashed_password: bytes) -> User:
        user = User(email=email, password_hash=hashed_password)
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def exists_by_email(email: str):
        db = session()
        try:
            result = db.scalar(select(1).where(User.email == email))

            return result is not None

        finally:
            db.close()

    @staticmethod
    def get_user_by_email(email: str) -> User:
        db = session()
        try:
            result = db.scalar(select(User).where(User.email == email))
            if result is None:
                raise UserNotFoundError(email=email)
            return result
        finally:
            db.close()
