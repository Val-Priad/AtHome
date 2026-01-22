from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from domain.user.services.me_service import MeService
from exceptions.error_catalog import get_code_for_exception
from infrastructure.db import session
from schemas.me_schema import PasswordRequest

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.patch("/update_password")
@jwt_required(fresh=True)
def update_password():
    db = session()
    try:
        data = PasswordRequest.model_validate(request.json)
        user_id = get_jwt_identity()

        return construct_response(
            message="Password was updated successfully", status=200
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()
