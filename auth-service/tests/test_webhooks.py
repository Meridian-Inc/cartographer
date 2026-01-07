"""
Unit tests for webhooks router.

Tests for Clerk webhook handling endpoints.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class MockSvix:
    """Mock svix module for testing."""

    class Webhook:
        def __init__(self, secret: str):
            self.secret = secret
            self._should_fail = False
            self._payload = {}

        def verify(self, body: bytes, headers: dict) -> dict:
            if self._should_fail:
                raise MockSvix.WebhookVerificationError("Invalid signature")
            return self._payload

    class WebhookVerificationError(Exception):
        pass


@pytest.fixture
def mock_svix():
    """Fixture to mock svix module."""
    mock = MockSvix()
    with patch.dict(sys.modules, {"svix": mock}):
        yield mock


@pytest.fixture
def app_with_webhooks():
    """Create test app with webhook router."""
    from app.routers.webhooks import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app_with_webhooks):
    """Create test client."""
    return TestClient(app_with_webhooks)


class TestClerkWebhookHealth:
    """Tests for clerk webhook health endpoint."""

    def test_health_returns_status(self, client):
        """Should return health status."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.auth_provider = "local"
            mock_settings.clerk_webhook_secret = None

            response = client.get("/webhooks/clerk/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["auth_provider"] == "local"
            assert data["webhook_configured"] is False

    def test_health_with_webhook_configured(self, client):
        """Should show webhook configured when secret set."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"

            response = client.get("/webhooks/clerk/health")

            assert response.status_code == 200
            data = response.json()
            assert data["auth_provider"] == "cloud"
            assert data["webhook_configured"] is True


class TestClerkWebhook:
    """Tests for clerk webhook endpoint."""

    def test_webhook_rejects_non_cloud_mode(self, client):
        """Should reject webhook when not in cloud mode."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.auth_provider = "local"

            response = client.post("/webhooks/clerk", json={})

            assert response.status_code == 400
            assert "only available in cloud mode" in response.json()["detail"]

    def test_webhook_rejects_missing_svix(self, client):
        """Should reject when svix not installed."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "svix":
                raise ImportError("No module named 'svix'")
            return original_import(name, *args, **kwargs)

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.object(builtins, "__import__", side_effect=mock_import),
        ):
            mock_settings.auth_provider = "cloud"

            response = client.post("/webhooks/clerk", json={})

            assert response.status_code == 500
            assert "not available" in response.json()["detail"]

    def test_webhook_rejects_missing_secret(self, client):
        """Should reject when webhook secret not configured."""
        mock_svix_module = MagicMock()
        mock_svix_module.Webhook = MagicMock()
        mock_svix_module.WebhookVerificationError = Exception

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = None

            response = client.post("/webhooks/clerk", json={})

            assert response.status_code == 500
            assert "not configured" in response.json()["detail"]

    def test_webhook_rejects_invalid_signature(self, client):
        """Should reject invalid webhook signature."""

        class MockWebhookVerificationError(Exception):
            pass

        mock_webhook = MagicMock()
        mock_webhook.verify.side_effect = MockWebhookVerificationError("Invalid")

        mock_svix_module = MagicMock()
        mock_svix_module.Webhook.return_value = mock_webhook
        mock_svix_module.WebhookVerificationError = MockWebhookVerificationError

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"

            response = client.post(
                "/webhooks/clerk",
                json={},
                headers={
                    "svix-id": "test-id",
                    "svix-timestamp": "12345",
                    "svix-signature": "invalid",
                },
            )

            assert response.status_code == 401
            assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_handles_user_created(self):
        """Should handle user.created event."""
        from app.routers.webhooks import _handle_clerk_user_created

        mock_db = AsyncMock()

        user_data = {
            "id": "clerk_user_123",
            "email_addresses": [
                {
                    "id": "email_1",
                    "email_address": "test@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "primary_email_address_id": "email_1",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        }

        user_id = uuid4()

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch("app.routers.webhooks.sync_provider_user") as mock_sync,
        ):
            mock_settings.clerk_secret_key = "sk_test_123"
            mock_sync.return_value = (user_id, True, False)

            result = await _handle_clerk_user_created(mock_db, user_data)

            assert result["received"] is True
            assert result["handled"] is True
            assert result["local_user_id"] == str(user_id)
            assert result["created"] is True
            assert result["updated"] is False
            mock_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_handles_user_updated(self):
        """Should handle user.updated event."""
        from app.routers.webhooks import _handle_clerk_user_updated

        mock_db = AsyncMock()

        user_data = {
            "id": "clerk_user_123",
            "email_addresses": [
                {
                    "id": "email_1",
                    "email_address": "test@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "primary_email_address_id": "email_1",
            "username": "testuser",
            "first_name": "Updated",
            "last_name": "Name",
        }

        user_id = uuid4()

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch("app.routers.webhooks.sync_provider_user") as mock_sync,
        ):
            mock_settings.clerk_secret_key = "sk_test_123"
            mock_sync.return_value = (user_id, False, True)

            result = await _handle_clerk_user_updated(mock_db, user_data)

            assert result["received"] is True
            assert result["handled"] is True
            assert result["local_user_id"] == str(user_id)
            assert result["updated"] is True
            mock_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_handles_user_deleted(self):
        """Should handle user.deleted event."""
        from app.routers.webhooks import _handle_clerk_user_deleted

        mock_db = AsyncMock()

        user_data = {"id": "clerk_user_123"}

        with patch("app.routers.webhooks.deactivate_provider_user") as mock_deactivate:
            mock_deactivate.return_value = True

            result = await _handle_clerk_user_deleted(mock_db, user_data)

            assert result["received"] is True
            assert result["handled"] is True
            assert result["deactivated"] is True
            mock_deactivate.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_handles_user_deleted_not_found(self):
        """Should handle user.deleted when user not found."""
        from app.routers.webhooks import _handle_clerk_user_deleted

        mock_db = AsyncMock()

        user_data = {"id": "clerk_user_nonexistent"}

        with patch("app.routers.webhooks.deactivate_provider_user") as mock_deactivate:
            mock_deactivate.return_value = False

            result = await _handle_clerk_user_deleted(mock_db, user_data)

            assert result["received"] is True
            assert result["handled"] is True
            assert result["deactivated"] is False

    def test_webhook_handles_unknown_event(self, client):
        """Should acknowledge but not handle unknown events."""
        mock_webhook = MagicMock()
        mock_webhook.verify.return_value = {"type": "organization.created", "data": {}}

        mock_svix_module = MagicMock()
        mock_svix_module.Webhook.return_value = mock_webhook
        mock_svix_module.WebhookVerificationError = Exception

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
            patch("app.routers.webhooks.get_db") as mock_get_db,
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            response = client.post(
                "/webhooks/clerk",
                json={},
                headers={
                    "svix-id": "test-id",
                    "svix-timestamp": "12345",
                    "svix-signature": "valid",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert data["handled"] is False

    def test_webhook_routes_user_created_event(self, client):
        """Should route user.created event to handler."""
        mock_webhook = MagicMock()
        mock_webhook.verify.return_value = {
            "type": "user.created",
            "data": {
                "id": "clerk_user_123",
                "email_addresses": [
                    {
                        "id": "email_1",
                        "email_address": "test@example.com",
                        "verification": {"status": "verified"},
                    }
                ],
                "primary_email_address_id": "email_1",
            },
        }

        mock_svix_module = MagicMock()
        mock_svix_module.Webhook.return_value = mock_webhook
        mock_svix_module.WebhookVerificationError = Exception

        user_id = uuid4()

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
            patch("app.routers.webhooks.get_db") as mock_get_db,
            patch("app.routers.webhooks.sync_provider_user") as mock_sync,
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"
            mock_settings.clerk_secret_key = "sk_test_123"

            mock_db = AsyncMock()

            async def db_generator():
                yield mock_db

            mock_get_db.return_value = db_generator()
            mock_sync.return_value = (user_id, True, False)

            response = client.post(
                "/webhooks/clerk",
                json={},
                headers={
                    "svix-id": "test-id",
                    "svix-timestamp": "12345",
                    "svix-signature": "valid",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert data["handled"] is True
            assert data["created"] is True

    def test_webhook_routes_user_updated_event(self, client):
        """Should route user.updated event to handler."""
        mock_webhook = MagicMock()
        mock_webhook.verify.return_value = {
            "type": "user.updated",
            "data": {
                "id": "clerk_user_123",
                "email_addresses": [
                    {
                        "id": "email_1",
                        "email_address": "test@example.com",
                        "verification": {"status": "verified"},
                    }
                ],
                "primary_email_address_id": "email_1",
            },
        }

        mock_svix_module = MagicMock()
        mock_svix_module.Webhook.return_value = mock_webhook
        mock_svix_module.WebhookVerificationError = Exception

        user_id = uuid4()

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
            patch("app.routers.webhooks.get_db") as mock_get_db,
            patch("app.routers.webhooks.sync_provider_user") as mock_sync,
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"
            mock_settings.clerk_secret_key = "sk_test_123"

            mock_db = AsyncMock()

            async def db_generator():
                yield mock_db

            mock_get_db.return_value = db_generator()
            mock_sync.return_value = (user_id, False, True)

            response = client.post(
                "/webhooks/clerk",
                json={},
                headers={
                    "svix-id": "test-id",
                    "svix-timestamp": "12345",
                    "svix-signature": "valid",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert data["handled"] is True
            assert data["updated"] is True

    def test_webhook_routes_user_deleted_event(self, client):
        """Should route user.deleted event to handler."""
        mock_webhook = MagicMock()
        mock_webhook.verify.return_value = {
            "type": "user.deleted",
            "data": {"id": "clerk_user_123"},
        }

        mock_svix_module = MagicMock()
        mock_svix_module.Webhook.return_value = mock_webhook
        mock_svix_module.WebhookVerificationError = Exception

        with (
            patch("app.routers.webhooks.settings") as mock_settings,
            patch.dict(sys.modules, {"svix": mock_svix_module}),
            patch("app.routers.webhooks.get_db") as mock_get_db,
            patch("app.routers.webhooks.deactivate_provider_user") as mock_deactivate,
        ):
            mock_settings.auth_provider = "cloud"
            mock_settings.clerk_webhook_secret = "whsec_test"

            mock_db = AsyncMock()

            async def db_generator():
                yield mock_db

            mock_get_db.return_value = db_generator()
            mock_deactivate.return_value = True

            response = client.post(
                "/webhooks/clerk",
                json={},
                headers={
                    "svix-id": "test-id",
                    "svix-timestamp": "12345",
                    "svix-signature": "valid",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert data["handled"] is True
            assert data["deactivated"] is True
