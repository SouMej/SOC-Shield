"""
Supervisor Agent — Orchestrator that performs initial pre-filtering of event batches.
"""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from ai_engine.prompts import SUPERVISOR_SYSTEM_PROMPT
from ai_engine.state import ThreatAnalysisState

logger = logging.getLogger(__name__)


async def supervisor_node(state: ThreatAnalysisState, llm) -> dict:
    """Supervisor agent: initial triage and routing decision."""
    events = state["raw_events"]
    event_summary = _summarize_events(events)

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this batch of {len(events)} security events:\n\n{event_summary}")
    ]

    try:
        response = await llm.ainvoke(messages)
        result = _parse_json(response.content)

        is_suspicious = result.get("is_suspicious", False)
        initial_score = result.get("initial_score", 0)
        severity = result.get("initial_severity", "INFO")

        logger.info(f"Supervisor: suspicious={is_suspicious}, score={initial_score}, type={result.get('suspected_attack_type')}")

        return {
            "messages": messages + [response],
            "threat_score": initial_score,
            "severity": severity,
            "attack_type": result.get("suspected_attack_type", "Unknown"),
            "should_alert": is_suspicious,
            "triage_result": result,
        }
    except Exception as e:
        logger.error(f"Supervisor agent error: {e}")
        return {
            "threat_score": 0,
            "severity": "INFO",
            "attack_type": "Error",
            "should_alert": False,
            "triage_result": {"error": str(e)},
        }


def _summarize_events(events: list[dict]) -> str:
    """Create a concise text summary of events for the LLM."""
    lines = []
    for i, e in enumerate(events[:50]):  # Summarize up to 50 events
        parts = [
            f"Event {i+1}:",
            f"  EventID={e.get('event_id', '?')}",
            f"  Category={e.get('event_category', '?')}",
            f"  Host={e.get('hostname', '?')}",
            f"  User={e.get('target_user', e.get('subject_user', '?'))}",
            f"  SourceIP={e.get('source_ip', '?')}",
            f"  Time={e.get('@timestamp', '?')}",
        ]
        if e.get("command_line"):
            parts.append(f"  CommandLine={e['command_line'][:200]}")
        if e.get("message"):
            parts.append(f"  Message={e['message'][:150]}")
        if e.get("failure_reason"):
            parts.append(f"  FailureReason={e['failure_reason']}")
        if e.get("logon_type"):
            parts.append(f"  LogonType={e['logon_type']}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"error": "Failed to parse LLM response", "raw": text[:500]}
