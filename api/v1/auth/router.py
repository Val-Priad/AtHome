from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from di import auth_service, email_verification_service
from exceptions.user import UserAlreadyExistsError, UserNotFoundError
from infrastructure.db import session

from .auth_schema import RegisterRequest, SendNewValidationTokenRequest

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@bp.post("/resend-verification")
def resend_token():
    db = session()
    try:
        data = SendNewValidationTokenRequest.model_validate(request.json)

        user = email_verification_service.get_user_by_email(db, data.email)

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
            f"There is no user with email {e.email}, register first",
            status=400,
        )
    except Exception:
        db.rollback()
        current_app.logger.exception("Resend validation token error")
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()


# TODO create route for validating user's email


@bp.post("/register")
def register():
    db = session()
    try:
        data = RegisterRequest.model_validate(request.json)

        user, raw_token = auth_service.add_user_and_token(
            db, data.email, data.password
        )
        db.commit()
    except ValidationError:
        return construct_response(message="Validation error", status=400)
    except UserAlreadyExistsError:
        return construct_response(
            message="User with such email already exists", status=409
        )
    except Exception:
        db.rollback()
        current_app.logger.exception("User and token creation failed")
        return construct_response(message="Internal server error", status=500)

    email_sent = False
    try:
        email_verification_service.send_verification_email(
            user.email, raw_token
        )
        email_sent = True
    except Exception:
        current_app.logger.exception("Email send failed")

    return construct_response(
        data={"created_user": user.to_dict(), "email_sent": email_sent},
        status=201,
    )
