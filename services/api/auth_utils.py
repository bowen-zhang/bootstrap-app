import datetime
import jwt

from shared.settings import settings


def create_access_token(user_id: str, extra_claims: dict = None) -> str:
    payload = {
        "sub": user_id,  # Subject (User ID)
        "type": "access",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=settings.jwt_settings.access_token_expiration_seconds),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
        
    return jwt.encode(payload, settings.jwt_settings.secret, algorithm=settings.jwt_settings.algorithm)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=settings.jwt_settings.refresh_token_expiration_seconds),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_settings.secret, algorithm=settings.jwt_settings.algorithm)


def validate_access_token(token: str) -> dict:
    return _validate_token(token, expected_type="access")


def validate_refresh_token(token: str) -> dict:
    return _validate_token(token, expected_type="refresh")


def _validate_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_settings.secret, algorithms=[settings.jwt_settings.algorithm])
        if payload.get("type") != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError(f"{expected_type.capitalize()} token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid {expected_type} token")