"""
WebSocket Connection Manager — Handles real-time streaming to dashboard clients.
Supports Redis Pub/Sub when available, falls back to direct local broadcast.
"""
import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Try importing redis, but make it optional
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ConnectionManager:
    """Manages WebSocket connections and broadcasts alerts.
    Uses Redis Pub/Sub when available for horizontal scalability,
    falls back to direct local broadcast otherwise."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._redis = None
        self._pubsub = None
        self._use_redis = False

    async def _init_redis(self):
        """Try to connect to Redis. Non-blocking — if it fails, we just use local broadcast."""
        if not REDIS_AVAILABLE:
            logger.info("Redis library not installed — using direct WebSocket broadcast")
            return
        try:
            self._redis = aioredis.Redis(host='localhost', port=6379, decode_responses=True)
            await self._redis.ping()
            self._pubsub = self._redis.pubsub()
            self._use_redis = True
            logger.info("✓ Redis connected — WebSocket Pub/Sub enabled")
        except Exception as e:
            logger.warning(f"✗ Redis not available ({e}) — using direct WebSocket broadcast")
            self._redis = None
            self._pubsub = None
            self._use_redis = False

    async def start_redis_listener(self):
        """Starts a background task to listen to Redis and broadcast to local WS clients."""
        await self._init_redis()
        if not self._use_redis:
            return  # Nothing to listen to, broadcast() will go direct
        await self._pubsub.subscribe("soc_alerts")
        logger.info("Subscribed to Redis channel: soc_alerts")
        while True:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self._local_broadcast(message['data'])
            except Exception as e:
                logger.error(f"Redis listener error: {e}")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send a message to all connected clients.
        If Redis is available, publish via Pub/Sub (supports horizontal scaling).
        Otherwise, broadcast directly to local connections."""
        payload = json.dumps(message, default=str)
        if self._use_redis:
            try:
                await self._redis.publish("soc_alerts", payload)
            except Exception as e:
                logger.error(f"Redis publish error: {e}, falling back to local broadcast")
                await self._local_broadcast(payload)
        else:
            await self._local_broadcast(payload)

    async def _local_broadcast(self, payload: str):
        """Broadcast a message directly to all locally connected clients."""
        if not self.active_connections:
            return
        disconnected = []
        async with self._lock:
            for conn in self.active_connections:
                try:
                    await conn.send_text(payload)
                except Exception:
                    disconnected.append(conn)
        for conn in disconnected:
            await self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            await self.disconnect(websocket)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)


ws_manager = ConnectionManager()
