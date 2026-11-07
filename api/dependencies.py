"""
API Dependencies
Reusable dependencies for authentication, rate limiting, etc.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

# Import auth verification
from api.auth import verify_token

# Security schemes
security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)


# Optional authentication - routes can use this to optionally require auth
def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns username if token is valid, None if no token provided.
    """
    if credentials is None:
        return None

    try:
        username = verify_token(credentials)
        return username
    except HTTPException:
        # Invalid token - treat as no auth
        return None


# Required authentication - routes use this to enforce auth
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Required authentication dependency.
    Raises 401/403 if no valid token provided.
    """
    username = verify_token(credentials)
    return username


# Feature flag checker
def check_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled via environment variable"""
    env_var = f"ENABLE_{feature.upper()}"
    return os.getenv(env_var, "true").lower() == "true"


# Rate limiting helper (placeholder for future implementation)
async def rate_limit_check():
    """
    Rate limiting dependency (placeholder).
    In production, implement with Redis or similar.
    """
    pass
