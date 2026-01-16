import bcrypt
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_service import (
    EmailVerificationService,
)
from domain.user.user_model import User
from domain.user.user_repository import UserRepository
from exceptions.user_exceptions import (
    PasswordVerificationError,
    UserAlreadyExistsError,
    UserIsNotVerifiedError,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        email_verification_service: EmailVerificationService,
    ):
        self.user_repository = user_repository
        self.email_verification_service = email_verification_service

    def add_user_and_token(
        self, db: Session, email: str, password: str
    ) -> tuple[User, str]:
        if self.user_repository.exists_by_email(db, email):
            raise UserAlreadyExistsError()

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        user = self.user_repository.add_user(db, email, hashed_password)

        raw_token = self.email_verification_service.add_token(
            db,
            user.id,
        )

        return user, raw_token

    def get_user_by_email(self, db: Session, email: str):
        return self.user_repository.get_user_by_email(db, email)

    def verify_password(self, db: Session, email, password):
        user = self.get_user_by_email(db, email)

        if not user.is_email_verified:
            raise UserIsNotVerifiedError()

        if not bcrypt.checkpw(password.encode(), user.password_hash):
            raise PasswordVerificationError()

        return user
