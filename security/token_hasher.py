import hashlib
import secrets


class TokenHasher:
    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(raw_token: str) -> bytes:
        return hashlib.sha256(raw_token.encode()).digest()
