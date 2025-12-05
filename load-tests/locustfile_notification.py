"""
Load Test for Notification Service (port 8005)

Tests notification preferences, history, Discord integration, 
ML anomaly detection, and scheduled broadcasts.
"""

import random
import uuid
from datetime import datetime, timedelta
from locust import HttpUser, task, between, tag
from faker import Faker

fake = Faker()

# Sample user IDs for testing
SAMPLE_USER_IDS = [
    str(uuid.uuid4()) for _ in range(10)
]

# Sample device IPs
SAMPLE_DEVICE_IPS = [
    "192.168.1.1",
    "192.168.1.100",
    "192.168.1.254",
    "10.0.0.1",
    "10.0.0.50",
]


class NotificationServiceUser(HttpUser):
    """
    Load test user for the Notification Service.
    
    Run with:
        locust -f locustfile_notification.py --host=http://localhost:8005
    """
    
    wait_time = between(1, 3)
    
    def _random_user_id(self):
        """Get a random user ID for testing"""
        return random.choice(SAMPLE_USER_IDS)
    
    def _user_headers(self, user_id=None):
        """Get headers with user ID"""
        return {"X-User-Id": user_id or self._random_user_id()}
    
    # ==================== Service Status ====================
    
    @task(10)
    @tag("status", "read")
    def get_service_status(self):
        """Get notification service status - high frequency"""
        self.client.get("/api/notifications/status")
    
    # ==================== Preferences ====================
    
    @task(8)
    @tag("preferences", "read")
    def get_preferences(self):
        """Get notification preferences for a user"""
        headers = self._user_headers()
        self.client.get(
            "/api/notifications/preferences",
            headers=headers
        )
    
    @task(2)
    @tag("preferences", "write")
    def update_preferences(self):
        """Update notification preferences"""
        headers = self._user_headers()
        with self.client.put(
            "/api/notifications/preferences",
            headers=headers,
            json={
                "email_enabled": random.choice([True, False]),
                "discord_enabled": random.choice([True, False]),
                "device_offline_enabled": True,
                "device_degraded_enabled": True,
            },
            name="/api/notifications/preferences (update)",
            catch_response=True
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
    
    # ==================== History & Stats ====================
    
    @task(6)
    @tag("history", "read")
    def get_notification_history(self):
        """Get notification history for a user"""
        headers = self._user_headers()
        page = random.randint(1, 5)
        self.client.get(
            f"/api/notifications/history?page={page}&per_page=20",
            headers=headers,
            name="/api/notifications/history"
        )
    
    @task(4)
    @tag("stats", "read")
    def get_notification_stats(self):
        """Get notification statistics"""
        headers = self._user_headers()
        self.client.get(
            "/api/notifications/stats",
            headers=headers
        )
    
    # ==================== Discord Integration ====================
    
    @task(5)
    @tag("discord", "read")
    def get_discord_info(self):
        """Get Discord bot information"""
        self.client.get("/api/notifications/discord/info")
    
    @task(3)
    @tag("discord", "read")
    def get_discord_guilds(self):
        """Get Discord servers the bot is in"""
        with self.client.get(
            "/api/notifications/discord/guilds",
            name="/api/notifications/discord/guilds",
            catch_response=True
        ) as response:
            # 503 if Discord not configured
            if response.status_code in [200, 503]:
                response.success()
    
    @task(2)
    @tag("discord", "read")
    def get_discord_invite_url(self):
        """Get Discord bot invite URL"""
        with self.client.get(
            "/api/notifications/discord/invite-url",
            name="/api/notifications/discord/invite-url",
            catch_response=True
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
    
    # ==================== ML/Anomaly Detection ====================
    
    @task(5)
    @tag("ml", "read")
    def get_ml_model_status(self):
        """Get ML anomaly detection model status"""
        self.client.get("/api/notifications/ml/status")
    
    @task(3)
    @tag("ml", "read")
    def get_device_baseline(self):
        """Get learned baseline for a device"""
        device_ip = random.choice(SAMPLE_DEVICE_IPS)
        with self.client.get(
            f"/api/notifications/ml/baseline/{device_ip}",
            name="/api/notifications/ml/baseline/[ip]",
            catch_response=True
        ) as response:
            # 404 if no baseline exists yet
            if response.status_code in [200, 404]:
                response.success()
    
    # ==================== Silenced Devices ====================
    
    @task(4)
    @tag("silenced", "read")
    def get_silenced_devices(self):
        """Get list of silenced devices"""
        self.client.get("/api/notifications/silenced-devices")
    
    @task(2)
    @tag("silenced", "read")
    def check_device_silenced(self):
        """Check if a specific device is silenced"""
        device_ip = random.choice(SAMPLE_DEVICE_IPS)
        self.client.get(
            f"/api/notifications/silenced-devices/{device_ip}",
            name="/api/notifications/silenced-devices/[ip]"
        )
    
    # ==================== Scheduled Broadcasts ====================
    
    @task(4)
    @tag("scheduled", "read")
    def get_scheduled_broadcasts(self):
        """Get all scheduled broadcasts"""
        self.client.get("/api/notifications/scheduled")
    
    @task(2)
    @tag("scheduled", "read")
    def get_scheduled_broadcast_by_id(self):
        """Get a specific scheduled broadcast"""
        broadcast_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/notifications/scheduled/{broadcast_id}",
            name="/api/notifications/scheduled/[id]",
            catch_response=True
        ) as response:
            # 404 is expected for random IDs
            if response.status_code in [200, 404]:
                response.success()
    
    # ==================== Version Updates ====================
    
    @task(5)
    @tag("version", "read")
    def get_version_status(self):
        """Get version status and update info"""
        self.client.get("/api/notifications/version")
    
    @task(2)
    @tag("version", "write")
    def check_for_updates(self):
        """Trigger version check"""
        with self.client.post(
            "/api/notifications/version/check",
            name="/api/notifications/version/check",
            catch_response=True
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    # ==================== Healthcheck ====================
    
    @task(5)
    @tag("system", "read")
    def healthz(self):
        """Service health check endpoint"""
        self.client.get("/healthz")


class NotificationWriteUser(HttpUser):
    """
    Load test user for notification write operations.
    
    Run with:
        locust -f locustfile_notification.py --host=http://localhost:8005
    """
    
    wait_time = between(3, 8)  # Slower for write operations
    weight = 1  # Lower weight
    
    def _random_user_id(self):
        return random.choice(SAMPLE_USER_IDS)
    
    def _user_headers(self, user_id=None):
        return {"X-User-Id": user_id or self._random_user_id()}
    
    @task(2)
    @tag("health-check", "write")
    def process_health_check(self):
        """Process a health check result"""
        device_ip = random.choice(SAMPLE_DEVICE_IPS)
        
        with self.client.post(
            "/api/notifications/process-health-check",
            params={
                "device_ip": device_ip,
                "success": random.choice([True, True, True, False]),  # 75% success
                "latency_ms": random.uniform(1, 100),
                "packet_loss": random.uniform(0, 0.1),
                "device_name": f"Device-{device_ip.split('.')[-1]}",
            },
            name="/api/notifications/process-health-check",
            catch_response=True
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    @task(1)
    @tag("silenced", "write")
    def toggle_device_silence(self):
        """Silence and unsilence a device"""
        device_ip = random.choice(SAMPLE_DEVICE_IPS)
        
        # Silence the device
        self.client.post(
            f"/api/notifications/silenced-devices/{device_ip}",
            name="/api/notifications/silenced-devices/[ip] (silence)"
        )
        
        # Unsilence the device
        self.client.delete(
            f"/api/notifications/silenced-devices/{device_ip}",
            name="/api/notifications/silenced-devices/[ip] (unsilence)"
        )
    
    @task(1)
    @tag("scheduled", "write")
    def create_and_cancel_broadcast(self):
        """Create and immediately cancel a scheduled broadcast"""
        headers = {"X-Username": "loadtest"}
        
        # Schedule for 1 hour from now
        scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        
        create_response = self.client.post(
            "/api/notifications/scheduled",
            headers=headers,
            json={
                "title": f"Load Test Broadcast {random.randint(1000, 9999)}",
                "message": "This is a load test broadcast that will be cancelled.",
                "scheduled_at": scheduled_time,
                "event_type": "system_status",
                "priority": "low",
            },
            name="/api/notifications/scheduled (create)",
            catch_response=True
        )
        
        if create_response.status_code == 200:
            create_response.success()
            data = create_response.json()
            broadcast_id = data.get("id")
            
            if broadcast_id:
                # Cancel the broadcast
                cancel_response = self.client.post(
                    f"/api/notifications/scheduled/{broadcast_id}/cancel",
                    name="/api/notifications/scheduled/[id]/cancel",
                    catch_response=True
                )
                if cancel_response.status_code in [200, 400]:
                    cancel_response.success()
                
                # Delete the broadcast
                delete_response = self.client.delete(
                    f"/api/notifications/scheduled/{broadcast_id}",
                    name="/api/notifications/scheduled/[id] (delete)",
                    catch_response=True
                )
                if delete_response.status_code in [200, 400]:
                    delete_response.success()
        else:
            if create_response.status_code in [400, 500]:
                create_response.success()


class NotificationTestUser(HttpUser):
    """
    Load test user for testing notification delivery.
    
    WARNING: This may send actual notifications via email/Discord!
    Use with caution and only in test environments.
    
    Run with:
        locust -f locustfile_notification.py --host=http://localhost:8005 --tags test-notify
    """
    
    wait_time = between(10, 30)  # Very slow - actual notifications
    weight = 1  # Lowest weight
    
    def _user_headers(self):
        return {"X-User-Id": random.choice(SAMPLE_USER_IDS)}
    
    @task(1)
    @tag("test-notify", "write")
    def send_test_notification(self):
        """
        Send a test notification.
        
        WARNING: This may send actual emails/Discord messages!
        """
        headers = self._user_headers()
        channel = random.choice(["email", "discord"])
        
        with self.client.post(
            "/api/notifications/test",
            headers=headers,
            json={
                "channel": channel,
            },
            name="/api/notifications/test",
            catch_response=True
        ) as response:
            # Various failures are acceptable
            if response.status_code in [200, 400, 500, 503]:
                response.success()

