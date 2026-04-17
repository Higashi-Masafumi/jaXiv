import uuid
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException
from logging import getLogger

from .config import get_auth_config

logger = getLogger(__name__)


@lru_cache
def get_jwks_client() -> PyJWKClient:
	return PyJWKClient(get_auth_config().jwks_url, cache_keys=True)


def verify_supabase_jwt(token: str) -> dict:
	"""Verify a Supabase-issued JWT using JWKS and return its decoded payload.

	Raises HTTPException(401) if the token is invalid or expired.
	"""
	try:
		signing_key = get_jwks_client().get_signing_key_from_jwt(token)
		return jwt.decode(
			token,
			signing_key.key,
			algorithms=['ES256', 'RS256'],
			options={'verify_aud': False},
		)
	except jwt.ExpiredSignatureError as e:
		raise HTTPException(status_code=401, detail='Token has expired.') from e
	except jwt.InvalidTokenError as e:
		raise HTTPException(status_code=401, detail='Invalid token.') from e


def get_user_id_from_payload(payload: dict) -> uuid.UUID:
	"""Extract the Supabase user UUID from a decoded JWT payload."""
	sub = payload.get('sub')
	if not sub:
		logger.error('Missing sub claim in token.')
		raise HTTPException(status_code=401, detail='Missing sub claim in token.')
	try:
		logger.info('Extracting user ID from token payload: %s', sub)
		return uuid.UUID(sub)
	except ValueError as e:
		logger.error('Invalid user ID in token.')
		raise HTTPException(status_code=401, detail='Invalid user ID in token.') from e
