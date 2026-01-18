from flask import (
    Blueprint,
    Response,
    jsonify,
    make_response,
    request,
)
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from pydantic import ValidationError

from di import auth_service, email_verification_service, password_reset_service
from exceptions.error_catalog import (
    get_code_for_exception,
    get_description,
)
from infrastructure.db import session

from .auth_schema import (
    EmailPasswordRequest,
    EmailRequest,
    TokenPasswordRequest,
    TokenRequest,
)

bp = Blueprint("users", __name__, url_prefix="/api/v1/auth")


def construct_response(data=None, message="OK", status=200) -> Response:
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return make_response(jsonify(payload), status)


def construct_error(code: str) -> Response:
    description = get_description(code)
    return make_response(
        jsonify({"error": {"code": code, "message": description.message}}),
        description.status,
    )


@bp.post("/register")
def register():
    db = session()
    try:
        data = EmailPasswordRequest.model_validate(request.json)

        user, raw_token = auth_service.add_user_and_token(
            db, data.email, data.password
        )

        email_verification_service.send_verification_email(
            user.email, raw_token
        )
        db.commit()
        return construct_response(
            message="User was created successfully",
            status=201,
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()


@bp.post("/verify-email")
def verify_token():
    db = session()
    try:
        data = TokenRequest.model_validate((request.json))
        email_verification_service.verify_token(db, data.token)
        db.commit()
        return construct_response(
            message="Verification is successful", status=200
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()


@bp.post("/resend-verification")
def resend_verification():
    db = session()
    try:
        data = EmailRequest.model_validate(request.json)
        user = email_verification_service.get_user_by_email(db, data.email)
        email_verification_service.check_user_is_not_verified(user)
        raw_token = email_verification_service.get_resend_token(db, user.id)

        db.commit()

        email_verification_service.send_verification_email(
            user.email, raw_token
        )

        return construct_response(
            message="Check your email for confirmation link", status=201
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()


@bp.post("/login")
def login():
    db = session()
    try:
        data = EmailPasswordRequest.model_validate(request.json)

        user = auth_service.verify_password(db, data.email, data.password)

        access_token = create_access_token(identity=user.id, fresh=True)
        response = construct_response(
            message="Logged in successfully",
            status=200,
        )
        set_access_cookies(response, access_token)
        return response
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()


@bp.post("/logout")
@jwt_required()
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response


@bp.post("/reset-password")
def reset_password():
    db = session()
    try:
        data = EmailRequest.model_validate(request.json)
        user = password_reset_service.get_user_by_email(db, data.email)
        raw_token = password_reset_service.get_token(db, user.id)

        db.commit()

        password_reset_service.send_reset_password_email(data.email, raw_token)

        return construct_response(
            message="Check your email for change password link", status=201
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()


@bp.post("/verify-new-password")
def verify_new_password():
    db = session()
    try:
        data = TokenPasswordRequest.model_validate(request.json)
        password_reset_service.reset_password(db, data.token, data.password)
        db.commit()
        return construct_response(
            message="Password reset successfully", status=200
        )
    except ValidationError:
        return construct_error("validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()
