import bcrypt

from exceptions import PasswordVerificationError


class PasswordHasher:
    @staticmethod
    def hash_password(raw_password: str) -> bytes:
        return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt())

    @staticmethod
    def check_password(raw_password: str, hashed_password: bytes) -> None:
        if not bcrypt.checkpw(raw_password.encode(), hashed_password):
            raise PasswordVerificationError()
