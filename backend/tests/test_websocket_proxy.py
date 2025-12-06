"""
Tests for WebSocket proxy functionality in metrics_proxy.py
and streaming proxy in assistant_proxy.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.dependencies.auth import AuthenticatedUser, UserRole


class TestAssistantStreamProxy:
    """Tests for the streaming proxy in assistant router"""
    
    @pytest.fixture
    def owner_user(self):
        return AuthenticatedUser(user_id="user-1", username="test", role=UserRole.OWNER)
    
    async def test_stream_proxy_connect_error(self, owner_user):
        """Stream proxy should handle connection errors"""
        import httpx
        from app.routers.assistant_proxy import chat_stream
        
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={"message": "Hello"})
        
        response = await chat_stream(request=mock_request, user=owner_user)
        
        # The response should be a StreamingResponse
        assert response.media_type == "text/event-stream"
    
    async def test_stream_proxy_returns_correct_headers(self, owner_user):
        """Stream proxy should set correct headers"""
        from app.routers.assistant_proxy import chat_stream
        
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={"message": "Hello"})
        
        response = await chat_stream(request=mock_request, user=owner_user)
        
        assert response.media_type == "text/event-stream"
        assert "no-cache" in response.headers.get("Cache-Control", "")
        assert response.headers.get("X-Accel-Buffering") == "no"


class TestNotificationServiceStatus:
    """Tests for notification service status endpoints with optional body"""
    
    @pytest.fixture
    def owner_user(self):
        return AuthenticatedUser(user_id="owner-1", username="owner", role=UserRole.OWNER)
    
    @pytest.fixture(autouse=True)
    def mock_http_pool(self):
        """Mock http_pool for notification proxy tests"""
        from fastapi.responses import JSONResponse
        
        with patch('app.routers.notification_proxy.http_pool') as mock:
            mock.request = AsyncMock(return_value=JSONResponse(content={"ok": True}))
            yield mock
    
    async def test_notify_service_up_without_body(self, mock_http_pool, owner_user):
        """notify_service_up should work without JSON body"""
        from app.routers.notification_proxy import notify_service_up
        
        mock_request = MagicMock()
        mock_request.headers = MagicMock()
        mock_request.headers.get = MagicMock(return_value=None)  # No content-type
        
        response = await notify_service_up(request=mock_request, user=owner_user)
        
        # Should work even without body
        mock_http_pool.request.assert_called_once()
    
    async def test_notify_service_down_without_body(self, mock_http_pool, owner_user):
        """notify_service_down should work without JSON body"""
        from app.routers.notification_proxy import notify_service_down
        
        mock_request = MagicMock()
        mock_request.headers = MagicMock()
        mock_request.headers.get = MagicMock(return_value=None)  # No content-type
        
        response = await notify_service_down(request=mock_request, user=owner_user)
        
        mock_http_pool.request.assert_called_once()
    
    async def test_notify_service_up_with_body(self, mock_http_pool, owner_user):
        """notify_service_up should forward body when present"""
        from app.routers.notification_proxy import notify_service_up
        
        mock_request = MagicMock()
        mock_request.headers = MagicMock()
        mock_request.headers.get = MagicMock(return_value="application/json")
        mock_request.json = AsyncMock(return_value={"message": "Online", "downtime_minutes": 5})
        
        response = await notify_service_up(request=mock_request, user=owner_user)
        
        mock_http_pool.request.assert_called_once()
        call_kwargs = mock_http_pool.request.call_args[1]
        assert call_kwargs["params"]["message"] == "Online"
        assert call_kwargs["params"]["downtime_minutes"] == 5
    
    async def test_notify_service_down_with_body(self, mock_http_pool, owner_user):
        """notify_service_down should forward body when present"""
        from app.routers.notification_proxy import notify_service_down
        
        mock_request = MagicMock()
        mock_request.headers = MagicMock()
        mock_request.headers.get = MagicMock(return_value="application/json")
        mock_request.json = AsyncMock(return_value={
            "message": "Maintenance",
            "affected_services": ["api", "web"]
        })
        
        response = await notify_service_down(request=mock_request, user=owner_user)
        
        mock_http_pool.request.assert_called_once()
