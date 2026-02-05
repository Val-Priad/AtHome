from domain.user.user_model import UserRole
from schemas.parent_types import RequestValidation


class RoleRequest(RequestValidation):
    role: UserRole
