import bcrypt

from db import session
from exceptions.user import UserAlreadyExistsError

from ..models.user import User
from ..repositories.user_repository import UserRepository
from ..services.email_verification_service import EmailVerificationService


class AuthService:
    @staticmethod
    def add_user_and_token(email: str, password: str) -> tuple[User, str]:
        if UserRepository.exists_by_email(email):
            raise UserAlreadyExistsError()

        db = session()
        try:
            hashed_password = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            )
            user = UserRepository.add_user(db, email, hashed_password)
            raw_token = EmailVerificationService.add_token(
                db,
                user.id,
            )
            db.commit()
            db.refresh(user)
            return user, raw_token
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
