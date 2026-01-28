from uuid import UUID

from sqlalchemy.orm import Session

from domain.user.user_model import UserRole
from domain.user.user_repository import UserRepository
from exceptions.user_exceptions import ForbiddenError


class AdminUsersService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user_by_id(self, db, user_id):
        return self.user_repository.get_user_by_id(db, user_id)

    def ensure_has_rights(
        self, session: Session, requester_id: UUID, *roles: UserRole
    ) -> None:
        requester = self.get_user_by_id(session, requester_id)
        if requester.role not in roles:
            raise ForbiddenError()
