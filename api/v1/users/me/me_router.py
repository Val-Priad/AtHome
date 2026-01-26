from uuid import UUID

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from di import me_service
from infrastructure.db import get_session
from schemas.me_schemas import PasswordRequest, UpdateUserPersonalDataRequest

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.patch("/update_password")
@jwt_required()
def update_password():
    db = get_session()
    try:
        data = PasswordRequest.model_validate(request.json)
        user_id = UUID(get_jwt_identity())

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
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()


@bp.patch("/update-personal-data")
@jwt_required()
def update_personal_data():
    db = get_session()
    try:
        data = UpdateUserPersonalDataRequest.model_validate(request.json)
        user_id = UUID(get_jwt_identity())
        user = me_service.update_personal_data(db, user_id, data)
        db.commit()
        db.refresh(user)
        return construct_response(
            data=user.to_dict(),
            message="User personal data was updated successfully",
        )
    except ValidationError:
        current_app.logger.exception("Validation error")
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()
