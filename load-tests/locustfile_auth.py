"""
Load Test for Auth Service (port 8002)

Tests authentication, user management, and invitation endpoints.
"""

import uuid
import random
from locust import HttpUser, task, between, tag, events
from faker import Faker

fake = Faker()


class AuthServiceUser(HttpUser):
    """
    Load test user for the Auth Service.
    
    Run with:
        locust -f locustfile_auth.py --host=http://localhost:8002
    """
    
    wait_time = between(1, 3)
    
    # Shared state for authenticated requests
    access_token = None
    test_user_id = None
    
    def on_start(self):
        """Setup: Try to authenticate if owner account exists"""
        # First check setup status
        response = self.client.get("/api/setup/status")
        if response.status_code == 200:
            data = response.json()
            if data.get("setup_complete"):
                # Try to login with test credentials
                # Note: In a real load test, you'd use env vars for credentials
                self._try_login()
    
    def _try_login(self):
        """Attempt to login with test credentials"""
        # This will fail if owner hasn't been set up with these credentials
        response = self.client.post(
            "/api/login",
            json={
                "username": "loadtest",
                "password": "loadtest123"
            },
            catch_response=True
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            response.success()
        else:
            # Auth failure is expected if user doesn't exist
            response.success()
    
    def _auth_headers(self):
        """Get authorization headers if logged in"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    # ==================== Public Endpoints ====================
    
    @task(10)
    @tag("public", "read")
    def get_setup_status(self):
        """Check setup status - high frequency public endpoint"""
        self.client.get("/api/setup/status")
    
    @task(2)
    @tag("public", "write")
    def failed_login(self):
        """Test invalid login - simulates brute force protection testing"""
        with self.client.post(
            "/api/login",
            json={
                "username": fake.user_name(),
                "password": fake.password()
            },
            name="/api/login (invalid)",
            catch_response=True
        ) as response:
            # 401 is expected for invalid credentials
            if response.status_code == 401:
                response.success()
    
    # ==================== Token Verification ====================
    
    @task(15)
    @tag("auth", "read")
    def verify_token(self):
        """Verify token validity - very high frequency in real apps"""
        headers = self._auth_headers()
        with self.client.post(
            "/api/verify",
            headers=headers,
            name="/api/verify",
            catch_response=True
        ) as response:
            # Both valid and invalid responses are acceptable
            if response.status_code == 200:
                response.success()
    
    @task(8)
    @tag("auth", "read")
    def get_session(self):
        """Get current session info"""
        headers = self._auth_headers()
        with self.client.get(
            "/api/session",
            headers=headers,
            name="/api/session",
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
    
    # ==================== User Profile ====================
    
    @task(6)
    @tag("profile", "read")
    def get_current_profile(self):
        """Get current user profile"""
        headers = self._auth_headers()
        with self.client.get(
            "/api/me",
            headers=headers,
            name="/api/me",
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
    
    # ==================== User Management ====================
    
    @task(4)
    @tag("users", "read")
    def list_users(self):
        """List all users"""
        headers = self._auth_headers()
        with self.client.get(
            "/api/users",
            headers=headers,
            name="/api/users",
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
    
    @task(2)
    @tag("users", "read")
    def get_user_by_id(self):
        """Get user by ID"""
        if not self.test_user_id:
            # Use a fake UUID
            user_id = str(uuid.uuid4())
        else:
            user_id = self.test_user_id
        
        headers = self._auth_headers()
        with self.client.get(
            f"/api/users/{user_id}",
            headers=headers,
            name="/api/users/[id]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                response.success()
    
    # ==================== Invitation Endpoints ====================
    
    @task(3)
    @tag("invites", "read")
    def list_invites(self):
        """List all invitations"""
        headers = self._auth_headers()
        with self.client.get(
            "/api/invites",
            headers=headers,
            name="/api/invites",
            catch_response=True
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
    
    @task(2)
    @tag("invites", "read")
    def verify_invite_token(self):
        """Verify an invite token (public endpoint)"""
        fake_token = fake.sha256()[:32]
        with self.client.get(
            f"/api/invite/verify/{fake_token}",
            name="/api/invite/verify/[token]",
            catch_response=True
        ) as response:
            # 404 is expected for invalid tokens
            if response.status_code in [200, 404]:
                response.success()
    
    # ==================== Healthcheck ====================
    
    @task(5)
    @tag("system", "read")
    def healthz(self):
        """Service health check endpoint"""
        self.client.get("/healthz")


class AuthServiceOwnerUser(HttpUser):
    """
    Load test for owner-level operations.
    Separate user class with lower weight for write operations.
    
    Run with:
        locust -f locustfile_auth.py --host=http://localhost:8002
    """
    
    wait_time = between(3, 8)  # Slower for write operations
    weight = 1  # Lower weight than regular users
    
    access_token = None
    created_users = []
    created_invites = []
    
    def on_start(self):
        """Setup: Authenticate as owner"""
        response = self.client.get("/api/setup/status")
        if response.status_code == 200:
            data = response.json()
            if data.get("setup_complete"):
                self._login_as_owner()
    
    def _login_as_owner(self):
        """Login with owner credentials"""
        response = self.client.post(
            "/api/login",
            json={
                "username": "loadtest_owner",
                "password": "loadtest_owner123"
            },
            catch_response=True
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            response.success()
        else:
            response.success()  # Expected if owner doesn't exist
    
    def _auth_headers(self):
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(1)
    @tag("users", "write")
    def create_and_delete_user(self):
        """Create and immediately delete a test user"""
        if not self.access_token:
            return
        
        headers = self._auth_headers()
        username = f"loadtest_{fake.user_name()}_{random.randint(1000, 9999)}"
        
        # Create user
        create_response = self.client.post(
            "/api/users",
            headers=headers,
            json={
                "username": username,
                "password": fake.password(length=12),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "role": "readonly"
            },
            name="/api/users (create)",
            catch_response=True
        )
        
        if create_response.status_code == 200:
            create_response.success()
            user_data = create_response.json()
            user_id = user_data.get("id")
            
            # Immediately delete the test user
            if user_id:
                delete_response = self.client.delete(
                    f"/api/users/{user_id}",
                    headers=headers,
                    name="/api/users/[id] (delete)",
                    catch_response=True
                )
                if delete_response.status_code in [200, 404]:
                    delete_response.success()
        else:
            if create_response.status_code in [400, 401, 403]:
                create_response.success()
    
    @task(1)
    @tag("invites", "write")
    def create_and_revoke_invite(self):
        """Create and immediately revoke an invitation"""
        if not self.access_token:
            return
        
        headers = self._auth_headers()
        email = fake.email()
        
        # Create invite
        create_response = self.client.post(
            "/api/invites",
            headers=headers,
            json={
                "email": email,
                "role": "readonly"
            },
            name="/api/invites (create)",
            catch_response=True
        )
        
        if create_response.status_code == 200:
            create_response.success()
            invite_data = create_response.json()
            invite_id = invite_data.get("id")
            
            # Immediately revoke
            if invite_id:
                revoke_response = self.client.delete(
                    f"/api/invites/{invite_id}",
                    headers=headers,
                    name="/api/invites/[id] (revoke)",
                    catch_response=True
                )
                if revoke_response.status_code in [200, 400, 404]:
                    revoke_response.success()
        else:
            if create_response.status_code in [400, 401, 403]:
                create_response.success()

