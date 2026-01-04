from flask import Blueprint, jsonify
from db import session
from .models import User
from sqlalchemy import delete, CursorResult
from typing import cast

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def construct_response(data=None, message="OK", status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@bp.get("/hello")
def hello():
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
