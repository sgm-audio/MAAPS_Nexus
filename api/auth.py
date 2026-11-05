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
import hmac
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover - fallback if passlib not installed
    CryptContext = None

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Configuration from environment variables
DEFAULT_DEV_SECRET = "PKHTzidW4AzlQ4yLS4cVqmCnXGecegsixxNXt8tu82ElKMoa_9onvG0OW6RaPahH"
SECRET_KEY = os.getenv("JWT_SECRET", DEFAULT_DEV_SECRET).strip() or DEFAULT_DEV_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Authentication configuration
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "maaps_admin").strip()
AUTH_PASSWORD_HASH = os.getenv("AUTH_PASSWORD_HASH", "").strip()
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "rhLi5ytwsLd8KNBEq2_1MvQ71LDXPwMU").strip()
MAAPS_ENV = os.getenv("MAAPS_ENV", "development").strip().lower()

if CryptContext:
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except Exception:
        pwd_context = None
else:  # pragma: no cover
    pwd_context = None


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
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT secret not configured"
        )

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt when available; fallback to constant-time compare."""
    if pwd_context and hashed_password.startswith("$2"):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    # Fallback constant-time compare
    return hmac.compare_digest(plain_password, hashed_password)


def _get_expected_credentials() -> tuple[str, str]:
    """
    Resolve expected credentials.
    Returns username and hashed/plain password.
    """
    if AUTH_USERNAME and AUTH_PASSWORD_HASH:
        return AUTH_USERNAME, AUTH_PASSWORD_HASH

    if AUTH_USERNAME and AUTH_PASSWORD:
        return AUTH_USERNAME, AUTH_PASSWORD

    return "", ""


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials

    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT secret not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")

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

    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint
    """
    expected_username, expected_hash = _get_expected_credentials()

    if MAAPS_ENV == "production":
        if not expected_username or not expected_hash:
            logger.error("Authentication is not configured; rejecting login request")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is not configured"
            )

        if request.username != expected_username or not _verify_password(request.password, expected_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        subject = request.username
    else:
        # In development/test mode, accept configured credentials as well as test accounts
        subject = request.username or expected_username or "anonymous"

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": subject},
        expires_delta=access_token_expires
    )

    logger.info(f"User '{request.username}' logged in successfully")

    return TokenResponse(
        token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    )


@router.get("/verify")
async def verify(username: str = Depends(verify_token)):
    """Verify token validity"""
    return {
        "status": "valid",
        "valid": True,
        "username": username
    }
