from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from di import me_service
from exceptions.error_catalog import get_code_for_exception
from infrastructure.db import session
from schemas.me_schemas import PasswordRequest

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.patch("/update_password")
@jwt_required()
def update_password():
    db = session()
    try:
        data = PasswordRequest.model_validate(request.json)
        user_id = get_jwt_identity()

        me_service.verify_password(db, user_id, data.old_password)

        me_service.ensure_new_password_differs(
            data.old_password, data.new_password
        )

        me_service.update_password(db, user_id, data.new_password)

        db.commit()

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
