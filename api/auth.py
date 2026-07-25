"""
Authentication Module
JWT-based authentication for API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging
import os
from .user_db import user_db

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

ALGORITHM = "HS256"

# Placeholder / default values that must never be used for JWT signing
_FORBIDDEN_SECRETS = frozenset(
    {
        "",
        "your-secret-key-change-in-production",
        "change-me-before-deploying",
        "change-me",
        "changeme",
        "secret",
        "secret-key",
        "replace-with-a-long-random-secret",
    }
)


def _parse_token_expire_minutes() -> int:
    raw = (os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60").strip() or "60"
    try:
        minutes = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer"
        ) from exc
    if minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer")
    return minutes


ACCESS_TOKEN_EXPIRE_MINUTES = _parse_token_expire_minutes()


def _is_forbidden_secret(key: str) -> bool:
    return not key or key.lower() in _FORBIDDEN_SECRETS


def _load_secret_key() -> str:
    """Load JWT secret from env; refuse placeholder/default values.

    Tries SECRET_KEY first, then API_SECRET_KEY if the first is missing/forbidden.
    """
    for env_name in ("SECRET_KEY", "API_SECRET_KEY"):
        key = (os.getenv(env_name) or "").strip()
        if key and not _is_forbidden_secret(key):
            return key
    raise RuntimeError(
        "SECRET_KEY (or API_SECRET_KEY) must be set to a non-placeholder value. "
        "Refusing to start with a default/forgeable JWT secret."
    )


SECRET_KEY = _load_secret_key()


class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""

    token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return username

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint

    Validates credentials against the user database with hashed passwords.
    """
    # Validate credentials
    if not request.username or not request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Authenticate user against database
    user = user_db.authenticate(request.username, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )

    logger.info(f"User '{request.username}' logged in successfully")

    return TokenResponse(
        token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    )


@router.get("/verify")
async def verify(username: str = Depends(verify_token)):
    """Verify token validity"""
    return {"status": "valid", "username": username}
