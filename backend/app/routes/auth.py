"""
Authentication API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    RefreshTokenRequest, LogoutRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, ErrorResponse,
    SendOTPRequest, VerifyOTPRequest, TwoFactorSetupRequest, TwoFactorVerifyRequest
)
from app.services.auth import AuthService
from app.security import verify_token
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user

    Args:
        authorization: Authorization header (Bearer token)
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = parts[1]

    user = await AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


# ============================================================================
# Public Routes
# ============================================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        409: {"model": ErrorResponse, "description": "Email or username already exists"},
    },
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user

    **Request body:**
    - email: Valid email address
    - username: 3-50 characters, alphanumeric + underscore/hyphen
    - password: Minimum 8 characters with uppercase, lowercase, digit, special character
    - first_name: Optional
    - last_name: Optional
    """
    try:
        user, access_token, refresh_token = await AuthService.register(db, request)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=86400,  # 24 hours in seconds
            user=UserResponse.from_orm(user),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user with email and password

    **Request body:**
    - email: User email
    - password: User password

    **Returns:**
    - access_token: JWT access token (24 hour expiry)
    - refresh_token: JWT refresh token (7 day expiry)
    - user: User information
    """
    try:
        # Extract device info from request
        user_agent = http_request.headers.get("user-agent", "")
        client_host = http_request.client.host if http_request.client else None

        user, access_token, refresh_token = await AuthService.login(
            db,
            request,
            ip_address=client_host,
            user_agent=user_agent,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=86400,  # 24 hours in seconds
            user=UserResponse.from_orm(user),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post(
    "/refresh",
    response_model=dict,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token

    **Request body:**
    - refresh_token: Valid refresh token

    **Returns:**
    - access_token: New JWT access token
    - refresh_token: New JWT refresh token
    - expires_in: Token expiry time in seconds
    """
    try:
        access_token, refresh_token = await AuthService.refresh_access_token(
            db,
            request.refresh_token,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post(
    "/password-reset",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password reset email sent"},
    },
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset - sends reset email

    **Request body:**
    - email: User email

    **Note:** Returns success regardless of whether email exists (security)
    """
    try:
        await AuthService.request_password_reset(db, request)
        return {"message": "Password reset email sent if account exists"}
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        return {"message": "Password reset email sent if account exists"}


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password reset successfully"},
        400: {"model": ErrorResponse, "description": "Invalid token or password"},
    },
)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm password reset with token

    **Request body:**
    - token: Password reset token from email
    - new_password: New password
    - confirm_password: Confirm new password
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    try:
        await AuthService.reset_password(
            db,
            request.token,
            request.new_password,
        )
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


# ============================================================================
# Protected Routes
# ============================================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def logout(
    current_user: User = Depends(get_current_user),
    request: Optional[LogoutRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user

    **Authorization:** Requires valid access token in header

    **Request body (optional):**
    - refresh_token: Optional refresh token (will be invalidated)
    """
    try:
        await AuthService.logout(db, current_user.id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Current user information"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user information

    **Authorization:** Requires valid access token in header
    """
    return UserResponse.from_orm(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password changed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid password"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user password

    **Authorization:** Requires valid access token in header

    **Request body:**
    - current_password: Current password
    - new_password: New password
    - confirm_password: Confirm new password
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    try:
        await AuthService.change_password(db, current_user.id, request)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


# ============================================================================
# OTP & Two-Factor Authentication
# ============================================================================

@router.post(
    "/otp/send",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP sent successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def send_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda auth=Header(None), db=Depends(get_db): get_current_user(auth, db) if auth else None),
):
    """
    Send OTP code for phone/email verification

    **Optional Authorization:** Requires access token for authenticated users

    **Request body:**
    - phone_number: Phone number to verify
    - email: Email to verify
    """
    try:
        user_id = current_user.id if current_user else None
        otp_code = await AuthService.send_otp(
            db,
            phone_number=request.phone_number if request.phone_number else None,
            email=request.email,
            user_id=user_id,
        )
        return {
            "message": "OTP sent successfully",
            "otp_code": otp_code,  # Return for dev/testing only - remove in production
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP",
        )


@router.post(
    "/otp/verify",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid OTP"},
    },
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda auth=Header(None), db=Depends(get_db): get_current_user(auth, db) if auth else None),
):
    """
    Verify OTP code

    **Request body:**
    - code: 6-digit OTP code
    - phone_number: Phone number (if verifying phone)
    - email: Email address (if verifying email)
    """
    try:
        user_id = current_user.id if current_user else None
        await AuthService.verify_otp(
            db,
            code=request.code,
            phone_number=request.phone_number,
            email=request.email,
            user_id=user_id,
        )
        return {"message": "OTP verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed",
        )


@router.post(
    "/2fa/setup",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "2FA setup initiated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Setup 2FA (TOTP) for account

    **Authorization:** Requires valid access token in header

    Returns QR code URI for authenticator app (Google Authenticator, Authy, etc.)
    """
    try:
        qr_code_uri = await AuthService.setup_two_factor(db, current_user.id)
        return {
            "message": "2FA setup initiated",
            "qr_code_uri": qr_code_uri,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA setup failed",
        )


@router.post(
    "/2fa/verify",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "2FA verified and enabled"},
        400: {"model": ErrorResponse, "description": "Invalid code"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify 2FA code and enable 2FA

    **Authorization:** Requires valid access token in header

    **Request body:**
    - code: 6-digit code from authenticator app
    """
    try:
        await AuthService.verify_two_factor(db, current_user.id, request.code)
        return {"message": "2FA enabled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"2FA verify error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA verification failed",
        )


@router.post(
    "/2fa/disable",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "2FA disabled"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable 2FA for account

    **Authorization:** Requires valid access token in header
    """
    try:
        await AuthService.disable_two_factor(db, current_user.id)
        return {"message": "2FA disabled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA disable failed",
        )
