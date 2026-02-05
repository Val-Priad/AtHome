from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from api.v1.responses import construct_error, construct_response
from di import admin_users_service
from domain.user.user_model import UserRole
from infrastructure.db import db_session
from infrastructure.jwt.jwt_utils import get_jwt_user_uuid
from schemas.admin_schemas.admin_users_schemas.admin_users_requests import (
    RoleRequest,
)
from schemas.admin_schemas.admin_users_schemas.admin_users_responses import (
    UserResponse,
)

bp = Blueprint("admin_users", __name__, url_prefix="/api/v1/admin/users")


@bp.get("/<uuid:user_id>")
@jwt_required()
def get_user(user_id: UUID):
    requester_id = get_jwt_user_uuid()

    with db_session() as session:
        admin_users_service.ensure_has_rights(
            session, requester_id, UserRole.admin
        )
        user = admin_users_service.get_user_by_id(session, user_id)

        return construct_response(data=UserResponse.from_model(user))


@bp.patch("/<uuid:user_id>/role")
@jwt_required()
def change_user_role(user_id: UUID):
    requester_id = get_jwt_user_uuid()

    data = RoleRequest.from_request(request.json)

    with db_session() as session:
        admin_users_service.change_user_role(
            session, requester_id, user_id, data.role
        )

        return construct_response()


@bp.delete("/<uuid:user_id>")
@jwt_required()
def delete_user(user_id: UUID):
    requester_id = get_jwt_user_uuid()

    with db_session() as session:
        admin_users_service.ensure_has_rights(
            session, requester_id, UserRole.admin
        )

        admin_users_service.delete_user_by_id(session, user_id)

        return construct_response()


@bp.errorhandler(Exception)
def handle_exception(e: Exception):
    return construct_error(e)


# TODO: 4.
# read users list (GDPR safe fields only)
# add filters for users list
# add sorting for users list
# TODO: 1. change user role to specified
# add sorting for users list
# TODO: 1. change user role to specified
