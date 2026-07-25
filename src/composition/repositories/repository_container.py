from dataclasses import dataclass

from domain.email_verification.email_verification_repository import (
    EmailVerificationRepository,
)
from domain.estate.estate_media_repository import EstateMediaRepository
from domain.estate.estate_repository import EstateRepository
from domain.media.media_upload_repository import MediaUploadRepository
from domain.password_reset.password_reset_repository import (
    PasswordResetRepository,
)
from domain.user.user_repository import UserRepository


@dataclass(frozen=True, slots=True)
class RepositoryContainer:
    users: UserRepository
    email_verifications: EmailVerificationRepository
    password_resets: PasswordResetRepository
    estates: EstateRepository
    estate_media: EstateMediaRepository
    media_uploads: MediaUploadRepository
