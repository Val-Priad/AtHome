from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from domain.user.user_model import User
from exceptions.custom_exceptions.user_exceptions import UserNotFoundError


class UserRepository:
    @staticmethod
    def exists_by_email(db: Session, email: str) -> bool:
        return db.execute(
            select(exists().where(User.email == email))
        ).scalar_one()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        result = db.scalar(select(User).where(User.email == email))

        if result is None:
            raise UserNotFoundError()

        return result

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        result = db.scalar(select(User).where(User.id == user_id))

        if result is None:
            raise UserNotFoundError()

        return result
