"""
Tests for DISABLE_ACTIVE_CHECKS security setting.

When DISABLE_ACTIVE_CHECKS=true, the health service should not perform
any outbound network probes (ping, port scan, DNS lookup).
"""

import os
from unittest.mock import AsyncMock, patch

import pytest


class TestDisableActiveChecks:
    """Tests for the disable_active_checks security setting."""

    @pytest.fixture
    def health_checker_with_checks_disabled(self, tmp_path):
        """Create HealthChecker with active checks disabled."""
        # Patch settings before importing
        with patch("app.config.settings.disable_active_checks", True):
            with patch("app.services.health_checker.settings.disable_active_checks", True):
                with patch("app.services.health_checker.DATA_DIR", tmp_path):
                    with patch(
                        "app.services.health_checker.GATEWAY_TEST_IPS_FILE",
                        tmp_path / "gateway_test_ips.json",
                    ):
                        with patch(
                            "app.services.health_checker.SPEED_TEST_RESULTS_FILE",
                            tmp_path / "speed_test_results.json",
                        ):
                            from app.services.health_checker import HealthChecker

                            checker = HealthChecker()
                            yield checker
                            if checker._monitoring_task:
                                checker._monitoring_task.cancel()

    async def test_ping_host_returns_failure_when_disabled(
        self, health_checker_with_checks_disabled
    ):
        """Ping should return failure without making network call when disabled."""
        result = await health_checker_with_checks_disabled.ping_host("192.168.1.1")

        assert result.success is False
        assert result.packet_loss_percent == 100.0

    async def test_check_port_returns_closed_when_disabled(
        self, health_checker_with_checks_disabled
    ):
        """Port check should return closed without making network call when disabled."""
        result = await health_checker_with_checks_disabled.check_port("192.168.1.1", 80)

        assert result.open is False
        assert result.port == 80

    async def test_check_dns_returns_failure_when_disabled(
        self, health_checker_with_checks_disabled
    ):
        """DNS check should return failure without making network call when disabled."""
        result = await health_checker_with_checks_disabled.check_dns("192.168.1.1")

        assert result.success is False

    async def test_scan_common_ports_returns_empty_when_disabled(
        self, health_checker_with_checks_disabled
    ):
        """Port scan should return empty list when disabled."""
        results = await health_checker_with_checks_disabled.scan_common_ports("192.168.1.1")

        # All ports should be reported as closed
        assert results == []

    def test_start_monitoring_does_nothing_when_disabled(self, health_checker_with_checks_disabled):
        """Background monitoring should not start when disabled."""
        health_checker_with_checks_disabled.start_monitoring()

        # Should not create a monitoring task
        assert health_checker_with_checks_disabled._monitoring_task is None


class TestActiveChecksEnabled:
    """Tests to verify active checks work normally when enabled."""

    async def test_ping_makes_network_call_when_enabled(self, health_checker_instance):
        """Ping should make network call when checks are enabled."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(
            return_value=(
                b"64 bytes from 192.168.1.1: time=10.5 ms\n3 packets transmitted, 3 received",
                b"",
            )
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            result = await health_checker_instance.ping_host("192.168.1.1", count=1)

            # Should have called subprocess
            mock_exec.assert_called_once()
            assert result.success is True

    async def test_check_port_makes_network_call_when_enabled(self, health_checker_instance):
        """Port check should make network call when checks are enabled."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection", return_value=(mock_reader, mock_writer)
        ) as mock_connect:
            result = await health_checker_instance.check_port("192.168.1.1", 80)

            # Should have attempted connection
            mock_connect.assert_called_once()
            assert result.open is True

    async def test_start_monitoring_creates_task_when_enabled(self, health_checker_instance):
        """Background monitoring should start when checks are enabled."""
        health_checker_instance.start_monitoring()

        # Should create a monitoring task
        assert health_checker_instance._monitoring_task is not None

        # Cleanup
        health_checker_instance.stop_monitoring()
