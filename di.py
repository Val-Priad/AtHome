from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.email_verification.email_verification_service import (
    EmailVerificationService,
)
from domain.password_reset.password_reset_repository import (
    PasswordResetRepository,
)
from domain.password_reset.password_reset_service import PasswordResetService
from domain.user.services.auth_service import AuthService
from domain.user.user_repository import UserRepository
from infrastructure.email.Mailer import Mailer

mailer = Mailer()
user_repository = UserRepository()
email_verification_repository = EmailVerificationRepository()
email_verification_service = EmailVerificationService(
    email_verification_repository, user_repository, mailer
)
password_reset_repository = PasswordResetRepository()
password_reset_service = PasswordResetService(
    password_reset_repository, user_repository, mailer
)

auth_service = AuthService(user_repository, email_verification_service)
