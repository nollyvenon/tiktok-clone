"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import uuid

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> tuple[str, str]:
    """
    Create a JWT access token

    Returns:
        tuple: (token, jti) - JWT token and JWT ID for revocation tracking
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    jti = str(uuid.uuid4())

    to_encode = {
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "exp": expire,
        "jti": jti,
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt, jti


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """
    Create a JWT refresh token

    Returns:
        tuple: (token, jti) - JWT token and JWT ID for revocation tracking
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)

    jti = str(uuid.uuid4())

    to_encode = {
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "exp": expire,
        "jti": jti,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt, jti


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Returns:
        dict: Token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(secrets.randbelow(1000000)).zfill(6)


def generate_random_token(length: int = 32) -> str:
    """Generate a random token (for password reset, etc)"""
    return secrets.token_urlsafe(length)


def verify_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

    if len(password) > settings.PASSWORD_MAX_LENGTH:
        return False, f"Password must not exceed {settings.PASSWORD_MAX_LENGTH} characters"

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        return False, "Password must contain at least one special character"

    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format

    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must not exceed 50 characters"

    if not username.replace("_", "").replace("-", "").isalnum():
        return False, "Username can only contain letters, numbers, hyphens, and underscores"

    return True, None
