from typing import cast

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import CursorResult, delete

from db import session
from exceptions.user import UserAlreadyExistsError

from .models.user import User
from .services.auth_service import AuthService
from .services.email_verification_service import EmailVerificationService

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


# TODO create route for asking new email verification token

# TODO create route for validating user's email


@bp.post("/register")
def register():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    # TODO create validation schema
    if not email:
        return construct_response(message="Missing email", status=400)
    if not password:
        return construct_response(message="Missing password", status=400)

    try:
        user = AuthService.register_user(email, password)

    except UserAlreadyExistsError:
        return construct_response(
            message="User with such email already exists", status=409
        )
    except Exception:
        current_app.logger.exception("💥💥💥")
        return construct_response(message="Internal server error", status=500)

    email_sent = False
    try:
        token = EmailVerificationService.generate_verification_token(user.id)
        EmailVerificationService.send_verification_email(user.email, token)
        email_sent = True
    except Exception:
        current_app.logger.exception("💥💥💥")
        return construct_response(message="Internal server error", status=500)

    return construct_response(
        data={"created_user": user.to_dict(), "email_sent": email_sent},
        status=201,
    )


@bp.get("/hello")
def hello():
    current_app.logger.info("Amogus")
    return construct_response(message="Hello Flask")


@bp.post("/add-test")
def add_test_user():
    db = session()
    try:
        user = User(name="Valera", age=19)
        db.add(user)
        db.commit()
        db.refresh(user)
        return construct_response(
            data=user.to_dict(),
            message="User was created successfully",
            status=201,
        )
    except Exception:
        db.rollback()
        return construct_response(message="Internal server error", status=500)

    finally:
        db.close()


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
