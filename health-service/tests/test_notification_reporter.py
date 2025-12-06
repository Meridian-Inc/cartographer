"""
Unit tests for notification_reporter service.
"""
import pytest
from unittest.mock import patch, AsyncMock
import httpx

from app.services.notification_reporter import (
    report_health_check,
    report_health_checks_batch,
    clear_state_tracking,
    sync_devices_with_notification_service,
    _previous_states,
)


class TestReportHealthCheck:
    """Tests for report_health_check function"""
    
    def setup_method(self):
        """Clear state before each test"""
        clear_state_tracking()
    
    async def test_report_success(self):
        """Should report successfully"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = ""
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await report_health_check(
                device_ip="192.168.1.1",
                success=True,
                latency_ms=25.0,
                packet_loss=0.0,
                device_name="router"
            )
            
            assert result is True
            mock_client.post.assert_called_once()
    
    async def test_report_with_previous_state(self):
        """Should include previous state when available"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # First call establishes state
            await report_health_check(device_ip="192.168.1.1", success=True)
            
            # Second call should include previous state
            await report_health_check(device_ip="192.168.1.1", success=False)
            
            # Check that second call had previous_state
            call_args = mock_client.post.call_args_list[1]
            params = call_args.kwargs.get('params', {})
            assert params.get('previous_state') == 'online'
    
    async def test_report_non_200_response(self):
        """Should return False for non-200 response"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal error"
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await report_health_check(
                device_ip="192.168.1.1",
                success=True
            )
            
            assert result is False
    
    async def test_report_connect_error(self):
        """Should handle connection error"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await report_health_check(
                device_ip="192.168.1.1",
                success=True
            )
            
            assert result is False
    
    async def test_report_generic_exception(self):
        """Should handle generic exception"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("Unknown error"))
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await report_health_check(
                device_ip="192.168.1.1",
                success=True
            )
            
            assert result is False
    
    async def test_report_with_optional_params(self):
        """Should send only provided optional params"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await report_health_check(
                device_ip="192.168.1.1",
                success=True,
                latency_ms=25.0
                # Not providing packet_loss or device_name
            )
            
            call_args = mock_client.post.call_args
            params = call_args.kwargs.get('params', {})
            
            assert 'latency_ms' in params
            assert 'packet_loss' not in params
            assert 'device_name' not in params


class TestReportHealthChecksBatch:
    """Tests for report_health_checks_batch function"""
    
    def setup_method(self):
        """Clear state before each test"""
        clear_state_tracking()
    
    async def test_batch_report_all_success(self):
        """Should report all checks in batch"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = {
                "192.168.1.1": (True, 25.0, 0.0, "device1"),
                "192.168.1.2": (True, 30.0, 0.0, "device2"),
                "192.168.1.3": (False, None, 1.0, "device3"),
            }
            
            count = await report_health_checks_batch(results)
            
            assert count == 3
    
    async def test_batch_report_some_failures(self):
        """Should count successful reports"""
        success_response = AsyncMock()
        success_response.status_code = 200
        
        failure_response = AsyncMock()
        failure_response.status_code = 500
        failure_response.text = "Error"
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return failure_response
            return success_response
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = mock_post
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = {
                "192.168.1.1": (True, 25.0, 0.0, "device1"),
                "192.168.1.2": (True, 30.0, 0.0, "device2"),
                "192.168.1.3": (True, 20.0, 0.0, "device3"),
            }
            
            count = await report_health_checks_batch(results)
            
            assert count == 2  # 1 failed


class TestClearStateTracking:
    """Tests for clear_state_tracking function"""
    
    async def test_clear_state(self):
        """Should clear all tracked states"""
        # First establish some state
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await report_health_check(device_ip="192.168.1.1", success=True)
        
        # Clear state
        clear_state_tracking()
        
        # Import and check the global state
        from app.services.notification_reporter import _previous_states
        assert len(_previous_states) == 0


class TestSyncDevicesWithNotificationService:
    """Tests for sync_devices_with_notification_service function"""
    
    async def test_sync_devices_success(self):
        """Should sync devices successfully"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await sync_devices_with_notification_service(
                ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
            )
            
            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args.kwargs.get('json') == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    
    async def test_sync_devices_non_200_response(self):
        """Should return False for non-200 response"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal error"
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await sync_devices_with_notification_service(
                ["192.168.1.1"]
            )
            
            assert result is False
    
    async def test_sync_devices_connect_error(self):
        """Should handle connection error"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await sync_devices_with_notification_service(
                ["192.168.1.1"]
            )
            
            assert result is False
    
    async def test_sync_devices_generic_exception(self):
        """Should handle generic exception"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("Unknown error"))
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await sync_devices_with_notification_service(
                ["192.168.1.1"]
            )
            
            assert result is False
    
    async def test_sync_empty_devices_list(self):
        """Should sync empty devices list (clearing all devices)"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await sync_devices_with_notification_service([])
            
            assert result is True
            call_args = mock_client.post.call_args
            assert call_args.kwargs.get('json') == []

