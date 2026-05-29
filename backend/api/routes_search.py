"""
Search API Routes — Log search and event browsing.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from services.elasticsearch_service import es_service

router = APIRouter(prefix="/api/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str = "*"
    time_from: str = "now-24h"
    time_to: str = "now"
    size: int = 100
    event_category: Optional[str] = None
    hostname: Optional[str] = None
    user: Optional[str] = None


@router.post("")
async def search_events(req: SearchRequest):
    """Full-text search across security events."""
    return await es_service.search_events(
        query=req.query, time_from=req.time_from, time_to=req.time_to,
        size=req.size, event_category=req.event_category,
        hostname=req.hostname, user=req.user,
    )


@router.get("/recent")
async def get_recent_events(
    size: int = Query(default=50, le=200),
    since: str = Query(default=None),
):
    """Get the most recent security events."""
    return await es_service.get_recent_events(size=size, since=since)


@router.get("/categories")
async def get_event_categories():
    """Get list of available event categories."""
    return [
        "authentication_success", "authentication_failure",
        "privilege_escalation", "process_creation",
        "account_management", "kerberos_activity",
        "service_creation", "sysmon_process_create",
        "sysmon_network_connect", "other",
    ]
