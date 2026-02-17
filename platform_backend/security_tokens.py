"""Token utilities for Milestone 1 auth flows.

- We store ONLY hashes of one-time tokens (email verify / password reset)
- Refresh tokens are stored as hashes too (rotation + revocation)

All hashes are SHA-256 over the raw token.
"""

import hashlib
import secrets


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def new_token_urlsafe(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def token_hash(token: str) -> str:
    return _sha256_hex(token)
