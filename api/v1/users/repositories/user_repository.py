from sqlalchemy import select

from db import session

from ..models.user import User


class UserRepository:
    @staticmethod
    def create_user(email: str, hashed_password: bytes) -> User:
        db = session()
        try:
            new_user = User(email=email, password_hash=hashed_password)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def exists_by_email(email: str):
        db = session()
        try:
            result = db.scalar(select(1).where(User.email == email))

            return result is not None

        finally:
            db.close()
