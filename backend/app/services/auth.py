"""
Authentication service for user authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import uuid

from app.models import User, Session, OAuthToken, PasswordReset, UserRole
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    PasswordChangeRequest, PasswordResetRequest
)
from app.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_token, validate_password, validate_username, verify_email,
    generate_random_token
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def register(
        db: AsyncSession,
        request: RegisterRequest,
    ) -> Tuple[User, str, str]:
        """
        Register a new user

        Args:
            db: Database session
            request: Registration request data

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ValueError: If email/username already exists or validation fails
        """
        # Validate email
        if not verify_email(request.email):
            raise ValueError("Invalid email format")

        # Validate username
        is_valid, error_msg = validate_username(request.username)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate password
        is_valid, error_msg = validate_password(request.password)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if email already exists
        existing_email = await db.execute(
            select(User).where(User.email == request.email).where(User.deleted_at == None)
        )
        if existing_email.scalar():
            raise ValueError("Email already registered")

        # Check if username already exists
        existing_username = await db.execute(
            select(User).where(User.username == request.username)
        )
        if existing_username.scalar():
            raise ValueError("Username already taken")

        # Create user
        user = User(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            is_active=True,
            role=UserRole.USER,
        )

        db.add(user)
        await db.flush()
        await db.commit()
        await db.refresh(user)

        logger.info(f"User registered: {user.id}")

        # Create tokens
        access_token, access_jti = create_access_token(user.id)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # Create session
        session = Session(
            user_id=user.id,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            is_active=True,
        )
        db.add(session)
        await db.commit()

        return user, access_token, refresh_token

    @staticmethod
    async def login(
        db: AsyncSession,
        request: LoginRequest,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """
        Login user with email and password

        Args:
            db: Database session
            request: Login request data
            device_id: Device identifier
            device_name: Device name
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request.email).where(User.deleted_at == None)
        )
        user = result.scalar()

        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is inactive")

        # Create tokens
        access_token, access_jti = create_access_token(user.id)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # Create session
        session = Session(
            user_id=user.id,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            is_active=True,
        )
        db.add(session)

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"User logged in: {user.id}")

        return user, access_token, refresh_token

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token

        Args:
            db: Database session
            refresh_token: Refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            ValueError: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid or expired refresh token")

        user_id = UUID(payload.get("sub"))
        jti = payload.get("jti")

        # Find session
        result = await db.execute(
            select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.refresh_token_jti == jti,
                    Session.is_active == True,
                )
            )
        )
        session = result.scalar()

        if not session:
            raise ValueError("Session not found or invalid")

        # Create new tokens
        new_access_token, new_access_jti = create_access_token(user_id)
        new_refresh_token, new_refresh_jti = create_refresh_token(user_id)

        # Update session
        session.access_token_jti = new_access_jti
        session.refresh_token_jti = new_refresh_jti
        session.last_activity = datetime.utcnow()
        await db.commit()

        logger.info(f"Token refreshed for user: {user_id}")

        return new_access_token, new_refresh_token

    @staticmethod
    async def logout(
        db: AsyncSession,
        user_id: UUID,
        session_id: Optional[UUID] = None,
    ) -> None:
        """
        Logout user - invalidate session(s)

        Args:
            db: Database session
            user_id: User ID
            session_id: Specific session ID to invalidate (if None, all sessions)
        """
        if session_id:
            # Logout from specific session
            result = await db.execute(
                select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.user_id == user_id,
                    )
                )
            )
            session = result.scalar()
            if session:
                session.is_active = False
        else:
            # Logout from all sessions
            result = await db.execute(
                select(Session).where(Session.user_id == user_id)
            )
            sessions = result.scalars().all()
            for session in sessions:
                session.is_active = False

        await db.commit()
        logger.info(f"User logged out: {user_id}")

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        access_token: str,
    ) -> Optional[User]:
        """
        Get current user from access token

        Args:
            db: Database session
            access_token: JWT access token

        Returns:
            User object or None if invalid
        """
        # Verify token
        payload = verify_token(access_token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user_id = UUID(user_id)
        except ValueError:
            return None

        # Find user
        result = await db.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.is_active == True,
                    User.deleted_at == None,
                )
            )
        )
        user = result.scalar()

        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: UUID,
        request: PasswordChangeRequest,
    ) -> None:
        """
        Change user password

        Args:
            db: Database session
            user_id: User ID
            request: Password change request

        Raises:
            ValueError: If current password is wrong or new password invalid
        """
        # Find user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar()

        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(request.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Verify passwords match
        if request.new_password != request.confirm_password:
            raise ValueError("New passwords do not match")

        # Validate new password
        is_valid, error_msg = validate_password(request.new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # Update password
        user.password_hash = hash_password(request.new_password)
        await db.commit()

        logger.info(f"Password changed for user: {user_id}")

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        request: PasswordResetRequest,
    ) -> None:
        """
        Request password reset - send reset email

        Args:
            db: Database session
            request: Password reset request
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request.email).where(User.deleted_at == None)
        )
        user = result.scalar()

        if not user:
            # Don't reveal if email exists
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            return

        # Create reset token
        token = generate_random_token()
        reset = PasswordReset(
            user_id=user.id,
            token=token,
        )
        db.add(reset)
        await db.commit()

        # TODO: Send email with reset link
        logger.info(f"Password reset requested for user: {user.id}")

    @staticmethod
    async def verify_password_reset_token(
        db: AsyncSession,
        token: str,
    ) -> Optional[User]:
        """
        Verify password reset token

        Args:
            db: Database session
            token: Reset token

        Returns:
            User associated with token or None if invalid
        """
        # Find reset token
        result = await db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.token == token,
                    PasswordReset.is_used == False,
                    PasswordReset.expires_at > datetime.utcnow(),
                )
            )
        )
        reset = result.scalar()

        if not reset:
            return None

        # Find user
        user_result = await db.execute(
            select(User).where(User.id == reset.user_id)
        )
        return user_result.scalar()

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> None:
        """
        Reset password with reset token

        Args:
            db: Database session
            token: Reset token
            new_password: New password

        Raises:
            ValueError: If token invalid or password invalid
        """
        # Verify token
        result = await db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.token == token,
                    PasswordReset.is_used == False,
                    PasswordReset.expires_at > datetime.utcnow(),
                )
            )
        )
        reset = result.scalar()

        if not reset:
            raise ValueError("Invalid or expired reset token")

        # Find user
        user_result = await db.execute(
            select(User).where(User.id == reset.user_id)
        )
        user = user_result.scalar()

        if not user:
            raise ValueError("User not found")

        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # Update password
        user.password_hash = hash_password(new_password)
        reset.is_used = True

        await db.commit()
        logger.info(f"Password reset for user: {user.id}")

    @staticmethod
    async def send_otp(
        db: AsyncSession,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> str:
        """
        Send OTP code for phone/email verification

        Args:
            db: Database session
            phone_number: Phone number to verify
            email: Email to verify
            user_id: User ID (if already authenticated)

        Returns:
            OTP code sent to user

        Raises:
            ValueError: If phone/email invalid or already verified
        """
        import random
        from app.models import OTP, OTPVerificationType

        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))

        if user_id:
            # Authenticated user sending OTP
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar()
            if not user:
                raise ValueError("User not found")

            verification_type = OTPVerificationType.PHONE if phone_number else OTPVerificationType.EMAIL
            target = phone_number or email or user.email

            # Delete existing OTP for this user and type
            await db.execute(
                delete(OTP).where(
                    and_(
                        OTP.user_id == user_id,
                        OTP.verification_type == verification_type,
                    )
                )
            )
        else:
            # Unauthenticated user
            verification_type = OTPVerificationType.PHONE if phone_number else OTPVerificationType.EMAIL
            target = phone_number or email
            if not target:
                raise ValueError("Phone number or email required")
            user_id = uuid.uuid4()  # Temporary user ID for signup flow

        # Create OTP record
        otp = OTP(
            user_id=user_id,
            phone_number=phone_number,
            email=email,
            code=otp_code,
            verification_type=verification_type,
        )
        db.add(otp)
        await db.commit()
        logger.info(f"OTP sent to {target}")

        # TODO: Send OTP via SMS/Email
        # - For phone: use Twilio
        # - For email: use SendGrid/SMTP

        return otp_code

    @staticmethod
    async def verify_otp(
        db: AsyncSession,
        code: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Verify OTP code

        Args:
            db: Database session
            code: OTP code to verify
            phone_number: Phone number
            email: Email address
            user_id: User ID

        Returns:
            True if OTP verified successfully

        Raises:
            ValueError: If OTP invalid, expired, or max attempts exceeded
        """
        from app.models import OTP, OTPVerificationType

        verification_type = OTPVerificationType.PHONE if phone_number else OTPVerificationType.EMAIL

        # Find OTP record
        otp_result = await db.execute(
            select(OTP).where(
                and_(
                    OTP.code == code,
                    OTP.verification_type == verification_type,
                    OTP.is_verified == False,
                    OTP.expires_at > datetime.utcnow(),
                    OTP.attempt_count < OTP.max_attempts,
                )
            )
        )
        otp = otp_result.scalar()

        if not otp:
            raise ValueError("Invalid, expired, or already verified OTP")

        # Verify code
        if otp.code != code:
            otp.attempt_count += 1
            await db.commit()
            if otp.attempt_count >= otp.max_attempts:
                raise ValueError("Maximum OTP attempts exceeded")
            raise ValueError("Invalid OTP code")

        # Mark as verified
        otp.is_verified = True
        otp.verified_at = datetime.utcnow()
        await db.commit()

        logger.info(f"OTP verified for {phone_number or email}")
        return True

    @staticmethod
    async def setup_two_factor(
        db: AsyncSession,
        user_id: UUID,
    ) -> str:
        """
        Setup 2FA (TOTP) for user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            QR code URL for authenticator app

        Raises:
            ValueError: If user not found
        """
        import pyotp

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar()

        if not user:
            raise ValueError("User not found")

        # Generate secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Store secret temporarily (should be activated after verification)
        user.two_factor_secret = secret
        await db.commit()

        # Generate QR code
        qr_code_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="TikTok Clone",
        )

        logger.info(f"2FA setup initiated for user: {user_id}")
        return qr_code_uri

    @staticmethod
    async def verify_two_factor(
        db: AsyncSession,
        user_id: UUID,
        code: str,
    ) -> bool:
        """
        Verify TOTP code and enable 2FA

        Args:
            db: Database session
            user_id: User ID
            code: 6-digit TOTP code

        Returns:
            True if verified

        Raises:
            ValueError: If code invalid or user not found
        """
        import pyotp

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar()

        if not user or not user.two_factor_secret:
            raise ValueError("2FA not setup for this user")

        totp = pyotp.TOTP(user.two_factor_secret)

        if not totp.verify(code):
            raise ValueError("Invalid TOTP code")

        # Enable 2FA
        user.two_factor_enabled = True
        await db.commit()

        logger.info(f"2FA enabled for user: {user_id}")
        return True

    @staticmethod
    async def disable_two_factor(
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        """
        Disable 2FA for user

        Args:
            db: Database session
            user_id: User ID

        Raises:
            ValueError: If user not found
        """
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar()

        if not user:
            raise ValueError("User not found")

        user.two_factor_enabled = False
        user.two_factor_secret = None
        await db.commit()

        logger.info(f"2FA disabled for user: {user_id}")
