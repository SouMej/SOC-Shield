"""
SOC Platform — FastAPI Main Entry Point

Ties together: Elasticsearch, AI Engine, WebSocket streaming,
log simulation, detection rules, and API routes.
"""
import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware import RateLimitMiddleware

from config import settings
from services.elasticsearch_service import es_service
from services.log_simulator import LogSimulator
from websocket.manager import ws_manager
from detection_rules.rule_engine import rule_engine
from ai_engine.graph import build_graph, analyze_events
from api.routes_dashboard import router as dashboard_router
from api.routes_alerts import router as alerts_router
from api.routes_search import router as search_router
from api.routes_chatbot import router as chatbot_router
from services.kafka_consumer import kafka_consumer_service

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("soc-platform")

# Global references
simulator = None
ai_graph = None
ai_task = None
sim_task = None


async def ai_analysis_loop():
    """Fallback: poll ES for new events and run rule engine + AI analysis.
    Only used when Kafka is NOT available."""
    global ai_graph
    last_timestamp = None
    event_buffer = []
    rate_limit_cooldown_until = 0

    while True:
        try:
            await asyncio.sleep(settings.AI_POLL_INTERVAL)

            # Fetch new events since last check
            events = await es_service.get_recent_events(
                size=50, since=last_timestamp
            )
            if not events:
                continue

            last_timestamp = events[0].get("@timestamp")
            event_buffer.extend(events)

            # 1) Run rule-based detection (always runs — no API cost)
            rule_matches = rule_engine.evaluate_batch(events)
            for match in rule_matches:
                alert_dict = match.to_alert_dict()
                await es_service.index_alert(alert_dict)
                await ws_manager.broadcast({
                    "type": "alert",
                    "data": alert_dict,
                })
                logger.info(f"Rule alert: {match.rule_name} — {match.attack_type}")

            # 2) Run AI analysis (if graph available and not rate limited)
            now = time.time()
            if now < rate_limit_cooldown_until:
                remaining = int(rate_limit_cooldown_until - now)
                if len(event_buffer) % 50 == 0:  # Log occasionally
                    logger.info(f"AI Agent paused (rate limit cooldown: {remaining}s remaining). Buffer: {len(event_buffer)} events")
                continue

            if ai_graph and (rule_matches or len(event_buffer) >= settings.AI_BATCH_SIZE):
                logger.info(f"Triggering AI Agent. Buffer size: {len(event_buffer)}, Rules fired: {len(rule_matches)}")
                result = await analyze_events(ai_graph, event_buffer, es_service)

                if result and result.get("rate_limited"):
                    rate_limit_cooldown_until = time.time() + 120  # Back off 2 minutes
                    logger.warning("⏸ Groq rate limited — AI Agent paused for 120 seconds")
                elif result and result.get("should_alert"):
                    await ws_manager.broadcast({
                        "type": "ai_alert",
                        "data": result,
                    })
                # Clear buffer after processing
                event_buffer = []

        except Exception as e:
            logger.error(f"AI analysis loop error: {e}")
            event_buffer = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    global simulator, ai_graph, ai_task, sim_task

    logger.info("=" * 60)
    logger.info("  SOC Threat Detection Platform Starting...")
    logger.info("=" * 60)

    # Connect to Elasticsearch
    try:
        await es_service.connect()
        logger.info("✓ Elasticsearch connected")
    except Exception as e:
        logger.warning(f"✗ Elasticsearch connection failed: {e}")
        logger.warning("  Platform will start without ES — some features unavailable")

    # Build AI graph
    try:
        ai_graph = build_graph()
        if ai_graph:
            logger.info("✓ AI Engine (LangGraph + Groq) initialized")
        else:
            logger.warning("✗ AI Engine not available (check GROQ_API_KEY)")
    except Exception as e:
        logger.warning(f"✗ AI Engine init failed: {e}")

    # Start Redis listener for WebSockets (non-blocking — falls back to local broadcast)
    redis_task = asyncio.create_task(ws_manager.start_redis_listener())

    # Try to start Kafka Consumer
    kafka_started = await kafka_consumer_service.start(ai_graph)

    # Start log simulator (if enabled)
    if settings.SIMULATOR_ENABLED:
        try:
            simulator = LogSimulator(es_service)
            sim_task = asyncio.create_task(
                simulator.start(interval=settings.SIMULATOR_INTERVAL)
            )
            logger.info("✓ Log simulator started")
        except Exception as e:
            logger.warning(f"✗ Log simulator failed: {e}")

    # If Kafka is NOT available, fall back to the ES polling loop
    if not kafka_started:
        ai_task = asyncio.create_task(ai_analysis_loop())
        logger.info("✓ AI analysis loop started (ES polling fallback)")
    else:
        logger.info("✓ AI analysis via Kafka consumer (event-driven)")

    logger.info("=" * 60)
    logger.info(f"  Dashboard: http://localhost:5173")
    logger.info(f"  API: http://localhost:{settings.PORT}/docs")
    logger.info(f"  WebSocket: ws://localhost:{settings.PORT}/api/alerts/stream")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down SOC Platform...")
    if simulator:
        await simulator.stop()
    await kafka_consumer_service.stop()
    if ai_task:
        ai_task.cancel()
    if sim_task:
        sim_task.cancel()
    await es_service.disconnect()
    logger.info("SOC Platform stopped.")


# Create FastAPI app
app = FastAPI(
    title="SOC Threat Detection Platform",
    description="AI-Powered Active Directory Threat Detection & Response",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)

# Register routers
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(search_router)
app.include_router(chatbot_router)


@app.get("/")
async def root():
    return {
        "name": "SOC Threat Detection Platform",
        "version": "1.0.0",
        "status": "running",
        "ws_clients": ws_manager.client_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
