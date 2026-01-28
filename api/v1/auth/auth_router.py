from flask import Blueprint, current_app, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from di import auth_service, email_verification_service, password_reset_service
from exceptions.mailer_exceptions import EmailSendError
from exceptions.user_exceptions import (
    PasswordVerificationError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserIsNotVerifiedError,
    UserNotFoundError,
)
from infrastructure.db import db_session
from infrastructure.rate_limiting.limiter_config import limiter
from schemas.auth_schemas import (
    EmailPasswordRequest,
    EmailRequest,
    TokenPasswordRequest,
    TokenRequest,
)

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@bp.post("/register")
@limiter.limit("2/minute")
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
    except EmailSendError:
        current_app.logger.exception("Registration email send failed")
    except Exception as e:
        current_app.logger.exception("Registration error")
        return construct_error(e)

    return construct_response(
        message="If there was no user, it was created, following instructions were sent to an email",
        status=202,
    )


@bp.post("/verify-email")
def verify_token():
    try:
        data = TokenRequest.model_validate((request.json))
    except ValidationError:
        return construct_error(code="validation_error")

    try:
        with db_session() as session:
            email_verification_service.verify_token(session, data.token)
    except Exception as e:
        current_app.logger.exception("Verify email token error")
        return construct_error(e)

    return construct_response()


@bp.post("/resend-verification")
@limiter.limit("2/minute")
def resend_verification():
    try:
        data = EmailRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

    try:
        with db_session() as session:
            user = email_verification_service.get_user_by_email(
                session, data.email
            )
            email_verification_service.ensure_user_is_not_verified(user)
            raw_token = email_verification_service.get_resend_token(
                session, user.id
            )

            email_verification_service.send_verification_email(
                user.email, raw_token
            )
    except (UserNotFoundError, UserAlreadyVerifiedError):
        pass
    except EmailSendError:
        current_app.logger.exception("Resend verification email failed")
    except Exception as e:
        current_app.logger.exception("Resend verification error")
        return construct_error(e)

    return construct_response(
        message="If the user exists and is not verified, a verification email has been sent",
        status=202,
    )


@bp.post("/login")
def login():
    try:
        data = EmailPasswordRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")
    try:
        with db_session() as session:
            user = auth_service.verify_password(
                session, data.email, data.password
            )
            user_id = user.id

    except (
        UserNotFoundError,
        UserIsNotVerifiedError,
        PasswordVerificationError,
    ):
        return construct_error(code="invalid_credentials")
    except Exception as e:
        current_app.logger.exception("Login error")
        return construct_error(e)

    access_token = create_access_token(identity=str(user_id), fresh=True)
    response = construct_response()
    set_access_cookies(response, access_token)
    return response


@bp.post("/logout")
@jwt_required()
def logout():
    response = construct_response()
    unset_jwt_cookies(response)
    return response


@bp.post("/reset-password")
@limiter.limit("2/minute")
def reset_password():
    try:
        data = EmailRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")
    try:
        with db_session() as session:
            user = password_reset_service.get_user_by_email(
                session, data.email
            )
            raw_token = password_reset_service.get_token(session, user.id)

            password_reset_service.send_reset_password_email(
                data.email, raw_token
            )
    except (UserNotFoundError, EmailSendError):
        pass
    except Exception as e:
        current_app.logger.exception("Reset password error")
        return construct_error(e)

    return construct_response(
        message="If user exists, password reset has been sent", status=202
    )


@bp.post("/verify-new-password")
def verify_new_password():
    try:
        data = TokenPasswordRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")
    try:
        with db_session() as session:
            password_reset_service.reset_password(
                session, data.token, data.password
            )
    except Exception as e:
        current_app.logger.exception("Verify new password error")
        return construct_error(e)

    return construct_response()
