import bcrypt
from sqlalchemy.orm import Session

from domain.email_verification.email_verification_service import (
    EmailVerificationService,
)
from domain.user.user_model import User
from domain.user.user_repository import UserRepository
from exceptions.user import UserAlreadyExistsError


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
