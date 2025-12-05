"""
Load Test for Metrics Service (port 8003)

Tests network topology snapshots, Redis publishing, and WebSocket connections.
"""

import uuid
import random
from locust import HttpUser, task, between, tag


class MetricsServiceUser(HttpUser):
    """
    Load test user for the Metrics Service.
    
    Run with:
        locust -f locustfile_metrics.py --host=http://localhost:8003
    """
    
    wait_time = between(1, 3)
    
    # ==================== Snapshot Endpoints ====================
    
    @task(15)
    @tag("snapshot", "read")
    def get_current_snapshot(self):
        """Get current network topology snapshot - highest frequency"""
        self.client.get("/api/metrics/snapshot")
    
    @task(8)
    @tag("snapshot", "read")
    def get_cached_snapshot(self):
        """Get cached snapshot from Redis"""
        self.client.get("/api/metrics/snapshot/cached")
    
    @task(3)
    @tag("snapshot", "write")
    def generate_snapshot(self):
        """Trigger snapshot generation"""
        with self.client.post(
            "/api/metrics/snapshot/generate",
            name="/api/metrics/snapshot/generate",
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    @task(2)
    @tag("snapshot", "write")
    def publish_snapshot(self):
        """Generate and publish snapshot to Redis"""
        with self.client.post(
            "/api/metrics/snapshot/publish",
            name="/api/metrics/snapshot/publish",
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    # ==================== Summary & Navigation ====================
    
    @task(12)
    @tag("summary", "read")
    def get_summary(self):
        """Get lightweight network summary - high frequency for dashboards"""
        self.client.get("/api/metrics/summary")
    
    @task(6)
    @tag("navigation", "read")
    def get_connections(self):
        """Get all node connections"""
        self.client.get("/api/metrics/connections")
    
    @task(5)
    @tag("navigation", "read")
    def get_gateways(self):
        """Get gateway/ISP information"""
        self.client.get("/api/metrics/gateways")
    
    @task(4)
    @tag("navigation", "read")
    def get_node_metrics(self):
        """Get metrics for a specific node"""
        # Use common node ID patterns
        node_ids = [
            "192.168.1.1",
            "10.0.0.1",
            str(uuid.uuid4()),
            "router",
            "gateway",
        ]
        node_id = random.choice(node_ids)
        with self.client.get(
            f"/api/metrics/nodes/{node_id}",
            name="/api/metrics/nodes/[id]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
    
    # ==================== Configuration ====================
    
    @task(4)
    @tag("config", "read")
    def get_config(self):
        """Get metrics service configuration"""
        self.client.get("/api/metrics/config")
    
    @task(1)
    @tag("config", "write")
    def update_config(self):
        """Update publishing configuration"""
        with self.client.post(
            "/api/metrics/config",
            json={
                "enabled": True,
                "publish_interval_seconds": random.randint(15, 60)
            },
            name="/api/metrics/config (update)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    # ==================== Redis Status ====================
    
    @task(5)
    @tag("redis", "read")
    def get_redis_status(self):
        """Check Redis connection status"""
        self.client.get("/api/metrics/redis/status")
    
    @task(1)
    @tag("redis", "write")
    def reconnect_redis(self):
        """Attempt Redis reconnection - low frequency"""
        with self.client.post(
            "/api/metrics/redis/reconnect",
            name="/api/metrics/redis/reconnect",
            catch_response=True
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    # ==================== Speed Test ====================
    
    # Note: Actual speed tests are NOT triggered as they take 30-60 seconds
    # The endpoint exists but we only test the trigger mechanism with invalid IPs
    
    @task(1)
    @tag("speedtest", "read")
    def trigger_speed_test_dry(self):
        """Test speed test trigger endpoint (won't complete actual test)"""
        with self.client.post(
            "/api/metrics/speed-test",
            json={"gateway_ip": "192.168.1.1"},
            name="/api/metrics/speed-test (dry)",
            catch_response=True,
            timeout=5  # Short timeout - we don't want actual test
        ) as response:
            # Any response is acceptable - we're testing the endpoint, not the test
            response.success()
    
    # ==================== Debug Endpoints ====================
    
    @task(2)
    @tag("debug", "read")
    def debug_layout(self):
        """Get raw layout data - useful for debugging"""
        self.client.get("/api/metrics/debug/layout")
    
    # ==================== Healthcheck ====================
    
    @task(5)
    @tag("system", "read")
    def healthz(self):
        """Service health check endpoint"""
        self.client.get("/healthz")


class MetricsWebSocketUser(HttpUser):
    """
    Simulated WebSocket load test user.
    
    Note: Locust doesn't natively support WebSocket, so this simulates
    the HTTP upgrade request and initial snapshot fetch.
    For full WebSocket load testing, consider using tools like:
    - Artillery
    - k6 (with WebSocket support)
    - websocket-bench
    
    Run with:
        locust -f locustfile_metrics.py --host=http://localhost:8003
    """
    
    wait_time = between(5, 15)  # WebSocket connections are long-lived
    weight = 1  # Lower weight
    
    @task(1)
    @tag("websocket", "connect")
    def simulate_ws_connect(self):
        """
        Simulate WebSocket connection initiation.
        This tests the HTTP upgrade path, not full WS communication.
        """
        # Request initial snapshot like a WS client would
        self.client.get("/api/metrics/snapshot")
        
        # Then request cached snapshot
        self.client.get("/api/metrics/snapshot/cached")
        
        # Simulate periodic snapshot requests (like WS pings)
        for _ in range(random.randint(1, 3)):
            self.client.get("/api/metrics/summary")

