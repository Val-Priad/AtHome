from typing import Literal

from pydantic import model_validator

from domain.user.user_model import UserRole
from schemas.parent_types import RequestValidation

BASE_USER_SORT_BY = {
    "created_at",
    "updated_at",
    "email",
    "name",
}

AGENT_SORT_BY = {
    *BASE_USER_SORT_BY,
    "adv_qty",
    "active_ads_qty",
}


class BaseUsersRequest(RequestValidation):
    page: int = 1
    page_size: int = 20

    role: UserRole = UserRole.user

    order: Literal["asc", "desc"] = "desc"
    sort_by: str = "name"

    @model_validator(mode="after")
    def sort_by_for_role(self):
        if (
            self.role == UserRole.user
            and self.sort_by not in BASE_USER_SORT_BY
        ):
            raise ValueError(f"Simple user doesn't have field {self.sort_by}")
        elif self.role == UserRole.agent and self.sort_by not in AGENT_SORT_BY:
            raise ValueError(f"Agent doesn't have field {self.sort_by}")
        return self
