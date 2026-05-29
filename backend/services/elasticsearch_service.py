"""
Elasticsearch Service — Async client wrapper for all ES operations.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from elasticsearch import AsyncElasticsearch
from config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Manages all Elasticsearch interactions for the SOC platform."""

    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None

    async def connect(self):
        self.client = AsyncElasticsearch(
            hosts=[settings.es_url], request_timeout=30,
            max_retries=3, retry_on_timeout=True,
        )
        info = await self.client.info()
        logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
        await self._create_index_templates()

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def _create_index_templates(self):
        events_mappings = {
            "properties": {
                "@timestamp": {"type": "date"}, "event_id": {"type": "integer"},
                "event_category": {"type": "keyword"}, "hostname": {"type": "keyword"},
                "source_ip": {"type": "ip", "ignore_malformed": True},
                "target_user": {"type": "keyword"}, "subject_user": {"type": "keyword"},
                "log_channel": {"type": "keyword"}, "provider": {"type": "keyword"},
                "message": {"type": "text"}, "process_name": {"type": "keyword"},
                "command_line": {"type": "text"}, "logon_type": {"type": "integer"},
                "status": {"type": "keyword"}, "severity": {"type": "keyword"},
            }
        }
        alerts_mappings = {
            "properties": {
                "@timestamp": {"type": "date"}, "alert_id": {"type": "keyword"},
                "severity": {"type": "keyword"}, "threat_score": {"type": "integer"},
                "attack_type": {"type": "keyword"}, "hostname": {"type": "keyword"},
                "target_user": {"type": "keyword"}, "source_ip": {"type": "ip", "ignore_malformed": True},
                "confidence": {"type": "integer"}, "explanation": {"type": "text"},
                "mitre_techniques": {"type": "keyword"}, "rule_name": {"type": "keyword"},
                "acknowledged": {"type": "boolean"}, "acknowledged_by": {"type": "keyword"},
                "acknowledged_at": {"type": "date"}, "related_events": {"type": "integer"},
                "ai_analysis": {"type": "boolean"},
            }
        }
        templates = [
            ("soc-events-template", f"{settings.ES_INDEX_EVENTS}-*", events_mappings),
            ("soc-alerts-template", f"{settings.ES_INDEX_ALERTS}-*", alerts_mappings),
        ]
        for name, pattern, mappings in templates:
            try:
                await self.client.indices.put_index_template(
                    name=name,
                    body={"index_patterns": [pattern], "template": {
                        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                        "mappings": mappings
                    }}
                )
            except Exception as e:
                logger.warning(f"Template {name} issue: {e}")

    def _idx(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}"

    async def index_event(self, event: dict) -> str:
        event.setdefault("@timestamp", datetime.now(timezone.utc).isoformat())
        r = await self.client.index(index=self._idx(settings.ES_INDEX_EVENTS), document=event, refresh="wait_for")
        return r["_id"]

    async def bulk_index_events(self, events: list[dict]) -> int:
        if not events:
            return 0
        ops = []
        for e in events:
            e.setdefault("@timestamp", datetime.now(timezone.utc).isoformat())
            ops.append({"index": {"_index": self._idx(settings.ES_INDEX_EVENTS)}})
            ops.append(e)
        await self.client.bulk(operations=ops, refresh="wait_for")
        return len(events)

    async def search_events(self, query="*", time_from="now-24h", time_to="now",
                            size=100, event_category=None, hostname=None, user=None):
        must = [{"range": {"@timestamp": {"gte": time_from, "lte": time_to}}}]
        if query != "*":
            must.append({"query_string": {"query": query}})
        if event_category:
            must.append({"term": {"event_category": event_category}})
        if hostname:
            must.append({"term": {"hostname": hostname}})
        if user:
            must.append({"bool": {"should": [
                {"term": {"target_user": user}}, {"term": {"subject_user": user}}
            ]}})
        r = await self.client.search(
            index=f"{settings.ES_INDEX_EVENTS}-*",
            body={"query": {"bool": {"must": must}}, "sort": [{"@timestamp": "desc"}], "size": size}
        )
        return [{**h["_source"], "_id": h["_id"]} for h in r["hits"]["hits"]]

    async def get_recent_events(self, size=50, since=None):
        must = []
        if since:
            must.append({"range": {"@timestamp": {"gt": since}}})
        q = {"bool": {"must": must}} if must else {"match_all": {}}
        r = await self.client.search(
            index=f"{settings.ES_INDEX_EVENTS}-*",
            body={"query": q, "sort": [{"@timestamp": "desc"}], "size": size}
        )
        return [{**h["_source"], "_id": h["_id"]} for h in r["hits"]["hits"]]

    async def index_alert(self, alert: dict) -> str:
        alert.setdefault("@timestamp", datetime.now(timezone.utc).isoformat())
        alert.setdefault("acknowledged", False)
        r = await self.client.index(index=self._idx(settings.ES_INDEX_ALERTS), document=alert, refresh="wait_for")
        return r["_id"]

    async def get_alerts(self, severity=None, acknowledged=None, size=100, time_from="now-24h"):
        must = [{"range": {"@timestamp": {"gte": time_from}}}]
        if severity:
            must.append({"term": {"severity.keyword": severity}})
        if acknowledged is not None:
            must.append({"term": {"acknowledged": acknowledged}})
        r = await self.client.search(
            index=f"{settings.ES_INDEX_ALERTS}-*",
            body={"query": {"bool": {"must": must}}, "sort": [{"@timestamp": "desc"}], "size": size}
        )
        return [{**h["_source"], "_id": h["_id"], "_index": h["_index"]} for h in r["hits"]["hits"]]

    async def get_recent_alerts(self, size=10):
        """Get the most recent alerts — used by the chatbot for context."""
        try:
            r = await self.client.search(
                index=f"{settings.ES_INDEX_ALERTS}-*",
                body={
                    "query": {"match_all": {}},
                    "sort": [{"@timestamp": "desc"}],
                    "size": size,
                }
            )
            return [{**h["_source"], "_id": h["_id"]} for h in r["hits"]["hits"]]
        except Exception as e:
            logger.warning(f"get_recent_alerts failed: {e}")
            return []

    async def acknowledge_alert(self, index: str, alert_id: str, user: str) -> bool:
        try:
            await self.client.update(index=index, id=alert_id, doc={
                "acknowledged": True, "acknowledged_by": user,
                "acknowledged_at": datetime.now(timezone.utc).isoformat()
            }, refresh="wait_for")
            return True
        except Exception as e:
            logger.error(f"Ack alert failed: {e}")
            return False

    async def index_ai_analysis(self, analysis: dict) -> str:
        analysis.setdefault("@timestamp", datetime.now(timezone.utc).isoformat())
        r = await self.client.index(index=self._idx(settings.ES_INDEX_AI), document=analysis, refresh="wait_for")
        return r["_id"]

    async def get_recent_ai_analyses(self, size=20):
        try:
            r = await self.client.search(
                index=f"{settings.ES_INDEX_AI}-*",
                body={"query": {"match_all": {}}, "sort": [{"@timestamp": "desc"}], "size": size}
            )
            return [{**h["_source"], "_id": h["_id"]} for h in r["hits"]["hits"]]
        except Exception:
            return []

    async def get_dashboard_stats(self, time_from="now-24h"):
        ev_body = {
            "size": 0, "query": {"range": {"@timestamp": {"gte": time_from}}},
            "aggs": {
                "total": {"value_count": {"field": "@timestamp"}},
                "by_cat": {"terms": {"field": "event_category.keyword", "size": 20}},
                "by_host": {"terms": {"field": "hostname.keyword", "size": 10}},
                "timeline": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}},
            }
        }
        ev = await self.client.search(index=f"{settings.ES_INDEX_EVENTS}-*", body=ev_body)
        al_body = {
            "size": 0, "query": {"range": {"@timestamp": {"gte": time_from}}},
            "aggs": {
                "total": {"value_count": {"field": "@timestamp"}},
                "by_sev": {"terms": {"field": "severity.keyword"}},
                "by_type": {"terms": {"field": "attack_type.keyword", "size": 10}},
                "unack": {"filter": {"term": {"acknowledged": False}}},
                "top_users": {"terms": {"field": "target_user.keyword", "size": 10}},
                "top_hosts": {"terms": {"field": "hostname.keyword", "size": 10}},
                "avg_score": {"avg": {"field": "threat_score"}},
            }
        }
        try:
            al = await self.client.search(index=f"{settings.ES_INDEX_ALERTS}-*", body=al_body)
            al_aggs = al["aggregations"]
        except Exception:
            al_aggs = {}

        def buckets(aggs, key):
            return [{"name": b["key"], "count": b["doc_count"]} for b in aggs.get(key, {}).get("buckets", [])]

        ev_aggs = ev["aggregations"]
        return {
            "events": {
                "total": ev_aggs["total"]["value"],
                "by_category": buckets(ev_aggs, "by_cat"),
                "by_hostname": buckets(ev_aggs, "by_host"),
                "timeline": [{"time": b["key_as_string"], "count": b["doc_count"]} for b in ev_aggs["timeline"]["buckets"]],
            },
            "alerts": {
                "total": al_aggs.get("total", {}).get("value", 0),
                "by_severity": buckets(al_aggs, "by_sev"),
                "by_attack_type": buckets(al_aggs, "by_type"),
                "unacknowledged": al_aggs.get("unack", {}).get("doc_count", 0),
                "top_users": buckets(al_aggs, "top_users"),
                "top_hosts": buckets(al_aggs, "top_hosts"),
                "avg_threat_score": round(al_aggs.get("avg_score", {}).get("value", 0) or 0),
            },
        }

    async def get_severity_distribution(self, time_from="now-24h"):
        try:
            r = await self.client.search(
                index=f"{settings.ES_INDEX_ALERTS}-*",
                body={"size": 0, "query": {"range": {"@timestamp": {"gte": time_from}}},
                      "aggs": {"sev": {"terms": {"field": "severity.keyword"}}}}
            )
            return [{"severity": b["key"], "count": b["doc_count"]} for b in r["aggregations"]["sev"]["buckets"]]
        except Exception:
            return []

    async def get_attack_timeline(self, time_from="now-24h", interval="1h"):
        try:
            r = await self.client.search(
                index=f"{settings.ES_INDEX_ALERTS}-*",
                body={"size": 0, "query": {"range": {"@timestamp": {"gte": time_from}}},
                      "aggs": {"tl": {"date_histogram": {"field": "@timestamp", "fixed_interval": interval},
                                      "aggs": {"by_sev": {"terms": {"field": "severity.keyword"}}}}}}
            )
            return [{"time": b["key_as_string"], "total": b["doc_count"],
                      "severities": {s["key"]: s["doc_count"] for s in b["by_sev"]["buckets"]}}
                     for b in r["aggregations"]["tl"]["buckets"]]
        except Exception:
            return []

    async def get_mitre_heatmap(self, time_from="now-7d"):
        try:
            r = await self.client.search(
                index=f"{settings.ES_INDEX_ALERTS}-*",
                body={"size": 0, "query": {"range": {"@timestamp": {"gte": time_from}}},
                      "aggs": {"tech": {"terms": {"field": "mitre_techniques.keyword", "size": 50}}}}
            )
            return [{"technique": b["key"], "count": b["doc_count"]} for b in r["aggregations"]["tech"]["buckets"]]
        except Exception:
            return []

    async def health_check(self):
        try:
            h = await self.client.cluster.health()
            return {"status": h["status"], "cluster": h["cluster_name"], "nodes": h["number_of_nodes"]}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}


es_service = ElasticsearchService()
