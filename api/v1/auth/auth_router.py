from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from di import auth_service, email_verification_service
from exceptions.error_catalog import (
    get_code_for_exception,
    get_description,
)
from exceptions.mailer_exceptions import EmailSendError
from infrastructure.db import session

from .auth_schema import (
    EmailPasswordRequest,
    SendNewValidationTokenRequest,
    VerifyTokenRequest,
)

bp = Blueprint("users", __name__, url_prefix="/api/v1/auth")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def construct_error(code: str):
    description = get_description(code)
    return jsonify(
        {"error": {"code": code, "message": description.message}}
    ), description.status


@bp.post("/login")
def login():
    db = session()
    try:
        data = EmailPasswordRequest.model_validate(request.json)

        user = auth_service.verify_password(db, data.email, data.password)

        access_token = create_access_token(identity=user.id)
        return construct_response(
            data={"access_token": access_token},
            message="Logged in successfully",
            status=200,
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
        data = VerifyTokenRequest.model_validate((request.json))
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


@bp.post("/register")
def register():
    db = session()
    try:
        data = EmailPasswordRequest.model_validate(request.json)

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
        return construct_error("validation_error")
    except EmailSendError:
        return construct_response(
            message="User was created successfully",
            data={"email_sent": False},
            status=201,
        )
    except Exception as e:
        db.rollback()
        return construct_error(get_code_for_exception(e))
    finally:
        db.close()
