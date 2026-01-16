from sqlalchemy import select
from sqlalchemy.orm import Session

from exceptions.user_exceptions import UserNotFoundError

from .user_model import User


class UserRepository:
    @staticmethod
    def add_user(db: Session, email: str, hashed_password: bytes) -> User:
        user = User(email=email, password_hash=hashed_password)
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def exists_by_email(db: Session, email: str):
        result = db.scalar(select(1).where(User.email == email))

        return result is not None

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        result = db.scalar(select(User).where(User.email == email))

        if result is None:
            raise UserNotFoundError()

        return result
