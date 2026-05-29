"""
Correlator Agent — Correlates events with historical context to identify attack chains.
"""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from ai_engine.prompts import CORRELATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def correlator_node(state: dict, llm) -> dict:
    """Correlator agent: cross-references events and identifies campaigns."""
    triage = state.get("triage_result", {})
    events = state["raw_events"]

    # Build correlation context
    source_ips = set()
    users = set()
    hosts = set()
    for e in events:
        if e.get("source_ip"):
            source_ips.add(e["source_ip"])
        for field in ["target_user", "subject_user"]:
            if e.get(field):
                users.add(e[field])
        if e.get("hostname"):
            hosts.add(e["hostname"])

    context = (
        f"Triage Result:\n{json.dumps(triage, default=str)}\n\n"
        f"Correlation Context:\n"
        f"- Unique Source IPs: {list(source_ips)}\n"
        f"- Unique Users: {list(users)}\n"
        f"- Unique Hosts: {list(hosts)}\n"
        f"- Event Count: {len(events)}\n"
        f"- Time Span: {events[-1].get('@timestamp', 'N/A')} to {events[0].get('@timestamp', 'N/A')}\n\n"
        f"Event Categories: {_count_categories(events)}\n"
    )

    messages = [
        SystemMessage(content=CORRELATOR_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    try:
        response = await llm.ainvoke(messages)
        result = _parse_json(response.content)

        adjusted_score = result.get("adjusted_threat_score", state.get("threat_score", 50))
        adjusted_severity = result.get("adjusted_severity", state.get("severity", "MEDIUM"))

        logger.info(f"Correlator: campaign={result.get('is_campaign')}, adj_score={adjusted_score}")

        return {
            "messages": state.get("messages", []) + messages + [response],
            "correlation_result": result,
            "threat_score": adjusted_score,
            "severity": adjusted_severity,
        }
    except Exception as e:
        logger.error(f"Correlator agent error: {e}")
        return {"correlation_result": {"error": str(e)}}


def _count_categories(events: list[dict]) -> dict:
    counts = {}
    for e in events:
        cat = e.get("event_category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"error": "Parse failed", "raw": text[:500]}
