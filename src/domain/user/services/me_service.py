from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from domain.user.services.password_hasher import PasswordHasher
from domain.user.user_model import User
from domain.user.user_repository import UserRepository
from exceptions.custom_exceptions.user_exceptions import (
    MissingUpdateDataError,
    NewPasswordMatchesOldError,
)


class MeService:
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def update_password(
        self, session: Session, user_id: UUID, raw_password: str
    ) -> None:
        user = self.user_repository.get_user_by_id(session, user_id)
        user.password_hash = self.password_hasher.hash_password(raw_password)

    @staticmethod
    def ensure_new_password_differs(
        old_password: str, new_password: str
    ) -> None:
        if old_password == new_password:
            raise NewPasswordMatchesOldError()

    def verify_password(
        self, session: Session, user_id: UUID, raw_password: str
    ) -> None:
        user = self.user_repository.get_user_by_id(session, user_id)
        self.password_hasher.verify_password(raw_password, user.password_hash)

    def update_personal_data(
        self,
        session: Session,
        user_id: UUID,
        updates: dict[str, Any],
    ) -> User:
        user = self.user_repository.get_user_by_id(session, user_id)

        if not updates:
            raise MissingUpdateDataError()

        for field, value in updates.items():
            setattr(user, field, value)

        return user

    def get_user_for_update(
        self,
        session: Session,
        user_id: UUID,
    ) -> User:
        return self.user_repository.get_user_by_id_for_update(session, user_id)
