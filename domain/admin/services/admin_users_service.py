from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from domain.admin.admin_types import BaseUserSortBy
from domain.user.user_model import User, UserRole
from domain.user.user_repository import UserRepository
from exceptions.custom_exceptions.user_exceptions import ForbiddenError
from schemas.admin_schemas.admin_users_schemas.admin_users_requests import (
    UsersRequest,
)


class AdminUsersService:
    SORT_MAP: dict[BaseUserSortBy, Any] = {
        "created_at": User.created_at,
        "updated_at": User.updated_at,
        "email": User.email,
        "name": User.name,
        "adv_qty": ...,  # TODO: not implemented
        "active_ads_qty": ...,  # TODO: not implemented
    }

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def _get_sort_column(self, sort_by):
        return self.SORT_MAP[sort_by]

    def get_user_by_id(self, db, user_id):
        return self.user_repository.get_user_by_id(db, user_id)

    def get_users_list(
        self, db: Session, data: UsersRequest
    ) -> tuple[list[User], int]:
        total = self.user_repository.get_users_qty_by_role(db, data.role)

        adv_qty = 0
        active_ads_qty = 0
        if data.role == UserRole.agent:
            adv_qty = self.user_repository.get_related_estate_qty(db)
            active_ads_qty = (
                self.user_repository.get_related_active_estate_qty(db)
            )

        sort_column = self._get_sort_column(data.sort_by)
        return ..., total  # TODO: not implemented

    def delete_user_by_id(self, db, user_id):
        return self.user_repository.delete_user_by_id(db, user_id)

    def ensure_has_rights(
        self, session: Session, requester_id: UUID, *roles: UserRole
    ) -> None:
        requester = self.get_user_by_id(session, requester_id)
        if requester.role not in roles:
            raise ForbiddenError()
