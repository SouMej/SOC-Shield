"""
Dashboard API Routes — Aggregated stats, charts, and overview data.
"""
from fastapi import APIRouter, Query
from services.elasticsearch_service import es_service
from ai_engine.tools.mitre_lookup import get_heatmap_data, get_all_techniques

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(time_from: str = Query(default="now-24h")):
    """Get aggregated dashboard statistics."""
    return await es_service.get_dashboard_stats(time_from=time_from)


@router.get("/severity-distribution")
async def get_severity_distribution(time_from: str = Query(default="now-24h")):
    """Get alert severity distribution for charts."""
    return await es_service.get_severity_distribution(time_from=time_from)


@router.get("/attack-timeline")
async def get_attack_timeline(
    time_from: str = Query(default="now-24h"),
    interval: str = Query(default="1h"),
):
    """Get attack events over time for timeline chart."""
    return await es_service.get_attack_timeline(time_from=time_from, interval=interval)


@router.get("/mitre-heatmap")
async def get_mitre_heatmap(time_from: str = Query(default="now-7d")):
    """Get MITRE ATT&CK heatmap data."""
    es_data = await es_service.get_mitre_heatmap(time_from=time_from)
    # Merge ES data with static MITRE data
    technique_counts = {item["technique"]: item["count"] for item in es_data}
    heatmap = get_heatmap_data()
    for tactic in heatmap:
        for tech in tactic["techniques"]:
            tech["count"] = technique_counts.get(tech["id"], 0)
    return heatmap


@router.get("/mitre-techniques")
async def get_mitre_techniques():
    """Get all MITRE ATT&CK techniques."""
    return get_all_techniques()


@router.get("/ai-analyses")
async def get_ai_analyses(size: int = Query(default=20, le=100)):
    """Get recent AI analysis results."""
    return await es_service.get_recent_ai_analyses(size=size)


@router.get("/health")
async def health_check():
    """Check system health."""
    es_health = await es_service.health_check()
    return {
        "status": "ok" if es_health.get("status") in ("green", "yellow") else "degraded",
        "elasticsearch": es_health,
    }
