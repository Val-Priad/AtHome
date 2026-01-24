from uuid import UUID

from sqlalchemy.orm import Session

from domain.user.user_repository import UserRepository
from exceptions import NewPasswordMatchesOldError, MissingUpdateDataError
from security import PasswordCrypto
from schemas.me_schemas import UpdateUserPersonalDataRequest


class MeService:
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordCrypto
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def update_password(self, db: Session, user_id: UUID, raw_password: str):
        self.user_repository.update_password(
            db, user_id, self.password_hasher.hash_password(raw_password)
        )

    @staticmethod
    def ensure_new_password_differs(
        old_password: str, new_password: str
    ) -> None:
        if old_password == new_password:
            raise NewPasswordMatchesOldError

    def verify_password(
        self, db: Session, user_id: UUID, raw_password: str
    ) -> None:
        user = self.user_repository.get_user_by_id(db, user_id)
        self.password_hasher.verify_password(raw_password, user.password_hash)

    def update_personal_data(
        self, db: Session, user_id: UUID, data: UpdateUserPersonalDataRequest
    ):
        user = self.user_repository.get_user_by_id(db, user_id)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise MissingUpdateDataError()

        for field, value in updates.items():
            setattr(user, field, value)

        return user
