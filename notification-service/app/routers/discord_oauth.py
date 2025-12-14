"""
Discord OAuth router for linking user Discord accounts.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from ..database import get_db
import os
from ..services.discord_oauth import discord_oauth_service
from ..services.user_preferences import user_preferences_service
from ..models.database import DiscordUserLink, UserNetworkNotificationPrefs, UserGlobalNotificationPrefs

logger = logging.getLogger(__name__)

APPLICATION_URL = os.environ.get("APPLICATION_URL", "http://localhost:5173")

router = APIRouter()


@router.get("/auth/discord/link")
async def initiate_discord_oauth(
    user_id: str = Query(..., description="User ID"),
):
    """Initiate Discord OAuth flow"""
    try:
        auth_url = discord_oauth_service.get_authorization_url(user_id)
        return {"authorization_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/discord/callback")
async def discord_oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state token"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Discord OAuth callback"""
    # Validate state
    user_id = discord_oauth_service.validate_state(state)
    if not user_id:
        return RedirectResponse(
            url=f"{APPLICATION_URL}?discord_oauth=error&message=Invalid or expired state token"
        )
    
    try:
        # Exchange code for tokens
        token_data = await discord_oauth_service.exchange_code_for_tokens(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        
        # Get user info
        user_info = await discord_oauth_service.get_user_info(access_token)
        discord_id = user_info["id"]
        discord_username = user_info.get("username", "Unknown")
        discord_avatar = user_info.get("avatar")
        if discord_avatar:
            discord_avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"
        
        # Create or update link
        link = await discord_oauth_service.create_or_update_link(
            db=db,
            user_id=user_id,
            discord_id=discord_id,
            discord_username=discord_username,
            discord_avatar=discord_avatar,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
        
        # Update user preferences to use this Discord ID and enable Discord notifications
        # Update all network preferences with the new Discord ID and enable Discord
        await db.execute(
            update(UserNetworkNotificationPrefs)
            .where(UserNetworkNotificationPrefs.user_id == user_id)
            .values(discord_user_id=discord_id, discord_enabled=True)
        )
        
        # Update global preferences
        global_prefs = await user_preferences_service.get_global_preferences(db, user_id)
        if global_prefs:
            global_prefs.discord_user_id = discord_id
            global_prefs.discord_enabled = True
        else:
            # Create global preferences if they don't exist
            # Use string value directly to match PostgreSQL enum (lowercase)
            new_prefs = UserGlobalNotificationPrefs(
                user_id=user_id,
                discord_user_id=discord_id,
                discord_enabled=True,
                minimum_priority="medium",
            )
            db.add(new_prefs)
        
        await db.commit()
        
        logger.info(f"Linked Discord account {discord_id} for user {user_id}")
        
        return RedirectResponse(
            url=f"{APPLICATION_URL}?discord_oauth=success&username={discord_username}"
        )
    
    except Exception as e:
        logger.error(f"Discord OAuth callback failed: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{APPLICATION_URL}?discord_oauth=error&message={str(e)}"
        )


@router.delete("/users/{user_id}/discord/link")
async def unlink_discord(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Unlink Discord account from user"""
    success = await discord_oauth_service.delete_link(db, user_id)
    
    if success:
        # Clear discord_user_id from preferences
        # Update all network preferences
        await db.execute(
            update(UserNetworkNotificationPrefs)
            .where(UserNetworkNotificationPrefs.user_id == user_id)
            .values(discord_user_id=None, discord_enabled=False)
        )
        
        await db.execute(
            update(UserGlobalNotificationPrefs)
            .where(UserGlobalNotificationPrefs.user_id == user_id)
            .values(discord_user_id=None, discord_enabled=False)
        )
        
        await db.commit()
    
    return {"success": success}


@router.get("/users/{user_id}/discord")
async def get_discord_info(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get linked Discord account info"""
    link = await discord_oauth_service.get_link(db, user_id)
    
    if not link:
        return {"linked": False}
    
    return {
        "linked": True,
        "discord_id": link.discord_id,
        "discord_username": link.discord_username,
        "discord_avatar": link.discord_avatar,
    }
