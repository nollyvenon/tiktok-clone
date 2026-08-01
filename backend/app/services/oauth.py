"""
OAuth authentication service - handles authorization URL generation and
provider callback exchange for Google, Facebook, and TikTok.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode
import logging

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, OAuthToken, OAuthProvider, UserRole, Session
from app.security import create_access_token, create_refresh_token, generate_random_token

logger = logging.getLogger(__name__)


class OAuthProviderConfig:
    """Static provider endpoint configuration"""

    CONFIGS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid email profile",
            "client_id": lambda: settings.GOOGLE_CLIENT_ID,
            "client_secret": lambda: settings.GOOGLE_CLIENT_SECRET,
        },
        "facebook": {
            "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,picture",
            "scope": "email public_profile",
            "client_id": lambda: settings.FACEBOOK_CLIENT_ID,
            "client_secret": lambda: settings.FACEBOOK_CLIENT_SECRET,
        },
        "tiktok": {
            "auth_url": "https://www.tiktok.com/v2/auth/authorize",
            "token_url": "https://open.tiktokapis.com/v2/oauth/token",
            "userinfo_url": "https://open.tiktokapis.com/v2/user/info/?fields=open_id,username,avatar_url",
            "scope": "user.info.basic",
            "client_id": lambda: settings.TIKTOK_CLIENT_ID,
            "client_secret": lambda: settings.TIKTOK_CLIENT_SECRET,
        },
    }

    @classmethod
    def get(cls, provider: str) -> dict:
        if provider not in cls.CONFIGS:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        return cls.CONFIGS[provider]


class OAuthService:
    """Service for OAuth authorization and callback handling"""

    @staticmethod
    def create_state_token(provider: str, redirect_uri: str) -> str:
        """
        Create a signed, short-lived state token binding the provider and
        redirect_uri, so the callback can be verified without server-side
        session storage (prevents CSRF on the OAuth flow).
        """
        expire = datetime.utcnow() + timedelta(seconds=settings.OAUTH_STATE_TTL_SECONDS)
        payload = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "exp": expire,
            "nonce": generate_random_token(16),
        }
        return jwt.encode(payload, settings.OAUTH_STATE_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_state_token(state: str, provider: str) -> Optional[dict]:
        """Verify and decode a state token, checking it matches the provider"""
        try:
            payload = jwt.decode(state, settings.OAUTH_STATE_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            return None
        if payload.get("provider") != provider:
            return None
        return payload

    @staticmethod
    def get_authorization_url(provider: str, redirect_uri: str) -> str:
        """Build the provider's OAuth authorization URL with a signed state param"""
        config = OAuthProviderConfig.get(provider)
        client_id = config["client_id"]()
        if not client_id:
            raise ValueError(f"OAuth provider '{provider}' is not configured")

        state = OAuthService.create_state_token(provider, redirect_uri)

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scope"],
            "state": state,
        }
        return f"{config['auth_url']}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(provider: str, code: str, redirect_uri: str) -> dict:
        """Exchange an authorization code for an access token with the provider"""
        config = OAuthProviderConfig.get(provider)
        client_id = config["client_id"]()
        client_secret = config["client_secret"]()
        if not client_id or not client_secret:
            raise ValueError(f"OAuth provider '{provider}' is not configured")

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                config["token_url"],
                data=data,
                headers={"Accept": "application/json"},
            )
            if response.status_code != 200:
                logger.error(f"OAuth token exchange failed for {provider}: {response.text}")
                raise ValueError("Failed to exchange authorization code")
            return response.json()

    @staticmethod
    async def fetch_user_info(provider: str, access_token: str) -> dict:
        """Fetch the user's profile info from the provider using their access token"""
        config = OAuthProviderConfig.get(provider)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                logger.error(f"OAuth userinfo fetch failed for {provider}: {response.text}")
                raise ValueError("Failed to fetch user profile from provider")
            return response.json()

    @staticmethod
    def _normalize_profile(provider: str, raw: dict) -> dict:
        """Normalize provider-specific profile payloads into a common shape"""
        if provider == "google":
            return {
                "provider_user_id": raw["sub"],
                "email": raw.get("email"),
                "name": raw.get("name"),
                "avatar_url": raw.get("picture"),
            }
        if provider == "facebook":
            return {
                "provider_user_id": raw["id"],
                "email": raw.get("email"),
                "name": raw.get("name"),
                "avatar_url": (raw.get("picture") or {}).get("data", {}).get("url"),
            }
        if provider == "tiktok":
            data = raw.get("data", {}).get("user", raw)
            return {
                "provider_user_id": data.get("open_id"),
                "email": None,  # TikTok does not provide email via basic scope
                "name": data.get("username"),
                "avatar_url": data.get("avatar_url"),
            }
        raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    async def handle_callback(
        db: AsyncSession,
        provider: str,
        code: str,
        state: str,
        redirect_uri: str,
    ) -> Tuple[User, str, str]:
        """
        Complete the OAuth flow: verify state, exchange code, fetch profile,
        find-or-create the user, persist tokens, and issue app JWTs.

        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        state_payload = OAuthService.verify_state_token(state, provider)
        if not state_payload:
            raise ValueError("Invalid or expired OAuth state")

        token_data = await OAuthService.exchange_code_for_token(provider, code, redirect_uri)
        provider_access_token = token_data.get("access_token")
        if not provider_access_token:
            raise ValueError("Provider did not return an access token")

        raw_profile = await OAuthService.fetch_user_info(provider, provider_access_token)
        profile = OAuthService._normalize_profile(provider, raw_profile)

        provider_enum = OAuthProvider(provider)

        # Find existing OAuth link
        result = await db.execute(
            select(OAuthToken).where(
                OAuthToken.provider == provider_enum,
                OAuthToken.provider_user_id == profile["provider_user_id"],
            )
        )
        oauth_token = result.scalar_one_or_none()

        if oauth_token:
            user = await db.get(User, oauth_token.user_id)
            oauth_token.access_token = provider_access_token
            oauth_token.refresh_token = token_data.get("refresh_token")
            oauth_token.expires_in = token_data.get("expires_in")
            oauth_token.updated_at = datetime.utcnow()
        else:
            user = None
            if profile.get("email"):
                result = await db.execute(select(User).where(User.email == profile["email"]))
                user = result.scalar_one_or_none()

            if not user:
                base_username = (profile.get("name") or f"{provider}_user").lower().replace(" ", "_")
                username = base_username
                suffix = 0
                while True:
                    result = await db.execute(select(User).where(User.username == username))
                    if not result.scalar_one_or_none():
                        break
                    suffix += 1
                    username = f"{base_username}{suffix}"

                user = User(
                    email=profile.get("email") or f"{profile['provider_user_id']}@{provider}.oauth",
                    username=username,
                    password_hash="",  # No password for OAuth-only accounts
                    first_name=profile.get("name"),
                    avatar_url=profile.get("avatar_url"),
                    is_active=True,
                    is_verified=bool(profile.get("email")),
                    role=UserRole.USER,
                )
                db.add(user)
                await db.flush()

            oauth_token = OAuthToken(
                user_id=user.id,
                provider=provider_enum,
                provider_user_id=profile["provider_user_id"],
                access_token=provider_access_token,
                refresh_token=token_data.get("refresh_token"),
                expires_in=token_data.get("expires_in"),
            )
            db.add(oauth_token)

        user.last_login = datetime.utcnow()

        access_token, access_jti = create_access_token(str(user.id))
        refresh_token, refresh_jti = create_refresh_token(str(user.id))

        # A Session row is required for get_current_user's revocation check
        # to pass - without it, logout couldn't invalidate OAuth-issued
        # tokens the same way it does password-login tokens.
        session = Session(
            user_id=user.id,
            device_name=f"OAuth ({provider})",
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            is_active=True,
        )
        db.add(session)

        await db.commit()
        await db.refresh(user)

        return user, access_token, refresh_token
