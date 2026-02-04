from typing import Literal

from domain.admin.admin_types import BaseUserSortBy
from domain.user.user_model import UserRole
from schemas.parent_types import RequestValidation


class UsersRequest(RequestValidation):
    page: int = 1
    page_size: int = 20

    role: UserRole = UserRole.user

    order: Literal["asc", "desc"] = "desc"
    sort_by: BaseUserSortBy = "name"
