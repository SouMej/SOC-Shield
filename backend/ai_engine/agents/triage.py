"""
Triage Agent — Classifies attack type, assigns threat scores, maps to MITRE.
"""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from ai_engine.prompts import TRIAGE_SYSTEM_PROMPT
from services.rag_service import rag_service

logger = logging.getLogger(__name__)


async def triage_node(state: dict, llm) -> dict:
    """Triage agent: detailed classification of suspicious events."""
    events = state["raw_events"]
    supervisor_result = state.get("triage_result", {})

    event_detail = _format_events_detailed(events)
    
    # RAG: Recherche de contexte pour enrichir l'analyse
    queries_for_rag = [e.get('command_line') for e in events if e.get('command_line')]
    rag_context = ""
    if queries_for_rag:
        try:
            rag_results = rag_service.search(queries_for_rag[0], k=2)
            if rag_results:
                rag_context = "\n\nRAG Knowledge Base context (MITRE):\n" + "\n".join([r["text"] for r in rag_results])
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")

    context = (
        f"The Supervisor flagged this batch as suspicious.\n"
        f"Supervisor findings: {json.dumps(supervisor_result, default=str)}\n\n"
        f"Full event details ({len(events)} events):\n{event_detail}"
        f"{rag_context}"
    )

    messages = [
        SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    try:
        response = await llm.ainvoke(messages)
        result = _parse_json(response.content)

        score = result.get("threat_score", state.get("threat_score", 50))
        severity = result.get("severity", state.get("severity", "MEDIUM"))
        mitre = result.get("mitre_techniques", [])

        logger.info(f"Triage: type={result.get('attack_type')}, score={score}, mitre={mitre}")

        return {
            "messages": state.get("messages", []) + messages + [response],
            "triage_result": result,
            "threat_score": score,
            "severity": severity,
            "attack_type": result.get("attack_type", state.get("attack_type", "Unknown")),
            "mitre_techniques": mitre,
            "should_alert": score >= 40,
        }
    except Exception as e:
        logger.error(f"Triage agent error: {e}")
        return {"triage_result": {"error": str(e)}}


def _format_events_detailed(events: list[dict]) -> str:
    lines = []
    for i, e in enumerate(events[:25]):
        parts = [f"[{i+1}] EventID={e.get('event_id')} | Cat={e.get('event_category')} | "
                 f"Host={e.get('hostname')} | User={e.get('target_user', e.get('subject_user', 'N/A'))} | "
                 f"SrcIP={e.get('source_ip', 'N/A')} | Time={e.get('@timestamp')}"]
        if e.get("command_line"):
            parts.append(f"    CMD: {e['command_line'][:200]}")
        if e.get("failure_reason"):
            parts.append(f"    Failure: {e['failure_reason']}")
        if e.get("logon_type"):
            parts.append(f"    LogonType: {e['logon_type']}")
        lines.append("\n".join(parts))
    return "\n".join(lines)


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
