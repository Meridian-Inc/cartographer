"""
Discord OAuth service for linking user accounts.
Supports per-network and global Discord linking.
"""

import os
import logging
import secrets
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode, quote
import httpx

from ..models.database import DiscordUserLink

logger = logging.getLogger(__name__)

# Discord OAuth configuration
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get(
    "DISCORD_REDIRECT_URI",
    "http://localhost:8005/api/auth/discord/callback"
)
APPLICATION_URL = os.environ.get("APPLICATION_URL", "http://localhost:5173")

# OAuth state storage (in production, use Redis or database)
_oauth_states: Dict[str, Dict[str, Any]] = {}


class DiscordOAuthService:
    """Service for handling Discord OAuth flow with per-network and global context support"""
    
    def get_authorization_url(
        self, 
        user_id: str, 
        context_type: str = "global",
        context_id: Optional[int] = None
    ) -> str:
        """
        Generate Discord OAuth authorization URL.
        
        Args:
            user_id: The user initiating the OAuth flow
            context_type: "network" or "global"
            context_id: The network_id if context_type is "network", None for "global"
        """
        if not DISCORD_CLIENT_ID:
            logger.error("DISCORD_CLIENT_ID not configured")
            raise ValueError("DISCORD_CLIENT_ID not configured. Please set DISCORD_CLIENT_ID environment variable.")
        
        # Generate state token
        state_token = secrets.token_urlsafe(32)
        _oauth_states[state_token] = {
            "user_id": user_id,
            "context_type": context_type,
            "context_id": context_id,
            "created_at": datetime.utcnow(),
        }
        
        # Build authorization URL
        scopes = ["identify", "email"]
        params = {
            "client_id": DISCORD_CLIENT_ID,
            "redirect_uri": DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state_token,
        }
        
        # Properly URL-encode all parameters
        query_string = urlencode(params)
        return f"https://discord.com/api/oauth2/authorize?{query_string}"
    
    def validate_state(self, state_token: str) -> Optional[Tuple[str, str, Optional[int]]]:
        """
        Validate OAuth state token and return context information.
        
        Returns:
            Tuple of (user_id, context_type, context_id) or None if invalid
        """
        if state_token not in _oauth_states:
            return None
        
        state_data = _oauth_states[state_token]
        
        # Check if state is expired (5 minutes)
        if (datetime.utcnow() - state_data["created_at"]).total_seconds() > 300:
            del _oauth_states[state_token]
            return None
        
        user_id = state_data["user_id"]
        context_type = state_data.get("context_type", "global")
        context_id = state_data.get("context_id")
        del _oauth_states[state_token]  # One-time use
        return (user_id, context_type, context_id)
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
            logger.error(f"Discord OAuth not configured: CLIENT_ID={'set' if DISCORD_CLIENT_ID else 'missing'}, CLIENT_SECRET={'set' if DISCORD_CLIENT_SECRET else 'missing'}")
            raise ValueError("Discord OAuth not configured. Please set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET environment variables.")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://discord.com/api/oauth2/token",
                data={
                    "client_id": DISCORD_CLIENT_ID,
                    "client_secret": DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": DISCORD_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            if response.status_code != 200:
                logger.error(f"Discord token exchange failed: {response.text}")
                raise ValueError(f"Failed to exchange code: {response.status_code}")
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Discord user information using access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                logger.error(f"Discord user info failed: {response.status_code}")
                raise ValueError(f"Failed to get user info: {response.status_code}")
            
            return response.json()
    
    async def create_or_update_link(
        self,
        db: AsyncSession,
        user_id: str,
        discord_id: str,
        discord_username: str,
        discord_avatar: Optional[str],
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int,
        context_type: str = "global",
        context_id: Optional[int] = None,
    ) -> DiscordUserLink:
        """
        Create or update Discord user link for a specific context.
        
        Args:
            user_id: The user's ID
            discord_id: The Discord user ID
            discord_username: The Discord username
            discord_avatar: The Discord avatar URL
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiration time in seconds
            context_type: "network" or "global"
            context_id: The network_id if context_type is "network", None for "global"
        """
        # Check if link exists for this context
        existing_link = await self.get_link(db, user_id, context_type, context_id)
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        
        if existing_link:
            # Update existing
            existing_link.discord_id = discord_id
            existing_link.discord_username = discord_username
            existing_link.discord_avatar = discord_avatar
            existing_link.access_token = access_token
            existing_link.refresh_token = refresh_token
            existing_link.expires_at = expires_at
            existing_link.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing_link)
            return existing_link
        else:
            # Create new
            new_link = DiscordUserLink(
                user_id=user_id,
                discord_id=discord_id,
                discord_username=discord_username,
                discord_avatar=discord_avatar,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                context_type=context_type,
                context_id=context_id,
            )
            db.add(new_link)
            await db.commit()
            await db.refresh(new_link)
            return new_link
    
    async def get_link(
        self, 
        db: AsyncSession, 
        user_id: str,
        context_type: str = "global",
        context_id: Optional[int] = None
    ) -> Optional[DiscordUserLink]:
        """
        Get Discord link for user in a specific context.
        
        Args:
            user_id: The user's ID
            context_type: "network" or "global"
            context_id: The network_id if context_type is "network", None for "global"
        """
        if context_type == "global" or context_id is None:
            result = await db.execute(
                select(DiscordUserLink).where(
                    and_(
                        DiscordUserLink.user_id == user_id,
                        DiscordUserLink.context_type == "global"
                    )
                )
            )
        else:
            result = await db.execute(
                select(DiscordUserLink).where(
                    and_(
                        DiscordUserLink.user_id == user_id,
                        DiscordUserLink.context_type == context_type,
                        DiscordUserLink.context_id == context_id
                    )
                )
            )
        return result.scalar_one_or_none()
    
    async def delete_link(
        self, 
        db: AsyncSession, 
        user_id: str,
        context_type: str = "global",
        context_id: Optional[int] = None
    ) -> bool:
        """
        Delete Discord link for user in a specific context.
        
        Args:
            user_id: The user's ID
            context_type: "network" or "global"
            context_id: The network_id if context_type is "network", None for "global"
        """
        link = await self.get_link(db, user_id, context_type, context_id)
        if link:
            await db.delete(link)
            await db.commit()
            return True
        return False


# Singleton instance
discord_oauth_service = DiscordOAuthService()
