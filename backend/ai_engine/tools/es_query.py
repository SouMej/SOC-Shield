"""
ES Query Tool — LangChain tool for querying Elasticsearch for event correlation.
"""
import logging

logger = logging.getLogger(__name__)


async def query_related_events(es_service, source_ip=None, user=None,
                                hostname=None, time_window="30m", size=50):
    """Query Elasticsearch for events related to the current analysis."""
    must = [{"range": {"@timestamp": {"gte": f"now-{time_window}"}}}]

    if source_ip:
        must.append({"term": {"source_ip": source_ip}})
    if user:
        must.append({"bool": {"should": [
            {"term": {"target_user": user}},
            {"term": {"subject_user": user}}
        ]}})
    if hostname:
        must.append({"term": {"hostname": hostname}})

    try:
        result = await es_service.client.search(
            index="soc-events-*",
            body={
                "query": {"bool": {"must": must}},
                "sort": [{"@timestamp": "desc"}],
                "size": size
            }
        )
        return [{**h["_source"], "_id": h["_id"]} for h in result["hits"]["hits"]]
    except Exception as e:
        logger.error(f"ES query tool error: {e}")
        return []


async def count_failed_logins(es_service, source_ip=None, user=None, time_window="5m"):
    """Count failed login attempts in a time window."""
    must = [
        {"range": {"@timestamp": {"gte": f"now-{time_window}"}}},
        {"term": {"event_id": 4625}}
    ]
    if source_ip:
        must.append({"term": {"source_ip": source_ip}})
    if user:
        must.append({"term": {"target_user": user}})

    try:
        result = await es_service.client.count(
            index="soc-events-*",
            body={"query": {"bool": {"must": must}}}
        )
        return result["count"]
    except Exception as e:
        logger.error(f"Count failed logins error: {e}")
        return 0
