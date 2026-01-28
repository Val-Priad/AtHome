from uuid import UUID

from flask import Blueprint
from flask_jwt_extended import jwt_required

from api.v1.responses import construct_error, construct_response
from di import admin_users_service
from domain.user.user_model import UserRole
from infrastructure.db import db_session
from infrastructure.jwt.jwt_utils import get_jwt_user_uuid

bp = Blueprint("admin_users", __name__, url_prefix="/api/v1/admin/users")


@bp.get("/<uuid:user_id>")
@jwt_required()
def get_user(user_id: UUID):
    try:
        requester_id = get_jwt_user_uuid()

        with db_session() as session:
            admin_users_service.ensure_has_rights(
                session, requester_id, UserRole.admin
            )
            user = admin_users_service.get_user_by_id(session, user_id)

        return construct_response(data=user.to_dict())
    except Exception as e:
        return construct_error(e)
