from typing import cast

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from sqlalchemy import CursorResult, delete

from exceptions.user import UserAlreadyExistsError, UserNotFoundError
from infrastructure.db import session

from domain.user.user_model import User
from .schemas.auth import RegisterRequest, SendNewValidationTokenRequest
from ....domain.services.auth_service import AuthService
from ....domain.services.email_verification_service import (
    EmailVerificationService,
)

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@bp.post("/resend-verification")
def resend_token():
    try:
        data = SendNewValidationTokenRequest.model_validate(request.json)
        user = EmailVerificationService.get_user_by_email(data.email)
        raw_token = EmailVerificationService.get_resend_token(user.id)
        EmailVerificationService.send_verification_email(user.email, raw_token)
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
        current_app.logger.exception("💥💥💥")
        return construct_response(message="Internal server error", status=500)


# TODO create route for validating user's email


@bp.post("/register")
def register():
    try:
        data = RegisterRequest.model_validate(request.json)
        user, raw_token = AuthService.add_user_and_token(
            data.email, data.password
        )
    except ValidationError:
        return construct_response(message="Validation error", status=400)
    except UserAlreadyExistsError:
        return construct_response(
            message="User with such email already exists", status=409
        )
    except Exception:
        current_app.logger.exception("User and token creation failed")
        return construct_response(message="Internal server error", status=500)

    email_sent = False
    try:
        EmailVerificationService.send_verification_email(user.email, raw_token)
        email_sent = True
    except Exception:
        current_app.logger.exception("Email send failed")

    return construct_response(
        data={"created_user": user.to_dict(), "email_sent": email_sent},
        status=201,
    )


@bp.delete("/delete-test")
def delete_test_user():
    db = session()
    try:
        user = db.get(User, "0476157b-ccee-41fb-9dee-965d7d3c0767")

        if not user:
            return construct_response(message="User not found", status=404)

        db.delete(user)
        db.commit()

        return construct_response(
            data=user, message="User deleted successfully", status=200
        )
    except Exception:
        db.rollback()
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()


@bp.delete("/delete-all-test")
def delete_all_test():
    db = session()
    try:
        result = cast(CursorResult, db.execute(delete(User)))
        db.commit()
        return construct_response(
            message=f"Successfully deleted {result.rowcount} records"
        )

    except Exception:
        db.rollback()
        return construct_response(message="Internal server error", status=500)
    finally:
        db.close()
