import bcrypt

from exceptions.user import UserAlreadyExistsError

from ..models.user import User
from ..repositories.user_repository import UserRepository
from .email_verification_service import EmailVerificationService


class AuthService:
    @staticmethod
    def register_user(email: str, password: str) -> User:
        if UserRepository.exists_by_email(email):
            raise UserAlreadyExistsError()

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return UserRepository.create_user(email, hashed_password)
