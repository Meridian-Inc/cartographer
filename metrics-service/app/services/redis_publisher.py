"""
Redis Publisher Service

Handles publishing metrics events to Redis pub/sub channels
and managing subscriptions for consuming services.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis
from pydantic import BaseModel

from ..models import (
    MetricsEvent,
    MetricsEventType,
    NetworkTopologySnapshot,
    NodeMetrics,
    SpeedTestMetrics,
)

logger = logging.getLogger(__name__)

# Redis configuration from environment
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

# Default channels
CHANNEL_TOPOLOGY = "metrics:topology"
CHANNEL_HEALTH = "metrics:health"
CHANNEL_SPEED_TEST = "metrics:speedtest"


class RedisPublisher:
    """
    Redis Pub/Sub publisher for metrics events.
    
    Publishes network topology metrics to Redis channels that
    other services can subscribe to for real-time updates.
    """
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._subscriber_tasks: List[asyncio.Task] = []
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Connect to Redis server.
        Returns True if connected successfully.
        """
        try:
            self._redis = redis.Redis.from_url(
                REDIS_URL,
                db=REDIS_DB,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {REDIS_URL}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis and cleanup resources."""
        # Cancel subscriber tasks
        for task in self._subscriber_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._subscriber_tasks.clear()
        
        # Close pubsub
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None
        
        # Close Redis connection
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        self._connected = False
        logger.info("Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._redis is not None
    
    async def _ensure_connected(self) -> bool:
        """Ensure we're connected to Redis, attempt reconnection if needed."""
        if not self.is_connected:
            return await self.connect()
        return True
    
    def _serialize_event(self, event: MetricsEvent) -> str:
        """Serialize a MetricsEvent to JSON string."""
        return event.model_dump_json()
    
    def _serialize_payload(self, payload: Any) -> str:
        """Serialize any payload to JSON string."""
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        return json.dumps(payload, default=str)
    
    async def publish(
        self,
        channel: str,
        event_type: MetricsEventType,
        payload: Any,
    ) -> bool:
        """
        Publish an event to a Redis channel.
        
        Args:
            channel: The Redis channel to publish to
            event_type: Type of the metrics event
            payload: The event payload (will be serialized)
            
        Returns:
            True if published successfully
        """
        if not await self._ensure_connected():
            logger.warning(f"Cannot publish to {channel}: not connected to Redis")
            return False
        
        try:
            event = MetricsEvent(
                event_type=event_type,
                timestamp=datetime.utcnow(),
                payload=payload if isinstance(payload, dict) else payload.model_dump() if isinstance(payload, BaseModel) else {"data": payload}
            )
            
            message = self._serialize_event(event)
            num_subscribers = await self._redis.publish(channel, message)
            
            logger.debug(f"Published {event_type.value} to {channel} ({num_subscribers} subscribers)")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing to {channel}: {e}")
            return False
    
    async def publish_topology_snapshot(self, snapshot: NetworkTopologySnapshot) -> bool:
        """Publish a full network topology snapshot."""
        return await self.publish(
            CHANNEL_TOPOLOGY,
            MetricsEventType.FULL_SNAPSHOT,
            snapshot
        )
    
    async def publish_node_update(self, node: NodeMetrics) -> bool:
        """Publish a single node update."""
        return await self.publish(
            CHANNEL_TOPOLOGY,
            MetricsEventType.NODE_UPDATE,
            node
        )
    
    async def publish_health_update(self, node_id: str, status: str, metrics: dict) -> bool:
        """Publish a health status update for a node."""
        return await self.publish(
            CHANNEL_HEALTH,
            MetricsEventType.HEALTH_UPDATE,
            {"node_id": node_id, "status": status, "metrics": metrics}
        )
    
    async def publish_speed_test_result(self, gateway_ip: str, result: SpeedTestMetrics) -> bool:
        """Publish a speed test result."""
        return await self.publish(
            CHANNEL_SPEED_TEST,
            MetricsEventType.SPEED_TEST_RESULT,
            {"gateway_ip": gateway_ip, "result": result}
        )
    
    # ==================== Subscription Methods ====================
    
    def add_handler(self, channel: str, handler: Callable):
        """Add a message handler for a channel."""
        if channel not in self._message_handlers:
            self._message_handlers[channel] = []
        self._message_handlers[channel].append(handler)
    
    def remove_handler(self, channel: str, handler: Callable):
        """Remove a message handler from a channel."""
        if channel in self._message_handlers:
            self._message_handlers[channel] = [
                h for h in self._message_handlers[channel] if h != handler
            ]
    
    async def subscribe(self, *channels: str) -> bool:
        """
        Subscribe to one or more Redis channels.
        Messages will be passed to registered handlers.
        """
        if not await self._ensure_connected():
            return False
        
        try:
            if self._pubsub is None:
                self._pubsub = self._redis.pubsub()
            
            await self._pubsub.subscribe(*channels)
            logger.info(f"Subscribed to channels: {', '.join(channels)}")
            
            # Start listener task if not already running
            if not any(not t.done() for t in self._subscriber_tasks):
                task = asyncio.create_task(self._listen_for_messages())
                self._subscriber_tasks.append(task)
            
            return True
            
        except redis.RedisError as e:
            logger.error(f"Failed to subscribe: {e}")
            return False
    
    async def unsubscribe(self, *channels: str) -> bool:
        """Unsubscribe from one or more Redis channels."""
        if self._pubsub is None:
            return True
        
        try:
            await self._pubsub.unsubscribe(*channels)
            logger.info(f"Unsubscribed from channels: {', '.join(channels)}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to unsubscribe: {e}")
            return False
    
    async def _listen_for_messages(self):
        """Background task to listen for pubsub messages."""
        logger.info("Starting Redis message listener")
        
        try:
            while self._pubsub:
                try:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    
                    if message and message["type"] == "message":
                        channel = message["channel"]
                        data = message["data"]
                        
                        # Parse the event
                        try:
                            event_data = json.loads(data)
                            event = MetricsEvent(**event_data)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Failed to parse message: {e}")
                            continue
                        
                        # Call handlers for this channel
                        handlers = self._message_handlers.get(channel, [])
                        for handler in handlers:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event)
                                else:
                                    handler(event)
                            except Exception as e:
                                logger.error(f"Handler error for {channel}: {e}")
                                
                except asyncio.TimeoutError:
                    continue
                    
        except asyncio.CancelledError:
            logger.info("Message listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
    
    # ==================== Utility Methods ====================
    
    async def get_last_snapshot(self) -> Optional[NetworkTopologySnapshot]:
        """
        Get the last published topology snapshot from Redis.
        We store the latest snapshot in a Redis key for new subscribers.
        """
        if not await self._ensure_connected():
            return None
        
        try:
            data = await self._redis.get("metrics:last_snapshot")
            if data:
                return NetworkTopologySnapshot.model_validate_json(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get last snapshot: {e}")
            return None
    
    async def store_last_snapshot(self, snapshot: NetworkTopologySnapshot) -> bool:
        """Store the latest snapshot for new subscribers to retrieve."""
        if not await self._ensure_connected():
            return False
        
        try:
            await self._redis.set(
                "metrics:last_snapshot",
                snapshot.model_dump_json(),
                ex=3600  # Expire after 1 hour
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store snapshot: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """Get Redis connection information for debugging."""
        return {
            "url": REDIS_URL,
            "db": REDIS_DB,
            "connected": self.is_connected,
            "channels": list(self._message_handlers.keys())
        }


# Singleton instance
redis_publisher = RedisPublisher()
