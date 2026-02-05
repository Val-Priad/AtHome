from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from domain.user.user_model import User, UserRole
from exceptions.custom_exceptions.user_exceptions import UserNotFoundError


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

        return result is not None  # FIXME: remove redundant comparison

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

    # FIXME: silent deletion
    @staticmethod
    def delete_user_by_id(db: Session, user_id: UUID):
        return db.execute(delete(User).where(User.id == user_id))

    # FIXME: silent update
    @staticmethod
    def update_password(db: Session, user_id: UUID, password: bytes):
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password)
        )

    @classmethod
    def change_user_role(
        cls, db: Session, user_id: UUID, role: UserRole
    ) -> UUID:
        return db.execute(
            update(User)
            .where(User.id == user_id)
            .values(role=role)
            .returning(User.id)
        ).scalar_one()
