from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.email_verification.email_verification_service import (
    EmailVerificationService,
)
from domain.user.services.auth_service import AuthService
from domain.user.user_repository import UserRepository
from infrastructure.email.Mailer import Mailer

mailer = Mailer()
user_repository = UserRepository()
email_verification_repository = EmailVerificationRepository()
email_verification_service = EmailVerificationService(
    email_verification_repository, user_repository, mailer
)
auth_service = AuthService(user_repository, email_verification_service)
