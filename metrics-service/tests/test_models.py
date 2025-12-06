"""
Unit tests for metrics service models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    HealthStatus,
    DeviceRole,
    PingMetrics,
    DnsMetrics,
    PortInfo,
    UptimeMetrics,
    CheckHistoryEntry,
    SpeedTestMetrics,
    TestIPMetrics,
    GatewayISPInfo,
    PortType,
    PortStatus,
    PoeStatus,
    LanPort,
    LanPortsConfig,
    NodeConnection,
    ConnectionSpeedInfo,
    NodeMetrics,
    NetworkTopologySnapshot,
    MetricsEventType,
    MetricsEvent,
    SubscriptionRequest,
    PublishConfig,
)


class TestHealthStatus:
    """Tests for HealthStatus enum"""
    
    def test_health_status_values(self):
        """Should have expected values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestDeviceRole:
    """Tests for DeviceRole enum"""
    
    def test_device_role_values(self):
        """Should have expected values"""
        assert DeviceRole.GATEWAY_ROUTER.value == "gateway/router"
        assert DeviceRole.SWITCH_AP.value == "switch/ap"
        assert DeviceRole.FIREWALL.value == "firewall"
        assert DeviceRole.SERVER.value == "server"
        assert DeviceRole.SERVICE.value == "service"
        assert DeviceRole.NAS.value == "nas"
        assert DeviceRole.CLIENT.value == "client"
        assert DeviceRole.UNKNOWN.value == "unknown"
        assert DeviceRole.GROUP.value == "group"


class TestPingMetrics:
    """Tests for PingMetrics model"""
    
    def test_ping_metrics_success(self):
        """Should create successful ping metrics"""
        metrics = PingMetrics(
            success=True,
            latency_ms=5.5,
            packet_loss_percent=0.0,
            min_latency_ms=4.0,
            max_latency_ms=7.0,
            avg_latency_ms=5.5,
            jitter_ms=0.5
        )
        assert metrics.success is True
        assert metrics.latency_ms == 5.5
        assert metrics.packet_loss_percent == 0.0
    
    def test_ping_metrics_defaults(self):
        """Should use defaults for optional fields"""
        metrics = PingMetrics(success=False)
        assert metrics.success is False
        assert metrics.latency_ms is None
        assert metrics.packet_loss_percent == 0.0


class TestDnsMetrics:
    """Tests for DnsMetrics model"""
    
    def test_dns_metrics(self):
        """Should create DNS metrics"""
        metrics = DnsMetrics(
            success=True,
            resolved_hostname="router.local",
            reverse_dns="router.local",
            resolution_time_ms=2.5
        )
        assert metrics.success is True
        assert metrics.resolved_hostname == "router.local"


class TestPortInfo:
    """Tests for PortInfo model"""
    
    def test_port_info(self):
        """Should create port info"""
        port = PortInfo(
            port=80,
            open=True,
            service="HTTP",
            response_time_ms=1.5
        )
        assert port.port == 80
        assert port.open is True
        assert port.service == "HTTP"


class TestUptimeMetrics:
    """Tests for UptimeMetrics model"""
    
    def test_uptime_metrics(self):
        """Should create uptime metrics"""
        now = datetime.utcnow()
        metrics = UptimeMetrics(
            uptime_percent_24h=99.5,
            avg_latency_24h_ms=5.0,
            checks_passed_24h=100,
            checks_failed_24h=1,
            last_seen_online=now,
            consecutive_failures=0
        )
        assert metrics.uptime_percent_24h == 99.5
        assert metrics.consecutive_failures == 0
    
    def test_uptime_metrics_defaults(self):
        """Should use defaults"""
        metrics = UptimeMetrics()
        assert metrics.checks_passed_24h == 0
        assert metrics.consecutive_failures == 0


class TestCheckHistoryEntry:
    """Tests for CheckHistoryEntry model"""
    
    def test_check_history_entry(self):
        """Should create check history entry"""
        now = datetime.utcnow()
        entry = CheckHistoryEntry(
            timestamp=now,
            success=True,
            latency_ms=5.0
        )
        assert entry.success is True
        assert entry.latency_ms == 5.0


class TestSpeedTestMetrics:
    """Tests for SpeedTestMetrics model"""
    
    def test_speed_test_metrics(self):
        """Should create speed test metrics"""
        now = datetime.utcnow()
        metrics = SpeedTestMetrics(
            success=True,
            timestamp=now,
            download_mbps=100.5,
            upload_mbps=50.2,
            ping_ms=15.0,
            server_name="TestServer",
            server_location="New York",
            client_isp="TestISP"
        )
        assert metrics.download_mbps == 100.5
        assert metrics.upload_mbps == 50.2


class TestTestIPMetrics:
    """Tests for TestIPMetrics model"""
    
    def test_test_ip_metrics(self):
        """Should create test IP metrics"""
        metrics = TestIPMetrics(
            ip="8.8.8.8",
            label="Google DNS",
            status=HealthStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        assert metrics.ip == "8.8.8.8"
        assert metrics.status == HealthStatus.HEALTHY


class TestGatewayISPInfo:
    """Tests for GatewayISPInfo model"""
    
    def test_gateway_isp_info(self):
        """Should create gateway ISP info"""
        info = GatewayISPInfo(
            gateway_ip="192.168.1.1",
            test_ips=[]
        )
        assert info.gateway_ip == "192.168.1.1"
        assert info.last_speed_test is None


class TestLanPort:
    """Tests for LAN port models"""
    
    def test_port_type_values(self):
        """Should have expected port type values"""
        assert PortType.RJ45.value == "rj45"
        assert PortType.SFP.value == "sfp"
        assert PortType.SFP_PLUS.value == "sfp+"
    
    def test_port_status_values(self):
        """Should have expected port status values"""
        assert PortStatus.ACTIVE.value == "active"
        assert PortStatus.UNUSED.value == "unused"
        assert PortStatus.BLOCKED.value == "blocked"
    
    def test_poe_status_values(self):
        """Should have expected PoE status values"""
        assert PoeStatus.OFF.value == "off"
        assert PoeStatus.POE.value == "poe"
        assert PoeStatus.POE_PLUS.value == "poe+"
        assert PoeStatus.POE_PLUS_PLUS.value == "poe++"
    
    def test_lan_port(self):
        """Should create LAN port"""
        port = LanPort(
            row=1,
            col=2,
            port_number=3,
            type=PortType.RJ45,
            status=PortStatus.ACTIVE,
            speed="1G",
            poe=PoeStatus.POE_PLUS
        )
        assert port.row == 1
        assert port.col == 2
        assert port.port_number == 3
    
    def test_lan_ports_config(self):
        """Should create LAN ports config"""
        config = LanPortsConfig(
            rows=2,
            cols=4,
            ports=[
                LanPort(row=1, col=1)
            ]
        )
        assert config.rows == 2
        assert config.cols == 4
        assert len(config.ports) == 1


class TestNodeConnection:
    """Tests for NodeConnection model"""
    
    def test_node_connection(self):
        """Should create node connection"""
        conn = NodeConnection(
            source_id="node-1",
            target_id="node-2",
            connection_speed="1GbE",
            latency_ms=2.5
        )
        assert conn.source_id == "node-1"
        assert conn.target_id == "node-2"


class TestConnectionSpeedInfo:
    """Tests for ConnectionSpeedInfo model"""
    
    def test_connection_speed_info(self):
        """Should create connection speed info"""
        info = ConnectionSpeedInfo(
            speed_label="1GbE",
            speed_mbps=1000.0,
            last_measured=datetime.utcnow()
        )
        assert info.speed_label == "1GbE"


class TestNodeMetrics:
    """Tests for NodeMetrics model"""
    
    def test_node_metrics(self):
        """Should create node metrics"""
        metrics = NodeMetrics(
            id="node-1",
            name="Test Node",
            ip="192.168.1.1",
            role=DeviceRole.SERVER,
            status=HealthStatus.HEALTHY,
            depth=2
        )
        assert metrics.id == "node-1"
        assert metrics.role == DeviceRole.SERVER
        assert metrics.depth == 2
        assert metrics.monitoring_enabled is True
    
    def test_node_metrics_defaults(self):
        """Should use defaults"""
        metrics = NodeMetrics(id="node-1", name="Test")
        assert metrics.status == HealthStatus.UNKNOWN
        assert metrics.depth == 0
        assert metrics.open_ports == []


class TestNetworkTopologySnapshot:
    """Tests for NetworkTopologySnapshot model"""
    
    def test_network_topology_snapshot(self):
        """Should create snapshot"""
        snapshot = NetworkTopologySnapshot(
            snapshot_id="snap-123",
            timestamp=datetime.utcnow(),
            version=1,
            total_nodes=5,
            healthy_nodes=3,
            degraded_nodes=1,
            unhealthy_nodes=1,
            unknown_nodes=0
        )
        assert snapshot.snapshot_id == "snap-123"
        assert snapshot.total_nodes == 5
        assert snapshot.nodes == {}
        assert snapshot.connections == []


class TestMetricsEvent:
    """Tests for MetricsEvent model"""
    
    def test_metrics_event_type_values(self):
        """Should have expected event types"""
        assert MetricsEventType.FULL_SNAPSHOT.value == "full_snapshot"
        assert MetricsEventType.NODE_UPDATE.value == "node_update"
        assert MetricsEventType.HEALTH_UPDATE.value == "health_update"
        assert MetricsEventType.SPEED_TEST_RESULT.value == "speed_test_result"
    
    def test_metrics_event(self):
        """Should create metrics event"""
        event = MetricsEvent(
            event_type=MetricsEventType.FULL_SNAPSHOT,
            timestamp=datetime.utcnow(),
            payload={"data": "test"}
        )
        assert event.event_type == MetricsEventType.FULL_SNAPSHOT


class TestSubscriptionRequest:
    """Tests for SubscriptionRequest model"""
    
    def test_subscription_request_default(self):
        """Should use default channels"""
        request = SubscriptionRequest()
        assert "metrics:topology" in request.channels
    
    def test_subscription_request_custom(self):
        """Should accept custom channels"""
        request = SubscriptionRequest(channels=["custom:channel"])
        assert request.channels == ["custom:channel"]


class TestPublishConfig:
    """Tests for PublishConfig model"""
    
    def test_publish_config_defaults(self):
        """Should use defaults"""
        config = PublishConfig()
        assert config.enabled is True
        assert config.publish_interval_seconds == 30
        assert config.include_history is True
        assert config.history_hours == 24
    
    def test_publish_config_custom(self):
        """Should accept custom values"""
        config = PublishConfig(
            enabled=False,
            publish_interval_seconds=60,
            include_history=False
        )
        assert config.enabled is False
        assert config.publish_interval_seconds == 60

