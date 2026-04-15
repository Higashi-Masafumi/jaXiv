import uuid

import jwt
from fastapi import HTTPException, Request


def verify_supabase_jwt(token: str, jwt_secret: str) -> dict:
    """Verify a Supabase-issued JWT and return its decoded payload.

    Raises HTTPException(401) if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=['HS256'],
            options={'verify_aud': False},
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail='Token has expired.') from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail='Invalid token.') from e


def extract_bearer_token(request: Request) -> str | None:
    """Extract the Bearer token from the Authorization header, or return None."""
    authorization = request.headers.get('Authorization', '')
    if authorization.startswith('Bearer '):
        return authorization[len('Bearer '):]
    return None


def get_user_id_from_payload(payload: dict) -> uuid.UUID:
    """Extract the Supabase user UUID from a decoded JWT payload."""
    sub = payload.get('sub')
    if not sub:
        raise HTTPException(status_code=401, detail='Missing sub claim in token.')
    try:
        return uuid.UUID(sub)
    except ValueError as e:
        raise HTTPException(status_code=401, detail='Invalid user ID in token.') from e
