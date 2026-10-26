import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt

from ..core.errors import AppError
from ..core.ids import utcnow


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 600_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        parts = encoded.split("$")
        if len(parts) == 2:  # Existing account hash compatibility for explicit migration.
            iterations, salt, expected = 100_000, parts[0], parts[1]
        elif len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations, salt, expected = int(parts[1]), parts[2], parts[3]
        else:
            return False
        if not 100_000 <= iterations <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        return hmac.compare_digest(actual.hex(), expected)
    except (TypeError, ValueError):
        return False


def check_secret(settings):
    if len(settings.auth_secret) < 32:
        raise AppError(503, "AUTH_CONFIGURATION_BLOCKED", "OW_AUTH_SECRET에 최소 32자 비밀값을 설정해야 합니다.")


def create_token(user, settings) -> str:
    check_secret(settings)
    now = utcnow()
    return jwt.encode({"sub": user.id, "iat": now, "exp": now + timedelta(seconds=settings.token_ttl_seconds),
                       "ver": user.token_version, "iss": "ontology-wiki"}, settings.auth_secret, algorithm="HS256")


def decode_token(token: str, settings) -> dict:
    check_secret(settings)
    try:
        return jwt.decode(token, settings.auth_secret, algorithms=["HS256"], issuer="ontology-wiki",
                          options={"require": ["sub", "exp", "iat", "ver"]})
    except jwt.PyJWTError:
        raise AppError(401, "INVALID_TOKEN", "인증 토큰이 유효하지 않거나 만료되었습니다.") from None
