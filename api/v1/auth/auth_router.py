from flask import (
    Blueprint,
    jsonify,
    request,
)
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from di import auth_service, email_verification_service, password_reset_service
from exceptions import UserAlreadyExistsError
from infrastructure.db import db_session, get_session
from infrastructure.rate_limiting.limiter_config import limiter
from schemas.auth_schemas import (
    EmailPasswordRequest,
    EmailRequest,
    TokenPasswordRequest,
    TokenRequest,
)
from flask import current_app

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@bp.post("/register")
@limiter.limit("5/minute")
def register():
    try:
        data = EmailPasswordRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

    try:
        with db_session() as session:
            user = auth_service.create_user(session, data.email, data.password)

            raw_token = email_verification_service.create_token(
                session,
                user.id,
            )

            email_verification_service.send_verification_email(
                user.email, raw_token
            )
    except UserAlreadyExistsError:
        pass
    except Exception as e:
        current_app.logger.exception("Registration error")
        return construct_error(e)

    return construct_response(
        message="If there was no user, it was created, following instructions were sent to an email",
        status=202,
    )


@bp.post("/verify-email")
def verify_token():
    db = get_session()
    try:
        data = TokenRequest.model_validate((request.json))

        email_verification_service.verify_token(db, data.token)

        db.commit()
        return construct_response(
            message="Verification is successful", status=200
        )
    except ValidationError:
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()


@bp.post("/resend-verification")  # TODO enumeration vulnerability
def resend_verification():
    db = get_session()
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
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()


@bp.post("/login")  # TODO enumeration vulnerability
def login():
    db = get_session()
    try:
        data = EmailPasswordRequest.model_validate(request.json)

        user = auth_service.verify_password(db, data.email, data.password)

        access_token = create_access_token(identity=str(user.id), fresh=True)
        response = construct_response(
            message="Logged in successfully",
            status=200,
        )
        set_access_cookies(response, access_token)
        return response
    except ValidationError:
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()


@bp.post("/logout")
@jwt_required()
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)

    return response


@bp.post("/reset-password")  # TODO enumeration vulnerability
def reset_password():
    db = get_session()
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
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()


@bp.post("/verify-new-password")
def verify_new_password():
    db = get_session()
    try:
        data = TokenPasswordRequest.model_validate(request.json)

        password_reset_service.reset_password(db, data.token, data.password)

        db.commit()
        return construct_response(
            message="Password reset successfully", status=200
        )
    except ValidationError:
        return construct_error(code="validation_error")
    except Exception as e:
        db.rollback()
        return construct_error(e)
    finally:
        db.close()
