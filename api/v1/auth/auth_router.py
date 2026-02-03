from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)

from api.v1.responses import construct_error, construct_response
from di import auth_service, email_verification_service, password_reset_service
from exceptions.custom_exceptions.mailer_exceptions import EmailSendError
from exceptions.custom_exceptions.user_exceptions import (
    InvalidCredentialsError,
    PasswordVerificationError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserIsNotVerifiedError,
    UserNotFoundError,
)
from infrastructure.db import db_session
from infrastructure.rate_limiting.limiter_config import limiter
from schemas.auth_schemas.auth_requests import (
    EmailPasswordRequest,
    EmailRequest,
    TokenPasswordRequest,
    TokenRequest,
)

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@bp.post("/register")
@limiter.limit("2/minute")
def register():
    data = EmailPasswordRequest.from_request(request.json)

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
    except (UserAlreadyExistsError, EmailSendError):
        pass
    return construct_response(
        message="If there was no user, it was created, following instructions were sent to an email",
        status=202,
    )


@bp.post("/verify-email")
def verify_token():
    data = TokenRequest.from_request((request.json))

    with db_session() as session:
        email_verification_service.verify_token(session, data.token)

    return construct_response()


@bp.post("/resend-verification")
@limiter.limit("2/minute")
def resend_verification():
    data = EmailRequest.from_request(request.json)

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
    except (UserNotFoundError, UserAlreadyVerifiedError, EmailSendError):
        pass

    return construct_response(
        message="If the user exists and is not verified, a verification email has been sent",
        status=202,
    )


@bp.post("/login")
def login():
    data = EmailPasswordRequest.from_request(request.json)

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
        return construct_error(InvalidCredentialsError())
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
    data = EmailRequest.from_request(request.json)

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

    return construct_response(
        message="If user exists, password reset has been sent", status=202
    )


@bp.post("/verify-new-password")
def verify_new_password():
    data = TokenPasswordRequest.from_request(request.json)

    with db_session() as session:
        password_reset_service.reset_password(
            session, data.token, data.password
        )
    return construct_response()


@bp.errorhandler(Exception)
def handle_exception(e: Exception):
    return construct_error(e)
