from uuid import UUID

from sqlalchemy.orm import Session

from domain.user.user_model import UserRole
from domain.user.user_repository import UserRepository
from exceptions.custom_exceptions.user_exceptions import (
    ForbiddenError,
    UserStateConflictError,
)


class AdminUsersService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user_by_id(self, db, user_id):
        return self.user_repository.get_user_by_id(db, user_id)

    def change_user_role(
        self, db: Session, requester_id: UUID, user_id: UUID, role: UserRole
    ):
        self.ensure_has_rights(db, requester_id, UserRole.admin)
        self.ensure_ids_differ(requester_id, user_id)

        user = self.user_repository.get_user_by_id(db, user_id)
        if role == user.role:
            raise UserStateConflictError()

        return self.user_repository.change_user_role(db, user_id, role)

    def delete_user_by_id(self, db, user_id):
        return self.user_repository.delete_user_by_id(db, user_id)

    def ensure_has_rights(
        self, session: Session, requester_id: UUID, *roles: UserRole
    ) -> None:
        requester = self.get_user_by_id(session, requester_id)
        if requester.role not in roles:
            raise ForbiddenError()

    @staticmethod
    def ensure_ids_differ(first: UUID, second: UUID) -> None:
        if first == second:
            raise UserStateConflictError()
        return None
