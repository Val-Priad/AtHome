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
from domain.user.services.me_service import MeService
from domain.user.user_repository import UserRepository
from infrastructure.email.Mailer import Mailer
from security import PasswordHasher, TokenHasher

# EXTERNAL
mailer = Mailer()

# INTERNAL
password_hasher = PasswordHasher()
token_hasher = TokenHasher()

# DOMAIN RELATED
user_repository = UserRepository()

email_verification_repository = EmailVerificationRepository()
email_verification_service = EmailVerificationService(
    email_verification_repository, user_repository, mailer, token_hasher
)

password_reset_repository = PasswordResetRepository()
password_reset_service = PasswordResetService(
    password_reset_repository,
    user_repository,
    mailer,
    token_hasher,
    password_hasher,
)

auth_service = AuthService(user_repository, password_hasher)
me_service = MeService(user_repository, password_hasher)
