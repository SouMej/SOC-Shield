"""
Kafka Consumer Service — Consumes log events from Kafka for real-time processing.
Falls back gracefully if Kafka is not available (the old polling loop takes over).
"""
import asyncio
import json
import logging
import time

from config import settings
from services.elasticsearch_service import es_service
from detection_rules.rule_engine import rule_engine
from ai_engine.graph import analyze_events
from websocket.manager import ws_manager

logger = logging.getLogger(__name__)

# Try importing Kafka, but make it optional
try:
    from aiokafka import AIOKafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


class KafkaConsumerService:
    def __init__(self):
        self.consumer = None
        self.is_running = False
        self.buffer = []
        self._use_kafka = False

    async def start(self, ai_graph):
        """Try to connect to Kafka. If unavailable, log a warning and return False."""
        if not KAFKA_AVAILABLE:
            logger.info("Kafka library not installed — Kafka consumer disabled")
            return False

        try:
            self.consumer = AIOKafkaConsumer(
                'soc-logs',
                bootstrap_servers='soc-kafka:9092',
                group_id="soc-backend-group",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset="latest"
            )
            await self.consumer.start()
            self.is_running = True
            self._use_kafka = True
            logger.info("✓ Kafka Consumer started on topic 'soc-logs'")
            asyncio.create_task(self.consume_loop(ai_graph))
            return True
        except Exception as e:
            logger.warning(f"✗ Kafka not available ({e}) — using ES polling fallback")
            self.consumer = None
            self._use_kafka = False
            return False

    async def consume_loop(self, ai_graph):
        rate_limit_cooldown = 0
        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                event = msg.value
                self.buffer.append(event)
                
                # Index the raw event to ES (since simulator sends to Kafka)
                try:
                    await es_service.index_event(event)
                except Exception as e:
                    logger.error(f"Failed to index event to ES: {e}")
                
                # Rule Engine Analysis (Synchronous, Low Latency)
                # We evaluate the entire buffer so multi-event rules (e.g. Brute Force) can trigger
                rule_matches = rule_engine.evaluate_batch(self.buffer)
                for match in rule_matches:
                    alert = match.to_alert_dict()
                    await es_service.index_alert(alert)
                    await ws_manager.broadcast({"type": "alert", "data": alert})
                    logger.info(f"Rule alert: {match.rule_name} — {match.attack_type}")

                # AI Engine Analysis (Batching)
                if len(self.buffer) >= settings.AI_BATCH_SIZE or rule_matches:
                    now = time.time()
                    if now >= rate_limit_cooldown and ai_graph:
                        result = await analyze_events(ai_graph, self.buffer, es_service)
                        if result and result.get("rate_limited"):
                            rate_limit_cooldown = time.time() + 120
                        elif result and result.get("should_alert"):
                            await ws_manager.broadcast({"type": "ai_alert", "data": result})
                    self.buffer.clear()
        except Exception as e:
            logger.error(f"Kafka consume loop error: {e}")

    @property
    def is_active(self):
        return self._use_kafka and self.is_running

    async def stop(self):
        self.is_running = False
        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info("Kafka Consumer stopped.")
            except Exception:
                pass

kafka_consumer_service = KafkaConsumerService()
