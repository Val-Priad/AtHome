from sqlalchemy.orm import Session

from domain.user.user_model import User
from domain.user.user_repository import UserRepository
from exceptions.custom_exceptions.user_exceptions import (
    UserAlreadyExistsError,
    UserIsNotVerifiedError,
)
from security import PasswordCrypto


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordCrypto,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def create_user(self, db: Session, email: str, password: str) -> User:
        if self.user_repository.exists_by_email(db, email):
            raise UserAlreadyExistsError()

        hashed_password = self.password_hasher.hash_password(password)

        user = User(email=email, password_hash=hashed_password)
        db.add(user)
        db.flush()
        return user

    def get_user_by_email(self, db: Session, email: str):
        return self.user_repository.get_user_by_email(db, email)

    def verify_password(self, db: Session, email, password):
        user = self.get_user_by_email(db, email)

        if not user.is_email_verified:
            raise UserIsNotVerifiedError()

        self.password_hasher.verify_password(password, user.password_hash)

        return user
