"""
Tests for Discord notification router.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.dependencies.auth import AuthenticatedUser, UserRole


class TestDiscordOAuthCallback:
    """Tests for Discord OAuth callback endpoint."""

    async def test_discord_callback_redirect_response(self):
        """Should return redirect when service returns 302"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_response.headers = {"location": "https://app.example.com/settings?linked=true"}

        mock_service = MagicMock()
        mock_service.client = AsyncMock()
        mock_service.client.get.return_value = mock_response

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="test-code", state="test-state")

            assert response.status_code == 307  # RedirectResponse default
            assert "settings?linked=true" in str(response.headers.get("location", ""))

    async def test_discord_callback_no_service(self):
        """Should return 500 if notification service not configured"""
        from app.routers.notification.discord import discord_oauth_callback

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {}

            with pytest.raises(HTTPException) as exc_info:
                await discord_oauth_callback(code="test-code", state="test-state")

            assert exc_info.value.status_code == 500
            assert "not available" in exc_info.value.detail.lower()

    async def test_discord_callback_initializes_service(self):
        """Should initialize service if client not ready"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        mock_service = MagicMock()
        mock_service.client = None
        mock_service.initialize = AsyncMock()

        # After initialize, client becomes available
        async def set_client():
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_service.client = mock_client

        mock_service.initialize.side_effect = set_client

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="test-code", state="test-state")

            mock_service.initialize.assert_awaited_once()

    async def test_discord_callback_json_response(self):
        """Should return JSON for non-redirect responses"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"linked": True, "discord_id": "12345"}
        mock_response.headers = {}

        mock_service = MagicMock()
        mock_service.client = AsyncMock()
        mock_service.client.get.return_value = mock_response

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="test-code", state="test-state")

            import json

            data = json.loads(response.body.decode())
            assert data["linked"] is True

    async def test_discord_callback_json_error_fallback(self):
        """Should handle non-JSON error responses"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.side_effect = Exception("Not JSON")
        mock_response.text = "Invalid code"
        mock_response.headers = {}

        mock_service = MagicMock()
        mock_service.client = AsyncMock()
        mock_service.client.get.return_value = mock_response

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="invalid", state="test-state")

            import json

            data = json.loads(response.body.decode())
            assert "detail" in data
            assert response.status_code == 400

    async def test_discord_callback_empty_response(self):
        """Should handle empty response body"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.side_effect = Exception("Empty")
        mock_response.text = ""
        mock_response.headers = {}

        mock_service = MagicMock()
        mock_service.client = AsyncMock()
        mock_service.client.get.return_value = mock_response

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="invalid", state="test-state")

            import json

            data = json.loads(response.body.decode())
            assert data["detail"] == "Empty response"

    async def test_discord_callback_redirect_303(self):
        """Should handle 303 redirect status"""
        from app.routers.notification.discord import discord_oauth_callback

        mock_response = MagicMock()
        mock_response.status_code = 303
        mock_response.headers = {"location": "https://app.example.com/"}

        mock_service = MagicMock()
        mock_service.client = AsyncMock()
        mock_service.client.get.return_value = mock_response

        with patch("app.services.http_client.http_pool") as mock_pool:
            mock_pool._services = {"notification": mock_service}

            response = await discord_oauth_callback(code="test-code", state="test-state")

            # Should be a redirect response
            assert hasattr(response, "headers")


class TestDiscordEndpoints:
    """Tests for Discord notification endpoints"""

    @pytest.fixture
    def owner_user(self):
        return AuthenticatedUser(user_id="owner-1", username="owner", role=UserRole.OWNER)

    async def test_get_discord_info(self, owner_user):
        """Should proxy discord info request"""
        from app.routers.notification.discord import get_discord_info

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"bot_id": "12345", "invite_url": "https://..."}

            result = await get_discord_info(user=owner_user)

            mock_proxy.assert_awaited_once_with("GET", "/discord/info")

    async def test_get_discord_guilds(self, owner_user):
        """Should proxy discord guilds request"""
        from app.routers.notification.discord import get_discord_guilds

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"guilds": []}

            result = await get_discord_guilds(user=owner_user)

            mock_proxy.assert_awaited_once_with("GET", "/discord/guilds")

    async def test_get_discord_channels(self, owner_user):
        """Should proxy discord channels request"""
        from app.routers.notification.discord import get_discord_channels

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"channels": []}

            result = await get_discord_channels(guild_id="guild-123", user=owner_user)

            mock_proxy.assert_awaited_once_with("GET", "/discord/guilds/guild-123/channels")

    async def test_get_discord_invite_url(self, owner_user):
        """Should proxy discord invite URL request"""
        from app.routers.notification.discord import get_discord_invite_url

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"url": "https://discord.com/..."}

            result = await get_discord_invite_url(user=owner_user)

            mock_proxy.assert_awaited_once_with("GET", "/discord/invite-url")

    async def test_initiate_discord_oauth_global(self, owner_user):
        """Should initiate OAuth with global context"""
        from app.routers.notification.discord import initiate_discord_oauth

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"auth_url": "https://discord.com/oauth2/..."}

            result = await initiate_discord_oauth(
                context_type="global", network_id=None, user=owner_user
            )

            call_args = mock_proxy.call_args
            assert "context_type=global" in call_args[0][1]
            assert "network_id" not in call_args[0][1]

    async def test_initiate_discord_oauth_network(self, owner_user):
        """Should initiate OAuth with network context"""
        from app.routers.notification.discord import initiate_discord_oauth

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"auth_url": "https://discord.com/oauth2/..."}

            result = await initiate_discord_oauth(
                context_type="network", network_id="net-123", user=owner_user
            )

            call_args = mock_proxy.call_args
            assert "context_type=network" in call_args[0][1]
            assert "network_id=net-123" in call_args[0][1]

    async def test_get_user_discord_info(self, owner_user):
        """Should get user Discord info"""
        from app.routers.notification.discord import get_user_discord_info

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"discord_id": "12345"}

            result = await get_user_discord_info(
                context_type="global", network_id=None, user=owner_user
            )

            mock_proxy.assert_awaited_once()
            call_args = mock_proxy.call_args
            assert call_args[1]["params"]["context_type"] == "global"

    async def test_get_user_discord_info_with_network(self, owner_user):
        """Should get user Discord info with network context"""
        from app.routers.notification.discord import get_user_discord_info

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"discord_id": "12345"}

            result = await get_user_discord_info(
                context_type="network", network_id="net-123", user=owner_user
            )

            call_args = mock_proxy.call_args
            assert call_args[1]["params"]["context_type"] == "network"
            assert call_args[1]["params"]["network_id"] == "net-123"

    async def test_unlink_discord_global(self, owner_user):
        """Should unlink Discord with global context"""
        from app.routers.notification.discord import unlink_discord

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"success": True}

            result = await unlink_discord(context_type="global", network_id=None, user=owner_user)

            mock_proxy.assert_awaited_once()
            call_args = mock_proxy.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[1]["params"]["context_type"] == "global"

    async def test_unlink_discord_network(self, owner_user):
        """Should unlink Discord with network context"""
        from app.routers.notification.discord import unlink_discord

        with patch("app.routers.notification.discord.proxy_notification_request") as mock_proxy:
            mock_proxy.return_value = {"success": True}

            result = await unlink_discord(
                context_type="network", network_id="net-123", user=owner_user
            )

            call_args = mock_proxy.call_args
            assert call_args[1]["params"]["context_type"] == "network"
            assert call_args[1]["params"]["network_id"] == "net-123"
