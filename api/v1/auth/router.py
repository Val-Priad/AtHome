from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from di import auth_service, email_verification_service
from exceptions.user import (
    EmailSendError,
    TokenVerificationError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
)
from infrastructure.db import session

from .auth_schema import (
    RegisterRequest,
    SendNewValidationTokenRequest,
    VerifyTokenRequest,
)

bp = Blueprint("users", __name__, url_prefix="/api/v1/auth")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@bp.post("/resend-verification")
def resend_verification():
    db = session()
    try:
        data = SendNewValidationTokenRequest.model_validate(request.json)

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
        return construct_response(message="Validation error", status=400)
    except UserNotFoundError as e:
        return construct_response(
            message=f"There is no user with email {e.email}, register first",
            status=400,
        )
    except UserAlreadyVerifiedError as e:
        return construct_response(
            message=f"User with email {e.email} was already verified",
            status=409,
        )
    except Exception:
        db.rollback()
        current_app.logger.exception("Resend validation token error")
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()


@bp.post("/verify-email")
def verify_token():
    db = session()
    try:
        data = VerifyTokenRequest.model_validate((request.json))
        email_verification_service.verify_token(db, data.token)
        db.commit()
        return construct_response(
            message="Verification is successful", status=200
        )
    except ValidationError:
        return construct_response(message="Validation error", status=400)
    except TokenVerificationError:
        return construct_response(message="Token invalid", status=400)
    except Exception:
        db.rollback()
        current_app.logger.exception("Verify email error")
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()


@bp.post("/register")
def register():
    db = session()
    try:
        data = RegisterRequest.model_validate(request.json)

        user, raw_token = auth_service.add_user_and_token(
            db, data.email, data.password
        )
        db.commit()

        email_verification_service.send_verification_email(
            user.email, raw_token
        )
        return construct_response(
            message="User was created successfully",
            data={"email_sent": True},
            status=201,
        )
    except ValidationError:
        return construct_response(message="Validation error", status=400)
    except UserAlreadyExistsError:
        return construct_response(
            message="User with such email already exists", status=409
        )
    except EmailSendError:
        return construct_response(
            message="User was created successfully",
            data={"email_sent": False},
            status=201,
        )
    except Exception:
        db.rollback()
        current_app.logger.exception("User and token creation failed")
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()
